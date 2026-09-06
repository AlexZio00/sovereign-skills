#!/usr/bin/env python3
"""session_hygiene_scan.py — collab-audit Step 0 / Step 0.6 deterministic gate.

Computes the Step 0.6 source hygiene filter (automated-session detection) and
the Step 0 minimum-sample verdict (2+ sessions OR 100+ messages, with a
single-session exception) deterministically. Principle: counting is a job for
code — pattern interpretation is a job for the LLM.

Usage:
  python session_hygiene_scan.py --meta-dir <DIR>   # scan every *.json session-meta file in DIR
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

# SKILL.md Step 0.6 detection criterion #2, strong signal: naming conventions
# specific to paired/multi-arm automated experiment harnesses. Unlikely to
# appear in an ordinary project name, so a confident 'exclude' is warranted.
_CWD_STRONG_HARNESS_PATTERN = re.compile(r"pair[-_]?run|\barm[-_]?[ab]\b|a[-_]?b[-_]?(test|arm)", re.IGNORECASE)
# Weak signal: a generic word that also shows up in perfectly ordinary user
# projects (data pipeline, CI/CD pipeline, ETL pipeline). On its own this is
# not enough to confidently exclude a session as automated — classify as
# 'uncertain' instead so a real project named e.g. "data-pipeline-tool" isn't
# silently misclassified as an automation harness.
_CWD_WEAK_HARNESS_PATTERN = re.compile(r"pipeline", re.IGNORECASE)


def classify_session(meta: dict) -> tuple:
    """Classify a session as organic, needing review, or auto-derived.

    Returns (status, reason) — status is one of:
      'include'   — organic user session
      'uncertain' — cannot confirm either way; needs human review, not
                    auto-folded into the analysis population
      'exclude'   — confidently auto-derived (subagent/thread_spawn/etc.)

    Caller contract: `meta` must already be a dict — non-dict roots (e.g. a
    JSON array) must be routed to the 'unreadable' bucket by the caller
    before calling this function, since a dict-only API here is what makes
    the .get()-based checks below safe.
    """
    session_meta = meta.get("session_meta")
    source = session_meta.get("source") if isinstance(session_meta, dict) else None
    if isinstance(source, dict):
        if source.get("thread_spawn"):
            return ("exclude", "subagent/thread_spawn auto-derived session")
        if source.get("subagent"):
            return ("exclude", "subagent/thread_spawn auto-derived session")

    if meta.get("agent_nickname"):
        return ("exclude", "agent_nickname present — automated session")

    cwd = meta.get("cwd", "")
    if isinstance(cwd, str):
        if _CWD_STRONG_HARNESS_PATTERN.search(cwd):
            return ("exclude", f"cwd matches automated-experiment harness naming pattern: {cwd}")
        if _CWD_WEAK_HARNESS_PATTERN.search(cwd):
            return ("uncertain", f"cwd contains generic automation-adjacent word ('pipeline') with no other automation signal — likely an ordinary project, needs manual review: {cwd}")

    originator = meta.get("originator", "")
    if isinstance(originator, str) and originator.lower() in ("sdk", "bot", "exec"):
        first_msg = meta.get("first_message", "")
        if not first_msg or not isinstance(first_msg, str):
            return ("exclude", f"originator={originator} + no direct user-input signal present")

    # No exclusion/uncertainty marker matched. Before defaulting to organic,
    # reject a completely empty metadata object — an empty {} carries zero
    # signal and must not be auto-classified as organic just because no
    # exclusion marker happened to be absent (absence of evidence for
    # automation is not evidence of an organic session).
    if len(meta) == 0:
        return ("uncertain", "empty metadata object — no signal to confirm organic origin")

    return ("include", "organic session")


def _coerce_count(value, field_name: str) -> int:
    """Strict numeric coercion for message/artifact count fields.

    Rejects strings, lists, dicts, bools etc. — a count field must actually
    be a number, not something that merely looks numeric (e.g. "10" or "many").
    Raises TypeError with a descriptive message on anything else; missing/None
    defaults to 0.
    """
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric, got {type(value).__name__}: {value!r}")
    return int(value)


def _coerce_ratio(value, field_name: str) -> float:
    """Strict numeric coercion for ratio fields (e.g. deep_conversation_ratio)."""
    if value is None:
        return 0.0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric, got {type(value).__name__}: {value!r}")
    return float(value)


def scan_sessions(paths: list) -> dict:
    """Classify a list of session-meta files -> aggregate counts + minimum-sample verdict.

    A single corrupted or malformed file does not abort the rest of the batch
    — corrupted JSON, non-object roots, and non-numeric count fields are all
    recorded under `unreadable` instead of crashing or being silently coerced.
    """
    included = []
    excluded = []
    uncertain = []
    unreadable = []
    total_messages = 0
    total_artifacts = 0
    deep_ratio_max = 0.0

    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            unreadable.append({"path": p, "error": str(e)})
            continue

        if not isinstance(meta, dict):
            unreadable.append({"path": p, "error": f"session-meta root must be a JSON object, got {type(meta).__name__}"})
            continue

        status, reason = classify_session(meta)
        if status == "exclude":
            excluded.append({"path": p, "reason": reason})
            continue
        if status == "uncertain":
            uncertain.append({"path": p, "reason": reason})
            continue

        try:
            msg_count = _coerce_count(meta.get("message_count"), "message_count")
            artifact_count = _coerce_count(meta.get("artifact_count"), "artifact_count")
            deep_ratio = _coerce_ratio(meta.get("deep_conversation_ratio"), "deep_conversation_ratio")
        except TypeError as e:
            unreadable.append({"path": p, "error": str(e)})
            continue

        included.append({"path": p, "reason": reason})
        total_messages += msg_count
        total_artifacts += artifact_count
        deep_ratio_max = max(deep_ratio_max, deep_ratio)

    n_sessions = len(included)
    single_session_exception = (
        n_sessions == 1
        and total_messages >= 50
        and (total_artifacts >= 3 or deep_ratio_max >= 0.70)
    )
    meets_minimum = (n_sessions >= 2) or (total_messages >= 100) or single_session_exception

    return {
        "included_count": n_sessions,
        "excluded_count": len(excluded),
        "uncertain_count": len(uncertain),
        "total_messages": total_messages,
        "total_artifacts": total_artifacts,
        "meets_minimum": meets_minimum,
        "single_session_exception": single_session_exception,
        "included": included,
        "excluded": excluded,
        "uncertain": uncertain,
        "unreadable": unreadable,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="collab-audit session hygiene filter + minimum-sample gate")
    ap.add_argument("--meta-dir", required=True, help="Directory containing session-meta JSON files")
    args = ap.parse_args(argv)

    paths = sorted(glob.glob(os.path.join(args.meta_dir, "*.json")))
    if not paths:
        print(json.dumps({"error": "no meta files found", "meta_dir": args.meta_dir}, ensure_ascii=False))
        return 1

    result = scan_sessions(paths)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
