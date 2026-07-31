"""validate_memory_claims.py — deterministic path-existence and provenance checks
for memory/handoff documents.

Adapted from the compound-engineering-plugin's validate-doc-claims.py pattern.
Two consumers motivated this: session-checkpoint's Key Files path-verification
step and memory-dream's self-referential completion-claim check, both of which
previously relied on an agent running Glob/Grep by hand and reporting the
result in prose. This script gives the same check a fixed exit-code contract
instead — something a completion claim can point at, rather than trusting the
prose that describes it.

Two independent checks (subcommands):
1. check-paths       — do backtick-quoted (`...`) file-path mentions in the
                        document actually exist on disk?
2. check-provenance   — does each completion-style claim ("done"/"completed"/
                        "verified"/"confirmed") have a date (YYYY-MM-DD)
                        nearby as evidence?

Exit codes (both subcommands): 0 = clean, 1 = issues found (see stdout for
detail), 2 = a target file could not be read.

Known limitation: path extraction is a backtick + common-extension pattern
match, so a generic backtick-quoted mention that isn't really a file
reference (e.g. `SKILL.md` used as a common noun rather than pointing at an
actual file) can also be misclassified as stale — check-paths output is a
lead for a human to confirm, not a final verdict.

Usage:
  python validate_memory_claims.py check-paths --file <path> [--file <path> ...] [--base <dir>]
  python validate_memory_claims.py check-provenance --file <path> [--file <path> ...]
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

_PATH_RE = re.compile(r"`([^`\n]+\.(?:py|md|json|jsonl|db|txt|yaml|yml|toml))`")
_CLAIM_RE = re.compile(r"(?<!not )(?<!un)(?<!in)\b(done|completed|verified|confirmed)\b", re.IGNORECASE)  # excludes "not done", "undone", "unverified", "unconfirmed"
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def extract_paths(text: str) -> list[str]:
    """Extract backtick-quoted strings ending in a common file extension (path candidates, duplicates preserved)."""
    return [m.group(1).strip() for m in _PATH_RE.finditer(text)]


def _resolve(raw: str, base: str | None) -> pathlib.Path:
    expanded = os.path.expanduser(raw)
    p = pathlib.Path(expanded)
    if p.is_absolute() or base is None:
        return p
    return pathlib.Path(base) / p


def check_paths(text: str, base: str | None = None) -> tuple[list[str], list[str]]:
    """Returns (existing paths, stale paths). Each distinct path string is judged only once."""
    existing: list[str] = []
    stale: list[str] = []
    seen: set[str] = set()
    for raw in extract_paths(text):
        if raw in seen:
            continue
        seen.add(raw)
        (existing if _resolve(raw, base).exists() else stale).append(raw)
    return existing, stale


def find_claim_lines(text: str) -> list[tuple[int, str]]:
    """All lines containing a done/completed/verified/confirmed keyword (1-indexed line_no, raw text). Negated forms ("not done", "unverified", etc.) excluded."""
    lines = text.splitlines()
    return [(i + 1, line.strip()) for i, line in enumerate(lines) if _CLAIM_RE.search(line)]


def find_unprovenanced_claims(text: str) -> list[tuple[int, str]]:
    """Return only the lines that carry a completion-style claim keyword but have no date (YYYY-MM-DD) as evidence.

    A date on the same line is sufficient provenance by itself. Otherwise, a date
    on an adjacent line (+-1) may be borrowed — unless that adjacent line is itself
    another claim, in which case its date is that neighbor's own provenance, not
    this line's (e.g. "Task A done" followed by "2026-07-01: Task B done" should
    still flag Task A as unprovenanced).
    """
    lines = text.splitlines()
    is_claim = [bool(_CLAIM_RE.search(ln)) for ln in lines]
    flagged: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not is_claim[i]:
            continue
        if _DATE_RE.search(line):
            continue
        neighbors = [lines[j] for j in (i - 1, i + 1) if 0 <= j < len(lines) and not is_claim[j]]
        if not any(_DATE_RE.search(n) for n in neighbors):
            flagged.append((i + 1, line.strip()))
    return flagged


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def cmd_check_paths(args) -> int:
    total_stale = 0
    for path in args.file:
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError) as e:
            sys.stderr.write(f"[VALIDATE-MEMORY ERROR] cannot read {path}: {e}\n")
            return 2
        existing, stale = check_paths(text, base=args.base)
        print(f"check-paths: file={path} total={len(existing) + len(stale)} stale={len(stale)}")
        for raw in stale:
            print(f"STALE: {raw}")
        total_stale += len(stale)
    return 1 if total_stale else 0


def cmd_check_provenance(args) -> int:
    total_flagged = 0
    for path in args.file:
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError) as e:
            sys.stderr.write(f"[VALIDATE-MEMORY ERROR] cannot read {path}: {e}\n")
            return 2
        claims = find_claim_lines(text)
        flagged = find_unprovenanced_claims(text)
        print(f"check-provenance: file={path} total_claims={len(claims)} unprovenanced={len(flagged)}")
        for lineno, line in flagged:
            print(f"UNPROVENANCED L{lineno}: {line}")
        total_flagged += len(flagged)
    return 1 if total_flagged else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Memory claim validator (paths + provenance)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_paths = sub.add_parser("check-paths")
    p_paths.add_argument("--file", action="append", required=True)
    p_paths.add_argument("--base", default=None)
    p_paths.set_defaults(func=cmd_check_paths)
    p_prov = sub.add_parser("check-provenance")
    p_prov.add_argument("--file", action="append", required=True)
    p_prov.set_defaults(func=cmd_check_provenance)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
