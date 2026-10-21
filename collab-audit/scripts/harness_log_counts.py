#!/usr/bin/env python3
"""harness_log_counts.py -- deterministic input for collab-audit Section 7.

Counts skill and agent invocation records, from every `source`, in
~/.claude/.harness/invocations/*.jsonl over the last N days and prints one JSON object.
The machine counts, the LLM interprets (see the Tool Usage Pattern section of SKILL.md).
It never reads prompt text. Missing or broken lines are skipped and counted in `skipped_lines`
(never silently turned into zero).

Record format: docs/FILE-CONVENTIONS.md ("Invocation ledger"). `discarded` entries are read in both
forms, a plain skill name or {"skill": ..., "reason": ...}. A growth record (`prior_session_id`)
continues an earlier session, so `sessions` counts each chain of records once.

usage: python harness_log_counts.py [--harness-dir ~/.claude/.harness] [--days 30] [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path


def _date_of(r: dict) -> str:
    d = r.get("date")
    if not d and isinstance(r.get("ts"), str):
        d = r["ts"][:10]
    return str(d or "")


def _read(dir_: Path, since: str, until: str):
    """(records, skipped) -- only records whose date string falls in the window."""
    recs, skipped = [], 0
    if not dir_.is_dir():
        return recs, skipped
    for f in sorted(dir_.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(r, dict):
                skipped += 1
            elif since <= _date_of(r) <= until:
                recs.append(r)
    return recs, skipped


def _names(value) -> list:
    return [x for x in (value or []) if isinstance(x, str) and x]


def discarded_skill(item):
    """Skill name of one `discarded` entry (string form or {"skill": ..., "reason": ...}); None if unusable."""
    if isinstance(item, dict):
        item = item.get("skill")
    return item if isinstance(item, str) and item else None


def _session_roots(records: list) -> set:
    """Distinct sessions; a record with prior_session_id belongs to the chain it continues."""
    parent = {}
    for r in records:
        sid, prior = r.get("session_id"), r.get("prior_session_id")
        if sid:
            parent[sid] = prior if isinstance(prior, str) and prior and prior != "unknown" else None
    roots = set()
    for sid in parent:
        seen = set()
        while parent.get(sid) and sid not in seen:
            seen.add(sid)
            sid = parent[sid]
        roots.add(sid)
    return roots


def summarize(harness: Path, days: int, today: date) -> dict:
    since, until = (today - timedelta(days=days)).isoformat(), today.isoformat()
    inv, skipped = _read(harness / "invocations", since, until)
    skills = Counter(s for r in inv for s in _names(r.get("skills")))
    agents = Counter(a for r in inv for a in _names(r.get("agents")))
    discarded = Counter(s for r in inv for s in map(discarded_skill, r.get("discarded") or []) if s)
    sources = Counter(str(r.get("source") or "unknown") for r in inv)
    return {
        "window": {"since": since, "until": until},
        "invocation_records": len(inv),
        "sessions": len(_session_roots(inv)),
        "skills_top": skills.most_common(10),
        "agents_top": agents.most_common(10),
        "discarded_total": sum(discarded.values()),
        "discarded_top": discarded.most_common(10),
        "sources": dict(sources),
        "skipped_lines": skipped,
    }


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness-dir", default=str(Path.home() / ".claude" / ".harness"))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--today", default=None, help="reference date YYYY-MM-DD (for tests)")
    a = ap.parse_args(argv)
    today = date.fromisoformat(a.today) if a.today else date.today()
    print(json.dumps(summarize(Path(a.harness_dir), a.days, today), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
