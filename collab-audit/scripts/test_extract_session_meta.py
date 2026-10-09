"""extract_session_meta self-test (pytest or direct run)."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_session_meta import summarize  # noqa: E402
from session_hygiene_scan import classify_session  # noqa: E402


def _write(dir_: Path, name: str, rows: list) -> Path:
    p = dir_ / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return p


ROWS = [
    {"type": "user", "message": {"content": "please do it"}},
    {"type": "assistant", "message": {"content": [{"type": "thinking"}, {"type": "tool_use", "name": "Edit"}]}},
    {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
    {"type": "assistant", "message": {"content": [{"type": "text"}]}},
]


def test_counts_exclude_tool_results():
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", ROWS))
    assert m["message_count"] == 3 and m["artifact_count"] == 1 and m["deep_conversation_ratio"] == 0.5
    assert m["session_meta"]["source"]["thread_spawn"] is False


def test_subagent_folder_marks_thread_spawn_and_classifier_excludes():
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "sess/subagents/agent-1.jsonl", ROWS))
    assert m["session_meta"]["source"]["thread_spawn"] is True
    assert classify_session(m)[0] == "exclude"


def test_output_feeds_classifier_as_organic():
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", ROWS))
    assert classify_session(m)[0] in ("include", "uncertain")


if __name__ == "__main__":
    fails = 0
    for n, fn in list(globals().items()):
        if n.startswith("test_"):
            try:
                fn()
                print("PASS", n)
            except AssertionError as e:
                fails += 1
                print("FAIL", n, e)
    raise SystemExit(1 if fails else 0)
