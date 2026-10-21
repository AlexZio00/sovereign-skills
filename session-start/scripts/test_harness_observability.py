"""test_harness_observability.py — regression tests for harness_observability."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness_observability as hobs

CASES = []
def case(name, fn):
    CASES.append((name, fn))

def _tmp_conn():
    conn = sqlite3.connect(":memory:")
    hobs.ensure_schema(conn)
    return conn

def _tmp_jsonl(lines):
    fd, path = tempfile.mkstemp(suffix=".jsonl", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return path

# 1. unpivot skills[]/agents[]
case("unpivot skills+agents", lambda: hobs._rows_from_invocation_record(
    {"ts": "t", "date": "2026-07-01", "skills": ["forge"], "agents": ["scout"], "discarded": [], "source": "s"}
)[0] == [
    {"ts": "t", "date": "2026-07-01", "month": "2026-07", "name": "forge", "kind": "skill", "source": "s", "session_id": None},
    {"ts": "t", "date": "2026-07-01", "month": "2026-07", "name": "scout", "kind": "agent", "source": "s", "session_id": None},
])

# 2. unpivot discarded (dict form)
case("unpivot discarded dict", lambda: hobs._rows_from_invocation_record(
    {"ts": "t", "date": "2026-07-01", "skills": [], "agents": [], "discarded": [{"skill": "X", "reason": "discard_if"}], "source": "s"}
)[1][0]["skill"] == "X")

# 3. load_invocations_month is idempotent (re-running yields same count)
def _idempotent_load():
    conn = _tmp_conn()
    path = _tmp_jsonl([{"ts": "t", "date": "2026-07-01", "skills": ["forge"], "agents": [], "discarded": [], "source": "s"}])
    n1, _ = hobs.load_invocations_month(conn, path, "2026-07")
    n2, _ = hobs.load_invocations_month(conn, path, "2026-07")
    count = conn.execute("SELECT COUNT(*) FROM invocations").fetchone()[0]
    os.unlink(path)
    return n1 == 1 and n2 == 1 and count == 1
case("load_invocations_month idempotent reload", _idempotent_load)

# 4. malformed line skipped, not crash
def _malformed_skip():
    conn = _tmp_conn()
    fd, path = tempfile.mkstemp(suffix=".jsonl", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("{not valid json\n")
        f.write(json.dumps({"ts": "t", "date": "2026-07-02", "skills": ["x"], "agents": [], "discarded": [], "source": "s"}) + "\n")
    n, _ = hobs.load_invocations_month(conn, path, "2026-07")
    os.unlink(path)
    return n == 1
case("malformed JSONL line skipped not crash", _malformed_skip)

# 5. secret redact: interventions.context / receipts.raw_json get masked on load
def _redact_on_load():
    conn = _tmp_conn()
    ipath = _tmp_jsonl([{"ts": "t", "date": "2026-07-01",
                         "context": "gate fired; leaked api_key: sk-abc123DEF456ghi789xyz"}])  # gitleaks:allow (synthetic test fixture)
    hobs.load_interventions_month(conn, ipath, "2026-07")
    ctx = conn.execute("SELECT context FROM interventions").fetchone()[0]
    os.unlink(ipath)
    return "sk-abc123" not in ctx and "[REDACTED]" in ctx
case("secret redact on interventions.context load", _redact_on_load)

# 6. gc_harness_logs: old files move to _archive, recent files are kept
def _gc_archive():
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, ".harness")
        inv = os.path.join(base, "invocations")
        os.makedirs(inv)
        old = os.path.join(inv, "2026-01.jsonl")
        new = os.path.join(inv, "2026-07.jsonl")
        for p in (old, new):
            with open(p, "w", encoding="utf-8") as f:
                f.write("{}\n")
        old_mtime = __import__("time").time() - 200 * 86400  # 200 days ago
        os.utime(old, (old_mtime, old_mtime))
        import pathlib as _pl
        moved = hobs.gc_harness_logs(ttl_days=90, harness_dir=_pl.Path(base))
        archived = os.path.exists(os.path.join(base, "_archive", "invocations", "2026-01.jsonl"))
        kept = os.path.exists(new) and not os.path.exists(old)
        return moved == 1 and archived and kept
case("gc_harness_logs archives old keeps recent", _gc_archive)


# 6b. gc_harness_logs: is the hook-blocks/ subdirectory also in scope for GC?
def _gc_archive_hook_blocks():
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, ".harness")
        hb = os.path.join(base, "hook-blocks")
        os.makedirs(hb)
        old = os.path.join(hb, "2026-01.jsonl")
        new = os.path.join(hb, "2026-07.jsonl")
        for p in (old, new):
            with open(p, "w", encoding="utf-8") as f:
                f.write("{}\n")
        old_mtime = __import__("time").time() - 200 * 86400  # 200 days ago
        os.utime(old, (old_mtime, old_mtime))
        import pathlib as _pl
        moved = hobs.gc_harness_logs(ttl_days=90, harness_dir=_pl.Path(base))
        archived = os.path.exists(os.path.join(base, "_archive", "hook-blocks", "2026-01.jsonl"))
        kept = os.path.exists(new) and not os.path.exists(old)
        return moved == 1 and archived and kept
case("gc_harness_logs archives old hook-blocks/ keeps recent", _gc_archive_hook_blocks)

# 7. model-tag-count: counts only records carrying a model field (HARNESS_DIR swapped temporarily)
def _model_tag_count():
    import io
    import pathlib as _pl
    import types
    from contextlib import redirect_stdout
    with tempfile.TemporaryDirectory() as td:
        base = _pl.Path(td) / ".harness"
        inv = base / "interventions"
        inv.mkdir(parents=True)
        with open(inv / "2026-07.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "t", "date": "2026-07-01", "model": "sonnet-5"}) + "\n")
            f.write(json.dumps({"ts": "t", "date": "2026-07-02", "type": "rejection"}) + "\n")
            f.write(json.dumps({"ts": "t", "date": "2026-07-03", "model": "opus-4.8"}) + "\n")
        orig = hobs.HARNESS_DIR
        hobs.HARNESS_DIR = base
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                hobs.cmd_model_tag_count(types.SimpleNamespace(since=None))
            out = buf.getvalue()
        finally:
            hobs.HARNESS_DIR = orig
        return "count=2" in out
case("cmd_model_tag_count counts model-tagged only", _model_tag_count)

# 8. rejection-rate: rejection/total computation
def _rejection_rate():
    import datetime as _d
    import io
    import pathlib as _pl
    import types
    from contextlib import redirect_stdout
    with tempfile.TemporaryDirectory() as td:
        base = _pl.Path(td) / ".harness"
        inv = base / "interventions"
        inv.mkdir(parents=True)
        today = _d.date.today().isoformat()
        with open(inv / "2026-07.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "t", "date": today, "type": "rejection"}) + "\n")
            f.write(json.dumps({"ts": "t", "date": today, "type": "gate"}) + "\n")
            f.write(json.dumps({"ts": "t", "date": today, "type": "gate"}) + "\n")
        orig = hobs.HARNESS_DIR
        hobs.HARNESS_DIR = base
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                hobs.cmd_rejection_rate(types.SimpleNamespace(period="30d"))
            out = buf.getvalue()
        finally:
            hobs.HARNESS_DIR = orig
        return "rejections=1 total=3 rate=33.3%" in out
case("cmd_rejection_rate computes rate", _rejection_rate)

# 9. rejection-rate: zero denominator -> N/A
def _rejection_rate_na():
    import io
    import pathlib as _pl
    import types
    from contextlib import redirect_stdout
    with tempfile.TemporaryDirectory() as td:
        base = _pl.Path(td) / ".harness"
        orig = hobs.HARNESS_DIR
        hobs.HARNESS_DIR = base
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                hobs.cmd_rejection_rate(types.SimpleNamespace(period="30d"))
            out = buf.getvalue()
        finally:
            hobs.HARNESS_DIR = orig
        return "rate=N/A" in out
case("cmd_rejection_rate N/A when denominator zero", _rejection_rate_na)


# 10. rejection-rate: invalid --period format -> exit 1, stderr error
def _rejection_rate_invalid_period():
    import types
    return hobs.cmd_rejection_rate(types.SimpleNamespace(period="not-a-period")) == 1
case("cmd_rejection_rate invalid --period returns exit 1", _rejection_rate_invalid_period)

# 11. interventions: the writer's `rule_reference` field is read (older `l0_clause` still accepted)
def _rule_reference_load():
    conn = _tmp_conn()
    path = _tmp_jsonl([
        {"ts": "t", "date": "2026-07-01", "type": "correction", "rule_reference": "rules/a.md"},
        {"ts": "t", "date": "2026-07-02", "type": "correction", "l0_clause": "legacy-clause"},
    ])
    hobs.load_interventions_month(conn, path, "2026-07")
    got = [r[0] for r in conn.execute("SELECT rule_reference FROM interventions ORDER BY date")]
    os.unlink(path)
    return got == ["rules/a.md", "legacy-clause"]
case("interventions rule_reference read, l0_clause alias kept", _rule_reference_load)

# 12. an older cache with the l0_clause column is renamed in place
def _old_column_migrates():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE interventions (ts TEXT NOT NULL, date TEXT NOT NULL, month TEXT NOT NULL,"
                 " session_id TEXT, type TEXT, skill TEXT, agent TEXT, model TEXT, l0_clause TEXT, context TEXT)")
    hobs.ensure_schema(conn)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(interventions)")]
    return "rule_reference" in cols and "l0_clause" not in cols
case("old l0_clause column is renamed to rule_reference", _old_column_migrates)

# 13. receipts: branch/commit are read from the writer's nested `subject` object
def _receipt_subject():
    conn = _tmp_conn()
    path = _tmp_jsonl([{"receiptId": "r1", "sessionId": "s1", "family": "checkpoint",
                        "createdAt": "2026-07-01T00:00:00Z", "sha256": "abc",
                        "subject": {"cwd": "/p", "branch": "main", "commit": "abc1234"}}])
    hobs.load_receipts_month(conn, path, "2026-07")
    row = conn.execute("SELECT branch, commit_sha FROM receipts").fetchone()
    os.unlink(path)
    return row == ("main", "abc1234")
case("receipts branch/commit read from subject", _receipt_subject)

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


def test_all_cases():
    """pytest entry point: this file uses its own runner, so without this wrapper `pytest` collects
    0 tests and exits 0 (looks like a pass)."""
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
