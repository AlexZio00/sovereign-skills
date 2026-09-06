"""Deterministic CLAUDE.md-as-machine-prompt scorer.

Scores a CLAUDE.md-style file as a per-turn machine prompt: rewards concrete
anchors (code fences, file paths, shell commands, imperative-mood lines),
penalizes vague directives and length over budget. Same additive scoring
skeleton as slop_detector.py, different weight table for a different reader
(a model re-reading its own instructions, not a human skimming a README).
[adamentwistle/claude-code-tools 차용]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LINE_BUDGET = 150

REWARDS: list[tuple[str, int, re.Pattern]] = [
    ("code_fence", 2, re.compile(r"^```", re.M)),
    ("file_path", 1, re.compile(r"\b[\w./\\-]+\.(py|md|json|ya?ml|ts|tsx|js|toml|cfg)\b")),
    ("shell_command", 1, re.compile(r"^\s*(pytest|python|npm|git|bash|sh)\b", re.M)),
    ("imperative_line", 1, re.compile(r"^-\s*(Never|Always|Do|Don't|Use|Prefer|Avoid)\b", re.M)),
]

PENALTIES: list[tuple[str, int, re.Pattern]] = [
    ("vague_directive", 2, re.compile(r"\b(적당히|알아서|경우에 따라|as appropriate|as needed|use your judgment)\b", re.I)),
]


def lint_text(text: str) -> dict:
    reward_hits: list[dict] = []
    penalty_hits: list[dict] = []
    reward_total = 0
    penalty_total = 0

    for category, weight, pattern in REWARDS:
        for m in pattern.finditer(text):
            reward_total += weight
            reward_hits.append({"category": category, "weight": weight, "match": m.group(0)[:40]})

    for category, weight, pattern in PENALTIES:
        for m in pattern.finditer(text):
            penalty_total += weight
            penalty_hits.append({"category": category, "weight": weight, "match": m.group(0)})

    line_count = text.count("\n") + 1
    over_budget = max(0, line_count - LINE_BUDGET)
    if over_budget:
        penalty_total += over_budget // 10  # 1 point per 10 lines over budget
        penalty_hits.append({"category": "over_line_budget", "weight": over_budget // 10,
                              "match": f"{line_count} lines (budget {LINE_BUDGET})"})

    net = reward_total - penalty_total
    if net >= 8:
        verdict = "STRONG"
    elif net >= 3:
        verdict = "OK"
    else:
        verdict = "WEAK"

    return {
        "reward_total": reward_total,
        "penalty_total": penalty_total,
        "net": net,
        "line_count": line_count,
        "verdict": verdict,
        "reward_hits": reward_hits,
        "penalty_hits": penalty_hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min", type=int, default=None, help="Exit 1 if net score is below this (CI gate)")
    args = parser.parse_args()

    try:
        text = args.path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"READ_ERROR: {args.path}: {e}", file=sys.stderr)
        return 2

    result = lint_text(text)
    result["path"] = str(args.path)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.path}: net={result['net']} (reward={result['reward_total']} penalty={result['penalty_total']}) "
              f"lines={result['line_count']} verdict={result['verdict']}")
        for h in result["penalty_hits"]:
            print(f"  [-{h['weight']}] {h['category']}: {h['match']}")

    if args.min is not None and result["net"] < args.min:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
