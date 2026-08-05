"""test_ct_promotion_queue.py — regression tests for ct_promotion_queue."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_promotion_queue as ctq

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ct_promotion_queue.py")

CASES = []
def case(name, fn):
    CASES.append((name, fn))

# 1. is_enabled: no marker -> False
def _is_enabled_false():
    with tempfile.TemporaryDirectory() as td:
        marker = os.path.join(td, "memory-ct-autopatch.enabled")
        return ctq.is_enabled(marker) is False
case("is_enabled: marker missing -> False", _is_enabled_false)

# 2. is_enabled: marker present -> True
def _is_enabled_true():
    with tempfile.TemporaryDirectory() as td:
        marker = os.path.join(td, "memory-ct-autopatch.enabled")
        with open(marker, "w", encoding="utf-8") as f:
            f.write("")
        return ctq.is_enabled(marker) is True
case("is_enabled: marker present -> True", _is_enabled_true)

# 3. extract_entries: only date-bracket lines, 1-indexed lineno, with/without leading dash
case("extract_entries: only date-bracket lines, 1-index lineno, optional leading dash", lambda: ctq.extract_entries(
    "unrelated header\n[2026-08-01] [EVENT] [ttl:30d] [ref:0] content1\nunrelated line\n- [2026-08-02] [EVENT] [ttl:30d] [ref:0] content2"
) == [(2, "[2026-08-01] [EVENT] [ttl:30d] [ref:0] content1"), (4, "- [2026-08-02] [EVENT] [ttl:30d] [ref:0] content2")])

# 4. extract_entries: empty text -> empty list
case("extract_entries: empty text -> []", lambda: ctq.extract_entries("") == [])

# 5. tokenize: extracts a file-path-shaped token
case("tokenize: extracts file-path-like token", lambda: "ct_promotion_queue.py" in ctq.tokenize(
    "wrote a new script ct_promotion_queue.py"
))

# 6. tokenize: extracts a quoted phrase
case("tokenize: extracts quoted token", lambda: "core-idea" in ctq.tokenize(
    'the core of this design is "core-idea", a three-stage split'
))

# 7. tokenize: extracts a proper noun
case("tokenize: extracts proper-noun token", lambda: "Stage" in ctq.tokenize(
    "Stage 1 is deterministic, Stage 2 is LLM-based"
))

# 8. tokenize: excludes generic stopwords
case("tokenize: excludes generic stopword tokens", lambda: "MEMORY" not in ctq.tokenize(
    "MEMORY promotion review"
))

# 8b. tokenize: excludes context-log TYPE tags (EVENT, etc.) — guards against cross-cluster contamination via shared tags
case("tokenize: excludes context-log TYPE tags (EVENT/MILESTONE/etc, cross-cluster contamination guard)", lambda: (
    "EVENT" not in ctq.tokenize("[2026-08-01] [EVENT] [ttl:30d] [ref:0] unrelated content")
    and "MILESTONE" not in ctq.tokenize("[2026-08-01] [MILESTONE] [ttl:90d] [ref:0] unrelated content")
))

# 9. cluster_entries: 3 lines sharing a token -> 1 cluster, mention_count=3
def _cluster_related():
    entries = [
        (1, "ct_promotion_queue.py design discussion"),
        (2, "ct_promotion_queue.py implementation start"),
        (3, "ct_promotion_queue.py test authoring"),
    ]
    clusters = ctq.cluster_entries(entries)
    return len(clusters) == 1 and clusters[0]["mention_count"] == 3
case("cluster_entries: 3 lines sharing token -> 1 cluster, mention_count=3", _cluster_related)

# 10. cluster_entries: 3 unrelated lines (no shared token) -> no cluster
def _cluster_unrelated():
    entries = [
        (1, "alpha.py discussion"),
        (2, "beta.py discussion"),
        (3, "gamma.py discussion"),
    ]
    clusters = ctq.cluster_entries(entries)
    return clusters == []
case("cluster_entries: unrelated lines (no shared token) -> no cluster", _cluster_unrelated)

# 11. cluster_entries: only 2 lines share a token (below T2) -> no cluster
def _cluster_below_threshold():
    entries = [
        (1, "delta.py discussion1"),
        (2, "delta.py discussion2"),
        (3, "unrelated content"),
    ]
    clusters = ctq.cluster_entries(entries)
    return clusters == []
case("cluster_entries: only 2 shared-token lines (below T2) -> no cluster", _cluster_below_threshold)

# 12. cluster_entries: realistic format (with TYPE tag) — two distinct topics must NOT merge just from sharing a tag (key regression)
def _cluster_no_tag_contamination():
    entries = [
        (1, "[2026-08-01] [EVENT] [ttl:30d] [ref:0] newfeature.py design"),
        (2, "[2026-08-01] [EVENT] [ttl:30d] [ref:0] newfeature.py implementation"),
        (3, "[2026-08-01] [EVENT] [ttl:30d] [ref:0] newfeature.py test"),
        (4, "[2026-08-01] [EVENT] [ttl:30d] [ref:0] oldfeature.py design"),
        (5, "[2026-08-01] [EVENT] [ttl:30d] [ref:0] oldfeature.py implementation"),
        (6, "[2026-08-01] [EVENT] [ttl:30d] [ref:0] oldfeature.py test"),
    ]
    clusters = ctq.cluster_entries(entries)
    topics = sorted(ctq.summarize_topic(c) for c in clusters)
    return len(clusters) == 2 and topics == ["newfeature.py", "oldfeature.py"]
case("cluster_entries: shared [EVENT] tag alone must NOT merge unrelated topics", _cluster_no_tag_contamination)

# 13. summarize_topic: most frequent token, ties broken alphabetically
def _summarize_topic_basic():
    cluster = {"lines": [
        (1, "ct_promotion_queue.py design"),
        (2, "ct_promotion_queue.py implementation"),
        (3, "ct_promotion_queue.py test"),
    ]}
    return ctq.summarize_topic(cluster) == "ct_promotion_queue.py"
case("summarize_topic: most frequent token wins", _summarize_topic_basic)

# 14. ct_topic_exists: present -> True
case("ct_topic_exists: substring present -> True", lambda: ctq.ct_topic_exists(
    "## Section\n- adopted ct_promotion_queue.py", "ct_promotion_queue.py"
) is True)

# 15. ct_topic_exists: absent -> False
case("ct_topic_exists: substring absent -> False", lambda: ctq.ct_topic_exists(
    "## Section\n- unrelated content", "ct_promotion_queue.py"
) is False)

# 16. load_queue_records: missing file -> []
def _load_queue_missing():
    with tempfile.TemporaryDirectory() as td:
        return ctq.load_queue_records(os.path.join(td, "nope.jsonl")) == []
case("load_queue_records: missing file -> []", _load_queue_missing)

# 17. load_queue_records: parses valid JSONL, skips corrupted lines
def _load_queue_parses_valid_skips_broken():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "q.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"topic_summary":"a","status":"queued"}\n')
            f.write("not json\n")
            f.write('{"topic_summary":"b","status":"drafted"}\n')
        records = ctq.load_queue_records(path)
        return len(records) == 2 and records[0]["topic_summary"] == "a" and records[1]["topic_summary"] == "b"
case("load_queue_records: parses valid lines, skips malformed", _load_queue_parses_valid_skips_broken)

# 18. append_record: creates file+directory fresh, then appends
def _append_record_creates_dir_and_file():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "sub", "q.jsonl")
        ctq.append_record({"topic_summary": "x", "status": "queued"}, path)
        records = ctq.load_queue_records(path)
        return len(records) == 1 and records[0]["topic_summary"] == "x"
case("append_record: creates parent dir + appends JSONL", _append_record_creates_dir_and_file)

# 19. is_duplicate_in_queue: matching topic_summary + queued status + scope -> True
# (a real record always has "scope" filled by build_record(), so including scope in the fixture is
#  realistic — covers the added scope/project_path matching, fixed by code-reviewer 2026-08-02, HIGH)
case("is_duplicate_in_queue: matches queued status + scope -> True", lambda: ctq.is_duplicate_in_queue(
    "topic-a", [{"topic_summary": "topic-a", "status": "queued", "scope": "global"}]
) is True)

# 20. is_duplicate_in_queue: applied status is excluded from duplicate detection -> False
case("is_duplicate_in_queue: applied status excluded -> False", lambda: ctq.is_duplicate_in_queue(
    "topic-a", [{"topic_summary": "topic-a", "status": "applied", "scope": "global"}]
) is False)

# 21. check_resurfaced: no tombstones directory -> False
def _check_resurfaced_no_dir():
    with tempfile.TemporaryDirectory() as td:
        return ctq.check_resurfaced({"foo"}, os.path.join(td, "nope")) is False
case("check_resurfaced: tombstones dir missing -> False", _check_resurfaced_no_dir)

# 22. check_resurfaced: 3+ tokens match -> True
def _check_resurfaced_match():
    with tempfile.TemporaryDirectory() as td:
        tpath = os.path.join(td, "2026-07.jsonl")
        with open(tpath, "w", encoding="utf-8") as f:
            f.write('{"item_summary":"ct_promotion_queue.py stage1 clustering rejected design"}\n')
        tokens = {"ct_promotion_queue.py", "stage1", "clustering"}
        return ctq.check_resurfaced(tokens, td) is True
case("check_resurfaced: 3+ token match -> True", _check_resurfaced_match)

# 23. check_resurfaced: only 2 tokens match (below threshold) -> False
def _check_resurfaced_below_threshold():
    with tempfile.TemporaryDirectory() as td:
        tpath = os.path.join(td, "2026-07.jsonl")
        with open(tpath, "w", encoding="utf-8") as f:
            f.write('{"item_summary":"ct_promotion_queue.py stage1 unrelated"}\n')
        tokens = {"ct_promotion_queue.py", "stage1", "unrelated-token"}
        return ctq.check_resurfaced(tokens, td) is False
case("check_resurfaced: only 2 token match (below threshold) -> False", _check_resurfaced_below_threshold)

# 24. build_record: project_path included only when scope=project
def _build_record_project_path():
    cluster = {"lines": [(1, "a"), (2, "a"), (3, "a")], "mention_count": 3}
    rec_project = ctq.build_record(cluster, "context-log.md", "project", "D:\\ProjectA", "clean:internal", False)
    rec_global = ctq.build_record(cluster, "context-log.md", "global", None, "clean:internal", False)
    return "project_path" in rec_project and "project_path" not in rec_global
case("build_record: project_path only when scope=project", _build_record_project_path)

# 25. build_record: flag included only when resurfaced=True
def _build_record_resurfaced_flag():
    cluster = {"lines": [(1, "a"), (2, "a"), (3, "a")], "mention_count": 3}
    rec_flagged = ctq.build_record(cluster, "context-log.md", "global", None, "clean:internal", True)
    rec_clean = ctq.build_record(cluster, "context-log.md", "global", None, "clean:internal", False)
    return rec_flagged.get("flag") == "resurfaced" and "flag" not in rec_clean
case("build_record: flag=resurfaced only when resurfaced=True", _build_record_resurfaced_flag)

# 26. run_scan: no opt-in marker -> doesn't even create the queue file (confirms the opt-in requirement is actually enforced)
def _run_scan_disabled_no_write():
    with tempfile.TemporaryDirectory() as td:
        marker = os.path.join(td, "marker.enabled")  # deliberately not created
        queue = os.path.join(td, "queue.jsonl")
        log_path = os.path.join(td, "context-log.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("[2026-08-01] [EVENT] [ttl:30d] [ref:0] x.py discussion\n")
        result = ctq.run_scan(log_path, os.path.join(td, "MEMORY.md"), os.path.join(td, "tomb"),
                               queue, marker, "global", None, "clean:internal")
        return result == {"enabled": False} and not os.path.exists(queue)
case("run_scan: opt-in disabled -> no queue file written", _run_scan_disabled_no_write)

# 27. run_scan: end-to-end 3-line cluster -> 1 enqueue, a topic already in CT only increments the skip count
def _run_scan_end_to_end():
    with tempfile.TemporaryDirectory() as td:
        marker = os.path.join(td, "marker.enabled")
        with open(marker, "w", encoding="utf-8") as f:
            f.write("")
        queue = os.path.join(td, "queue.jsonl")
        log_path = os.path.join(td, "context-log.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] newfeature.py design\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] newfeature.py implementation\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] newfeature.py test\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] oldfeature.py design\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] oldfeature.py implementation\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] oldfeature.py test\n"
            )
        memory_md = os.path.join(td, "MEMORY.md")
        with open(memory_md, "w", encoding="utf-8") as f:
            f.write("## Current Status\n- oldfeature.py already in CT\n")
        result = ctq.run_scan(log_path, memory_md, os.path.join(td, "tomb"), queue, marker,
                               "global", None, "clean:internal")
        records = ctq.load_queue_records(queue)
        return (
            result["enqueued"] == 1
            and result["skipped_ct_exists"] == 1
            and len(records) == 1
            and records[0]["topic_summary"] == "newfeature.py"
            and records[0]["mention_count"] == 3
        )
case("run_scan: end-to-end enqueues new topic, skips CT-existing topic", _run_scan_end_to_end)

# 28. run_scan: a cluster matching a tombstone -> resurfaced count + record flag set ("resurfacing" requirement)
def _run_scan_resurfaced_flag():
    with tempfile.TemporaryDirectory() as td:
        marker = os.path.join(td, "marker.enabled")
        with open(marker, "w", encoding="utf-8") as f:
            f.write("")
        tomb_dir = os.path.join(td, "tomb")
        os.makedirs(tomb_dir)
        with open(os.path.join(tomb_dir, "2026-07.jsonl"), "w", encoding="utf-8") as f:
            f.write('{"item_summary":"ghosttopic.py clusterx legacy rejected design"}\n')
        log_path = os.path.join(td, "context-log.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] GhostTopic.py re-discussion 'ClusterX' Legacy\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] GhostTopic.py re-review 'ClusterX' Legacy\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] GhostTopic.py re-confirmation 'ClusterX' Legacy\n"
            )
        memory_md = os.path.join(td, "MEMORY.md")
        with open(memory_md, "w", encoding="utf-8") as f:
            f.write("")
        queue = os.path.join(td, "queue.jsonl")
        result = ctq.run_scan(log_path, memory_md, tomb_dir, queue, marker, "global", None, "clean:internal")
        records = ctq.load_queue_records(queue)
        return result["resurfaced"] == 1 and len(records) == 1 and records[0].get("flag") == "resurfaced"
case("run_scan: tombstone-matching cluster sets resurfaced flag + count", _run_scan_resurfaced_flag)

# 29. cmd_scan CLI: subprocess integration — prints enabled + summary line, exit 0
def _cli_cmd_scan_smoke():
    with tempfile.TemporaryDirectory() as td:
        marker = os.path.join(td, "marker.enabled")
        with open(marker, "w", encoding="utf-8") as f:
            f.write("")
        log_path = os.path.join(td, "context-log.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] clituple.py design\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] clituple.py implementation\n"
                "[2026-08-01] [EVENT] [ttl:30d] [ref:0] clituple.py test\n"
            )
        memory_md = os.path.join(td, "MEMORY.md")
        queue = os.path.join(td, "queue.jsonl")
        proc = subprocess.run(
            [sys.executable, SCRIPT, "scan", "--context-log", log_path, "--memory-md", memory_md,
             "--queue", queue, "--marker", marker, "--tombstones-dir", os.path.join(td, "tomb")],
            capture_output=True, text=True,
        )
        return proc.returncode == 0 and "enqueued=1" in proc.stdout
case("cmd_scan CLI: end-to-end subprocess -> exit 0, enqueued=1 in stdout", _cli_cmd_scan_smoke)

# 30. static self-test: memory_md_path is never opened in write/append mode (no-leak oracle)
def _no_memory_md_write_leak():
    with open(SCRIPT, encoding="utf-8") as f:
        source = f.read()
    forbidden = [
        'open(memory_md_path, "w"', "open(memory_md_path, 'w'",
        'open(memory_md_path, "a"', "open(memory_md_path, 'a'",
    ]
    return not any(p in source for p in forbidden)
case("static: memory_md_path never opened write/append mode (no-leak oracle)", _no_memory_md_write_leak)

# 31. is_duplicate_in_queue: when queued -> expired is appended in that order, the latest (expired) status allows re-queueing (HIGH regression, code-reviewer 2026-08-02)
case("is_duplicate_in_queue: latest-status-wins allows re-queue after resolution", lambda: ctq.is_duplicate_in_queue(
    "topic-x", [
        {"topic_summary": "topic-x", "status": "queued", "scope": "global"},
        {"topic_summary": "topic-x", "status": "expired", "scope": "global"},
    ]
) is False)

# 32. is_duplicate_in_queue: same topic_summary but scope=project + a different project_path -> not a duplicate
case("is_duplicate_in_queue: same topic_summary, different project_path -> not duplicate", lambda: ctq.is_duplicate_in_queue(
    "config.py",
    [{"topic_summary": "config.py", "status": "queued", "scope": "project", "project_path": "D:\\ProjectA"}],
    scope="project", project_path="D:\\ProjectB",
) is False)

# 33. load_queue_records: a valid-JSON but non-dict line (bare list) is skipped, no crash (MEDIUM regression)
def _load_queue_skips_non_dict_json():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "q.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[1,2,3]\n")
            f.write('{"topic_summary":"a","status":"queued"}\n')
        records = ctq.load_queue_records(path)
        return len(records) == 1 and records[0]["topic_summary"] == "a"
case("load_queue_records: skips valid-JSON-but-non-dict lines, no crash", _load_queue_skips_non_dict_json)

# 34. check_resurfaced: a tombstone file with a valid-JSON but non-dict line mixed in still gets judged from the rest, no crash
def _check_resurfaced_skips_non_dict_json():
    with tempfile.TemporaryDirectory() as td:
        tpath = os.path.join(td, "2026-07.jsonl")
        with open(tpath, "w", encoding="utf-8") as f:
            f.write('"just a string"\n')
            f.write('{"item_summary":"ct_promotion_queue.py stage1 clustering rejected design"}\n')
        tokens = {"ct_promotion_queue.py", "stage1", "clustering"}
        return ctq.check_resurfaced(tokens, td) is True
case("check_resurfaced: skips valid-JSON-but-non-dict lines, no crash", _check_resurfaced_skips_non_dict_json)


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
