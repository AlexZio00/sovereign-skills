"""extract_session_meta self-test (pytest or direct run)."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_session_meta import select_files, summarize  # noqa: E402
from session_hygiene_scan import classify_session  # noqa: E402


def _write(dir_: Path, name: str, rows: list) -> Path:
    p = dir_ / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return p


ROWS = [
    {"type": "user", "cwd": "/work/app", "entrypoint": "cli", "message": {"content": "please do it"}},
    {"type": "assistant", "message": {"id": "m1", "content": [{"type": "thinking"}]}},
    {"type": "assistant", "message": {"id": "m1", "content": [{"type": "tool_use", "id": "t1", "name": "Edit"}]}},
    {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
    {"type": "assistant", "message": {"id": "m2", "content": [{"type": "text"}]}},
]


def test_counts_exclude_tool_results_and_dedupe_message_ids():
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", ROWS))
    # 1 human + 2 distinct assistant messages (m1 is written as 2 rows); m1 has the thinking block
    assert m["message_count"] == 3 and m["artifact_count"] == 1 and m["deep_conversation_ratio"] == 0.5
    assert m["session_meta"]["source"]["thread_spawn"] is False


def test_repeated_rows_of_one_message_count_once():
    rows = [{"type": "user", "message": {"content": "go"}}] + [
        {"type": "assistant", "message": {"id": "same", "content": [{"type": "text"}]}} for _ in range(6)]
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", rows))
    assert m["message_count"] == 2


def test_rows_without_message_id_count_one_each():
    rows = [{"type": "assistant", "message": {"content": [{"type": "text"}]}} for _ in range(3)]
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", rows))
    assert m["message_count"] == 3


def test_cwd_and_entrypoint_are_emitted_when_present_and_omitted_otherwise():
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", ROWS))
        bare = summarize(_write(Path(d), "t.jsonl", ROWS[1:]))
    assert m["cwd"] == "/work/app" and m["entrypoint"] == "cli"
    assert "cwd" not in bare and "entrypoint" not in bare


def test_emitted_cwd_reaches_the_hygiene_classifier():
    rows = [{"type": "user", "cwd": "/exp/pair-run-3", "message": {"content": "go"}}] + ROWS[1:]
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", rows))
    assert classify_session(m)[0] == "exclude"


def test_subagent_folder_marks_thread_spawn_and_classifier_excludes():
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "sess/subagents/agent-1.jsonl", ROWS))
    assert m["session_meta"]["source"]["thread_spawn"] is True
    assert classify_session(m)[0] == "exclude"


def test_output_feeds_classifier_as_organic():
    with tempfile.TemporaryDirectory() as d:
        m = summarize(_write(Path(d), "s.jsonl", ROWS))
    assert classify_session(m)[0] in ("include", "uncertain")


def test_subagent_files_are_filtered_before_the_max_cut():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        organic = _write(root, "proj/s1.jsonl", ROWS)
        os.utime(organic, (1_000_000_000, 1_000_000_000))  # oldest file
        for i in range(3):  # newer subagent files would fill --max 1 if they were not removed first
            _write(root, f"proj/s1/subagents/agent-{i}.jsonl", ROWS)
        files, skipped = select_files(root, 100000, 1)
    assert [p.name for p in files] == ["s1.jsonl"] and skipped == 3


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
