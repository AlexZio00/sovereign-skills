"""test_skill_snapshot.py - temp directories only."""
from __future__ import annotations

import datetime as dt
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_snapshot as ss

CASES = []


def case(n, f):
    CASES.append((n, f))


def _env():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "skills", "foo"))
    open(os.path.join(root, "skills", "foo", "SKILL.md"), "w", encoding="utf-8").write("v1\n")
    os.makedirs(os.path.join(root, "agents"))
    open(os.path.join(root, "agents", "bar.md"), "w", encoding="utf-8").write("agent\n")
    return root, os.path.join(root, ".harness", "snapshots")


T = dt.datetime(2026, 10, 13, 9, 0, 0)


def t_skill():
    root, sr = _env()
    r = ss.snapshot("foo", root, sr, now=T)
    return r["status"] == "WORKING" and os.path.isfile(os.path.join(sr, "foo", "2026-10-13-090000", "SKILL.md"))


case("skill snapshot created and cmp-verified", t_skill)


def t_agent():
    root, sr = _env()
    r = ss.snapshot("bar", root, sr, label="pre-x", now=T)
    return r["status"] == "WORKING" and os.path.isfile(os.path.join(sr, "bar", "2026-10-13-090000-pre-x", "bar.md"))


case("agent snapshot with label", t_agent)


def t_dup():
    root, sr = _env()
    ss.snapshot("foo", root, sr, now=T)
    return ss.snapshot("foo", root, sr, now=T + dt.timedelta(hours=1))["status"] == "DUPLICATE"


case("same-day identical content -> DUPLICATE", t_dup)


def t_changed():
    root, sr = _env()
    ss.snapshot("foo", root, sr, now=T)
    open(os.path.join(root, "skills", "foo", "SKILL.md"), "w", encoding="utf-8").write("v2\n")
    return ss.snapshot("foo", root, sr, now=T + dt.timedelta(hours=1))["status"] == "WORKING"


case("same-day changed content -> new snapshot", t_changed)


def t_missing():
    root, sr = _env()
    return ss.snapshot("nope", root, sr, now=T)["status"] == "BROKEN"


case("missing source -> BROKEN", t_missing)


def t_scope():
    root, sr = _env()
    out = os.path.join(tempfile.mkdtemp(), "x.md")
    open(out, "w").write("x")
    return ss.snapshot(out, root, sr, now=T)["status"] == "BROKEN"


case("path outside skills/agents -> BROKEN", t_scope)


def t_prune():
    root, sr = _env()
    r = None
    for i in range(7):
        open(os.path.join(root, "skills", "foo", "SKILL.md"), "w").write(f"v{i}\n")
        r = ss.snapshot("foo", root, sr, now=T + dt.timedelta(days=i))
    return (len(r["prune"]) == 2 and r["prune"][0] == "2026-10-13-090000"
            and len(os.listdir(os.path.join(sr, "foo"))) == 7)


case("snapshots beyond 5 are listed, not deleted", t_prune)


def t_bad_label():
    root, sr = _env()
    return ss.snapshot("foo", root, sr, label="a b/c", now=T)["status"] == "BROKEN"


case("label validation", t_bad_label)


def t_audit():
    sr = tempfile.mkdtemp()
    os.makedirs(os.path.join(sr, "good", "2026-10-13-090000"))
    os.makedirs(os.path.join(sr, "labeled", "2026-10-13-090000-pre"))
    os.makedirs(os.path.join(sr, "old", "2026-09-19-pre-defect-fix"))
    os.makedirs(os.path.join(sr, "flat"))
    open(os.path.join(sr, "flat", "x.md"), "w").write("x")
    r = ss.audit(sr)
    names = {x["name"] for x in r["nonstandard"]}
    return r["total_dirs"] == 4 and names == {"old", "flat"}


case("audit reports only entries outside the layout", t_audit)


def t_quote_paths():
    root2 = os.path.join(tempfile.mkdtemp(), "my claude")
    os.makedirs(os.path.join(root2, "skills", "foo"))
    open(os.path.join(root2, "skills", "foo", "SKILL.md"), "w", encoding="utf-8").write("v1\n")
    sr2 = os.path.join(root2, ".harness", "snapshots")
    r = ss.snapshot("foo", root2, sr2, now=T)
    one = ss.shlex.split(r["rollback"])
    return r["status"] == "WORKING" and len(one) == 3 and one[0] == "cp" and one[1] == os.path.join(
        r["snapshot"], "SKILL.md") and one[2] == os.path.join(root2, "skills", "foo", "SKILL.md")


case("rollback command quotes paths that contain spaces", t_quote_paths)


def t_agent_rollback_name():
    root, sr = _env()
    r = ss.snapshot("bar", root, sr, now=T)
    parts = ss.shlex.split(r["rollback"])
    return os.path.basename(parts[1]) == "bar.md" and os.path.basename(parts[2]) == "bar.md"


case("agent rollback uses the original file name, not SKILL.md", t_agent_rollback_name)


def t_prune_command_quoted():
    cmd = ss.prune_command(os.path.join("some dir", "it's"))
    if os.name == "nt":
        return cmd.startswith("Remove-Item") and ("'" + os.path.join("some dir", "it''s") + "'") in cmd
    return ss.shlex.split(cmd)[:3] == ["rm", "-rf", "--"] and ss.shlex.split(cmd)[3] == os.path.join("some dir", "it's")


case("prune command quotes the snapshot path", t_prune_command_quoted)


def t_audit_none():
    missing = os.path.join(tempfile.mkdtemp(), "nope")
    r = ss.audit(missing)
    import subprocess
    out = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill_snapshot.py"),
                          "audit", "--snap-root", missing], capture_output=True, text=True)
    empty = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skill_snapshot.py"),
                            "audit", "--snap-root", tempfile.mkdtemp()], capture_output=True, text=True)
    return (r["total_dirs"] == 0 and out.returncode == 0 and "no snapshots" in out.stdout
            and "Traceback" not in out.stderr and "no snapshots" in empty.stdout)


case("audit with no snapshots says so (missing or empty folder)", t_audit_none)


def test_all_cases():
    """pytest entry point: this file uses its own runner."""
    assert main() == 0


def main():
    fails = 0
    for n, f in CASES:
        try:
            ok = f()
        except Exception as e:
            ok, n = False, f"{n} [EXC {e}]"
        print(("PASS " if ok else "FAIL ") + n)
        fails += not ok
    print(f"{len(CASES) - fails}/{len(CASES)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
