"""test_skill_health_bucket.py — regression tests for skill_health_bucket."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_health_bucket as shb

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill_health_bucket.py")


def _run_cli(args):
    return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)

CASES = []
def case(name, fn):
    CASES.append((name, fn))

# bucket_status
case("bucket_status Active (count>=2)", lambda: shb.bucket_status(3, "2026-07-01", 0.0) == "Active")
case("bucket_status Low (count 1-1)", lambda: shb.bucket_status(1, "2026-07-01", 0.0) == "Low")
case("bucket_status Discarded (count=0, discard_rate>0)", lambda: shb.bucket_status(0, None, 0.5) == "Discarded")
case("bucket_status Unknown (no log, no discard)", lambda: shb.bucket_status(0, None, 0.0) == "Unknown")
case("bucket_status Dead (count=0, last_seen 200d ago)", lambda: shb.bucket_status(
    0, "2026-01-01", 0.0) == "Dead")

# structural_score
_MD_FULL = """
## Purpose
**Dominant Variable**: something

## Discard If
- x

## Invariants
- rule 1. Violation -> bad thing happens

## Scope Boundary
| Does | Does NOT |
|------|------|
| a | b |
| c | d |

## Rationalization Table
| Rationalization | Rebuttal |
|---|---|
| r1 | c1 |
| r2 | c2 |
| r3 | c3 |
"""
case("structural_score full markdown = 5.0", lambda: shb.structural_score(_MD_FULL) == 5.0)
case("structural_score empty markdown = 0.0", lambda: shb.structural_score("") == 0.0)

# usage_score
case("usage_score max = 4.5 (2+1+1+0.5 per documented weights, not 5.0)", lambda: shb.usage_score(10, 0.1, 5, True) == 4.5)
case("usage_score 0 invocations gets no Discard bonus", lambda: shb.usage_score(0, 0.0, 200, False) == 0.0)
case("usage_score 1 invocation low discard rate gets bonus", lambda: shb.usage_score(1, 0.0, 200, False) == 2.0)
case("usage_score zero activity", lambda: shb.usage_score(0, 0.5, 200, False) == 0.0)

# s_q
case("s_q sums structural+usage", lambda: shb.s_q(3.0, 2.0) == 5.0)

# Regression found via review: a ### subheading (multi-mode skill) was being mistaken
# for a section end — confirmed empirically against a real multi-mode SKILL.md, where
# both Scope Boundary and Rationalization Table were under-counted by this pattern.
_MD_MULTIMODE_DECOY = """
## Scope Boundary
### Create mode
| Does | Does NOT |
|------|------|
| a | b |
| c | d |

### Audit mode
| Does | Does NOT |
|------|------|
| e | f |

## Rationalization Table
### Create mode
| Rationalization | Rebuttal |
|---|---|
| r1 | c1 |
| r2 | c2 |
| r3 | c3 |
"""
case("structural_score not truncated by ### submode decoy (regression)",
     lambda: shb.structural_score(_MD_MULTIMODE_DECOY) == 2.0)

# Regression found via review: an off-by-one bug where Scope Boundary scored with
# just 1 data row
_MD_SCOPE_ONE_ROW = """
## Scope Boundary
| Does | Does NOT |
|------|------|
| a | b |
"""
case("structural_score scope boundary with only 1 data row does NOT score (regression)",
     lambda: shb.structural_score(_MD_SCOPE_ONE_ROW) == 0.0)

# Regression found via review: a false-positive bug where a "Violation ->" phrase
# outside the Invariants section still scored
_MD_VIOLATION_OUTSIDE_INVARIANTS = """
## Invariants
- rule 1 (no violation clause here)

