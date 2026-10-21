"""Tests for ruff_changed_lines.py (fail-closed line-level ruff gate). Run: python test_ruff_changed_lines.py"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "ruff_changed_lines.py")


def sh(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", **kw)


def run(cwd, files, base="", ruff_bin="ruff"):
    args = [sys.executable, SCRIPT, "--ruff-bin", ruff_bin] + (["--base", base] if base else [])
    return sh(args, cwd, input="\n".join(files) + "\n")


def make_repo(tmp):
    sh(["git", "init", "-q"], tmp)
    sh(["git", "config", "user.email", "t@t"], tmp)
    sh(["git", "config", "user.name", "t"], tmp)
    with open(os.path.join(tmp, "a.py"), "w", encoding="utf-8") as f:
        f.write("import os\n\ndef f():\n    return 1\n")  # preexisting F401 on line 1
    sh(["git", "add", "."], tmp)
    sh(["git", "commit", "-qm", "base"], tmp)
    return sh(["git", "rev-parse", "HEAD"], tmp).stdout.strip()


def append(tmp, text):
    with open(os.path.join(tmp, "a.py"), "a", encoding="utf-8") as f:
        f.write(text)


def test_preexisting_only_passes_and_new_staged_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(tmp)
        append(tmp, "\ndef g():\n    return 2\n")  # clean addition
        sh(["git", "add", "."], tmp)
        r = run(tmp, ["a.py"])
        assert r.returncode == 0, r.stdout + r.stderr
        assert "0 on changed lines" in r.stdout
        append(tmp, "import sys\n")  # new F401 on a changed line
        sh(["git", "add", "."], tmp)
        r = run(tmp, ["a.py"])
        assert r.returncode == 1 and "F401" in r.stdout and "a.py:" in r.stdout, r.stdout + r.stderr


def test_committed_outgoing_violation_blocks_only_with_base():
    with tempfile.TemporaryDirectory() as tmp:
        base = make_repo(tmp)
        append(tmp, "import json\n")
        sh(["git", "add", "."], tmp)
        sh(["git", "commit", "-qm", "add"], tmp)
        assert run(tmp, ["a.py"]).returncode == 0  # not visible without --base (documented)
        r = run(tmp, ["a.py"], base=base)
        assert r.returncode == 1 and "F401" in r.stdout, r.stdout + r.stderr


def test_syntax_error_in_changed_file_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(tmp)
        append(tmp, "def broken(:\n")
        sh(["git", "add", "."], tmp)
        r = run(tmp, ["a.py"])
        assert r.returncode == 1, r.stdout + r.stderr


def test_missing_ruff_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(tmp)
        append(tmp, "x = 1\n")
        sh(["git", "add", "."], tmp)
        r = run(tmp, ["a.py"], ruff_bin="ruff-does-not-exist")
        assert r.returncode == 2, r.stdout + r.stderr


def test_git_quoted_non_ascii_path_is_unquoted():
    # git quotes non-ASCII paths (core.quotepath on) as octal escapes - the changed-line key must be the real name
    import ruff_changed_lines as rcl
    out = {}
    bs = chr(92)  # real git output contains literal backslash-octal text for the UTF-8 bytes of the name
    diff = '+++ "b/caf' + bs + '303' + bs + '251.py"\n@@ -0,0 +1,2 @@\n+x=1\n+y=2\n'
    rcl.added_lines(diff, out)
    assert list(out) == ["café.py"] and out["café.py"] == {1, 2}, out


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, str(e)[:300])
    sys.exit(1 if fails else 0)
