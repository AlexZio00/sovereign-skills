#!/usr/bin/env python3
"""skill_health_bucket.py — deterministic scoring for skill-ops Health/Quality mode.

All inputs are pre-computed scalars (count/last-seen/discard-rate/file text) — no DB access.
Principle: counting is a job for the machine; judgment (e.g. whether to retire a skill)
stays with the user/LLM.

Usage:
  python skill_health_bucket.py bucket --count N --last-seen YYYY-MM-DD --discard-rate 0.0
  python skill_health_bucket.py structural --file <path to SKILL.md>
  python skill_health_bucket.py usage --invocation-count-30d N --discard-rate 0.0
      --days-since-modified N [--has-related-lesson]
  python skill_health_bucket.py sq --structural F --usage F
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys


def bucket_status(count: int, last_seen, discard_rate: float) -> str:
    if count == 0 and discard_rate > 0:
        return "Discarded"
    if count >= 2:
        return "Active"
    if count >= 1:
        return "Low"
    if last_seen is None:
        return "Unknown"
    try:
        last = _dt.date.fromisoformat(last_seen)
    except ValueError:
        return "Unknown"
    days_since = (_dt.date.today() - last).days
    return "Dead" if days_since >= 90 else "Unused"


def structural_score(md_text: str) -> float:
    # (?=\n##(?!#)|\Z) — a section only ends at a level-2 (##) heading. Treating a
    # ###+ subheading (e.g. "### Create mode" in a multi-mode skill) as the section
    # end would miss real table rows below it.
    score = 0.0
    if re.search(r"Dominant Variable", md_text, re.IGNORECASE):
        score += 1
    if re.search(r"Discard If", md_text, re.IGNORECASE):
        score += 1
    inv_match = re.search(r"##\s*Invariants(.*?)(?=\n##(?!#)|\Z)", md_text, re.DOTALL | re.IGNORECASE)
    if inv_match and re.search(r"Violation\s*(→|->)", inv_match.group(1)):
        score += 1
    scope_match = re.search(r"##\s*Scope Boundary(.*?)(?=\n##(?!#)|\Z)", md_text, re.DOTALL | re.IGNORECASE)
    if scope_match:
        rows = [l for l in scope_match.group(1).splitlines() if l.strip().startswith("|")]
        data_rows = rows[2:] if len(rows) > 2 else []
        if len(data_rows) >= 2:  # "2+ rows on each side of Scope Boundary" per the spec (1 row used to pass)
            score += 1
    rat_match = re.search(r"##\s*Rationalization Table(.*?)(?=\n##(?!#)|\Z)", md_text, re.DOTALL | re.IGNORECASE)
    if rat_match:
        rows = [l for l in rat_match.group(1).splitlines() if l.strip().startswith("|")]
        data_rows = rows[2:] if len(rows) > 2 else []
        if len(data_rows) >= 3:
            score += 1
    return score


def usage_score(invocation_count_30d: int, discard_rate: float, days_since_modified: int,
                 has_related_lesson: bool) -> float:
    score = 0.0
    if invocation_count_30d >= 5:
        score += 2
    elif invocation_count_30d >= 1:
        score += 1
    if discard_rate < 0.30:
        score += 1
    if days_since_modified <= 30:
        score += 1
    elif days_since_modified <= 90:
        score += 0.5
    if has_related_lesson:
        score += 0.5
    return score


def s_q(structural: float, usage: float) -> float:
    return structural + usage


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic scoring for skill-ops Health/Quality mode")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_bucket = sub.add_parser("bucket")
    p_bucket.add_argument("--count", type=int, required=True)
    p_bucket.add_argument("--last-seen", default=None)
    p_bucket.add_argument("--discard-rate", type=float, required=True)
    p_bucket.set_defaults(func=lambda a: print(bucket_status(a.count, a.last_seen, a.discard_rate)) or 0)

    p_struct = sub.add_parser("structural")
    p_struct.add_argument("--file", required=True)
    p_struct.set_defaults(func=lambda a: _run_structural(a))

    p_usage = sub.add_parser("usage")
    p_usage.add_argument("--invocation-count-30d", type=int, required=True)
    p_usage.add_argument("--discard-rate", type=float, required=True)
    p_usage.add_argument("--days-since-modified", type=int, required=True)
    p_usage.add_argument("--has-related-lesson", action="store_true")
    p_usage.set_defaults(func=lambda a: print(json.dumps({"usage_score": usage_score(
        a.invocation_count_30d, a.discard_rate, a.days_since_modified, a.has_related_lesson)})) or 0)

    p_sq = sub.add_parser("sq")
    p_sq.add_argument("--structural", type=float, required=True)
    p_sq.add_argument("--usage", type=float, required=True)
    p_sq.set_defaults(func=lambda a: print(json.dumps({"s_q": s_q(a.structural, a.usage)})) or 0)

    args = ap.parse_args(argv)
    return args.func(args)


def _run_structural(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    print(json.dumps({"structural_score": structural_score(text)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
