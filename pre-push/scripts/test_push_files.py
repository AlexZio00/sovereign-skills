"""PP7 regression: a .py committed but not pushed must reach Step 4's CHANGED_PY.

Runs the real Step 1 and Step 4 bash blocks extracted from ../SKILL.md inside a temporary
repo with a bare origin, so the test breaks if the SKILL.md wiring regresses.
Run: python test_push_files.py  (or pytest)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "SKILL.md")


def _git_bash():
    """Git for Windows bash (never WSL's System32 bash); plain bash elsewhere."""
    exec_path = subprocess.run(["git", "--exec-path"], capture_output=True, text=True).stdout.strip()
    for rel in ("../../../bin/bash.exe", "../../../usr/bin/bash.exe"):
        cand = os.path.normpath(os.path.join(exec_path, rel))
        if os.path.isfile(cand):
            return cand
    return shutil.which("bash")


SKILL_DIR = os.path.normpath(os.path.join(HERE, "..")).replace("\\", "/")


def _sub(text):
    """Claude Code replaces ${CLAUDE_SKILL_DIR} in the SKILL.md body before the model sees it; do the same here."""
    return text.replace("${CLAUDE_SKILL_DIR}", SKILL_DIR)


def _blocks():
    text = _sub(open(SKILL, encoding="utf-8").read())
    step1 = text.split("## Step 1:", 1)[1].split("## Step 2:", 1)[0]
    step4 = text.split("## Step 4:", 1)[1].split("**Python**", 1)[0]
    grab = lambda s: re.findall(r"```bash\n(.*?)```", s, re.S)[0]  # noqa: E731
    return grab(step1), grab(step4)


def _bash(bash, script, cwd):
    """Run a bash script from a temp file. `bash -c <script>` goes through Windows command-line quoting,
    which can corrupt long scripts that mix quotes and backslashes."""
    fd, path = tempfile.mkstemp(suffix=".sh")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(script)
        return subprocess.run([bash, path], cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace").stdout
    finally:
        os.remove(path)


def _run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def test_committed_unpushed_py_reaches_changed_py():
    bash = _git_bash()
    assert bash, "bash not found"
    step1, step4 = _blocks()
    tmp = tempfile.mkdtemp()
    try:
        origin, work = os.path.join(tmp, "origin.git"), os.path.join(tmp, "work")
        _run(["git", "init", "-q", "--bare", origin], tmp)
        _run(["git", "clone", "-q", origin, work], tmp)
        for k, v in (("user.email", "t@example.invalid"), ("user.name", "t")):
            _run(["git", "config", k, v], work)
        open(os.path.join(work, "README.md"), "w").write("x\n")
        _run(["git", "add", "."], work)
        _run(["git", "commit", "-q", "-m", "init"], work)
        _run(["git", "push", "-q", "-u", "origin", "HEAD"], work)
        os.makedirs(os.path.join(work, "pkg"))
        open(os.path.join(work, "pkg", "mod.py"), "w").write("def f():\n    return 1\n")
        _run(["git", "add", "."], work)
        _run(["git", "commit", "-q", "-m", "add mod"], work)  # committed, not pushed; staging empty
        script = step1 + "\n" + step4 + '\necho "CHANGED_PY=[$CHANGED_PY]"\necho "PUSH_DIFF_LINES=[$PUSH_DIFF_LINES]"\n'
        out = _bash(bash, script, work)
        assert "CHANGED_PY=[pkg/mod.py]" in out, out[-800:]
        assert "PUSH_DIFF_LINES=[0]" not in out, out[-800:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)



def _mkrepo(tmp):
    origin, work = os.path.join(tmp, "origin.git"), os.path.join(tmp, "work")
    _run(["git", "init", "-q", "--bare", origin], tmp)
    _run(["git", "clone", "-q", origin, work], tmp)
    for k, v in (("user.email", "t@example.invalid"), ("user.name", "t")):
        _run(["git", "config", k, v], work)
    open(os.path.join(work, "README.md"), "w").write("x\n")
    _run(["git", "add", "."], work)
    _run(["git", "commit", "-q", "-m", "init"], work)
    _run(["git", "push", "-q", "-u", "origin", "HEAD"], work)
    return work


def _block_after(marker):
    text = _sub(open(SKILL, encoding="utf-8").read())
    return re.findall(r"```bash\n(.*?)```", text.split(marker, 1)[1], re.S)[0]


def test_secret_added_then_removed_in_outgoing_commits_still_blocks():
    """A secret added in commit A and removed in commit B is absent from the net diff but is pushed inside A."""
    bash = _git_bash()
    step1, _ = _blocks()
    tmp = tempfile.mkdtemp()
    try:
        work = _mkrepo(tmp)
        key = "AKIA" + "ABCDEFGHIJKLMNOP"  # scan-secrets: allow (synthetic fixture; scanners that rejoin split strings still see it)
        open(os.path.join(work, "cfg.txt"), "w").write('aws_key = "%s"\n' % key)
        _run(["git", "add", "."], work)
        _run(["git", "commit", "-q", "-m", "add key"], work)
        open(os.path.join(work, "cfg.txt"), "w").write("aws_key = os.environ['K']\n")
        _run(["git", "add", "."], work)
        _run(["git", "commit", "-q", "-m", "remove key"], work)
        out = _bash(bash, step1 + '\necho "SECRETS_EXIT=[$SECRETS_EXIT]"', work)
        assert "SECRETS_EXIT=[1]" in out and "AWS Access Key" in out, out[-800:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gitleaks_second_scan_never_changes_secrets_exit():
    bash = _git_bash()
    step1, _ = _blocks()
    tmp = tempfile.mkdtemp()
    try:
        work = _mkrepo(tmp)
        open(os.path.join(work, "m.py"), "w").write("def f():\n    return 1\n")
        _run(["git", "add", "."], work)
        _run(["git", "commit", "-q", "-m", "m"], work)
        out = _bash(bash, step1 + '\necho "SECRETS_EXIT=[$SECRETS_EXIT]"', work)
        assert "SECRETS_EXIT=[0]" in out, out[-800:]
        assert "gitleaks" in out, out[-800:]  # clean line, or the not-installed line
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_database_reviewer_sql_in_diff_trigger():
    bash = _git_bash()
    step1, _ = _blocks()
    db_block = _block_after("Trigger `database-reviewer` (sonnet)")
    tmp = tempfile.mkdtemp()
    try:
        work = _mkrepo(tmp)
        os.makedirs(os.path.join(work, "tests"))
        open(os.path.join(work, "tests", "test_x.py"), "w").write('S = "CREATE TABLE t (a)"\n')  # test path: ignored
        open(os.path.join(work, "reader.py"), "w").write(
            "import sqlite3\nc = sqlite3.connect('x')\nc.execute('SELECT 1')\n")  # read-only: no trigger
        open(os.path.join(work, "schema.py"), "w").write('DDL = "CREATE TABLE t (a INTEGER)"\n')
        _run(["git", "add", "."], work)
        _run(["git", "commit", "-q", "-m", "x"], work)
        out = _bash(bash, step1 + "\n" + db_block, work)
        assert "schema.py" in out and "reader.py" not in out and "test_x.py" not in out, out[-800:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    bad = 0
    for name in ("test_committed_unpushed_py_reaches_changed_py",
                 "test_secret_added_then_removed_in_outgoing_commits_still_blocks",
                 "test_gitleaks_second_scan_never_changes_secrets_exit",
                 "test_database_reviewer_sql_in_diff_trigger"):
        try:
            globals()[name]()
            print("PASS", name)
        except AssertionError as e:
            bad += 1
            print("FAIL", name, e)
    sys.exit(1 if bad else 0)
