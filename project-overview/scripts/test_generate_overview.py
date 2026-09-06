#!/usr/bin/env python3
"""
test_generate_overview.py — plain-assert test harness for generate_overview.py.
No pytest dependency. Run: python test_generate_overview.py
Exit code 0 = all pass, 1 = failure.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_overview import (
    MarkerCorruptionError,
    apply_auto_markers,
    load_project_entries,
    parse_state_snapshot,
    render_overview_block,
)

FAILURES = []


def check(name, condition):
    if condition:
        print(f"PASS: {name}")
    else:
        print(f"FAIL: {name}")
        FAILURES.append(name)


# ---- parse_state_snapshot ----

SAMPLE_HANDOFF = '''---
name: Session Handoff — Latest
description: some desc
type: handoff
---
<!-- state-snapshot v1 -->
```yaml
ts: 2026-07-05
ctx: "environment check complete"
next:
  - "task 1"
diff:
  - op: mod
    item: "x"
```

# Session Handoff (title)
'''

result = parse_state_snapshot(SAMPLE_HANDOFF)
check("parse_state_snapshot returns dict", isinstance(result, dict))
check("parse_state_snapshot ts field", result is not None and result.get("ts") == "2026-07-05")
check(
    "parse_state_snapshot ctx field",
    result is not None and result.get("ctx") == "environment check complete",
)

NO_SNAPSHOT_HANDOFF = '''---
name: Session Handoff — Latest
type: handoff
---
# Session Handoff (no snapshot block)
'''
result_none = parse_state_snapshot(NO_SNAPSHOT_HANDOFF)
check("parse_state_snapshot returns None when block missing", result_none is None)

MALFORMED_HANDOFF = '''---
name: X
---
<!-- state-snapshot v1 -->
```yaml
ctx: "no ts field here"
```
'''
result_malformed = parse_state_snapshot(MALFORMED_HANDOFF)
check(
    "parse_state_snapshot returns None when ts missing",
    result_malformed is None,
)

# ---- render_overview_block ----

entries = [
    {"name": "ProjectA", "path": "/path/to/project-a", "ts": "2026-07-05", "ctx": "environment check complete"},
    {"name": "ProjectB", "path": "/path/to/project-b", "ts": None, "ctx": None},
]
block = render_overview_block(entries)
check("render_overview_block includes project name", "ProjectA" in block)
check("render_overview_block includes ts", "2026-07-05" in block)
check("render_overview_block includes ctx", "environment check complete" in block)
check(
    "render_overview_block marks missing snapshot",
    "no snapshot" in block.lower() and "no handoff" in block.lower(),
)

# idempotency of render itself (same input -> byte-identical output)
block2 = render_overview_block(entries)
check("render_overview_block idempotent (byte-identical)", block == block2)

# ---- render_overview_block: untrusted-text escaping ----

DIRTY_ENTRIES = [
    {
        "name": "Proj|Pipe",
        "path": "/path/with|pipe",
        "ts": "2026-07-05",
        "ctx": "line one\nline two | not a new column",
    },
]
dirty_block = render_overview_block(DIRTY_ENTRIES)
dirty_rows = [ln for ln in dirty_block.splitlines() if ln.startswith("|")]
check(
    "render_overview_block escapes '|' in cross-project text",
    "\\|" in dirty_block,
)
check(
    "render_overview_block strips newlines from cross-project text (row count unchanged)",
    len(dirty_rows) == 3,  # header + separator + 1 data row, no extra rows from the embedded '\n'
)

# ---- apply_auto_markers ----

EXISTING_OVERVIEW_WITH_HUMAN_TEXT = '''# Project Overview

Human-written note — must never be dropped.

<!-- AUTO:START -->
(old auto content)
<!-- AUTO:END -->

Human-written text after the block too.
'''

new_block_content = "(new auto content)"
updated = apply_auto_markers(EXISTING_OVERVIEW_WITH_HUMAN_TEXT, new_block_content)
check(
    "apply_auto_markers preserves text before AUTO:START",
    "Human-written note — must never be dropped." in updated,
)
check(
    "apply_auto_markers preserves text after AUTO:END",
    "Human-written text after the block too." in updated,
)
check(
    "apply_auto_markers replaces old auto content",
    "(old auto content)" not in updated,
)
check(
    "apply_auto_markers inserts new auto content",
    "(new auto content)" in updated,
)

# idempotency: applying twice with same new_block yields byte-identical result
updated_twice = apply_auto_markers(updated, new_block_content)
check("apply_auto_markers idempotent (byte-identical)", updated == updated_twice)

# no markers present -> markers created, content appended
NO_MARKER_OVERVIEW = "# Project Overview\n\nOnly human text here.\n"
created = apply_auto_markers(NO_MARKER_OVERVIEW, new_block_content)
check("apply_auto_markers creates markers when absent", "<!-- AUTO:START -->" in created)
check("apply_auto_markers creates markers when absent (END)", "<!-- AUTO:END -->" in created)
check(
    "apply_auto_markers preserves existing text when creating markers",
    "Only human text here." in created,
)

# malformed markers: END appears before START -> this is corruption, not
# "no markers present". Auto-splicing here used to re-append a fresh pair
# every run, so on the *second* run start_idx (old orphaned START, now the
# first START in the file) still came after end_idx (old orphaned END,
# still the first END in the file) -> it kept re-triggering "append fresh
# pair" forever, growing an extra AUTO:START/AUTO:END pair on every run
# (non-idempotent). Fixed behavior: raise, don't touch the text at all.
MALFORMED_MARKER_OVERVIEW = (
    "# Project Overview\n\n"
    "<!-- AUTO:END -->\n"
    "some stray content\n"
    "<!-- AUTO:START -->\n"
)
try:
    apply_auto_markers(MALFORMED_MARKER_OVERVIEW, new_block_content)
    check("apply_auto_markers raises MarkerCorruptionError when END precedes START", False)
except MarkerCorruptionError:
    check("apply_auto_markers raises MarkerCorruptionError when END precedes START", True)

# orphan START (START present, no END) -> also corruption. The old
# recovery appended a fresh pair after the orphan START, so on a *second*
# run the first AUTO:START found was still the orphan one but the first
# AUTO:END found was now the newly-appended one -> everything between them
# (including any manual text a human wrote after the orphan START) got
# replaced by the AUTO block, silently deleting that manual text. Fixed
# behavior: raise, don't touch the text — the manual text must survive.
ORPHAN_START_OVERVIEW = (
    "# Project Overview\n\n"
    "<!-- AUTO:START -->\n"
    "manually written text that must never be silently deleted\n"
)
try:
    apply_auto_markers(ORPHAN_START_OVERVIEW, new_block_content)
    check("apply_auto_markers raises MarkerCorruptionError on orphan START", False)
except MarkerCorruptionError:
    check("apply_auto_markers raises MarkerCorruptionError on orphan START", True)

# corruption must never mutate input or produce partial output as a side
# effect — calling it repeatedly on the same corrupted text must keep
# raising, never "heal" into a growing marker count.
for _ in range(3):
    try:
        apply_auto_markers(MALFORMED_MARKER_OVERVIEW, new_block_content)
        check("repeated calls on corrupted markers keep raising (no silent growth)", False)
        break
    except MarkerCorruptionError:
        continue
else:
    check("repeated calls on corrupted markers keep raising (no silent growth)", True)

# ---- load_project_entries: non-UTF-8 handoff isolation ----

def fake_reader(path):
    if "bad-project" in path:
        # Simulate a handoff file saved in a non-UTF-8 encoding.
        raise UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 1, "invalid start byte")
    if "good-project" in path:
        return (
            "<!-- state-snapshot v1 -->\n```yaml\nts: 2026-07-05\nctx: \"ok\"\n```\n"
        )
    raise FileNotFoundError(path)

projects_mixed = [
    {"name": "BadProject", "path": "/tmp/bad-project"},
    {"name": "GoodProject", "path": "/tmp/good-project"},
]
mixed_entries = load_project_entries(projects_mixed, base_reader=fake_reader)
bad_entry = next(e for e in mixed_entries if e["name"] == "BadProject")
good_entry = next(e for e in mixed_entries if e["name"] == "GoodProject")
check(
    "load_project_entries isolates a non-UTF-8 handoff instead of crashing",
    bad_entry["error"] == "decode_error" and bad_entry["ts"] is None,
)
check(
    "load_project_entries still processes the remaining project after a decode failure",
    good_entry["ts"] == "2026-07-05" and good_entry["error"] is None,
)

decode_error_block = render_overview_block(mixed_entries)
check(
    "render_overview_block surfaces the decode error distinctly (not silently 'no handoff')",
    "decode error" in decode_error_block.lower(),
)

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
else:
    print("ALL PASS")
    sys.exit(0)
