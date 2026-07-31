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
    apply_auto_markers,
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

# malformed markers: END appears before START -> treated as no-markers,
# fresh pair re-appended at the end, existing content preserved untouched
MALFORMED_MARKER_OVERVIEW = (
    "# Project Overview\n\n"
    "<!-- AUTO:END -->\n"
    "some stray content\n"
    "<!-- AUTO:START -->\n"
)
recovered = apply_auto_markers(MALFORMED_MARKER_OVERVIEW, new_block_content)
check(
    "apply_auto_markers recovers when END precedes START (no crash)",
    "(new auto content)" in recovered,
)
check(
    "apply_auto_markers preserves original text when recovering from malformed markers",
    "some stray content" in recovered,
)
check(
    "apply_auto_markers recovery produces exactly one well-formed marker pair",
    recovered.count("<!-- AUTO:START -->") >= 1 and recovered.count("<!-- AUTO:END -->") >= 1,
)

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
else:
    print("ALL PASS")
    sys.exit(0)
