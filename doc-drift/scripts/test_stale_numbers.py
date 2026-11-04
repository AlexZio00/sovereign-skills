"""Tests for stale_numbers.py (run: python -m pytest scripts -q)."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stale_numbers as sn  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def test_undated_count_reported():
    hits = sn.scan_text("- Project has 2909 tests and 99 skills\n")
    assert [(h["count"], h["unit"]) for h in hits] == [("2909", "tests"), ("99", "skills")]


def test_dated_or_command_line_not_reported():
    assert sn.scan_text("- 2909 tests (measured 2026-10-20)\n") == []
    assert sn.scan_text("- count with `pytest --collect-only -q | tail -1` (about 2900 tests)\n") == []


def test_korean_units_and_thousands():
    hits = sn.scan_text("파일 3,495개 중 2872 파일\n")
    pairs = [(h["count"], h["unit"]) for h in hits]
    assert ("3,495", "개") in pairs and ("2872", "파일") in pairs


def test_thresholds_are_rules_not_counts():
    assert sn.scan_text("- 30줄 초과 출력은 금지\n- 500 lines+ of test output\n- 20 files max\n") == []


def test_code_fence_and_single_digit_ignored():
    assert sn.scan_text("```\n2909 tests\n```\n3 tests retried\n") == []


def test_number_glued_to_word_or_decimal_ignored():
    assert sn.scan_text("v2.10 lines\nabc12 tests\n") == []


def test_cli_exit_codes(tmp_path):
    clean = tmp_path / "clean.md"
    clean.write_text("Run the tests before every commit.\n", encoding="utf-8")
    stale = tmp_path / "stale.md"
    stale.write_text("We have 120 agents.\n", encoding="utf-8")
    script = os.path.join(HERE, "stale_numbers.py")
    run = lambda *a: subprocess.run([sys.executable, script, *a], capture_output=True, text=True)  # noqa: E731
    assert run(str(clean)).returncode == 0
    r = run(str(stale), "--json")
    assert r.returncode == 1 and '"120"' in r.stdout
    assert run(str(tmp_path / "missing.md")).returncode == 2
