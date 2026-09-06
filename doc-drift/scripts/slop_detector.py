"""Deterministic AI-tell text scorer.

Cheap regex/keyword pre-pass for doc-drift's Step 0 -- flags density of
hedging phrases, hype vocabulary, empty intensifiers, and antithesis
constructions ("it's not just X, it's Y"). This is a heuristic, not a
verdict: doc-drift's Invariant 2 (exclude confidence < 80%) still governs
whether any flagged span becomes a reported finding. [adamentwistle/claude-code-tools 차용]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# (category, weight, compiled pattern) -- additive scoring, transparent by design.
PATTERNS: list[tuple[str, int, re.Pattern]] = [
    ("hedging", 1, re.compile(r"\b(it seems|it appears|arguably|perhaps|might suggest|could be seen as)\b", re.I)),
    ("hype_vocab", 1, re.compile(r"\b(robust|leverage|seamless|cutting-edge|game-chang\w*|unlock\w*|elevate\w*)\b", re.I)),
    ("empty_intensifier", 1, re.compile(r"\b(very|really|truly|incredibly|remarkably)\b", re.I)),
    ("antithesis", 2, re.compile(r"\bit'?s not (?:just|only)\b.{0,60}\bit'?s\b", re.I)),
    ("em_dash", 1, re.compile(r"—")),
]


def score_text(text: str) -> dict:
    hits: list[dict] = []
    total = 0
    for category, weight, pattern in PATTERNS:
        for m in pattern.finditer(text):
            total += weight
            hits.append({"category": category, "weight": weight, "match": m.group(0), "pos": m.start()})
    words = max(len(text.split()), 1)
    density = total / words
    if density >= 0.05:
        verdict = "HIGH"
    elif density >= 0.02:
        verdict = "MEDIUM"
    else:
        verdict = "LOW"
    return {"score": total, "words": words, "density": density, "verdict": verdict, "hits": hits}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-density", type=float, default=None,
                         help="Exit 1 if density exceeds this threshold (CI gate)")
    args = parser.parse_args()

    try:
        text = args.path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"READ_ERROR: {args.path}: {e}", file=sys.stderr)
        return 2

    result = score_text(text)
    result["path"] = str(args.path)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.path}: score={result['score']} density={result['density']:.4f} verdict={result['verdict']}")
        for h in result["hits"]:
            print(f"  [{h['category']}] '{h['match']}' @ {h['pos']}")

    if args.max_density is not None and result["density"] > args.max_density:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
