#!/usr/bin/env python3
"""
download_bills.py (cached)

Downloads *all* bills by:
  1) paging the index endpoint:
     GET /api/v1/Bills?CurrentHouse=All&OriginatingHouse=All&Skip=...&Take=...
  2) for each bill_id, fetching details:
     GET /api/v1/Bills/{bill_id}

Caching:
- Detail cache: cache/bills/{bill_id}.json
- Index cache (optional): cache/index/skip_{skip}_take_{take}.json
- On rerun, only fetches details that are missing from cache.

Outputs (snake_case):
- bills.json
- bills.csv (flattened + raw_json)

Resiliency:
- retries on DNS/timeout/429/5xx with exp backoff + jitter
- continues on per-bill failure (detail_ok=0 + detail_error)

Install:
  pip install requests

Run:
  python3 download_bills.py --take 200 --workers 16 --debug
  python3 download_bills.py --take 200 --workers 16 --debug --cache-dir cache --cache-index
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException

INDEX_URL = "https://bills-api.parliament.uk/api/v1/Bills"
DETAIL_URL_TPL = "https://bills-api.parliament.uk/api/v1/Bills/{bill_id}"


# ----------------------------
# logging
# ----------------------------

def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def log(msg: str, debug: bool) -> None:
    if debug:
        print(f"[{utc_now()}] {msg}", flush=True)


def elog(msg: str) -> None:
    print(f"[{utc_now()}] {msg}", file=sys.stderr, flush=True)


# ----------------------------
# helpers
# ----------------------------

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "uk-bills-downloader/3.0", "Accept": "application/json"})
    return s


def normalize_title(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def to_snake_case_key(k: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", k)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def snake_case_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out[to_snake_case_key(str(k))] = snake_case_obj(v)
        return out
    if isinstance(obj, list):
        return [snake_case_obj(x) for x in obj]
    return obj


def flatten_json(obj: Any, prefix: str = "", out: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if out is None:
        out = {}
    sep = "__"

    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}{sep}{k}" if prefix else str(k)
            flatten_json(v, key, out)
    elif isinstance(obj, list):
        out[prefix] = json.dumps(obj, ensure_ascii=False)
    else:
        out[prefix] = obj
    return out


# ----------------------------
# caching
# ----------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        return None


def write_json_file(path: str, data: Any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def bill_cache_path(cache_dir: str, bill_id: int) -> str:
    return os.path.join(cache_dir, "bills", f"{bill_id}.json")


def index_cache_path(cache_dir: str, skip: int, take: int) -> str:
    return os.path.join(cache_dir, "index", f"skip_{skip}_take_{take}.json")


# ----------------------------
# resilient request
# ----------------------------

def request_json_with_retries(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, Any]],
    timeout: int,
    max_retries: int,
    debug: bool,
) -> Any:
    attempt = 0
    backoff = 0.75

    while True:
        attempt += 1
        try:
            r = session.get(url, params=params, timeout=timeout)

            if r.status_code == 429 or 500 <= r.status_code <= 599:
                if attempt <= max_retries:
                    wait = backoff * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
                    log(f"RETRY {attempt}/{max_retries} HTTP {r.status_code} wait={wait:.2f}s url={r.url}", debug)
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"HTTP {r.status_code} after retries for {r.url}: {r.text[:300]}")

            if r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code} for {r.url}: {r.text[:300]}")

            return r.json()

        except RequestException as e:
            if attempt <= max_retries:
                wait = backoff * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
                log(f"RETRY {attempt}/{max_retries} EXC {type(e).__name__}: {e} wait={wait:.2f}s", debug)
                time.sleep(wait)
                continue
            raise


# ----------------------------
# index + details (with caching)
# ----------------------------

def fetch_index_all(
    take: int,
    timeout: int,
    max_retries: int,
    sleep_pages: float,
    debug: bool,
    cache_dir: str,
    cache_index: bool,
) -> List[Dict[str, Any]]:
    s = make_session()
    ensure_dir(os.path.join(cache_dir, "index"))

    skip = 0
    page = 0
    all_items: List[Dict[str, Any]] = []
    total: Optional[int] = None

    while True:
        page += 1
        params = {"CurrentHouse": "All", "OriginatingHouse": "All", "Skip": skip, "Take": take}

        cached_payload = None
        if cache_index:
            cpath = index_cache_path(cache_dir, skip, take)
            cached_payload = read_json_file(cpath)
            if cached_payload is not None:
                log(f"INDEX cache hit page={page} skip={skip}", debug)

        if cached_payload is None:
            log(f"INDEX fetch page={page} skip={skip} take={take}", debug)
            payload = request_json_with_retries(
                s, INDEX_URL, params=params, timeout=timeout, max_retries=max_retries, debug=debug
            )
            if cache_index:
                write_json_file(index_cache_path(cache_dir, skip, take), payload)
        else:
            payload = cached_payload

        items = payload.get("items") or []
        if total is None and payload.get("totalResults") is not None:
            total = int(payload["totalResults"])
            log(f"INDEX total_results={total}", debug)

        log(f"INDEX got_items={len(items)} downloaded={len(all_items)}", debug)

        if not items:
            break

        all_items.extend(items)
        skip += take

        if total is not None and len(all_items) >= total:
            break

        if sleep_pages:
            time.sleep(sleep_pages)

    log(f"INDEX DONE count={len(all_items)}", debug)
    return all_items


def fetch_detail_cached(
    bill_id: int,
    timeout: int,
    max_retries: int,
    debug: bool,
    cache_dir: str,
) -> Tuple[int, Dict[str, Any], bool]:
    """
    Returns (bill_id, detail_payload, from_cache)
    """
    ensure_dir(os.path.join(cache_dir, "bills"))
    cpath = bill_cache_path(cache_dir, bill_id)

    cached = read_json_file(cpath)
    if cached is not None:
        return bill_id, cached, True

    # fetch (thread-local session)
    s = make_session()
    url = DETAIL_URL_TPL.format(bill_id=bill_id)
    payload = request_json_with_retries(
        s, url, params=None, timeout=timeout, max_retries=max_retries, debug=debug
    )
    # save to cache immediately
    write_json_file(cpath, payload)
    return bill_id, payload, False


# ----------------------------
# main
# ----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", type=int, default=200)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--sleep-pages", type=float, default=0.0)
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--json", dest="json_path", default="bills.json")
    ap.add_argument("--csv", dest="csv_path", default="bills.csv")
    ap.add_argument("--max-bills", type=int, default=None, help="testing only")
    ap.add_argument("--cache-dir", type=str, default="cache")
    ap.add_argument("--cache-index", action="store_true", help="also cache index pages")
    args = ap.parse_args()

    ensure_dir(args.cache_dir)
    ensure_dir(os.path.join(args.cache_dir, "bills"))
    ensure_dir(os.path.join(args.cache_dir, "index"))

    # 1) index
    index_items = fetch_index_all(
        take=args.take,
        timeout=args.timeout,
        max_retries=args.max_retries,
        sleep_pages=args.sleep_pages,
        debug=args.debug,
        cache_dir=args.cache_dir,
        cache_index=args.cache_index,
    )
    if args.max_bills is not None:
        index_items = index_items[: args.max_bills]
        log(f"TEST MODE max_bills={args.max_bills}", args.debug)

    bill_ids = [int(it["billId"]) for it in index_items if it.get("billId") is not None]
    log(f"DETAIL start count={len(bill_ids)} workers={args.workers}", args.debug)

    detail_by_id: Dict[int, Dict[str, Any]] = {}
    started = time.time()
    cache_hits = 0
    fetched = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(fetch_detail_cached, bid, args.timeout, args.max_retries, args.debug, args.cache_dir): bid
            for bid in bill_ids
        }

        done = 0
        try:
            for fut in as_completed(futures):
                bid = futures[fut]
                try:
                    bill_id, det, from_cache = fut.result()
                    detail_by_id[bill_id] = det
                    if from_cache:
                        cache_hits += 1
                    else:
                        fetched += 1
                except Exception as e:
                    detail_by_id[bid] = {"detail_ok": 0, "detail_error": str(e)}
                    elog(f"DETAIL error bill_id={bid}: {e}")

                done += 1
                if args.debug and (done % 200 == 0 or done == len(futures)):
                    rate = done / max(0.001, (time.time() - started))
                    log(
                        f"DETAIL progress {done}/{len(futures)} rate={rate:.2f} bills/sec "
                        f"(cache_hits={cache_hits}, fetched={fetched})",
                        args.debug,
                    )

        except KeyboardInterrupt:
            elog("Ctrl+C received during detail fetch. Writing partial outputs…")

    # 2) merge (detail wins), snake_case
    merged_items: List[Dict[str, Any]] = []
    for idx in index_items:
        bid = idx.get("billId")
        if bid is None:
            continue
        bid = int(bid)
        det = detail_by_id.get(bid, {"detail_ok": 0, "detail_error": "missing_detail"})
        merged = dict(idx)
        merged.update(det)
        merged_snake = snake_case_obj(merged)
        if "detail_ok" not in merged_snake:
            merged_snake["detail_ok"] = 1
        merged_items.append(merged_snake)

    # 3) md5 + duplicates (short_title)
    seen = set()
    for rec in merged_items:
        title = str(rec.get("short_title") or "")
        h = md5_hex(normalize_title(title))
        rec["short_title_md5"] = h
        rec["duplicated"] = 1 if h in seen else 0
        if rec["duplicated"] == 0:
            seen.add(h)

    # 4) JSON
    out_json = {
        "downloaded_at": utc_now(),
        "index_endpoint": INDEX_URL,
        "detail_endpoint_template": DETAIL_URL_TPL,
        "count": len(merged_items),
        "items": merged_items,
        "cache": {
            "cache_dir": args.cache_dir,
            "detail_cache_hits": cache_hits,
            "detail_fetched": fetched,
        },
    }
    with open(args.json_path, "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)
    print(f"Wrote JSON: {args.json_path} ({len(merged_items)} records)", flush=True)

    # 5) CSV flatten + raw_json
    flat_rows: List[Dict[str, Any]] = []
    cols = set()

    for rec in merged_items:
        flat = flatten_json(rec)
        flat["raw_json"] = json.dumps(rec, ensure_ascii=False)
        flat_rows.append(flat)
        cols.update(flat.keys())

    preferred = [
        "bill_id",
        "short_title",
        "short_title_md5",
        "duplicated",
        "originating_house",
        "current_house",
        "last_update",
        "long_title",
        "summary",
        "detail_ok",
        "detail_error",
        "raw_json",
    ]
    ordered_cols = [c for c in preferred if c in cols] + [c for c in sorted(cols) if c not in preferred]

    with open(args.csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ordered_cols, extrasaction="ignore")
        w.writeheader()
        for row in flat_rows:
            w.writerow(row)

    print(
        f"Wrote CSV:  {args.csv_path} ({len(flat_rows)} rows, {len(ordered_cols)} cols) "
        f"| cache_hits={cache_hits} fetched={fetched}",
        flush=True,
    )


if __name__ == "__main__":
    main()
