#!/usr/bin/env python3
"""coverage_check.py - deterministic requirement <-> task coverage check for scope Full mode.

Scope Core Rule 4 / Invariant 10 ("every task needs `Fulfills: R{n}.{m}`") was prose only. This script
reads requirement ids (R1, R1.1, ...) and the tasks' `Fulfills:` lines and reports:
  - UNCOVERED:   a requirement no task points at (a task pointing at parent R1 also covers its R1.x children)
  - NO-FULFILLS: a task with no `Fulfills:` line
  - UNDEFINED:   a Fulfills reference to an R-id that is not defined
  - DUPLICATE:   the same R-id defined twice
  - VAGUE (warning only): unmeasurable adjectives / placeholders on requirement lines (fast, intuitive, robust, TBD, ...)
Zero requirement ids is a FAIL, not a PASS (an empty input is never counted as passing).

Usage:
  python coverage_check.py --spec spec.md              # requirements and tasks in one file
  python coverage_check.py --spec spec.md --plan plan.md
Exit codes: 0 = PASS, 1 = FAIL, 2 = input file could not be read.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

# A requirement is DEFINED when its id opens a line (after markdown list/heading/bold/table markers).
_DEF = re.compile(r"^\s*(?:[-*+]\s+|#{1,6}\s+|\|\s*)?(?:\*\*)?(R\d+(?:\.\d+)*)(?:\*\*)?(?=[\s:.)|]|$)")
_TASK = re.compile(r"^\s*#{2,6}\s+(Task\s+[\w.-]+|T\d+[\w.-]*)")
_FULFILLS = re.compile(r"Fulfills\s*[:\uff1a]\s*(.+)", re.I)
_ID = re.compile(r"\bR\d+(?:\.\d+)*\b")
# English terms only; add your own language's vague words here.
VAGUE_TERMS = [
    "robust", "fast", "scalable", "intuitive", "secure", "user-friendly", "efficient", "seamless",
    "easy", "appropriate", "sufficient", "quickly", "reliable",
    "TBD", "TODO", "TKTK", "???",
]


def parse_requirements(text: str) -> list[str]:
    ids = []
    for line in text.splitlines():
        if _TASK.match(line) or _FULFILLS.search(line):
            continue
        m = _DEF.match(line)
        if m:
            ids.append(m.group(1))
    return ids


def parse_tasks(text: str) -> dict[str, list[str]]:
    tasks: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = _TASK.match(line)
        if m:
            current = re.sub(r"\s+", " ", m.group(1)).strip()
            tasks.setdefault(current, [])
            continue
        f = _FULFILLS.search(line)
        if f and current is not None:
            tasks[current].extend(_ID.findall(f.group(1)))
    return tasks


def _requirement_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if _TASK.match(line) or _FULFILLS.search(line):
            continue
        m = _DEF.match(line)
        if m:
            out.setdefault(m.group(1), line[m.end():])
    return out


def check(spec_text: str, plan_text: str | None = None) -> dict:
    reqs = parse_requirements(spec_text)
    tasks = parse_tasks(plan_text if plan_text is not None else spec_text)
    if plan_text is not None:  # tasks may also live in the spec
        for k, v in parse_tasks(spec_text).items():
            tasks.setdefault(k, []).extend(v)
    if not reqs:
        return {"ok": False, "reason": "no requirement ids found", "uncovered": [], "tasks_without_fulfills": [],
                "undefined_refs": {}, "duplicates": [], "vague": []}
    defined = set(reqs)
    duplicates = sorted({r for r in reqs if reqs.count(r) > 1})
    refs = {r for ids in tasks.values() for r in ids}

    def covered(rid: str) -> bool:
        # covered if referenced itself, by an ancestor (R1 covers R1.2), or if all its children are covered
        parts = rid.split(".")
        if any(".".join(parts[:i]) in refs for i in range(1, len(parts) + 1)):
            return True
        children = [r for r in defined if r.startswith(rid + ".") and r.count(".") == rid.count(".") + 1]
        return bool(children) and all(covered(c) for c in children)

    uncovered = [r for r in dict.fromkeys(reqs) if not covered(r)]
    no_fulfills = [t for t, ids in tasks.items() if not ids]
    undefined = {t: [r for r in ids if r not in defined] for t, ids in tasks.items()}
    undefined = {t: v for t, v in undefined.items() if v}
    vague = []
    for rid, rest in _requirement_lines(spec_text).items():
        low = rest.lower()
        hits = [t for t in VAGUE_TERMS if t.lower() in low]
        if hits:
            vague.append({"id": rid, "terms": hits})
    ok = not (uncovered or no_fulfills or undefined or duplicates)
    return {"ok": ok, "reason": "" if ok else "gaps found", "uncovered": uncovered,
            "tasks_without_fulfills": no_fulfills, "undefined_refs": undefined, "duplicates": duplicates,
            "vague": vague, "requirements": len(set(reqs)), "tasks": len(tasks)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="requirement-task coverage check")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--plan")
    a = ap.parse_args(argv)
    try:
        spec = Path(a.spec).read_text(encoding="utf-8")
        plan = Path(a.plan).read_text(encoding="utf-8") if a.plan else None
    except OSError as e:
        print(f"COVERAGE: ERROR cannot read input: {e}".encode("ascii", "backslashreplace").decode("ascii"))
        return 2
    r = check(spec, plan)
    if r.get("reason") == "no requirement ids found":
        print("COVERAGE: FAIL - no requirement ids (R1, R1.1 ...) found; nothing to check is not a pass")
        return 1
    for rid in r["uncovered"]:
        print(f"UNCOVERED {rid}")
    for t in r["tasks_without_fulfills"]:
        print(f"NO-FULFILLS {t}")
    for t, ids in r["undefined_refs"].items():
        print(f"UNDEFINED {t} -> {', '.join(ids)}")
    for rid in r["duplicates"]:
        print(f"DUPLICATE {rid}")
    for w in r["vague"]:
        print(f"VAGUE(warn) {w['id']}: {', '.join(w['terms'])}")
    print(f"COVERAGE: {'PASS' if r['ok'] else 'FAIL'} - requirements {r['requirements']}, tasks {r['tasks']}, "
          f"uncovered {len(r['uncovered'])}, no-fulfills {len(r['tasks_without_fulfills'])}, "
          f"undefined {len(r['undefined_refs'])}, duplicates {len(r['duplicates'])}, vague {len(r['vague'])}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
