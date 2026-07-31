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

# SKILL.md Step 0.6 detection criterion #2: directory/cwd matches a recurring
# automated-experiment harness naming pattern.
_CWD_HARNESS_PATTERN = re.compile(r"pair[-_]?run|\barm[-_]?[ab]\b|a[-_]?b[-_]?(test|arm)|pipeline", re.IGNORECASE)


def classify_session(meta: dict) -> tuple:
    """Classify whether a session is auto-derived. Returns (status, reason) — status is 'include' or 'exclude'."""
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
    if isinstance(cwd, str) and _CWD_HARNESS_PATTERN.search(cwd):
        return ("exclude", f"cwd matches automated-experiment harness naming pattern: {cwd}")

    originator = meta.get("originator", "")
    if isinstance(originator, str) and originator.lower() in ("sdk", "bot", "exec"):
        first_msg = meta.get("first_message", "")
        if not first_msg or not isinstance(first_msg, str):
            return ("exclude", f"originator={originator} + no direct user-input signal present")

    return ("include", "organic session")


def scan_sessions(paths: list) -> dict:
    """Classify a list of session-meta files -> aggregate counts + minimum-sample verdict.

    A single corrupted file does not abort the rest of the batch — corrupted
    files are recorded under `unreadable`.
    """
    included = []
    excluded = []
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
        status, reason = classify_session(meta)
        if status == "exclude":
            excluded.append({"path": p, "reason": reason})
            continue
        included.append({"path": p, "reason": reason})
        total_messages += int(meta.get("message_count", 0) or 0)
        total_artifacts += int(meta.get("artifact_count", 0) or 0)
        deep_ratio_max = max(deep_ratio_max, float(meta.get("deep_conversation_ratio", 0.0) or 0.0))

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
        "total_messages": total_messages,
        "total_artifacts": total_artifacts,
        "meets_minimum": meets_minimum,
        "single_session_exception": single_session_exception,
        "included": included,
        "excluded": excluded,
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
