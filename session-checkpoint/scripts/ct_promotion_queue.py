#!/usr/bin/env python3
"""ct_promotion_queue.py — Stage 1: deterministic, opt-in detection and
queueing of CT (permanent-fact) promotion candidates.

Called on every session-checkpoint Phase 1.5 run (only when the opt-in
marker file exists). Scans context-log.md, finds token-overlap clusters that
reach a T2 threshold (3+ mentions), confirms they don't already exist in
MEMORY.md's CT section, and appends the survivors to
~/.claude/.harness/ct-promotion-queue.jsonl.

This script never writes to MEMORY.md or context-log.md — read-only on both.
The queue-file append is its only write path (statically verifiable: no code
path opens memory_md_path in write/append mode — test_ct_promotion_queue.py's
no-leak static self-test checks this). No LLM judgment anywhere — pure
counting and string matching.

Usage:
  python ct_promotion_queue.py scan --context-log <path> --memory-md <path>
      [--tombstones-dir <dir>] [--queue <path>] [--marker <path>]
      [--scope global|project] [--project-path <path>] [--source <trusted:X|clean:internal|untrusted:X>]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import UTC, datetime

_ENTRY_RE = re.compile(r"^-?\s*\[(\d{4}-\d{2}-\d{2})\]")
_PATH_TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\-]+\.[A-Za-z]{1,5}")
_QUOTE_TOKEN_RE = re.compile(r"[\"'`]([^\"'`]{2,40})[\"'`]")
_PROPER_NOUN_RE = re.compile(r"\b[A-Z][A-Za-z0-9_]{2,}\b")

# TYPE tags from memory-format.md's context-log type list, plus common memory
# abbreviations. Leaving these out of the stopword set would let unrelated
# entries get merged into one cluster just because they share the same
# [EVENT] tag (regression test: see test 12).
_STOPWORD_TOKENS = {
    "MEMORY", "TL", "CT", "TODO", "TBD",
    "EVENT", "PLAN", "DECISION", "MILESTONE", "LESSON",
    "CRYSTALLIZE_CANDIDATE", "QUARANTINE", "INCIDENT",
}

T2_THRESHOLD = 3
NOVELTY_SIMILARITY_THRESHOLD = 0.9  # reference only — the actual decision is is_duplicate_in_queue's exact-match implementation (see its docstring)
REGRET_KEYWORD_MIN_MATCH = 3
DEFAULT_MARKER = os.path.expanduser("~/.claude/.harness/memory-ct-autopatch.enabled")
DEFAULT_QUEUE = os.path.expanduser("~/.claude/.harness/ct-promotion-queue.jsonl")
DEFAULT_TOMBSTONES_DIR = os.path.expanduser("~/.claude/.harness/memory-tombstones")


def is_enabled(marker_path: str = DEFAULT_MARKER) -> bool:
    """Whether the opt-in marker file exists. If not, the caller must end
    Stage 1 entirely without reading anything else."""
    return os.path.isfile(marker_path)


def extract_entries(text: str) -> list[tuple[int, str]]:
    """From context-log.md, extract only lines that start with a date
    bracket (returns 1-indexed line number, stripped original text)."""
    lines = text.splitlines()
    return [(i + 1, line.strip()) for i, line in enumerate(lines) if _ENTRY_RE.match(line.strip())]


def tokenize(line: str) -> set[str]:
    """File-path-shaped tokens + quoted phrases + proper nouns — a
    lightweight clustering heuristic (DRY with memory-dream SKILL.md's SAGE
    lightweight discriminator: string matching only, no new similarity
    engine)."""
    tokens: set[str] = set()
    tokens.update(_PATH_TOKEN_RE.findall(line))
    tokens.update(m.strip() for m in _QUOTE_TOKEN_RE.findall(line))
    tokens.update(_PROPER_NOUN_RE.findall(line))
    return {t for t in tokens if t and t not in _STOPWORD_TOKENS}


def cluster_entries(entries: list[tuple[int, str]]) -> list[dict]:
    """Greedily merge lines that share 1+ token. Only returns clusters where
    mention_count >= T2_THRESHOLD.

    Returns: [{"lines": [(lineno, text), ...], "tokens": set, "mention_count": N}, ...]
    """
    tokenized = [(lineno, text, tokenize(text)) for lineno, text in entries]
    tokenized = [t for t in tokenized if t[2]]  # a line with no tokens can't be clustered — drop it
    clusters: list[dict] = []
    used: set[int] = set()
    for i, (lineno_i, text_i, tokens_i) in enumerate(tokenized):
        if lineno_i in used:
            continue
        group = [(lineno_i, text_i)]
        group_tokens = set(tokens_i)
        used.add(lineno_i)
        for lineno_j, text_j, tokens_j in tokenized[i + 1:]:
            if lineno_j in used:
                continue
            if group_tokens & tokens_j:
                group.append((lineno_j, text_j))
                group_tokens |= tokens_j
                used.add(lineno_j)
        if len(group) >= T2_THRESHOLD:
            clusters.append({"lines": group, "tokens": group_tokens, "mention_count": len(group)})
    return clusters


def summarize_topic(cluster: dict) -> str:
    """Pick the cluster's most frequent token as the representative topic
    (ties broken by alphabetical minimum — deterministic tie-break)."""
    freq: dict[str, int] = {}
    for _lineno, text in cluster["lines"]:
        for tok in tokenize(text):
            freq[tok] = freq.get(tok, 0) + 1
    if not freq:
        return "(no tokens)"
    max_count = max(freq.values())
    return sorted(t for t, c in freq.items() if c == max_count)[0]


def ct_topic_exists(memory_md_text: str, topic: str) -> bool:
    """Whether the topic string already appears in MEMORY.md's text (plain
    substring check — deterministic, equivalent to grep)."""
    return topic in memory_md_text


def load_queue_records(queue_path: str) -> list[dict]:
    """Read the queue JSONL and return a list of records. Returns [] if the
    file doesn't exist. Corrupted lines and non-dict lines are skipped
    (append-only tolerance) — json.loads can succeed on a line that parses
    to something other than a dict (a bare list/str/number), and a
    downstream record.get() call on that would crash with AttributeError
    (found by code-reviewer 2026-08-02, MEDIUM; reachable because
    memory-dream's Step 5d appends to this file directly without schema
    validation)."""
    if not os.path.isfile(queue_path):
        return []
    records: list[dict] = []
    with open(queue_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                records.append(parsed)
    return records


def append_record(record: dict, queue_path: str) -> None:
    """Append one record to the queue JSONL (creating the directory if
    needed) — this script's only write path."""
    parent = os.path.dirname(queue_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(queue_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def is_duplicate_in_queue(topic_summary: str, existing_records: list[dict],
                           scope: str = "global", project_path=None) -> bool:
    """Duplicate decision based on the status of the *most recent* record
    matching the same (scope, project_path, topic_summary) key.

    Because the queue is append-only, the record appended latest in the file
    is the most current one — using first-match instead would permanently
    block re-queueing after an old `queued` record later resolves to
    expired/rejected (regression: see test_ct_promotion_queue.py's
    "re-queue after resolution" case; found by code-reviewer 2026-08-02,
    HIGH). scope/project_path are part of the key too, to avoid false-
    positive collisions when two different projects happen to share the
    same topic_summary (e.g. "config.py").

    Since summarize_topic() always returns a single representative token,
    Jaccard similarity (NOVELTY_SIMILARITY_THRESHOLD) reduces to comparing
    two singleton sets (intersection=1 → 1.0, else 0.0) — so this is
    simplified to a plain string-equality check instead of adding a
    separate similarity engine (reuses the existing Novelty gate, DRY).
    """
    latest_status = None
    for record in existing_records:
        if record.get("topic_summary") != topic_summary:
            continue
        if record.get("scope") != scope:
            continue
        if scope == "project" and record.get("project_path") != project_path:
            continue
        latest_status = record.get("status")
    return latest_status in ("queued", "drafted")


def check_resurfaced(topic_tokens: set[str], tombstones_dir: str) -> bool:
    """If REGRET_KEYWORD_MIN_MATCH or more of topic_tokens match a
    tombstone's (normalized) item_summary, treat this as a previously
    deleted fact resurfacing (reuses memory-dream SKILL.md's "Regret
    comparison" logic)."""
    if not os.path.isdir(tombstones_dir):
        return False
    normalized_tokens = {t.strip().lower() for t in topic_tokens if t.strip()}
    if not normalized_tokens:
        return False
    for path in sorted(glob.glob(os.path.join(tombstones_dir, "*.jsonl"))):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    summary = str(record.get("item_summary", "")).lower()
                    match_count = sum(1 for t in normalized_tokens if t in summary)
                    if match_count >= REGRET_KEYWORD_MIN_MATCH:
                        return True
        except OSError:
            continue
    return False


def build_record(cluster: dict, context_log_name: str, scope: str, project_path,
                  source: str, resurfaced: bool) -> dict:
    """Assemble one queue record per the design doc's schema (field order
    also matches the design doc's example)."""
    topic = summarize_topic(cluster)
    lines_sorted = sorted(cluster["lines"], key=lambda x: x[0])
    record: dict = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "scope": scope,
    }
    if scope == "project" and project_path:
        record["project_path"] = project_path
    record["topic_summary"] = topic
    record["mention_count"] = cluster["mention_count"]
    record["evidence_refs"] = [f"{context_log_name} L{lineno}" for lineno, _ in lines_sorted]
    record["source"] = source
    record["status"] = "queued"
    if resurfaced:
        record["flag"] = "resurfaced"
    return record


def run_scan(context_log_path: str, memory_md_path: str, tombstones_dir: str, queue_path: str,
             marker_path: str, scope: str, project_path, source: str) -> dict:
    """The full Stage 1 pipeline. If the opt-in condition isn't met, returns
    immediately without reading any file at all."""
    if not is_enabled(marker_path):
        return {"enabled": False}

    with open(context_log_path, encoding="utf-8") as f:
        context_log_text = f.read()
    memory_md_text = ""
    if os.path.isfile(memory_md_path):
        with open(memory_md_path, encoding="utf-8") as f:
            memory_md_text = f.read()

    entries = extract_entries(context_log_text)
    clusters = cluster_entries(entries)
    existing_records = load_queue_records(queue_path)
    context_log_name = os.path.basename(context_log_path)

    enqueued = 0
    skipped_ct_exists = 0
    skipped_duplicate = 0
    resurfaced_count = 0
    resurfaced_topics: list[str] = []

    for cluster in clusters:
        topic = summarize_topic(cluster)
        if ct_topic_exists(memory_md_text, topic):
            skipped_ct_exists += 1
            continue
        if is_duplicate_in_queue(topic, existing_records, scope, project_path):
            skipped_duplicate += 1
            continue
        resurfaced = check_resurfaced(cluster["tokens"], tombstones_dir)
        record = build_record(cluster, context_log_name, scope, project_path, source, resurfaced)
        append_record(record, queue_path)
        existing_records.append(record)
        enqueued += 1
        if resurfaced:
            resurfaced_count += 1
            resurfaced_topics.append(topic)

    return {
        "enabled": True,
        "clusters_found": len(clusters),
        "enqueued": enqueued,
        "skipped_ct_exists": skipped_ct_exists,
        "skipped_duplicate": skipped_duplicate,
        "resurfaced": resurfaced_count,
        "resurfaced_topics": resurfaced_topics,
    }


def cmd_scan(args) -> int:
    try:
        result = run_scan(
            context_log_path=args.context_log,
            memory_md_path=args.memory_md,
            tombstones_dir=args.tombstones_dir,
            queue_path=args.queue,
            marker_path=args.marker,
            scope=args.scope,
            project_path=args.project_path,
            source=args.source,
        )
    except (OSError, UnicodeDecodeError) as e:
        failing_path = getattr(e, "filename", None) or "(unknown path)"
        sys.stderr.write(f"[CT-PROMOTION-QUEUE ERROR] I/O failure at {failing_path}: {e}\n")
        return 2
    if not result["enabled"]:
        print("[CT Promotion Queue] no opt-in marker — skipping")
        return 0
    print(
        f"[CT Promotion Queue] clusters={result['clusters_found']} "
        f"enqueued={result['enqueued']} skip_ct_exists={result['skipped_ct_exists']} "
        f"skip_duplicate={result['skipped_duplicate']} resurfaced={result['resurfaced']}"
    )
    for topic in result["resurfaced_topics"]:
        print(f"⚠️ Resurfaced: {topic}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Stage 1 CT promotion queue scanner (deterministic, opt-in)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--context-log", required=True)
    p_scan.add_argument("--memory-md", required=True)
    p_scan.add_argument("--tombstones-dir", default=DEFAULT_TOMBSTONES_DIR)
    p_scan.add_argument("--queue", default=DEFAULT_QUEUE)
    p_scan.add_argument("--marker", default=DEFAULT_MARKER)
    p_scan.add_argument("--scope", default="global", choices=["global", "project"])
    p_scan.add_argument("--project-path", default=None)
    p_scan.add_argument("--source", default="clean:internal")
    p_scan.set_defaults(func=cmd_scan)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
