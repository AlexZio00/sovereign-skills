"""harness_observability.py — indexes and aggregates .harness JSONL logs into
SQLite, for read-only observability queries (usage counts, intervention
rates, model-tag trends) without re-scanning raw log files on every call.

Reimplementation of the agentsview indexing pattern (not a copy) — uses only
the sqlite3 stdlib. Loading re-reads a month's file in full each time
(DELETE+INSERT, idempotent). Output is fixed-ASCII (safe under narrow
locale encodings such as cp949).

Usage:
  python harness_observability.py rebuild
  python harness_observability.py usage --name <NAME> [--kind skill|agent|any] [--since YYYY-MM-DD]
  python harness_observability.py intervention-rate --period <Nd>
  python harness_observability.py top [--n N] [--kind skill|agent|any]
  python harness_observability.py model-tag-count [--since YYYY-MM-DD]
  python harness_observability.py rejection-rate --period <Nd>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import re
import shutil
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import secret_redact  # noqa: E402 — masks secrets in this module's own observability logs

HARNESS_DIR = pathlib.Path.home() / ".claude" / ".harness"
GC_TTL_DAYS = 90  # active window for .harness JSONL logs before archival

DDL = """
CREATE TABLE IF NOT EXISTS invocations (
  ts TEXT NOT NULL, date TEXT NOT NULL, month TEXT NOT NULL,
  name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('skill','agent')),
  source TEXT, session_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_invocations_name ON invocations(name);
CREATE INDEX IF NOT EXISTS idx_invocations_month ON invocations(month);
CREATE INDEX IF NOT EXISTS idx_invocations_date ON invocations(date);

