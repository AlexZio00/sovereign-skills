#!/usr/bin/env python3
"""ambiguity_gate.py — deterministic gating for the scope skill's Quick/Full modes.

quick_gate: proceed if the average of the 4 ambiguity dimension scores is >= 7.
full_gate: warn if the average L2 Decision clarity score is < 3.5.
min_items_check: BRIEF.md minimum items (Scope OUT>=2 / Risk Flags>=1 / Contraindication>=1 / Constraints>=1).

Usage:
  python ambiguity_gate.py quick --scores '{"function":8,"boundary":7,"verification":6,"assumptions":9}'
  python ambiguity_gate.py full --scores "5,3,4,5"
  python ambiguity_gate.py min-items --file <path to brief.md or a text file>
"""
from __future__ import annotations

import argparse
import json
import sys

_REQUIRED_QUICK_KEYS = ("function", "boundary", "verification", "assumptions")


def _validate_quick_scores(scores) -> None:
    """Validate quick-gate input: exactly the 4 required dimension keys, each a real
    number (bool excluded — Python's bool is a subclass of int) within 0-10 inclusive.
    Raises ValueError naming the specific problem; callers turn that into a clear
    stdout error + exit 1 instead of silently passing malformed input."""
    if not isinstance(scores, dict):
        raise ValueError("scores must be a JSON object (dict)")
    missing = [k for k in _REQUIRED_QUICK_KEYS if k not in scores]
    if missing:
        raise ValueError(
            f"missing required keys: {', '.join(missing)} — need all of {_REQUIRED_QUICK_KEYS}"
        )
    extra = sorted(set(scores) - set(_REQUIRED_QUICK_KEYS))
    if extra:
        raise ValueError(f"unexpected keys: {', '.join(extra)} — only {_REQUIRED_QUICK_KEYS} allowed")
    for k in _REQUIRED_QUICK_KEYS:
        v = scores[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"'{k}' must be a number (int/float), got {type(v).__name__}: {v!r}")
        if not (0 <= v <= 10):
            raise ValueError(f"'{k}' must be within 0-10 inclusive, got {v}")


def quick_gate(scores: dict) -> tuple:
    if not scores:
        raise ValueError("scores must not be empty")
    _validate_quick_scores(scores)
    avg = sum(scores.values()) / len(scores)
    weakest = min(scores, key=scores.get)
    return (avg >= 7, avg, weakest)


def full_gate(clarity_scores: list) -> tuple:
    if not clarity_scores:
        raise ValueError("clarity_scores must not be empty")
    avg = sum(clarity_scores) / len(clarity_scores)
    return (avg >= 3.5, avg)


# Full set of BRIEF.md template section headers — keep in sync with the skill's Step 3 template.
_KNOWN_HEADERS = ("Scope IN", "Scope OUT", "Constraints", "Exit Criteria", "Risk Flags", "Contraindication")


def _count_bullets_under(text: str, header: str) -> int:
    lines = text.splitlines()
    counting = False
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"**{header}"):
            counting = True
            continue
        if counting:
            # Only stop counting on another *known* section header — a bolded aside inside
            # the section (e.g. "**Note**: ...") is not a known header, so it must not
            # terminate the count.
            if any(stripped.startswith(f"**{h}") for h in _KNOWN_HEADERS if h != header):
                break
            if stripped.startswith("- "):
                count += 1
    return count


def min_items_check(brief_text: str, is_new_project: bool = False) -> dict:
    """is_new_project=True waives the Constraints >= 1 requirement (new projects have no
    existing system to constrain against)."""
    scope_out = _count_bullets_under(brief_text, "Scope OUT")
    risk_flags = _count_bullets_under(brief_text, "Risk Flags")
    contraindication = _count_bullets_under(brief_text, "Contraindication")
    constraints = _count_bullets_under(brief_text, "Constraints")
    constraints_ok = is_new_project or constraints >= 1
    ok = scope_out >= 2 and risk_flags >= 1 and contraindication >= 1 and constraints_ok
    return {
        "scope_out": scope_out, "risk_flags": risk_flags,
        "contraindication": contraindication, "constraints": constraints, "ok": ok,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic ambiguity gating for the scope skill")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_quick = sub.add_parser("quick")
    p_quick.add_argument("--scores", required=True, help='JSON dict e.g. {"function":8,"boundary":7,"verification":6,"assumptions":9}')
    p_quick.set_defaults(func=lambda a: _run_quick(a))

    p_full = sub.add_parser("full")
    p_full.add_argument("--scores", required=True, help='comma-separated e.g. "5,3,4,5"')
    p_full.set_defaults(func=lambda a: _run_full(a))

    p_min = sub.add_parser("min-items")
    p_min.add_argument("--file", required=True)
    p_min.add_argument("--new-project", action="store_true",
                        help="new project — waives the Constraints >= 1 requirement (Invariant 6)")
    p_min.set_defaults(func=lambda a: _run_min_items(a))

    args = ap.parse_args(argv)
    return args.func(args)


def _run_quick(args) -> int:
    scores = json.loads(args.scores)
    try:
        ok, avg, weakest = quick_gate(scores)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": ok, "avg": avg, "weakest": weakest}, ensure_ascii=False))
    return 0


def _run_full(args) -> int:
    scores = [float(s) for s in args.scores.split(",")]
    ok, avg = full_gate(scores)
    print(json.dumps({"ok": ok, "avg": avg}, ensure_ascii=False))
    return 0


def _run_min_items(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    print(json.dumps(min_items_check(text, is_new_project=args.new_project), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
