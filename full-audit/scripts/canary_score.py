#!/usr/bin/env python3
"""canary_score.py — scores a full-audit review pass's findings against the
manifest canary_mix.py produced: false positives on the clean control file(s),
and misses on the seeded (defective) file(s). Seeded results are appended
(append-only) to a recall ledger for a longer-run recall trend. Each ledger
record carries a hash of the manifest, and a (skill, manifest hash, seeded_id)
triple is recorded only once, so re-scoring the same manifest does not
double-count.

Matching rules:
- Only CONFIRMED findings count (UNCERTAIN/NIT/FALSE-POSITIVE are neither a
  detection nor a false positive).
- Path matching: compares against the manifest's staged_path (falling back to
  path). Backslash/case differences are ignored, a trailing ":line" or
  ":line:col" is stripped, and a reviewer that wrote only a relative path or
  bare file name still matches on a path suffix. Verdicts are compared
  case-insensitively ("confirmed" counts as CONFIRMED). Keep staged
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

Default ledger: ~/.claude/full-audit/recall_ledger.jsonl (outside the install
folder, so a skill update does not erase it). Override with --recall-ledger or
the FULL_AUDIT_RECALL_LEDGER environment variable.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import re


def _default_ledger() -> pathlib.Path:
    env = os.environ.get("FULL_AUDIT_RECALL_LEDGER")
    if env:
        return pathlib.Path(env)
    return pathlib.Path.home() / ".claude" / "full-audit" / "recall_ledger.jsonl"


DEFAULT_RECALL_LEDGER = _default_ledger()
MIN_RECALL_N = 5
TEXT_FIELDS = ("summary", "title", "detail", "description", "reason", "evidence", "message")


def load_manifest(path: pathlib.Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def load_findings(path: pathlib.Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


_LOC_SUFFIX = re.compile(r":\d+(?::\d+)?$")


def _norm(p: str) -> str:
    """Normalize a finding/manifest path: slashes, case, and a trailing :line(:col)."""
    return _LOC_SUFFIX.sub("", str(p).replace("\\", "/").strip()).lower()


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
    confirmed = [f for f in findings
                 if str(f.get("verdict", "")).strip().upper() == "CONFIRMED"]
    fp_on_clean = [m for m in manifest if m["kind"] == "clean"
                   and any(_same_file(f.get("file", ""), m.get("staged_path") or m["path"]) for f in confirmed)]
    missed_seeded = [m for m in manifest if m["kind"] == "seeded" and not _detected(m, confirmed)]
    return {"fp_on_clean": fp_on_clean, "missed_seeded": missed_seeded}


def manifest_hash(manifest: list) -> str:
    blob = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _ledger_records(ledger_path: pathlib.Path) -> list:
    recs = []
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                recs.append(rec)
    return recs


def append_recall_ledger(entries: list, ledger_path: pathlib.Path) -> int:
    """Append entries; skip an entry whose (skill, manifest_sha, seeded_id) is already
    recorded. Entries without manifest_sha are always appended. Returns the number appended."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    seen = {(r.get("skill"), r.get("manifest_sha"), r.get("seeded_id"))
            for r in _ledger_records(ledger_path) if r.get("manifest_sha")}
    added = 0
    with ledger_path.open("a", encoding="utf-8") as f:
        for e in entries:
            key = (e.get("skill"), e.get("manifest_sha"), e.get("seeded_id"))
            if e.get("manifest_sha") and key in seen:
                continue
            seen.add(key)
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
            added += 1
    return added


def recall_summary(ledger_path: pathlib.Path, skill: str) -> dict:
    """{detected, total, unmeasured(n<5)} across all of a skill's seeded records."""
    recs = [r for r in _ledger_records(ledger_path) if r.get("skill") == skill]
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
    mhash = manifest_hash(manifest)
    entries = [{"date": today, "skill": args.skill, "manifest_sha": mhash,
                "seeded_id": m.get("defect_id", m["path"]),
                "detected": id(m) not in missed}
               for m in manifest if m["kind"] == "seeded"]
    added = append_recall_ledger(entries, pathlib.Path(args.recall_ledger))
    if added < len(entries):
        print(f"  [NOTE] {len(entries) - added} seeded result(s) already in the ledger for this manifest; not counted again")
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
