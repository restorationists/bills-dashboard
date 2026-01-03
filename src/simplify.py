#!/usr/bin/env python3
"""
dedupe_simplify.py (deduping + related)

Reads bills.json (snake_case output from download_bills.py) and produces:
- bills_simplified.json
- bills_simplified.csv

Deduping rule:
- Bills are grouped by normalized short_title (internally via MD5).
- For each group, keep the record with the HIGHEST bill_id as canonical.
- Add `related: [dupe_id, dupe_id, ...]` to canonical JSON record containing the
  other bill_ids in that group (sorted ascending).

Output fields (and ONLY these):
JSON item fields:
  bill_id
  house                (originating_house)
  short_title
  long_title
  member_id
  member_name
  party
  constituency         (member_from)
  related              (list[int])

CSV fields:
  bill_id
  house
  short_title
  long_title
  member_id
  member_name
  party
  constituency
  related              (JSON string list)

NOTE:
- short_title_md5 and duplicated are NOT included anywhere in outputs.
- Sponsor selection: first sponsor with a member object on the canonical bill.
"""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def normalize_title(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name


def md5_hex(s: str) -> str:
    # internal only; not output
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def first_member_sponsor(bill: Dict[str, Any]) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    """
    Returns (member_id, member_name, party, constituency) from first sponsor that has a member.
    If none, returns (None, None, None, None).
    """
    sponsors = bill.get("sponsors")
    if not isinstance(sponsors, list):
        return None, None, None, None

    for sp in sponsors:
        if not isinstance(sp, dict):
            continue
        mem = sp.get("member")
        if isinstance(mem, dict):
            return (
                mem.get("member_id"),
                mem.get("name"),
                mem.get("party"),
                mem.get("member_from"),
            )

    return None, None, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="bills.json")
    ap.add_argument("--json", dest="json_path", default="bills_simplified.json")
    ap.add_argument("--csv", dest="csv_path", default="bills_simplified.csv")
    args = ap.parse_args()

    with open(args.in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items: List[Dict[str, Any]] = data.get("items", [])

    # 1) Group by normalized short_title (internally hashed)
    groups: Dict[str, List[Dict[str, Any]]] = {}

    for bill in items:
        bill_id = bill.get("bill_id")
        if bill_id is None:
            continue
        title = str(bill.get("short_title") or "")
        key = md5_hex(normalize_title(title))
        groups.setdefault(key, []).append(bill)

    # 2) For each group, select canonical (highest bill_id), add related ids
    simplified: List[Dict[str, Any]] = []

    for _, bills in groups.items():
        # sort by bill_id numeric
        bills_sorted = sorted(bills, key=lambda b: int(b.get("bill_id") or -1))
        canonical = bills_sorted[-1]  # highest bill_id
        canonical_id = int(canonical.get("bill_id"))

        related_ids = [int(b.get("bill_id")) for b in bills_sorted[:-1] if b.get("bill_id") is not None]
        # Keep related sorted ascending for stability
        related_ids.sort()

        member_id, member_name, party, constituency = first_member_sponsor(canonical)

        simplified.append(
            {
                "bill_id": canonical_id,
                "house": canonical.get("originating_house") or "",
                "short_title": canonical.get("short_title") or "",
                "long_title": canonical.get("long_title") or "",
                "member_id": member_id,
                "member_name": member_name,
                "party": party,
                "constituency": constituency,
                "related": related_ids,
            }
        )

    # 3) Stable output ordering: by bill_id descending (optional but handy)
    simplified.sort(key=lambda r: int(r["bill_id"]), reverse=True)

    out_json = {
        "generated_at": utc_now(),
        "source": args.in_path,
        "count": len(simplified),
        "items": simplified,
    }

    with open(args.json_path, "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)

    # 4) CSV (exact requested fields; related as JSON string)
    fieldnames = [
        "bill_id",
        "house",
        "short_title",
        "long_title",
        "member_id",
        "member_name",
        "party",
        "constituency",
        "related",
    ]

    with open(args.csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in simplified:
            csv_row = dict(row)
            csv_row["related"] = json.dumps(row["related"], ensure_ascii=False)
            w.writerow(csv_row)

    print(f"Wrote JSON: {args.json_path} ({len(simplified)} items)")
    print(f"Wrote CSV:  {args.csv_path} ({len(simplified)} rows)")


if __name__ == "__main__":
    main()
