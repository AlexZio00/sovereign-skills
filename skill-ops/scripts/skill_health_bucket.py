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
  python skill_health_bucket.py report [--inv-dir DIR] [--skills-dir DIR] [--days 30] [--out FILE]
      (single implementation of the Health-mode Phase 1-3 rollup; counts records from every source;
       without --out it prints to stdout and creates no file; --out creates missing parent folders)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


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
    # Discard bonus needs a denominator: with 0 invocations the rate is undefined.
    if invocation_count_30d >= 1 and discard_rate < 0.30:
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


def discarded_names(record: dict) -> list:
    """Skill names in a record's discarded[]. Entries may be plain strings or {"skill": ..., "reason": ...} objects."""
    names = []
    for entry in record.get("discarded") or []:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("skill"), str):
            names.append(entry["skill"])
    return names


def aggregate_invocations(inv_dir: str, skill_names, days: int = 30, today=None) -> dict:
    """Per-skill count/last_seen/discard_rate/status. Counts records from every source (any `source` value).

    Status rules: no log records at all -> Unknown. Records exist but the skill was never invoked and
    never discarded -> Unused (or Dead when last seen 90+ days ago). An empty window with older records
    leaves never-seen skills Unknown, because an empty window says nothing about them.
    """
    import glob
    import os
    today = today or _dt.date.today()
    start = today - _dt.timedelta(days=days)
    recs = []
    for fp in sorted(glob.glob(os.path.join(inv_dir, "*.jsonl"))):
        with open(fp, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if not isinstance(r, dict):  # skip list/null/number lines
                        continue
                    d = _dt.date.fromisoformat(str(r.get("date", ""))[:10])
                except (ValueError, TypeError):
                    continue
                recs.append((d, r))
    win = [(d, r) for d, r in recs if start <= d <= today]
    out = {}
    for name in skill_names:
        cnt = sum(1 for _, r in win if name in (r.get("skills") or []))
        disc = sum(1 for _, r in win if name in discarded_names(r))
        seen = [d for d, r in recs if name in (r.get("skills") or [])]
        last = max(seen).isoformat() if seen else None
        rate = disc / (cnt + disc) if (cnt + disc) else 0.0
        if not recs:
            status = "Unknown"
        elif cnt == 0 and last is None and rate == 0.0:
            status = "Unused" if win else "Unknown"
        else:
            status = bucket_status(cnt, last, rate)
        out[name] = {"count": cnt, "last_seen": last, "discard_rate": round(rate, 3),
                     "status": status}
    return {"window_days": days, "records_in_window": len(win), "skills": out}


def render_report(agg: dict, today=None) -> str:
    today = today or _dt.date.today()
    rows = sorted(agg["skills"].items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    counts = {}
    for _, v in rows:
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    lines = [f"# Skill Health - {today.isoformat()}",
             "Denominator: %d skills / %d-day window, %d records (all sources)"
             % (len(rows), agg["window_days"], agg["records_in_window"]),
             " | ".join(f"{k} {v}" for k, v in sorted(counts.items())), "",
             "| skill | count | last_seen | discard_rate | status |", "|---|---|---|---|---|"]
    for n, v in rows:
        lines.append(f"| {n} | {v['count']} | {v['last_seen'] or '-'} | {v['discard_rate']} | {v['status']} |")
    lines.append("")
    lines.append("Active/Low labels are frequency buckets, not a retire verdict.")
    return "\n".join(lines) + "\n"


def _run_report(args) -> int:
    import os
    home = os.path.join(os.path.expanduser("~"), ".claude")
    inv = args.inv_dir or os.path.join(home, ".harness", "invocations")
    sk = args.skills_dir or os.path.join(home, "skills")
    if not os.path.isdir(sk):
        print(f"ERROR: skills folder not found: {sk} (pass --skills-dir <folder that holds <skill>/SKILL.md>)",
              file=sys.stderr)
        return 2
    names = sorted(d for d in os.listdir(sk) if os.path.isfile(os.path.join(sk, d, "SKILL.md")))
    text = render_report(aggregate_invocations(inv, names, args.days))
    if args.out:
        parent = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(parent, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {args.out}")
    else:
        print(text, end="")
    return 0


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

    p_rep = sub.add_parser("report")
    p_rep.add_argument("--inv-dir", default=None)
    p_rep.add_argument("--skills-dir", default=None)
    p_rep.add_argument("--days", type=int, default=30)
    p_rep.add_argument("--out", default=None)
    p_rep.set_defaults(func=_run_report)

    args = ap.parse_args(argv)
    return args.func(args)


def _run_structural(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    print(json.dumps({"structural_score": structural_score(text)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