## Somewhere Else
Violation -> this is unrelated context, not inside Invariants
"""
case("structural_score violation phrase outside Invariants section does not score (regression)",
     lambda: shb.structural_score(_MD_VIOLATION_OUTSIDE_INVARIANTS) == 0.0)
case("structural_score violation phrase inside Invariants section still scores",
     lambda: shb.structural_score("## Invariants\n- rule. Violation -> bad") == 1.0)

# CLI entry-point coverage (main()/argparse — closes a gap where only pure functions were tested)
case("CLI bucket subcommand runs", lambda: _run_cli(
    ["bucket", "--count", "3", "--last-seen", "2026-07-01", "--discard-rate", "0.0"]
).stdout.strip() == "Active")
case("CLI usage subcommand runs", lambda: '"usage_score"' in _run_cli(
    ["usage", "--invocation-count-30d", "5", "--discard-rate", "0.1",
     "--days-since-modified", "10"]).stdout)
case("CLI sq subcommand runs", lambda: '"s_q"' in _run_cli(
    ["sq", "--structural", "3.0", "--usage", "2.0"]).stdout)

def _cli_structural_on_real_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(_MD_FULL)
        path = f.name
    try:
        r = _run_cli(["structural", "--file", path])
        return r.returncode == 0 and '"structural_score": 5.0' in r.stdout
    finally:
        os.unlink(path)
case("CLI structural subcommand reads file end-to-end", _cli_structural_on_real_file)

# report / aggregate_invocations (temp directories only)
import datetime as _dt  # noqa: E402
import json as _json  # noqa: E402

def _mk_inv(recs):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "2026-10.jsonl"), "w", encoding="utf-8") as f:
        for r in recs:
            f.write(_json.dumps(r) + "\n")
    return d

_T = _dt.date(2026, 10, 13)
_INV = _mk_inv([
    {"date": "2026-10-10", "skills": ["a", "a2"], "discarded": [], "source": "realtime-hook"},
    {"date": "2026-10-11", "skills": ["a"], "discarded": [], "source": "realtime-hook"},
    {"date": "2026-10-11", "skills": ["a", "a2"], "discarded": ["d"], "source": "session-summary"},
    {"date": "2026-10-12", "skills": [], "discarded": [{"skill": "e", "reason": "discard_if"}],
     "source": "session-checkpoint-phase1.6.5"},
    {"date": "2026-01-01", "skills": ["old"], "discarded": [], "source": "realtime-hook"},
])
_AGG = shb.aggregate_invocations(_INV, ["a", "a2", "d", "e", "old", "never"], 30, today=_T)["skills"]
case("report: counts records from every source", lambda: _AGG["a"]["count"] == 3 and _AGG["a"]["status"] == "Active")
case("report: second source counts too -> a2 has 2 -> Active", lambda: _AGG["a2"]["count"] == 2 and _AGG["a2"]["status"] == "Active")
case("report: discarded given as {skill, reason} object -> Discarded", lambda: _AGG["e"]["status"] == "Discarded" and _AGG["e"]["discard_rate"] == 1.0)
case("discarded_names accepts strings and objects, ignores junk", lambda: shb.discarded_names(
    {"discarded": ["x", {"skill": "y", "reason": "r"}, {"reason": "no skill"}, 5, None]}) == ["x", "y"])
case("report: logs present, skill never invoked -> Unused (not Unknown)", lambda: _AGG["never"]["status"] == "Unused")
case("report: discarded counted across sources -> Discarded", lambda: _AGG["d"]["status"] == "Discarded")
case("report: last call outside window, 90d+ ago -> Dead", lambda: _AGG["old"]["status"] == "Dead" and _AGG["old"]["last_seen"] == "2026-01-01")
def _empty_window_unknown():
    d = _mk_inv([{"date": "2025-01-01", "skills": ["x"], "source": "session-checkpoint-phase3.7-fallback"}])
    return shb.aggregate_invocations(d, ["never"], 30, today=_T)["skills"]["never"]["status"] == "Unknown"
case("report: only old records, skill never seen -> Unknown", _empty_window_unknown)
case("report: empty log dir -> all Unknown", lambda: shb.aggregate_invocations(
    tempfile.mkdtemp(), ["a"], 30, today=_T)["skills"]["a"]["status"] == "Unknown")
def _non_dict_lines_skipped():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "2026-10.jsonl"), "w", encoding="utf-8") as f:
        f.write("[1, 2]\nnull\n42\n\"str\"\n")
        f.write(_json.dumps({"date": "2026-10-11", "skills": ["a"], "source": "realtime-hook"}) + "\n")
    agg = shb.aggregate_invocations(d, ["a"], 30, today=_T)["skills"]
    return agg["a"]["count"] == 1
case("report: non-dict JSON lines are skipped without crashing", _non_dict_lines_skipped)

def _cli_report():
    sk = tempfile.mkdtemp()
    os.makedirs(os.path.join(sk, "a"))
    open(os.path.join(sk, "a", "SKILL.md"), "w").write("x")
    out = os.path.join(tempfile.mkdtemp(), "r.md")
    r = _run_cli(["report", "--inv-dir", _INV, "--skills-dir", sk, "--days", "36500", "--out", out])
    return r.returncode == 0 and "| a |" in open(out, encoding="utf-8").read()
case("report CLI: file written only with --out, table included", _cli_report)

def _cli_report_creates_out_parent():
    sk = tempfile.mkdtemp()
    os.makedirs(os.path.join(sk, "a"))
    open(os.path.join(sk, "a", "SKILL.md"), "w").write("x")
    out = os.path.join(tempfile.mkdtemp(), "new", "deeper", "r.md")
    r = _run_cli(["report", "--inv-dir", _INV, "--skills-dir", sk, "--out", out])
    return r.returncode == 0 and os.path.isfile(out)
case("report CLI: --out creates missing parent folders", _cli_report_creates_out_parent)

def _cli_report_missing_skills_dir():
    missing = os.path.join(tempfile.mkdtemp(), "nope")
    r = _run_cli(["report", "--inv-dir", _INV, "--skills-dir", missing])
    return r.returncode == 2 and "skills folder not found" in r.stderr and "Traceback" not in r.stderr
case("report CLI: missing skills dir -> message, no traceback", _cli_report_missing_skills_dir)

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

def test_all_cases():
    """pytest entry point: this file uses its own runner, so plain `pytest` would collect 0 tests."""
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
