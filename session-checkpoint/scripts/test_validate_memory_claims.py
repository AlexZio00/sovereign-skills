"""test_validate_memory_claims.py — regression tests for validate_memory_claims."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import types
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_memory_claims as vmc

CASES = []
def case(name, fn):
    CASES.append((name, fn))

# 1. extract_paths: pulls backtick paths, ignores backtick text with no extension
case("extract_paths finds backtick md/py paths, skips non-path", lambda: vmc.extract_paths(
    "Entry: `run_office.py` | Doc: `docs/INDEX.md` | not-a-path `v1.21.0`"
) == ["run_office.py", "docs/INDEX.md"])

# 2. extract_paths: duplicates preserved as-is (dedupe is check_paths's job)
case("extract_paths preserves duplicates for caller to dedupe", lambda: vmc.extract_paths(
    "`a.py` and again `a.py`"
) == ["a.py", "a.py"])

# 3. check_paths: splits existing/stale by absolute path
def _check_paths_basic():
    with tempfile.TemporaryDirectory() as td:
        real = os.path.join(td, "real.py")
        with open(real, "w", encoding="utf-8") as f:
            f.write("# x")
        ghost = os.path.join(td, "ghost.py")
        text = f"`{real}` and `{ghost}`"
        existing, stale = vmc.check_paths(text)
        return existing == [real] and stale == [ghost]
case("check_paths splits existing vs stale (absolute paths)", _check_paths_basic)

# 4. check_paths: --base resolves relative paths
def _check_paths_base():
    with tempfile.TemporaryDirectory() as td:
        sub_dir = os.path.join(td, "sub")
        os.makedirs(sub_dir)
        real = os.path.join(sub_dir, "real.py")
        with open(real, "w", encoding="utf-8") as f:
            f.write("# x")
        text = "`sub/real.py` and `sub/ghost.py`"
        existing, stale = vmc.check_paths(text, base=td)
        return existing == ["sub/real.py"] and stale == ["sub/ghost.py"]
case("check_paths resolves relative paths against --base", _check_paths_base)

# 5. check_paths: the same path mentioned repeatedly is judged only once
def _check_paths_dedupe():
    with tempfile.TemporaryDirectory() as td:
        real = os.path.join(td, "real.py")
        with open(real, "w", encoding="utf-8") as f:
            f.write("# x")
        text = f"`{real}` mentioned twice: `{real}`"
        existing, stale = vmc.check_paths(text)
        return existing == [real] and stale == []
case("check_paths dedupes repeated path mentions", _check_paths_dedupe)

# 6. find_claim_lines: counts keyword lines
case("find_claim_lines counts keyword lines", lambda: len(vmc.find_claim_lines(
    "2026-07-01: task done\nunrelated line\n2026-07-02: verified"
)) == 2)

# 7. find_unprovenanced_claims: date on the same line -> not flagged
case("find_unprovenanced_claims: date same line not flagged", lambda: vmc.find_unprovenanced_claims(
    "2026-07-01: task done"
) == [])

# 8. find_unprovenanced_claims: date on an adjacent line (+-1) -> not flagged
case("find_unprovenanced_claims: date adjacent line not flagged", lambda: vmc.find_unprovenanced_claims(
    "2026-07-01 measured\ntask done\nnext line"
) == [])

# 9. find_unprovenanced_claims: no date nearby -> flagged
case("find_unprovenanced_claims: no date nearby flagged", lambda: len(vmc.find_unprovenanced_claims(
    "unrelated line 1\ntask done\nunrelated line 2"
)) == 1)

# 9b. find_unprovenanced_claims: an adjacent line's OWN date isn't borrowed by a DIFFERENT claim (window-bleed regression)
case("find_unprovenanced_claims: adjacent line's OWN date is not borrowed by a different claim", lambda: vmc.find_unprovenanced_claims(
    "task A done\n2026-07-01: task B done"
) == [(1, "task A done")])

# 9c. find_claim_lines: negated forms ("not done" etc.) are not treated as completion claims
case("find_claim_lines: negated forms (not done/unverified/unconfirmed) excluded", lambda: vmc.find_claim_lines(
    "this task is not done yet\nthis value is unverified\nthis is unconfirmed"
) == [])

# 10. cmd_check_paths CLI: stale found -> exit 1 + STALE line printed
def _cli_check_paths_stale():
    with tempfile.TemporaryDirectory() as td:
        ghost = os.path.join(td, "ghost.py")
        doc = os.path.join(td, "doc.md")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write(f"`{ghost}`")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vmc.cmd_check_paths(types.SimpleNamespace(file=[doc], base=None))
        return rc == 1 and "STALE:" in buf.getvalue()
case("cmd_check_paths exit 1 when stale paths found", _cli_check_paths_stale)

# 11. cmd_check_paths CLI: all paths exist -> exit 0
def _cli_check_paths_clean():
    with tempfile.TemporaryDirectory() as td:
        real = os.path.join(td, "real.py")
        with open(real, "w", encoding="utf-8") as fh:
            fh.write("# x")
        doc = os.path.join(td, "doc.md")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write(f"`{real}`")
        rc = vmc.cmd_check_paths(types.SimpleNamespace(file=[doc], base=None))
        return rc == 0
case("cmd_check_paths exit 0 when all paths exist", _cli_check_paths_clean)

# 12. cmd_check_provenance CLI: unprovenanced claim found -> exit 1
def _cli_check_provenance_flag():
    with tempfile.TemporaryDirectory() as td:
        doc = os.path.join(td, "doc.md")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write("unrelated line\ntask done\nunrelated line")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vmc.cmd_check_provenance(types.SimpleNamespace(file=[doc]))
        return rc == 1 and "UNPROVENANCED" in buf.getvalue()
case("cmd_check_provenance exit 1 when unprovenanced claim found", _cli_check_provenance_flag)

# 13. cmd_check_provenance CLI: all claims provenanced -> exit 0
def _cli_check_provenance_clean():
    with tempfile.TemporaryDirectory() as td:
        doc = os.path.join(td, "doc.md")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write("2026-07-01: task done")
        rc = vmc.cmd_check_provenance(types.SimpleNamespace(file=[doc]))
        return rc == 0
case("cmd_check_provenance exit 0 when all claims provenanced", _cli_check_provenance_clean)

# 14. unreadable file: exit 2 (missing_data — must not pass silently)
case("cmd_check_paths returns 2 on unreadable file", lambda: vmc.cmd_check_paths(
    types.SimpleNamespace(file=["/no/such/file-xyz.md"], base=None)
) == 2)

# 15. non-UTF-8 file: exit 2 instead of crashing (UnicodeDecodeError regression)
def _cli_non_utf8_file():
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "bad.md")
        with open(bad, "wb") as fh:
            fh.write(b"\xff\xfe\x00\x01invalid utf-8 bytes")
        return vmc.cmd_check_paths(types.SimpleNamespace(file=[bad], base=None)) == 2
case("cmd_check_paths returns 2 (not a crash) on non-UTF-8 file", _cli_non_utf8_file)

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
