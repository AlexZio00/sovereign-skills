"""ruff_changed_lines.py - pre-push Step 5a helper: ruff findings on lines this push changed.

Why: running ruff on whole changed files mostly reports old findings the push did not touch. This
script keeps the BLOCK semantics of Step 5a but only counts findings whose row falls inside lines
added by the push (staged plus outgoing commits).

Usage:  printf '%s\n' "$CHANGED_PY" | python ruff_changed_lines.py [--base MERGE_BASE] [--ruff-bin ruff]
Exit codes (fail closed):
  0  no finding on a changed line
  1  at least one finding on a changed line, or a syntax error in a changed file
  2  could not run ruff / could not parse its JSON / could not read the diff (treat as BLOCK)

Known limits (what this does NOT detect):
  - a finding that is caused by a changed line but reported on an unchanged line (e.g. an unused
    import reported at the import line after the only use was removed far below);
  - files absent from stdin (renamed-from paths, deleted files);
  - committed changes when --base is empty: only the staged diff is read. pre-push therefore calls this
    script only when MERGE_BASE is set and falls back to whole-file ruff otherwise;
  - line drift: staged lines are numbered by the index, outgoing lines by HEAD, and ruff reads the
    working tree. Unstaged edits in the same file can move a new finding off the changed-line set.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def git(args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout


def added_lines(diff_text, into):
    """Parse a -U0 diff and add {path: set(row)} for the new-side line numbers."""
    path = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            tgt = line[4:].strip()
            if len(tgt) >= 2 and tgt[0] == tgt[-1] == '"':  # git quotes non-ASCII paths (core.quotepath on)
                tgt = tgt[1:-1].encode("latin-1", "backslashreplace").decode("unicode_escape").encode("latin-1", "replace").decode("utf-8", "replace")
            path = None if tgt == "/dev/null" else (tgt[2:] if tgt.startswith("b/") else tgt)
            continue
        m = HUNK.match(line)
        if m and path:
            start = int(m.group(1))
            count = 1 if m.group(2) is None else int(m.group(2))
            into.setdefault(path, set()).update(range(start, start + count))


def norm(p, top):
    ap = p if os.path.isabs(p) else os.path.join(top, p)
    return os.path.relpath(ap, top).replace("\\", "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--ruff-bin", default="ruff")
    a = ap.parse_args()
    files = [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
    if not files:
        print("ruff_changed_lines: no files on stdin - nothing to lint")
        return 0
    try:
        top = git(["rev-parse", "--show-toplevel"]).strip()
        changed = {}
        added_lines(git(["diff", "--staged", "-U0", "--no-color", "--"] + files), changed)
        if a.base:
            added_lines(git(["diff", "-U0", "--no-color", a.base + "..HEAD", "--"] + files), changed)
    except (RuntimeError, OSError) as e:
        print("ruff_changed_lines: cannot read diff - %s" % e)
        return 2
    try:
        r = subprocess.run([a.ruff_bin, "check", "--output-format=json", "--no-cache", "--", *files],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=top)
        findings = json.loads(r.stdout or "[]")
    except (OSError, ValueError) as e:
        print("ruff_changed_lines: ruff failed to run or returned non-JSON - %s" % e)
        return 2
    if r.returncode not in (0, 1):
        print("ruff_changed_lines: ruff exit %s: %s" % (r.returncode, (r.stderr or "")[:300]))
        return 2
    hits = []
    for f in findings:
        rel = norm(f.get("filename", ""), top)
        row = (f.get("location") or {}).get("row")
        end = (f.get("end_location") or {}).get("row") or row
        code = f.get("code")
        lines = changed.get(rel, set())
        on_changed = row is not None and any(n in lines for n in range(row, end + 1))
        if code is None or on_changed:  # code None = syntax error: always blocks
            hits.append("%s:%s:%s: %s %s" % (rel, row, (f.get("location") or {}).get("column"),
                                            code or "SYNTAX", f.get("message", "")))
    print("ruff_changed_lines: %d finding(s) in %d changed file(s), %d on changed lines"
          % (len(findings), len(files), len(hits)))
    for h in hits[:20]:
        print(h)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
