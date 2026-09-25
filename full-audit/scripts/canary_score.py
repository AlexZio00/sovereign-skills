#!/usr/bin/env python3
"""canary_score.py — scores a full-audit review pass's findings against the
manifest canary_mix.py produced: false positives on the clean control file(s),
and misses on the seeded (defective) file(s). Seeded results are appended
(append-only) to a recall ledger for a longer-run recall trend.

Matching rules:
- Only CONFIRMED findings count (UNCERTAIN/NIT/FALSE-POSITIVE are neither a
  detection nor a false positive).
- Path matching: compares against the manifest's staged_path (falling back to
  path). Backslash/case differences are ignored, and a reviewer that wrote only
  a relative path or bare file name still matches on a path suffix. Keep staged
  file names unique within the bundle, or a same-named real file could be
  mismatched to the canary.
- If a seeded entry has expected_finding_keywords and the finding has any
  descriptive text, at least one keyword must appear in that text to count as a
  detection (this keeps a CONFIRMED finding for the wrong reason from counting
  as a hit). If there's no descriptive text at all, a path match alone counts.
  Keywords should describe the defect's nature only, never a variable/function
  name from the source file itself — otherwise any finding that happens to
  quote that name gets counted as a hit for the wrong reason.

This script only records; it never softens or blocks anything. If a clean
control comes back as a false positive, the SKILL.md procedure is what marks
this run's CONFIRMED findings for re-verification — this script doesn't.

Usage:
  python canary_score.py --manifest <path> --findings <path> [--skill full-audit] [--recall-ledger <path>]
  python canary_score.py --summary [--skill full-audit] [--recall-ledger <path>]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib

# Default ledger lives inside this skill's bundled canary pool directory so
# recall history works out of the box with no environment-specific setup.
DEFAULT_RECALL_LEDGER = pathlib.Path(__file__).resolve().parent / "canaries" / "recall_ledger.jsonl"
MIN_RECALL_N = 5
TEXT_FIELDS = ("summary", "title", "detail", "description", "reason", "evidence", "message")


def load_manifest(path: pathlib.Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def load_findings(path: pathlib.Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(p: str) -> str:
    return str(p).replace("\\", "/").strip().lower()


def _same_file(finding_path: str, target_path: str) -> bool:
    f, t = _norm(finding_path), _norm(target_path)
    if not f or not t:
        return False
    return f == t or t.endswith("/" + f.lstrip("/")) or f.endswith("/" + t.lstrip("/"))


def _mentions(finding: dict, keywords: list) -> bool:
    text = " ".join(str(finding.get(k, "")) for k in TEXT_FIELDS).lower()
    if not text.strip() or not keywords:
        return True
    return any(str(kw).lower() in text for kw in keywords)


def _detected(entry: dict, confirmed: list) -> bool:
    target = entry.get("staged_path") or entry["path"]
    return any(_same_file(f.get("file", ""), target)
               and _mentions(f, entry.get("expected_finding_keywords") or [])
               for f in confirmed)


def score(manifest: list, findings: list) -> dict:
    """Returns {"fp_on_clean": [...], "missed_seeded": [...]}"""
    confirmed = [f for f in findings if f.get("verdict") == "CONFIRMED"]
    fp_on_clean = [m for m in manifest if m["kind"] == "clean"
                   and any(_same_file(f.get("file", ""), m.get("staged_path") or m["path"]) for f in confirmed)]
    missed_seeded = [m for m in manifest if m["kind"] == "seeded" and not _detected(m, confirmed)]
    return {"fp_on_clean": fp_on_clean, "missed_seeded": missed_seeded}


def append_recall_ledger(entries: list, ledger_path: pathlib.Path) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def recall_summary(ledger_path: pathlib.Path, skill: str) -> dict:
    """{detected, total, unmeasured(n<5)} across all of a skill's seeded records."""
    recs = []
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict) and rec.get("skill") == skill:
                recs.append(rec)
    detected = sum(1 for r in recs if r.get("detected") is True)
    return {"detected": detected, "total": len(recs), "unmeasured": len(recs) < MIN_RECALL_N}


def cmd_score(args) -> int:
    manifest = load_manifest(pathlib.Path(args.manifest))
    findings = load_findings(pathlib.Path(args.findings))
    result = score(manifest, findings)
    print(f"[CANARY-SCORE] fp_on_clean={len(result['fp_on_clean'])} missed_seeded={len(result['missed_seeded'])}")
    if result["fp_on_clean"]:
        print("  [WARN] a clean control file came back CONFIRMED -- mark every CONFIRMED finding in this run for re-verification")
    today = _dt.date.today().isoformat()
    missed = {id(m) for m in result["missed_seeded"]}
    entries = [{"date": today, "skill": args.skill, "seeded_id": m.get("defect_id", m["path"]),
                "detected": id(m) not in missed}
               for m in manifest if m["kind"] == "seeded"]
    append_recall_ledger(entries, pathlib.Path(args.recall_ledger))
    return 0


def cmd_summary(args) -> int:
    s = recall_summary(pathlib.Path(args.recall_ledger), args.skill)
    line = f"recall: {s['detected']}/{s['total']} (seeded)"
    if s["unmeasured"]:
        line += f" [WARN] RECALL_UNMEASURED(n<{MIN_RECALL_N})"
    print(line)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Score a review's findings against a canary manifest")
    ap.add_argument("--manifest")
    ap.add_argument("--findings")
    ap.add_argument("--summary", action="store_true", help="print only the aggregate recall ledger summary")
    ap.add_argument("--skill", default="full-audit")
    ap.add_argument("--recall-ledger", default=str(DEFAULT_RECALL_LEDGER), dest="recall_ledger")
    args = ap.parse_args(argv)
    if args.summary:
        return cmd_summary(args)
    if not (args.manifest and args.findings):
        ap.error("--manifest and --findings are required (or use --summary)")
    return cmd_score(args)


if __name__ == "__main__":
    raise SystemExit(main())
