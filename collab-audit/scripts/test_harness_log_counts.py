import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness_log_counts as h  # noqa: E402


def _w(p: Path, rows, extra=""):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in rows) + extra, encoding="utf-8")


def test_counts_window_all_sources_and_bad_lines(tmp_path):
    _w(tmp_path / "invocations" / "2026-10.jsonl", [
        {"date": "2026-10-12", "session_id": "a", "skills": ["x", "y"], "agents": ["g"],
         "source": "session-checkpoint-phase1.6.5"},
        {"date": "2026-10-12", "session_id": "b", "skills": ["x"], "agents": [],
         "source": "session-checkpoint-phase3.7-fallback"},
        {"date": "2026-10-12", "session_id": "c", "skills": ["x"], "source": "some-other-writer"},
        {"date": "2026-08-01", "session_id": "d", "skills": ["old"], "source": "session-checkpoint-phase1.6.5"},
    ], extra="\n{broken")
    r = h.summarize(tmp_path, 30, date(2026, 10, 13))
    assert r["invocation_records"] == 3 and r["sessions"] == 3  # every source counts, old record is out of window
    assert r["skills_top"][0] == ("x", 3) and ("old", 1) not in r["skills_top"]
    assert r["agents_top"] == [("g", 1)]
    assert r["sources"] == {"session-checkpoint-phase1.6.5": 1, "session-checkpoint-phase3.7-fallback": 1,
                            "some-other-writer": 1}
    assert r["skipped_lines"] == 1


def test_discarded_counted_in_both_forms(tmp_path):
    _w(tmp_path / "invocations" / "2026-10.jsonl", [
        {"date": "2026-10-12", "session_id": "a", "discarded": [{"skill": "scope", "reason": "discard_if"}, "scope"]},
        {"date": "2026-10-12", "session_id": "b", "discarded": ["freeze", {"reason": "no skill key"}, 7]},
    ])
    r = h.summarize(tmp_path, 30, date(2026, 10, 13))
    assert r["discarded_total"] == 3
    assert r["discarded_top"][0] == ("scope", 2) and ("freeze", 1) in r["discarded_top"]


def test_growth_record_continues_its_session(tmp_path):
    _w(tmp_path / "invocations" / "2026-10.jsonl", [
        {"date": "2026-10-12", "session_id": "2026-10-12T09:00:00", "skills": ["a"]},
        {"date": "2026-10-12", "session_id": "2026-10-12T11:00:00", "skills": ["b"],
         "prior_session_id": "2026-10-12T09:00:00", "source": "session-checkpoint-phase1.6.5-growth"},
        {"date": "2026-10-12", "session_id": "2026-10-12T15:00:00", "skills": ["c"], "prior_session_id": "unknown"},
    ])
    r = h.summarize(tmp_path, 30, date(2026, 10, 13))
    assert r["invocation_records"] == 3 and r["sessions"] == 2


def test_date_falls_back_to_ts(tmp_path):
    _w(tmp_path / "invocations" / "2026-10.jsonl", [{"ts": "2026-10-12T09:00:00", "session_id": "a", "skills": ["x"]}])
    assert h.summarize(tmp_path, 30, date(2026, 10, 13))["invocation_records"] == 1


def test_missing_dirs_give_zero_not_crash(tmp_path):
    r = h.summarize(tmp_path / "nope", 30, date(2026, 10, 13))
    assert r["invocation_records"] == 0 and r["skipped_lines"] == 0
