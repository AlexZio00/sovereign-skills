"""test_coverage_check.py - requirement <-> task coverage."""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_check as cc

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coverage_check.py")

SPEC = """## L3 Requirements
- **R1** Users can log in
  - R1.1: With the right password, create a session
  - R1.2: With a wrong password, show an error
- **R2**: Admins see the list quickly
- R3: Export format is TBD

## L4 Tasks
### Task 1: Login handler
Fulfills: R1.1, R1.2
### Task 2: Admin list
Fulfills: R2, R9
### Task 3: Cleanup job
Description only, no link
"""


def test_parse_requirements_and_tasks():
    reqs = cc.parse_requirements(SPEC)
    assert reqs == ["R1", "R1.1", "R1.2", "R2", "R3"]
    tasks = cc.parse_tasks(SPEC)
    assert tasks == {"Task 1": ["R1.1", "R1.2"], "Task 2": ["R2", "R9"], "Task 3": []}


def test_report_finds_gaps():
    r = cc.check(SPEC)
    assert r["uncovered"] == ["R3"]            # R1 is covered through its children R1.1/R1.2
    assert r["tasks_without_fulfills"] == ["Task 3"]
    assert r["undefined_refs"] == {"Task 2": ["R9"]}
    assert r["ok"] is False


def test_parent_reference_covers_children():
    spec = "- R1: a\n  - R1.1: b\n  - R1.2: c\n### Task 1: x\nFulfills: R1\n"
    r = cc.check(spec)
    assert r["uncovered"] == [] and r["ok"] is True


def test_vague_words_and_placeholders_are_warnings_only():
    r = cc.check(SPEC)
    flagged = {w["id"]: w["terms"] for w in r["vague"]}
    assert "quickly" in flagged["R2"]
    assert "TBD" in flagged["R3"]
    clean = "- R1: Redirect to the login screen 30 minutes after the session expires\n### Task 1: x\nFulfills: R1\n"
    assert cc.check(clean)["vague"] == [] and cc.check(clean)["ok"] is True


def test_duplicate_requirement_ids_flagged():
    r = cc.check("- R1: a\n- R1: b\n### Task 1: x\nFulfills: R1\n")
    assert r["duplicates"] == ["R1"] and r["ok"] is False


def test_no_requirements_is_not_a_pass():
    r = cc.check("### Task 1: x\nFulfills: R1\n")
    assert r["ok"] is False and r["reason"] == "no requirement ids found"


def test_cli_exit_codes(tmp_path):
    good = tmp_path / "good.md"
    good.write_text("- R1: a\n### Task 1: x\nFulfills: R1\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text(SPEC, encoding="utf-8")
    ok = subprocess.run([sys.executable, SCRIPT, "--spec", str(good)], capture_output=True, text=True,
                        encoding="utf-8")
    assert ok.returncode == 0 and "COVERAGE: PASS" in ok.stdout
    ng = subprocess.run([sys.executable, SCRIPT, "--spec", str(bad)], capture_output=True, text=True,
                        encoding="utf-8")
    assert ng.returncode == 1 and "UNCOVERED R3" in ng.stdout


def test_unreadable_input_exits_2(tmp_path):
    p = subprocess.run([sys.executable, SCRIPT, "--spec", str(tmp_path / "missing.md")],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 2


def test_separate_plan_file(tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("- R1: a\n- R2: b\n", encoding="utf-8")
    plan = tmp_path / "plan.md"
    plan.write_text("### Task 1: x\nFulfills: R1, R2\n", encoding="utf-8")
    p = subprocess.run([sys.executable, SCRIPT, "--spec", str(spec), "--plan", str(plan)],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
