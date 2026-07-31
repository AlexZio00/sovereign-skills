#!/usr/bin/env python3
"""
generate_overview.py — Deterministic cross-project map generator.

Reads projects-registry.md (opt-in list of {name, absolute path}), parses
each project's memory/session-handoff-LATEST.md for the
<!-- state-snapshot v1 --> YAML block (ts + ctx fields only — no new schema),
and writes the result into the AUTO:START/AUTO:END marker region of
~/.claude/OVERVIEW.md.

Idempotency oracle: running this script twice on unchanged inputs must
produce a byte-identical AUTO block. Text outside the markers (written by a
human) must survive re-runs untouched.

Usage:
  python generate_overview.py --registry <path> --output <path>
  python generate_overview.py   # uses default paths (see DEFAULT_* below)
"""
import argparse
import os
import re
import sys

DEFAULT_REGISTRY = os.path.expanduser("~/.claude/projects-registry.md")
DEFAULT_OUTPUT = os.path.expanduser("~/.claude/OVERVIEW.md")
HANDOFF_RELATIVE_PATH = os.path.join("memory", "session-handoff-LATEST.md")

AUTO_START = "<!-- AUTO:START -->"
AUTO_END = "<!-- AUTO:END -->"

# Matches: "- {name}: {path}" lines in projects-registry.md. Ignores lines
# starting with "#" (comments) or ">" (blockquote notes) or blank lines.
REGISTRY_LINE_RE = re.compile(r"^-\s*([^:]+):\s*(.+?)\s*$")

# Matches the state-snapshot v1 fenced yaml block after its HTML comment marker.
SNAPSHOT_BLOCK_RE = re.compile(
    r"<!--\s*state-snapshot v1\s*-->\s*```yaml\s*\n(.*?)```",
    re.DOTALL,
)

TS_LINE_RE = re.compile(r"^ts:\s*(.+?)\s*$", re.MULTILINE)
CTX_LINE_RE = re.compile(r'^ctx:\s*"?(.*?)"?\s*$', re.MULTILINE)


def parse_registry(registry_text):
    """Parse projects-registry.md text -> list of {"name": str, "path": str}.

    Ignores comment lines (#), blockquote lines (>), and blank lines.
    Does NOT touch the filesystem — pure text parsing (testable in isolation).
    """
    projects = []
    for line in registry_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">"):
            continue
        m = REGISTRY_LINE_RE.match(stripped)
        if m:
            name = m.group(1).strip()
            path = m.group(2).strip()
            projects.append({"name": name, "path": path})
    return projects


def parse_state_snapshot(handoff_text):
    """Extract {"ts": ..., "ctx": ...} from a session-handoff-LATEST.md text.

    Returns None if the state-snapshot v1 block is missing, or if the
    required 'ts' field is absent (malformed block treated as no-snapshot).
    """
    block_match = SNAPSHOT_BLOCK_RE.search(handoff_text)
    if not block_match:
        return None
    block = block_match.group(1)
    ts_match = TS_LINE_RE.search(block)
    if not ts_match:
        return None
    ctx_match = CTX_LINE_RE.search(block)
    ts = ts_match.group(1).strip()
    ctx = ctx_match.group(1).strip() if ctx_match else ""
    return {"ts": ts, "ctx": ctx}


def load_project_entries(projects, base_reader=None):
    """For each {"name","path"} project, read its handoff file and parse.

    base_reader: injectable function(path) -> str for testability (defaults to
    reading from filesystem). Returns list of entries with keys:
    name, path, ts, ctx (ts/ctx are None if handoff or snapshot missing).
    """
    if base_reader is None:
        def base_reader(p):
            with open(p, encoding="utf-8") as f:
                return f.read()

    entries = []
    for proj in projects:
        handoff_path = os.path.join(proj["path"], HANDOFF_RELATIVE_PATH)
        ts, ctx = None, None
        try:
            text = base_reader(handoff_path)
            snap = parse_state_snapshot(text)
            if snap:
                ts, ctx = snap["ts"], snap["ctx"]
        except (FileNotFoundError, OSError):
            pass
        entries.append({"name": proj["name"], "path": proj["path"], "ts": ts, "ctx": ctx})
    return entries


def _escape_table_cell(value):
    """Neutralize markdown-table-breaking characters in untrusted handoff text.

    state-snapshot v1 fields are data pulled from another project's handoff
    file, not something this script's own author wrote — treat it as
    untrusted input, not markup. A literal '|' would split into extra
    columns; a newline would break the row.
    """
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", "")


def render_overview_block(entries):
    """Render the AUTO block body from parsed entries. Deterministic: same
    entries list (same order) -> byte-identical output every time.
    """
    lines = []
    lines.append("| Project | Path | Last Update | Context |")
    lines.append("|---|---|---|---|")
    for e in entries:
        name = _escape_table_cell(e["name"])
        path = _escape_table_cell(e["path"])
        ts = _escape_table_cell(e.get("ts") or "no snapshot")
        ctx = _escape_table_cell(e.get("ctx") or "no handoff")
        lines.append(f"| {name} | `{path}` | {ts} | {ctx} |")
    return "\n".join(lines) + "\n"


def apply_auto_markers(existing_text, new_block_content):
    """Replace text between AUTO:START/AUTO:END markers with new_block_content.
    Text outside the markers is preserved byte-for-byte. If markers are absent,
    or END appears before START (mangled/orphaned markers from a manual edit),
    markers are (re)appended to the end of the file (existing content preserved above).
    """
    start_idx = existing_text.find(AUTO_START)
    end_idx = existing_text.find(AUTO_END)

    if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
        separator = "" if existing_text.endswith("\n") else "\n"
        return (
            existing_text
            + separator
            + "\n"
            + AUTO_START
            + "\n"
            + new_block_content
            + AUTO_END
            + "\n"
        )

    before = existing_text[:start_idx]
    after = existing_text[end_idx + len(AUTO_END):]
    return before + AUTO_START + "\n" + new_block_content + AUTO_END + after


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate cross-project OVERVIEW.md AUTO block")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    if not os.path.exists(args.registry):
        print(f"BLOCKED: registry not found at {args.registry}", file=sys.stderr)
        return 1

    with open(args.registry, encoding="utf-8") as f:
        registry_text = f.read()
    projects = parse_registry(registry_text)

    if not projects:
        print(f"BLOCKED: no projects registered in {args.registry}", file=sys.stderr)
        return 1

    entries = load_project_entries(projects)
    new_block = render_overview_block(entries)

    if os.path.exists(args.output):
        with open(args.output, encoding="utf-8") as f:
            existing_text = f.read()
    else:
        existing_text = "# Project Overview\n\n"

    updated_text = apply_auto_markers(existing_text, new_block)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(updated_text)

    print(f"WORKING: {len(projects)} project(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
