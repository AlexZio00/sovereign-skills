"""Claude Code session JSONL -> session-meta JSON for session_hygiene_scan.py --meta-dir.

Why: the `--meta-dir` gate in SKILL.md Step 0/0.6 needs one session-meta JSON per session, but real Claude Code
JSONL files (~/.claude/projects/<proj>/<session>.jsonl) have no `session_meta.source.thread_spawn` field, so the
gate could not run on real data. This script does that conversion.

Field definitions (deterministic):
- message_count: human-typed user rows (user rows holding only tool_result are excluded) + assistant messages.
  One assistant message is written as several JSONL rows (one per content block), all sharing `message.id`,
  so assistant messages are counted by distinct `message.id` (a row without an id counts as its own message).
- artifact_count: distinct assistant tool_use calls (by tool_use id) to Write / Edit / NotebookEdit / Artifact
- deep_conversation_ratio: assistant messages with a thinking block / assistant messages (a proxy for depth of reasoning)
- session_meta.source.thread_spawn: True if the file sits under a `subagents/` folder or most rows are isSidechain
- cwd: the first non-empty `cwd` value in the file (the project folder the session ran in); omitted if absent
- entrypoint: the first non-empty `entrypoint` value (how Claude Code was started, for example "cli"); omitted if absent
- originator / first_message: NOT emitted. Claude Code JSONL carries no such fields, so the `originator` rule in
  session_hygiene_scan.py cannot fire on this script's output. It applies only to meta files that bring those fields.
Prompt text is never stored (counts and the two short fields above only).

Subagent transcripts (files under a `subagents/` folder) are skipped before the --max cut so that they cannot use up
the sample; their number is reported on stderr as subagent_files_skipped.

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


def is_subagent_file(path: Path) -> bool:
    return "subagents" in path.parts


def summarize(path: Path) -> dict:
    human = sidechain = rows = 0
    assistant_ids = set()  # distinct message.id values
    thinking_ids = set()
    tool_use_ids = set()
    anonymous_assistant = anonymous_thinking = anonymous_artifacts = 0  # rows with no message.id / tool_use id
    cwd = entrypoint = None
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if cwd is None and isinstance(obj.get("cwd"), str) and obj["cwd"]:
                cwd = obj["cwd"]
            if entrypoint is None and isinstance(obj.get("entrypoint"), str) and obj["entrypoint"]:
                entrypoint = obj["entrypoint"]
            t = obj.get("type")
            if t not in ("user", "assistant"):
                continue
            rows += 1
            if obj.get("isSidechain"):
                sidechain += 1
            message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            content = message.get("content")
            if t == "user":
                if not _is_tool_result_only(content):
                    human += 1
                continue
            blocks = content if isinstance(content, list) else []
            mid = message.get("id")
            has_thinking = any(isinstance(b, dict) and b.get("type") == "thinking" for b in blocks)
            if mid:
                assistant_ids.add(mid)
                if has_thinking:
                    thinking_ids.add(mid)
            else:
                anonymous_assistant += 1
                anonymous_thinking += 1 if has_thinking else 0
            for b in blocks:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ARTIFACT_TOOLS:
                    if b.get("id"):
                        tool_use_ids.add(b["id"])
                    else:
                        anonymous_artifacts += 1
    assistant = len(assistant_ids) + anonymous_assistant
    thinking = len(thinking_ids) + anonymous_thinking
    spawned = is_subagent_file(path) or (rows > 0 and sidechain / rows > 0.5)
    meta = {
        "message_count": human + assistant,
        "artifact_count": len(tool_use_ids) + anonymous_artifacts,
        "deep_conversation_ratio": round(thinking / assistant, 4) if assistant else 0.0,
        "session_meta": {"source": {"thread_spawn": spawned}},
        "_source": {"file": path.name, "human_messages": human, "assistant_messages": assistant},
    }
    if cwd:
        meta["cwd"] = cwd
    if entrypoint:
        meta["entrypoint"] = entrypoint
    return meta


def select_files(projects_dir: Path, days: int, max_files: int):
    """(files, subagent_files_skipped): newest first, subagent transcripts removed BEFORE the --max cut."""
    cutoff = time.time() - days * 86400
    recent = [p for p in projects_dir.rglob("*.jsonl") if p.stat().st_mtime >= cutoff]
    organic = [p for p in recent if not is_subagent_file(p)]
    organic.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return organic[:max_files], len(recent) - len(organic)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--projects-dir", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--max", type=int, default=20)
    a = ap.parse_args(argv)
    files, skipped = select_files(Path(a.projects_dir), a.days, a.max)
    os.makedirs(a.out_dir, exist_ok=True)
    for p in files:
        name = f"{p.parent.name}__{p.stem}.json"
        with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as f:
            json.dump(summarize(p), f, ensure_ascii=False, indent=2)
    print(f"sessions={len(files)} subagent_files_skipped={skipped} out={a.out_dir}", file=sys.stderr)
    return 0 if files else 1


if __name__ == "__main__":
    raise SystemExit(main())
