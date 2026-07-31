"""test_session_hygiene_scan.py — regression tests for session_hygiene_scan."""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import session_hygiene_scan as shs

CASES = []
def case(name, fn):
    CASES.append((name, fn))

# 1. subagent/thread_spawn marker -> exclude
case("thread_spawn excluded", lambda: shs.classify_session(
    {"session_meta": {"source": {"thread_spawn": True}}})[0] == "exclude")
case("subagent excluded", lambda: shs.classify_session(
    {"session_meta": {"source": {"subagent": True}}})[0] == "exclude")

# 2. agent_nickname marker -> exclude
case("agent_nickname excluded", lambda: shs.classify_session(
    {"agent_nickname": "worker-3"})[0] == "exclude")

# 3. originator=sdk + no direct user-input signal -> exclude
case("originator=sdk no first_message excluded", lambda: shs.classify_session(
    {"originator": "sdk"})[0] == "exclude")

# 4. organic session -> include
case("organic session included", lambda: shs.classify_session(
    {"originator": "user", "first_message": "what should I start with today"})[0] == "include")

# 4b. cwd automated-experiment harness naming pattern -> exclude
case("cwd pair-run pattern excluded", lambda: shs.classify_session(
    {"originator": "user", "first_message": "hi", "cwd": "/home/user/experiments/pair-run-42"})[0] == "exclude")
case("cwd arm-a pattern excluded", lambda: shs.classify_session(
    {"originator": "user", "first_message": "hi", "cwd": "/data/ab-test/arm-a"})[0] == "exclude")
case("cwd pipeline pattern excluded", lambda: shs.classify_session(
    {"originator": "user", "first_message": "hi", "cwd": "/ci/pipeline-run-7"})[0] == "exclude")
case("cwd normal path not excluded", lambda: shs.classify_session(
    {"originator": "user", "first_message": "hi", "cwd": "/home/user/projects/my-app"})[0] == "include")

# 5. scan_sessions: 2+ sessions -> meets_minimum True
def _scan_two_sessions():
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, msgs in enumerate([10, 10]):
            p = os.path.join(td, f"s{i}.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"originator": "user", "first_message": "hi", "message_count": msgs,
                           "artifact_count": 0}, f)
            paths.append(p)
        result = shs.scan_sessions(paths)
        return result["included_count"] == 2 and result["meets_minimum"] is True
case("scan_sessions 2 sessions meets minimum", _scan_two_sessions)

# 6. scan_sessions: 1 session + 100+ messages -> meets_minimum True (message threshold alone is sufficient)
def _scan_single_100msg():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "s0.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"originator": "user", "first_message": "hi", "message_count": 150,
                       "artifact_count": 0}, f)
        result = shs.scan_sessions([p])
        return result["meets_minimum"] is True
case("scan_sessions single session 150 msgs meets minimum", _scan_single_100msg)

# 7. scan_sessions: single-session exception (50+ messages AND 3+ artifacts)
def _scan_single_exception_artifacts():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "s0.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"originator": "user", "first_message": "hi", "message_count": 60,
                       "artifact_count": 3}, f)
        result = shs.scan_sessions([p])
        return result["single_session_exception"] is True and result["meets_minimum"] is True
case("scan_sessions single session exception via artifacts", _scan_single_exception_artifacts)

# 8. scan_sessions: single-session exception NOT met (50+ messages but <3 artifacts AND <70% deep-ratio)
def _scan_single_no_exception():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "s0.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"originator": "user", "first_message": "hi", "message_count": 60,
                       "artifact_count": 1, "deep_conversation_ratio": 0.2}, f)
        result = shs.scan_sessions([p])
        return result["meets_minimum"] is False
case("scan_sessions single session no exception -> fails minimum", _scan_single_no_exception)

# 9. scan_sessions: reports excluded-automated-session count
def _scan_excludes_reported():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "s0.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"session_meta": {"source": {"thread_spawn": True}}}, f)
        result = shs.scan_sessions([p])
        return result["excluded_count"] == 1 and result["included_count"] == 0
case("scan_sessions reports excluded count", _scan_excludes_reported)


# 10. scan_sessions: one corrupted JSON file does not kill the rest of the batch
def _scan_survives_malformed_file():
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "bad.json")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        good = os.path.join(td, "good.json")
        with open(good, "w", encoding="utf-8") as f:
            json.dump({"originator": "user", "first_message": "hi", "message_count": 10, "artifact_count": 0}, f)
        result = shs.scan_sessions([bad, good])
        return (len(result["unreadable"]) == 1 and result["unreadable"][0]["path"] == bad
                and result["included_count"] == 1)
case("scan_sessions survives malformed JSON file", _scan_survives_malformed_file)

def main():
    fails = []
    for name, fn in CASES:
        try:
            ok = fn()
        except Exception as e:
            ok = False
            name = f"{name}  [EXC: {e}]"
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            fails.append(name)
    print(f"\n{len(CASES) - len(fails)}/{len(CASES)} passed")
    return 1 if fails else 0

if __name__ == "__main__":
    raise SystemExit(main())
