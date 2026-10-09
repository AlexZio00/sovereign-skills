"""Claude Code session JSONL -> session-meta JSON for session_hygiene_scan.py --meta-dir.

Why: the `--meta-dir` gate in SKILL.md Step 0/0.6 needs one session-meta JSON per session, but real Claude Code
JSONL files (~/.claude/projects/<proj>/<session>.jsonl) have no `session_meta.source.thread_spawn` field, so the
gate could not run on real data. This script does that conversion.

Field definitions (deterministic):
- message_count: human-typed user rows (user rows holding only tool_result are excluded) + assistant rows
- artifact_count: assistant tool_use calls to Write / Edit / NotebookEdit / Artifact
- deep_conversation_ratio: assistant rows with a thinking block / assistant rows (a proxy for depth of reasoning)
- session_meta.source.thread_spawn: True if the file sits under a `subagents/` folder or most rows are isSidechain
Prompt text is never stored (counts only).

usage: python extract_session_meta.py --out-dir DIR [--projects-dir ~/.claude/projects] [--days 30] [--max 20]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ARTIFACT_TOOLS = {"Write", "Edit", "NotebookEdit", "Artifact"}


def _is_tool_result_only(content) -> bool:
    return isinstance(content, list) and bool(content) and all(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def summarize(path: Path) -> dict:
    human = assistant = sidechain = rows = artifacts = thinking_turns = 0
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = obj.get("type")
        if t not in ("user", "assistant"):
            continue
        rows += 1
        if obj.get("isSidechain"):
            sidechain += 1
        content = (obj.get("message") or {}).get("content")
        if t == "user":
            if not _is_tool_result_only(content):
                human += 1
            continue
        assistant += 1
        blocks = content if isinstance(content, list) else []
        if any(isinstance(b, dict) and b.get("type") == "thinking" for b in blocks):
            thinking_turns += 1
        artifacts += sum(1 for b in blocks if isinstance(b, dict) and b.get("type") == "tool_use"
                         and b.get("name") in ARTIFACT_TOOLS)
    spawned = "subagents" in path.parts or (rows > 0 and sidechain / rows > 0.5)
    return {
        "message_count": human + assistant,
        "artifact_count": artifacts,
        "deep_conversation_ratio": round(thinking_turns / assistant, 4) if assistant else 0.0,
        "session_meta": {"source": {"thread_spawn": spawned}},
        "_source": {"file": path.name, "human_messages": human, "assistant_messages": assistant},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--projects-dir", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--max", type=int, default=20)
    a = ap.parse_args(argv)
    cutoff = time.time() - a.days * 86400
    files = sorted((p for p in Path(a.projects_dir).rglob("*.jsonl") if p.stat().st_mtime >= cutoff),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:a.max]
    os.makedirs(a.out_dir, exist_ok=True)
    for p in files:
        name = f"{p.parent.name}__{p.stem}.json"
        with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as f:
            json.dump(summarize(p), f, ensure_ascii=False, indent=2)
    print(f"sessions={len(files)} out={a.out_dir}", file=sys.stderr)
    return 0 if files else 1


if __name__ == "__main__":
    raise SystemExit(main())
