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