CREATE TABLE IF NOT EXISTS discards (
  ts TEXT NOT NULL, date TEXT NOT NULL, month TEXT NOT NULL,
  skill TEXT NOT NULL, reason TEXT, source TEXT, session_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_discards_month ON discards(month);

CREATE TABLE IF NOT EXISTS interventions (
  ts TEXT NOT NULL, date TEXT NOT NULL, month TEXT NOT NULL,
  session_id TEXT, type TEXT, skill TEXT, agent TEXT, model TEXT,
  l0_clause TEXT, context TEXT
);
CREATE INDEX IF NOT EXISTS idx_interventions_month ON interventions(month);
CREATE INDEX IF NOT EXISTS idx_interventions_date ON interventions(date);

CREATE TABLE IF NOT EXISTS receipts (
  receipt_id TEXT, session_id TEXT, family TEXT, created_at TEXT,
  month TEXT, branch TEXT, commit_sha TEXT, sha256 TEXT, raw_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_receipts_month ON receipts(month);
"""


def get_db_path() -> pathlib.Path:
    return HARNESS_DIR / "observability.db"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()


def connect(db_path: pathlib.Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    ensure_schema(conn)
    return conn


def _warn(msg: str) -> None:
    sys.stderr.write("[HARNESS-OBS WARN] " + msg + "\n")


def _info(msg: str) -> None:
    sys.stderr.write("[HARNESS-OBS INFO] " + msg + "\n")


def _rows_from_invocation_record(rec: dict) -> tuple[list[dict], list[dict]]:
    """Unpivot skills[]/agents[] into (name, kind) rows; discarded[] becomes
    a separate list."""
    date = rec.get("date", "")
    month = date[:7] if len(date) >= 7 else ""
    base = {
        "ts": rec.get("ts", ""),
        "date": date,
        "month": month,
        "source": rec.get("source"),
        "session_id": rec.get("session_id"),
    }
    inv_rows: list[dict] = []
    for name in rec.get("skills") or []:
        inv_rows.append({**base, "name": name, "kind": "skill"})
    for name in rec.get("agents") or []:
        inv_rows.append({**base, "name": name, "kind": "agent"})
    disc_rows: list[dict] = []
    for item in rec.get("discarded") or []:
        if isinstance(item, dict):
            skill, reason = item.get("skill", ""), item.get("reason")
        else:
            skill, reason = str(item), None
        disc_rows.append({**base, "skill": skill, "reason": reason})
    return inv_rows, disc_rows


def _iter_jsonl(jsonl_path) -> list[dict]:
    records = []
    path = pathlib.Path(jsonl_path)
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                _warn(f"malformed JSON {path}:{lineno} - skipped")
    return records


def load_invocations_month(conn, jsonl_path, month: str) -> tuple[int, int]:
    conn.execute("DELETE FROM invocations WHERE month = ?", (month,))
    conn.execute("DELETE FROM discards WHERE month = ?", (month,))
    n_inv = n_disc = 0
    for rec in _iter_jsonl(jsonl_path):
        inv_rows, disc_rows = _rows_from_invocation_record(rec)
        for r in inv_rows:
            conn.execute(
                "INSERT INTO invocations (ts,date,month,name,kind,source,session_id) VALUES (?,?,?,?,?,?,?)",
                (r["ts"], r["date"], r["month"], r["name"], r["kind"], r["source"], r["session_id"]),
            )
            n_inv += 1
        for r in disc_rows:
            conn.execute(
                "INSERT INTO discards (ts,date,month,skill,reason,source,session_id) VALUES (?,?,?,?,?,?,?)",
                (r["ts"], r["date"], r["month"], r["skill"], r["reason"], r["source"], r["session_id"]),
            )
            n_disc += 1
    conn.commit()
    return n_inv, n_disc


def load_interventions_month(conn, jsonl_path, month: str) -> int:
    conn.execute("DELETE FROM interventions WHERE month = ?", (month,))
    n = 0
    for rec in _iter_jsonl(jsonl_path):
        date = rec.get("date", "")
        conn.execute(
            "INSERT INTO interventions (ts,date,month,session_id,type,skill,agent,model,l0_clause,context)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (rec.get("ts", ""), date, date[:7] if len(date) >= 7 else month,
             rec.get("session_id"), rec.get("type"), rec.get("skill"), rec.get("agent"),
             rec.get("model"), rec.get("l0_clause"),
             secret_redact.redact(rec.get("context"), limit=2000)),  # mask secrets in our own log field
        )
        n += 1
    conn.commit()
    return n


def load_receipts_month(conn, jsonl_path, month: str) -> int:
    conn.execute("DELETE FROM receipts WHERE month = ?", (month,))
    n = 0
    for rec in _iter_jsonl(jsonl_path):
        conn.execute(
            "INSERT INTO receipts (receipt_id,session_id,family,created_at,month,branch,commit_sha,sha256,raw_json)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (rec.get("receiptId") or rec.get("receipt_id"), rec.get("sessionId") or rec.get("session_id"),
             rec.get("family"), rec.get("createdAt") or rec.get("created_at"), month,
             rec.get("branch"), rec.get("commit") or rec.get("commit_sha"), rec.get("sha256"),
             secret_redact.scrub(json.dumps(rec, ensure_ascii=True))),  # preserve the audit trail, masking only secrets
        )
        n += 1
    conn.commit()
    return n


def gc_harness_logs(ttl_days: int = GC_TTL_DAYS, harness_dir: pathlib.Path | None = None) -> int:
    """Move .harness JSONL logs untouched for N+ days into _archive/ instead
    of deleting them (avoids an irreversible delete).

    Targets: {invocations,interventions,receipts,hook-blocks}/*.jsonl files
    with mtime < cutoff. The current month's file is naturally excluded
    since its mtime is recent. Archived files are preserved under
    _archive/{subdir}/. Returns the number of files moved. Errors are
    absorbed (best-effort, fail-open).
    """
    base = harness_dir or HARNESS_DIR
    cutoff = time.time() - ttl_days * 86400
    moved = 0
    for subdir in ("invocations", "interventions", "receipts", "hook-blocks"):
        src = base / subdir
        if not src.is_dir():
            continue
        dst = base / "_archive" / subdir
        for p in src.glob("*.jsonl"):
            try:
                if p.stat().st_mtime >= cutoff:
                    continue
                dst.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(dst / p.name))
                moved += 1
            except OSError:
                continue
    return moved


def _month_files(subdir: str) -> list[tuple[pathlib.Path, str]]:
    d = HARNESS_DIR / subdir
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.jsonl")):
        m = re.match(r"^(\d{4}-\d{2})", p.stem)
        out.append((p, m.group(1) if m else p.stem))
    return out


def cmd_rebuild(args) -> int:
    conn = connect()
    totals = {"invocations": 0, "discards": 0, "interventions": 0}
    inv_dir = HARNESS_DIR / "invocations"
    if inv_dir.is_dir():
        for path, month in _month_files("invocations"):
            ni, nd = load_invocations_month(conn, path, month)
            totals["invocations"] += ni
            totals["discards"] += nd
    else:
        _warn(f"{inv_dir} not found - skipping")
    itv_dir = HARNESS_DIR / "interventions"
    if itv_dir.is_dir():
        for path, month in _month_files("interventions"):
            totals["interventions"] += load_interventions_month(conn, path, month)
    else:
        _warn(f"{itv_dir} not found - skipping")
    rcp_dir = HARNESS_DIR / "receipts"
    receipts_out = "skipped (dir absent)"
    if rcp_dir.is_dir():
        n_r = 0
        for path, month in _month_files("receipts"):
            n_r += load_receipts_month(conn, path, month)
        receipts_out = str(n_r)
    else:
        _info(f"{rcp_dir} not present - optional table skipped")
    gc_moved = gc_harness_logs()
    print(f"rebuilt: invocations={totals['invocations']} discards={totals['discards']}"
          f" interventions={totals['interventions']} receipts={receipts_out}"
          f" gc_archived={gc_moved}")
    return 0


def _kind_clause(kind: str) -> tuple[str, tuple]:
    if kind in ("skill", "agent"):
        return " AND kind = ?", (kind,)
    return "", ()


def cmd_usage(args) -> int:
    conn = connect()
    sql = "SELECT COUNT(*) FROM invocations WHERE name = ?"
    params: tuple = (args.name,)
    clause, extra = _kind_clause(args.kind)
    sql += clause
    params += extra
    if args.since:
        sql += " AND date >= ?"
        params += (args.since,)
    count = conn.execute(sql, params).fetchone()[0]
    print(f"usage: name={args.name} kind={args.kind} count={count} since={args.since or 'all-time'}")
    return 0


def _parse_period_since(period: str):
    """Parse a period string of the form 'Nd' into a since-date (ISO format).
    Returns None on format mismatch."""
    m = re.match(r"^(\d+)d$", period)
    if not m:
        return None
    days = int(m.group(1))
    return (_dt.date.today() - _dt.timedelta(days=days)).isoformat()


def cmd_intervention_rate(args) -> int:
    since = _parse_period_since(args.period)
    if since is None:
        sys.stderr.write("[HARNESS-OBS ERROR] --period must match ^(\\d+)d$ e.g. 7d, 30d\n")
        return 1
    conn = connect()
    n_itv = conn.execute("SELECT COUNT(*) FROM interventions WHERE date >= ?", (since,)).fetchone()[0]
    n_inv = conn.execute("SELECT COUNT(*) FROM invocations WHERE date >= ?", (since,)).fetchone()[0]
    rate = "N/A" if n_inv == 0 else f"{100.0 * n_itv / n_inv:.1f}%"
    print(f"intervention-rate: period={args.period} interventions={n_itv} invocations={n_inv} rate={rate}")
    return 0


def cmd_top(args) -> int:
    conn = connect()
    clause, params = _kind_clause(args.kind)
    sql = ("SELECT name, kind, COUNT(*) AS c FROM invocations WHERE 1=1" + clause
           + " GROUP BY name, kind ORDER BY c DESC LIMIT ?")
    rows = conn.execute(sql, params + (args.n,)).fetchall()
    print(f"top {args.n} ({args.kind}):")
    for i, (name, kind, c) in enumerate(rows, 1):
        print(f"{i}. {name} [{kind}] count={c}")
    return 0


def cmd_model_tag_count(args) -> int:
    """session-start Phase 2.2 — count of intervention records carrying a
    `model` field (scans JSONL directly; no `rebuild` required)."""
    count = 0
    for path, _month in _month_files("interventions"):
        for rec in _iter_jsonl(path):
            if args.since and rec.get("date", "") < args.since:
                continue
            if rec.get("model"):
                count += 1
    print(f"model-tag-count: since={args.since or 'all-time'} count={count}")
    return 0


def cmd_rejection_rate(args) -> int:
    """session-start Phase 2.4 — autoimmunity rate (rejection / total
    intervention x100)."""
    since = _parse_period_since(args.period)
    if since is None:
        sys.stderr.write("[HARNESS-OBS ERROR] --period must match ^(\\d+)d$ e.g. 7d, 30d\n")
        return 1
    n_rejection = 0
    n_total = 0
    for path, _month in _month_files("interventions"):
        for rec in _iter_jsonl(path):
            date = rec.get("date", "")
            if date < since:
                continue
            n_total += 1
            if rec.get("type") == "rejection":
                n_rejection += 1
    rate = "N/A" if n_total == 0 else f"{100.0 * n_rejection / n_total:.1f}%"
    print(f"rejection-rate: period={args.period} rejections={n_rejection} total={n_total} rate={rate}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Harness observability index (JSONL -> SQLite)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rebuild").set_defaults(func=cmd_rebuild)
    p_usage = sub.add_parser("usage")
    p_usage.add_argument("--name", required=True)
    p_usage.add_argument("--kind", choices=["skill", "agent", "any"], default="any")
    p_usage.add_argument("--since", default=None)
    p_usage.set_defaults(func=cmd_usage)
    p_rate = sub.add_parser("intervention-rate")
    p_rate.add_argument("--period", required=True)
    p_rate.set_defaults(func=cmd_intervention_rate)
    p_top = sub.add_parser("top")
    p_top.add_argument("--n", type=int, default=10)
    p_top.add_argument("--kind", choices=["skill", "agent", "any"], default="any")
    p_top.set_defaults(func=cmd_top)
    p_mtc = sub.add_parser("model-tag-count")
    p_mtc.add_argument("--since", default=None)
    p_mtc.set_defaults(func=cmd_model_tag_count)
    p_rr = sub.add_parser("rejection-rate")
    p_rr.add_argument("--period", required=True)
    p_rr.set_defaults(func=cmd_rejection_rate)
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except sqlite3.Error as e:
        sys.stderr.write(f"[HARNESS-OBS ERROR] sqlite failure: {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
