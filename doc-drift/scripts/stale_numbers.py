#!/usr/bin/env python3
"""stale_numbers.py — find hard-coded counts in instruction/memory docs that go stale silently.

Idea from rlaope/oh-my-hermes (MIT), omh-agent-instructions: "write the command that counts, not the count".
Re-implemented here. Report-only: it never edits a file.

A line is reported when it states a count of something that changes (tests, rows, skills, agents, tickers,
files, lines, ...) and carries neither a measurement date (YYYY-MM-DD) nor a command in backticks that would
re-count it. The suggestion is: replace the number with the counting command, or at least stamp the date.
Units are matched in English and Korean, so Korean-language docs are covered too.

  python stale_numbers.py <file> [<file> ...] [--json]
Exit: 0 none found / 1 found / 2 unreadable file.
Known false positives: fixed facts that look like counts (a count in a frozen spec, version numbers,
"3 attempts" in a rule). Known misses: counts written as words, counts in tables split across cells.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

UNIT = (r"tests?|테스트|rows?|행|skills?|스킬|agents?|에이전트|tickers?|종목|files?|파일|LOC|lines?|줄|"
        r"hooks?|훅|commits?|커밋|entries|items?|건|개")
# A count is 2+ digits or a thousands-grouped number, not glued to a word or a decimal point.
COUNT = re.compile(rf"(?<![\w.])(\d{{1,3}}(?:,\d{{3}})+|\d{{2,}})\s*(?:개의\s*)?({UNIT})\b", re.I)
THRESHOLD_AFTER = re.compile(r"^\s*(\+|초과|이상|이하|미만|cap|limit|max|min|까지)", re.I)
DATED = re.compile(r"\b20\d\d-\d\d-\d\d\b|\b\d{4}-\d\d\b")
COMMAND = re.compile(r"`[^`]*\b(pytest|python|grep|wc|ls|sqlite3|git|find|SELECT|COUNT)\b[^`]*`", re.I)


def scan_text(text: str) -> list[dict]:
    out = []
    in_code = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for m in COUNT.finditer(line):
            if DATED.search(line) or COMMAND.search(line):
                continue
            if THRESHOLD_AFTER.match(line[m.end():]):  # "over 30 lines", "500 lines+" are rules, not counts
                continue
            out.append({"line": i, "count": m.group(1), "unit": m.group(2), "text": line.strip()[:140]})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    found = {}
    for f in a.files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as e:
            print(f"ERROR {e}", file=sys.stderr)
            return 2
        hits = scan_text(text)
        if hits:
            found[f] = hits
    if a.json:
        print(json.dumps(found, ensure_ascii=False))
    else:
        for f, hits in found.items():
            for h in hits:
                print(f"{f}:{h['line']}  {h['count']} {h['unit']}  | {h['text']}")
        n = sum(len(v) for v in found.values())
        print(f"stale-numbers: {n} undated count(s) - replace with the counting command or stamp the date")
    return 1 if found else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
