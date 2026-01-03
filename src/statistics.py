#!/usr/bin/env python3
"""
statistics.py

Compute summary statistics from bills.json (snake_case output).

Outputs statistics.json with:
- bills by originating house / current house
- bills by party (from sponsor members)
- bills by member (from sponsor members)
- bills by bill_type_id
- bills by introduced_session_id
- bills by current stage
- bills by year / year-month (last_update)
- sponsor count distributions
- data quality metrics

Run:
  python3 statistics.py --in bills.json --out statistics.json --top 50
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


def safe_str(x: Any) -> str:
    return "" if x is None else str(x).strip()


def parse_dt(value: Any) -> Optional[datetime]:
    """
    Robust ISO datetime parser for API timestamps like:
      2025-09-16T17:08:18.2184786
      2025-09-16T17:08:18Z
    """
    if not value:
        return None

    text = str(value).strip().replace("Z", "")
    try:
        if "." in text:
            head, frac = text.split(".", 1)
            frac = "".join(ch for ch in frac if ch.isdigit())
            frac = (frac + "000000")[:6]
            text = f"{head}.{frac}"
        return datetime.fromisoformat(text)
    except Exception:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d")
        except Exception:
            return None


def top_n(counter: Counter, n: int) -> List[Dict[str, Any]]:
    return [{"key": k, "count": v} for k, v in counter.most_common(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="bills.json")
    ap.add_argument("--out", dest="out_path", default="statistics.json")
    ap.add_argument("--top", type=int, default=50)
    args = ap.parse_args()

    with open(args.in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items: List[Dict[str, Any]] = data.get("items", [])
    bill_ids: Set[int] = set()

    # Counters
    by_originating_house = Counter()
    by_current_house = Counter()
    by_bill_type_id = Counter()
    by_introduced_session_id = Counter()
    by_stage = Counter()
    by_year = Counter()
    by_year_month = Counter()

    party_bills = defaultdict(set)
    member_bills = defaultdict(set)
    org_bills = defaultdict(set)

    sponsor_member_count_dist = Counter()
    sponsor_total_count_dist = Counter()

    missing_long_title = 0
    missing_sponsors = 0
    detail_failures = 0
    missing_current_stage = 0

    is_act_count = 0
    withdrawn_count = 0
    defeated_count = 0

    for bill in items:
        bill_id = bill.get("bill_id")
        if bill_id is None:
            continue
        bill_id = int(bill_id)
        bill_ids.add(bill_id)

        by_originating_house[safe_str(bill.get("originating_house")) or ""] += 1
        by_current_house[safe_str(bill.get("current_house")) or ""] += 1

        if bill.get("bill_type_id") is not None:
            by_bill_type_id[str(bill.get("bill_type_id"))] += 1
        if bill.get("introduced_session_id") is not None:
            by_introduced_session_id[str(bill.get("introduced_session_id"))] += 1

        cs = bill.get("current_stage")
        if isinstance(cs, dict):
            by_stage[safe_str(cs.get("description")) or ""] += 1
        else:
            missing_current_stage += 1

        dt = parse_dt(bill.get("last_update"))
        if dt:
            by_year[str(dt.year)] += 1
            by_year_month[f"{dt.year:04d}-{dt.month:02d}"] += 1

        if not safe_str(bill.get("long_title")):
            missing_long_title += 1
        if bill.get("detail_ok") == 0:
            detail_failures += 1

        if bill.get("is_act") is True:
            is_act_count += 1
        if bill.get("bill_withdrawn") is not None:
            withdrawn_count += 1
        if bill.get("is_defeated") is True:
            defeated_count += 1

        sponsors = bill.get("sponsors")
        if not isinstance(sponsors, list) or not sponsors:
            missing_sponsors += 1
            sponsor_member_count_dist[0] += 1
            sponsor_total_count_dist[0] += 1
            continue

        sponsor_total_count_dist[len(sponsors)] += 1

        member_count = 0
        for sp in sponsors:
            mem = sp.get("member") if isinstance(sp, dict) else None
            org = sp.get("organisation") if isinstance(sp, dict) else None

            if isinstance(mem, dict) and mem.get("member_id") is not None:
                member_count += 1
                mid = int(mem.get("member_id"))
                name = safe_str(mem.get("name"))
                party = safe_str(mem.get("party"))
                member_bills[f"{mid}|{name}"].add(bill_id)
                if party:
                    party_bills[party].add(bill_id)

            if isinstance(org, dict):
                oname = safe_str(org.get("name"))
                if oname:
                    org_bills[oname].add(bill_id)

        sponsor_member_count_dist[member_count] += 1

    party_counts = Counter({k: len(v) for k, v in party_bills.items()})
    member_counts = Counter({k: len(v) for k, v in member_bills.items()})
    org_counts = Counter({k: len(v) for k, v in org_bills.items()})

    def member_top(n: int):
        out = []
        for k, c in member_counts.most_common(n):
            mid, name = (k.split("|", 1) + [""])[:2]
            out.append({"member_id": int(mid), "name": name, "bill_count": c})
        return out

    out = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source": args.in_path,
        "overall": {
            "unique_bills": len(bill_ids),
            "records_in_file": len(items),
            "detail_failures": detail_failures,
            "missing_long_title": missing_long_title,
            "missing_sponsors": missing_sponsors,
            "missing_current_stage": missing_current_stage,
            "is_act_true": is_act_count,
            "withdrawn_non_null": withdrawn_count,
            "defeated_true": defeated_count,
        },
        "bills_by_originating_house": top_n(by_originating_house, 100),
        "bills_by_current_house": top_n(by_current_house, 100),
        "bills_by_bill_type_id": top_n(by_bill_type_id, 100),
        "bills_by_introduced_session_id": top_n(by_introduced_session_id, 200),
        "bills_by_current_stage_description": top_n(by_stage, 200),
        "bills_by_year_last_update": top_n(by_year, 200),
        "bills_by_year_month_last_update": top_n(by_year_month, 500),
        "bills_by_party_from_sponsors": top_n(party_counts, args.top),
        "bills_by_member_from_sponsors": member_top(args.top),
        "bills_by_sponsor_organisation": top_n(org_counts, args.top),
        "distributions": {
            "sponsor_member_count_per_bill": top_n(sponsor_member_count_dist, 1000),
            "sponsor_total_count_per_bill": top_n(sponsor_total_count_dist, 1000),
        },
    }

    with open(args.out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.out_path} (unique_bills={len(bill_ids)})")


if __name__ == "__main__":
    main()
