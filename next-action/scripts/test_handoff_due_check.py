"""handoff_due_check self-test (pytest or `python test_handoff_due_check.py`)."""
import datetime as dt
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handoff_due_check import STALE_DAYS, carry_age, classify, due_of, todo_lines  # noqa: E402

HANDOFF = """# Session Handoff (2026-10-10)
```yaml
next:
  - "2026-10-11 07:45/08:00 first scheduled run (urgency: H)"
  - "around 2026-11-09 shadow period ends"
```
## What to do now
1. 2026-10-11 07:45 first scheduled run: check run_at.
2. Fix the KeyError in loader.py.
3. 2026-10-15 failure capture ends.

## System understanding
- 2026-10-01 background note, not a to-do.
"""


def test_classifies_against_now():
    now = dt.datetime(2026, 10, 11, 13, 50)
    lines = todo_lines(HANDOFF)
    assert not any("background note" in ln for ln in lines)  # outside the to-do sections
    got = [(lab, when) for ln in lines for lab, when in classify(ln, now)]
    assert ("PAST", "2026-10-11 07:45") in got
    assert ("FUTURE", "2026-10-15") in got
    assert ("FUTURE", "2026-11-09") in got
    assert all(when != "2026-10-01" for _, when in got)


def test_same_day_without_time_is_today():
    now = dt.datetime(2026, 10, 15, 9, 0)
    assert classify("2026-10-15 failure capture ends", now) == [("TODAY", "2026-10-15")]


def test_bad_time_falls_back_to_date():
    now = dt.datetime(2026, 10, 11, 9, 0)
    assert classify("2026-10-11 07:75 job", now) == [("TODAY", "2026-10-11")]
    assert classify("2026-10-11 24:00 job", now) == [("TODAY", "2026-10-11")]


def test_heading_boundaries():
    text = (
        "## Nextcloud setup\n1. 2026-01-01 not a to-do\n"
        "## What to do now\n### detail\n1. 2026-12-01 kept\n"
        "## System understanding\n- 2026-01-02 no\n"
    )
    lines = todo_lines(text)
    assert lines == ["1. 2026-12-01 kept"], lines


def test_since_date_is_not_a_due_date():
    now = dt.datetime(2026, 10, 11, 9, 0)
    assert classify("2026-10-15 capture ends (since: 2026-10-01)", now) == [("FUTURE", "2026-10-15")]
    assert classify("evaluation round (since: 2026-09-20)", now) == []


def test_carry_age_and_stale_threshold():
    now = dt.datetime(2026, 10, 11, 9, 0)
    assert carry_age("x (since: 2026-09-20)", now) == 21
    assert carry_age("x without since", now) is None
    assert carry_age("x (since: 2026-10-05)", now) < STALE_DAYS <= carry_age("y (since: 2026-09-27)", now)


def test_pending_decisions_section_is_read():
    text = "## Pending decisions\n- evaluation round (since: 2026-09-01) - urgency: L\n## Outstanding issues\n- other\n"
    assert todo_lines(text) == ["- evaluation round (since: 2026-09-01) - urgency: L"]


def test_scheduled_section_is_read_so_due_dates_surface():
    text = "## Scheduled checks (by date)\n- 2026-10-15 capture ends (since: 2026-10-08)\n## Outstanding issues\n- x\n"
    lines = todo_lines(text)
    assert classify(lines[0], dt.datetime(2026, 10, 15, 9, 0)) == [("TODAY", "2026-10-15")]


def test_latest_date_on_a_line_is_the_due_date():
    """Reference dates (changed-on, plan file name) must not make a future item PAST."""
    now = dt.datetime(2026, 10, 13, 9, 0)
    line = "7. around 2026-11-09 shadow period ends, see docs/plans/2026-10-08-risk-plan.md"
    assert due_of(line, now) == ("FUTURE", "2026-11-09 +1")
    assert due_of("2. 2026-10-11 first run of the changed agent", now) == ("PAST", "2026-10-11")
    assert due_of("no date here", now) is None


def _run(text, now, tmp_path):
    f = tmp_path / "handoff.md"
    f.write_text(text, encoding="utf-8")
    here = os.path.dirname(os.path.abspath(__file__))
    out = subprocess.run(
        [sys.executable, os.path.join(here, "handoff_due_check.py"), str(f), "--now", now, "--json"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    return json.loads(out)["items"]


def test_future_item_with_old_since_is_not_stale(tmp_path):
    text = "## Scheduled checks (by date)\n- 2026-11-09 shadow period ends (since: 2026-09-01)\n"
    items = _run(text, "2026-10-20 09:00", tmp_path)
    assert [i["status"] for i in items] == ["FUTURE"]


def test_undated_or_past_item_with_old_since_is_still_stale(tmp_path):
    text = ("## Pending decisions\n- evaluation round (since: 2026-09-01)\n"
            "## Scheduled checks (by date)\n- 2026-10-01 old check (since: 2026-09-01)\n")
    items = _run(text, "2026-10-20 09:00", tmp_path)
    assert sorted(i["status"] for i in items) == ["PAST", "STALE", "STALE"]


def test_latest_date_is_picked_by_parsed_time_not_text():
    now = dt.datetime(2026, 10, 11, 8, 0)
    # as text "9:30" > "10:00"; as time 10:00 is later, so the due time is 10:00 (still ahead at 08:00, labelled TODAY)
    assert due_of("2026-10-11 9:30 and 2026-10-11 10:00 run", now) == ("TODAY", "2026-10-11 10:00 +1")
    # a dated line without a time ends at end of day, so it outranks an earlier time on the same day
    assert due_of("2026-10-11 07:45 start, due 2026-10-11", now) == ("TODAY", "2026-10-11 +1")


def test_next_block_entry_restating_a_prose_item_is_reported_once():
    lines = todo_lines(HANDOFF)
    assert sum("first scheduled run" in ln for ln in lines) == 1
    # a next: entry with no prose twin is kept
    assert any("shadow period ends" in ln for ln in lines)


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, e)
    raise SystemExit(1 if fails else 0)
