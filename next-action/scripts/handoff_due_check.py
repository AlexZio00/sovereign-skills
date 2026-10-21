#!/usr/bin/env python3
"""Flag handoff to-do items whose date/time has already passed.

A handoff that says "2026-10-11 07:45 first scheduled run" can be carried forward as a
plain to-do at 13:50 the same day if nobody compares item dates with the current time.
This script does that comparison deterministically.

Reads the to-do lines of a handoff file: the YAML `next:` list of a state-snapshot block
and the numbered/bulleted lines under a "What to do now" / "Next steps" heading. For each
line with a YYYY-MM-DD (optional HH:MM after it) it prints PAST / TODAY / FUTURE. When a
line has several dates, the latest one (compared by parsed date and time, not as text) is its
due date (earlier ones are context; shown as "+N"). PAST means "verify what happened before
carrying it over", not "done". Items under "Pending decisions" and "Scheduled checks" are read
too. An item whose `since:` date is STALE_DAYS or more old gets a STALE row, unless its due
date is still in the future (a scheduled item that is simply waiting is not stale). An item
that appears both in the `next:` block and in a prose section is reported once.

Usage:
    python handoff_due_check.py <handoff.md> [--now "2026-10-11 13:50"] [--json]
Exit code is always 0 (report-only); prints "no dated items" when nothing matched.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys

DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})(?:[ T(]+(\d{1,2}:\d{2}))?")
HEAD_RE = re.compile(
    r"^(#{1,4})\s*(What to do now|To do|Next steps?|Next actions?|Next|Pending decisions|"
    r"Scheduled checks)\s*(?:\(|$)", re.I)
# `since: YYYY-MM-DD` = the date an item was first listed. It is not a due date: it is
# stripped before classify() and used only for the carry age. Items carried STALE_DAYS or
# more are flagged STALE so the checkpoint can ask whether to move them to a global state
# file or drop them.
SINCE_RE = re.compile(r"since:\s*(20\d{2}-\d{2}-\d{2})")
STALE_DAYS = 14


def collect_lines(text: str) -> list[tuple[bool, str]]:
    """(from_next_block, line) for every to-do line, in file order."""
    lines, out, in_next, section_level = text.splitlines(), [], False, 0
    for ln in lines:
        s = ln.strip()
        if s.startswith("next:"):
            in_next = True
            continue
        if in_next:
            if s.startswith("- "):
                out.append((True, s[2:]))
                continue
            if s and not s.startswith("#"):
                in_next = False
        head = HEAD_RE.match(s)
        if head:
            section_level = len(head.group(1))
            continue
        if section_level:
            hashes = len(s) - len(s.lstrip("#"))
            if hashes and s[hashes:hashes + 1] == " " and hashes <= section_level:
                section_level = 0  # same or higher-level heading closes the section; sub-headings don't
                continue
            if re.match(r"^(\d+\.|-|\*)\s", s):
                out.append((False, s))
    return out


TOKEN_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|[A-Za-z_][\w.-]*|\d+")
NOISE_RE = re.compile(r"\((?:urgency|risk|basis)\s*:[^)]*\)|since:\s*\d{4}-\d{2}-\d{2}", re.I)
DUP_OVERLAP = 0.75


def _tokens(line: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(NOISE_RE.sub("", line))}


def _same_item(compact: str, prose: str) -> bool:
    """A `next:` entry is a compressed copy of a prose line when most of its tokens
    (dates and times included) occur in that prose line."""
    small = _tokens(compact)
    return bool(small) and len(small & _tokens(prose)) / len(small) >= DUP_OVERLAP


def todo_lines(text: str) -> list[str]:
    """To-do lines in file order; a `next:` entry that restates a prose line is dropped."""
    tagged = collect_lines(text)
    prose = [ln for from_next, ln in tagged if not from_next]
    return [ln for from_next, ln in tagged
            if not (from_next and any(_same_item(ln, p) for p in prose))]


def carry_age(line: str, now: dt.datetime) -> int | None:
    """Days since the item's `since:` date, or None if it has none."""
    m = SINCE_RE.search(line)
    if not m:
        return None
    try:
        return (now.date() - dt.date.fromisoformat(m.group(1))).days
    except ValueError:
        return None


def classify(line: str, now: dt.datetime) -> list[tuple[str, str]]:
    res = []
    for d, t in DATE_RE.findall(SINCE_RE.sub("", line)):
        try:
            day = dt.date.fromisoformat(d)
        except ValueError:
            continue
        when = None
        if t:
            try:
                hh, mm = map(int, t.split(":"))
                when = dt.datetime.combine(day, dt.time(hh, mm))
            except ValueError:  # "07:75", "24:00": fall back to the date alone
                t = ""
        if when is not None:
            label = "PAST" if when < now else ("TODAY" if day == now.date() else "FUTURE")
        else:
            label = "PAST" if day < now.date() else ("TODAY" if day == now.date() else "FUTURE")
        res.append((label, f"{d} {t}".strip()))
    return res


def _when_key(when: str) -> dt.datetime:
    """Sort key for a "YYYY-MM-DD[ H:MM]" string. A date without a time counts as end of day."""
    parts = when.split()
    day = dt.date.fromisoformat(parts[0])
    if len(parts) > 1:
        hh, mm = map(int, parts[1].split(":"))
        return dt.datetime.combine(day, dt.time(hh, mm))
    return dt.datetime.combine(day, dt.time(23, 59, 59))


def due_of(line: str, now: dt.datetime) -> tuple[str, str] | None:
    """One (label, when) per line: the LATEST date on the line is its due date.

    A to-do line often cites earlier dates as context ("changed on 2026-10-11 ...", a plan
    file name like 2026-10-08-...md) next to the real deadline; judging each date separately
    would print PAST for a line that is not due yet. "+N" = N earlier dates on the line were
    not judged.
    """
    res = classify(line, now)
    if not res:
        return None
    label, when = max(res, key=lambda r: _when_key(r[1]))
    return label, when + (f" +{len(res) - 1}" if len(res) > 1 else "")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("handoff")
    ap.add_argument("--now", help='override current time, "YYYY-MM-DD HH:MM"')
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        now = dt.datetime.strptime(a.now, "%Y-%m-%d %H:%M") if a.now else dt.datetime.now()
    except ValueError:
        print(f'bad --now {a.now!r} (want "YYYY-MM-DD HH:MM"), no check done')
        return 0
    try:
        with open(a.handoff, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        print(f"handoff not readable: {e}")
        return 0
    rows = []
    for ln in todo_lines(text):
        due = due_of(ln, now)
        if due:
            rows.append({"status": due[0], "when": due[1], "item": ln[:140]})
        age = carry_age(ln, now)
        if age is not None and age >= STALE_DAYS and not (due and due[0] == "FUTURE"):
            rows.append({"status": "STALE", "when": f"{age}d carried", "item": ln[:140]})
    if a.json:
        print(json.dumps({"now": now.strftime("%Y-%m-%d %H:%M"), "items": rows}, ensure_ascii=False))
    elif not rows:
        print("no dated items")
    else:
        for r in rows:
            print(f"{r['status']:6} {r['when']:16} {r['item']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
