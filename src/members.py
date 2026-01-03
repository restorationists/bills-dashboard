#!/usr/bin/env python3
"""
members.py

Read bills.json (from download_bills.py) and produce members.json:

{
  "data": [
    {
      "member_id": 123,
      "name": "Jane Doe",
      "party": "Labour",
      "photo": "...",
      "page": "...",
      "constituency": "Somewhere"
    },
    ...
  ]
}

- Iterates bills.json -> items[*].sponsors[*].member
- Dedupes by member_id
- If a member appears multiple times, keeps the "best" fields (prefers non-empty)
- Sorts A–Z by name (case-insensitive)

Run:
  python3 members.py --in bills.json --out members.json
"""

import argparse
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def pick_best(existing: Optional[str], candidate: Optional[str]) -> Optional[str]:
    """
    Prefer non-empty strings; otherwise keep existing.
    """
    if candidate is None:
        return existing
    cand = str(candidate).strip()
    if cand:
        if existing is None or not str(existing).strip():
            return cand
        # If existing exists, keep it (stable) unless candidate is longer/more informative
        if len(cand) > len(str(existing).strip()):
            return cand
    return existing


def member_from_sponsor(sp: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(sp, dict):
        return None
    mem = sp.get("member")
    if isinstance(mem, dict) and mem.get("member_id") is not None:
        return mem
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="bills.json")
    ap.add_argument("--out", dest="out_path", default="members.json")
    args = ap.parse_args()

    with open(args.in_path, "r", encoding="utf-8") as f:
        bills = json.load(f)

    items = bills.get("items", [])
    members: Dict[int, Dict[str, Any]] = {}

    for bill in items:
        sponsors = bill.get("sponsors")
        if not isinstance(sponsors, list):
            continue

        for sp in sponsors:
            mem = member_from_sponsor(sp)
            if not mem:
                continue

            mid = int(mem["member_id"])

            # Map fields to requested output keys
            name = mem.get("name")
            party = mem.get("party")
            photo = mem.get("member_photo") or mem.get("photo")
            page = mem.get("member_page") or mem.get("page")
            constituency = mem.get("member_from") or mem.get("constituency")

            if mid not in members:
                members[mid] = {
                    "member_id": mid,
                    "name": str(name).strip() if name is not None else None,
                    "party": str(party).strip() if party is not None else None,
                    "photo": str(photo).strip() if photo is not None else None,
                    "page": str(page).strip() if page is not None else None,
                    "constituency": str(constituency).strip() if constituency is not None else None,
                }
            else:
                # Merge: prefer non-empty / more informative values
                m = members[mid]
                m["name"] = pick_best(m.get("name"), name)
                m["party"] = pick_best(m.get("party"), party)
                m["photo"] = pick_best(m.get("photo"), photo)
                m["page"] = pick_best(m.get("page"), page)
                m["constituency"] = pick_best(m.get("constituency"), constituency)

    # Sort A–Z by name, then member_id
    data = sorted(
        members.values(),
        key=lambda r: ((r.get("name") or "").casefold(), r["member_id"]),
    )

    out = {
        "generated_at": utc_now(),
        "source": args.in_path,
        "count": len(data),
        "data": data,
    }

    with open(args.out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.out_path} ({len(data)} members)")


if __name__ == "__main__":
    main()
