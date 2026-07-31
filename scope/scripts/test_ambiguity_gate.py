"""test_ambiguity_gate.py — regression tests for ambiguity_gate."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ambiguity_gate as ag

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ambiguity_gate.py")


def _run_cli(args):
    return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)

CASES = []
def case(name, fn):
    CASES.append((name, fn))

# quick_gate: average of the 4 dimensions >= 7 -> proceed
case("quick_gate avg=7 exactly proceeds", lambda: ag.quick_gate(
    {"function": 7, "boundary": 7, "verification": 7, "assumptions": 7})[0] is True)
case("quick_gate avg<7 blocks", lambda: ag.quick_gate(
    {"function": 5, "boundary": 6, "verification": 5, "assumptions": 6})[0] is False)
case("quick_gate identifies weakest", lambda: ag.quick_gate(
    {"function": 9, "boundary": 3, "verification": 9, "assumptions": 9})[2] == "boundary")

# full_gate: average < 3.5 -> warn
case("full_gate avg=3.5 exactly proceeds", lambda: ag.full_gate([3, 4, 3.5, 3.5])[0] is True)
case("full_gate avg<3.5 warns", lambda: ag.full_gate([1, 2, 3, 3])[0] is False)

# min_items_check: BRIEF.md template parsing
_BRIEF_OK = """
**Scope OUT**
- item1
- item2

**Constraints**
- c1

**Risk Flags**
- r1

**Contraindication**
- x1
"""
case("min_items_check all satisfied -> ok True", lambda: ag.min_items_check(_BRIEF_OK)["ok"] is True)

_BRIEF_BAD = """
**Scope OUT**
- item1

**Constraints**
- c1
"""
case("min_items_check missing sections -> ok False", lambda: ag.min_items_check(_BRIEF_BAD)["ok"] is False)
case("min_items_check counts scope_out correctly", lambda: ag.min_items_check(_BRIEF_OK)["scope_out"] == 2)

# Regression: a bolded aside inside a section (e.g. "**Note**: ...") was mistaken for a new
# section header and silently truncated the count.
_BRIEF_WITH_BOLD_ASIDE = """
**Scope OUT**
- item1
**Note**: this is an aside, not a new section header
- item2

**Constraints**
- c1

**Risk Flags**
- r1

**Contraindication**
- x1
"""
case("min_items_check bold aside inside section does not truncate count (regression)",
     lambda: ag.min_items_check(_BRIEF_WITH_BOLD_ASIDE)["scope_out"] == 2)
case("min_items_check bold aside -> ok still True (regression)",
     lambda: ag.min_items_check(_BRIEF_WITH_BOLD_ASIDE)["ok"] is True)

# is_new_project=True — Constraints<1 still ok (Invariant 6: Constraints applies to existing projects only)
_BRIEF_NEW_PROJECT_NO_CONSTRAINTS = """
**Scope OUT**
- item1
- item2

**Risk Flags**
- r1

**Contraindication**
- x1
"""
case("min_items_check new project waives constraints requirement",
     lambda: ag.min_items_check(_BRIEF_NEW_PROJECT_NO_CONSTRAINTS, is_new_project=True)["ok"] is True)
case("min_items_check existing project (default) still requires constraints",
     lambda: ag.min_items_check(_BRIEF_NEW_PROJECT_NO_CONSTRAINTS, is_new_project=False)["ok"] is False)

# CLI entry-point coverage (quick/full/min-items all exercise the argparse path)
case("CLI quick subcommand runs", lambda: _run_cli(
    ["quick", "--scores", '{"a":8,"b":8,"c":8,"d":8}']).returncode == 0)
case("CLI full subcommand runs", lambda: _run_cli(["full", "--scores", "5,5,5,5"]).returncode == 0)

def _cli_min_items_new_project():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(_BRIEF_NEW_PROJECT_NO_CONSTRAINTS)
        path = f.name
    try:
        r = _run_cli(["min-items", "--file", path, "--new-project"])
        return r.returncode == 0 and '"ok": true' in r.stdout
    finally:
        os.unlink(path)
case("CLI min-items --new-project waives constraints", _cli_min_items_new_project)

def main():
    fails = []
    for name, fn in CASES:
        try:
            ok = fn()
        except Exception as e:
            ok = False
            name = f"{name}  [EXC: {e}]"
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            fails.append(name)
    print(f"\n{len(CASES) - len(fails)}/{len(CASES)} passed")
    return 1 if fails else 0

if __name__ == "__main__":
    raise SystemExit(main())
