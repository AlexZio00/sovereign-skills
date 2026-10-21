"""intake_ledger self-test (pytest or `python test_intake_ledger.py`)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intake_ledger import load, main, violation  # noqa: E402

BASE = {"source": "https://github.com/x/y", "candidate": "pattern p", "reason": "r"}


def test_adopted_needs_target_and_passes_shared_gates():
    assert violation({**BASE, "verdict": "adopted", "scope": "single"}) is not None              # no target
    assert violation({**BASE, "verdict": "adopted", "target_files": ["skills/a/SKILL.md"]}) is not None  # no scope
    assert violation({**BASE, "verdict": "adopted", "target_files": ["skills/a/SKILL.md"], "scope": "single"}) is None
    # text-only target without reason -> refused (same rule_only gate as the paper ledger)
    assert violation({**BASE, "verdict": "adopted", "target_files": ["rules/agents.md"], "scope": "single"}) is not None
    # multi scope with exec-only target -> refused (needs a text home)
    assert violation({**BASE, "verdict": "adopted", "target_files": ["agents/a.md", "agents/b.md"], "scope": "multi"}) is not None


def test_deferred_needs_state_target():
    assert violation({**BASE, "verdict": "deferred", "target_files": ["skills/a/SKILL.md"]}) is not None
    assert violation({**BASE, "verdict": "deferred", "target_files": ["~/.claude/STATE.md"]}) is None


def test_rejected_needs_next_path():
    assert violation({**BASE, "verdict": "rejected"}) is not None
    assert violation({**BASE, "verdict": "rejected", "next_path": "revisit if legacy migration starts"}) is None


def test_cli_refuses_then_records():
    led = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    base = ["--ledger", led, "record", "--source", "u", "--candidate", "c", "--verdict", "adopted", "--reason", "r"]
    assert main(base) == 2 and load(led) == []
    assert main(base + ["--target-file", "agents/x.md", "--scope", "single"]) == 0
    assert len(load(led)) == 1 and load(led)[0]["scope"] == "single"


def test_lookup_finds_prior_verdict_by_normalized_repo():
    from intake_ledger import _repo_key
    assert _repo_key("https://github.com/Acme/Widget/tree/main/x") == "acme/widget"
    assert _repo_key("acme/widget") == "acme/widget"
    assert _repo_key("https://github.com/Acme/Widget.git?tab=x#readme") == "acme/widget"
    led = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    main(["--ledger", led, "record", "--source", "https://github.com/Acme/Widget", "--candidate", "c",
          "--verdict", "rejected", "--reason", "r", "--next-path", "later"])
    assert main(["--ledger", led, "lookup", "https://github.com/acme/widget/tree/main"]) == 0
    assert main(["--ledger", led, "lookup", "zz-none-owner/zz-none-repo-7f3"]) == 1  # fresh intake
    led2 = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    main(["--ledger", led2, "record", "--source", "https://github.com/zz-acme/zz-widget-pro", "--candidate", "c",
          "--verdict", "rejected", "--reason", "r", "--next-path", "later"])
    assert main(["--ledger", led2, "lookup", "zz-acme/zz-widget"]) == 1  # prefix of another repo is not a hit


def test_review_marks_observed_dormant_missing_na():
    """review: did adopted patterns stay in place and did their asset get used afterwards?"""
    import json

    from intake_ledger import review_rows
    home = tempfile.mkdtemp()
    for rel in ("skills/used/SKILL.md", "agents/idle.md", "scripts/tool.py"):
        p = os.path.join(home, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write("x")
    inv = os.path.join(home, "inv")
    os.makedirs(inv)
    with open(os.path.join(inv, "2026-10.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"date": "2026-10-09", "skills": ["used"], "agents": []}) + "\n")
        f.write(json.dumps({"date": "2026-09-01", "skills": [], "agents": ["idle"]}) + "\n")
    recs = [
        {"source": "s", "candidate": "a", "verdict": "adopted", "date": "2026-09-05",
         "target_files": ["~/.claude/skills/used/SKILL.md"]},
        {"source": "s", "candidate": "b", "verdict": "adopted", "date": "2026-09-05", "target_files": ["agents/idle.md"]},
        {"source": "s", "candidate": "c", "verdict": "adopted", "date": "2026-09-05", "target_files": ["skills/gone/SKILL.md"]},
        {"source": "s", "candidate": "d", "verdict": "adopted", "date": "2026-09-05", "target_files": ["scripts/tool.py"]},
        {"source": "s", "candidate": "e", "verdict": "adopted", "date": "2026-10-10", "target_files": ["agents/idle.md"]},
        {"source": "s", "candidate": "f", "verdict": "rejected", "date": "2026-09-05", "next_path": "x"},
    ]
    rows = {r["candidate"]: r["status"] for r in review_rows(recs, today="2026-10-12", days=30, home=home, inv_dir=inv)}
    assert rows == {"a": "observed", "b": "dormant", "c": "missing", "d": "n/a"}, rows
    # no invocation log at all -> existing skill/agent targets are "unmeasured", never "dormant"
    rows = {r["candidate"]: r["status"] for r in review_rows(recs, today="2026-10-12", days=30, home=home, inv_dir=None)}
    assert rows == {"a": "unmeasured", "b": "unmeasured", "c": "missing", "d": "n/a"}, rows


def test_lookup_greps_extra_search_paths():
    import contextlib
    import io
    d = tempfile.mkdtemp()
    note = os.path.join(d, "notes.md")
    open(note, "w", encoding="utf-8").write("seen zz-acme/zz-note-repo once\n")
    led = os.path.join(d, "ledger.jsonl")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["--ledger", led, "lookup", "zz-acme/zz-note-repo", "--search", note]) == 0
    assert "[DOC]" in buf.getvalue() and "notes.md:1" in buf.getvalue()


def test_screened_records_split_and_rerun_is_idempotent():
    """screen-batch: repo-sweep merge result -> verdict=screened; split separates PRIOR from FRESH."""
    import json
    d = tempfile.mkdtemp()
    led = os.path.join(d, "ledger.jsonl")
    merged = os.path.join(d, "merged.json")
    table = [{"repo_url": "https://github.com/Acme/Widget", "verdict": "reject", "reason": "dup", "wave": 1},
             {"repo_url": "https://github.com/acme/other", "verdict": "APPROVE", "rationale": "good", "safety_flag": "x"},
             {"repo_url": "https://github.com/acme/bad", "verdict": "MAYBE"},
             {"repo_url": "", "verdict": "REJECT"}]
    json.dump({"table": table, "conflicts": [], "totals": {}}, open(merged, "w", encoding="utf-8"))
    assert main(["--ledger", led, "screen-batch", "--file", merged, "--date", "2026-10-13"]) == 0
    recs = load(led)
    assert [(r["screen"], r["verdict"]) for r in recs] == [("REJECT", "screened"), ("APPROVE", "screened")], recs
    assert recs[1]["reason"] == "good" and recs[1]["safety_flag"] == "x"
    assert violation(recs[0]) is None and violation({**recs[0], "screen": "NOPE"}) is not None
    assert main(["--ledger", led, "screen-batch", "--file", merged]) == 0 and len(load(led)) == 2  # unchanged -> no new rows
    table[0]["verdict"] = "REVISE"
    json.dump(table, open(merged, "w", encoding="utf-8"))  # bare array form
    main(["--ledger", led, "screen-batch", "--file", merged, "--date", "2026-10-13"])  # pinned: the split check reads this date
    assert [r["screen"] for r in load(led)] == ["REJECT", "APPROVE", "REVISE"]  # changed -> new row, append-only
    lst = os.path.join(d, "urls.txt")
    open(lst, "w", encoding="utf-8").write("\n".join(["# comment", "acme/widget", "https://github.com/Acme/Widget.git", "zz/fresh-repo-1"]))
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["--ledger", led, "split", "--file", lst, "acme/other"]) == 0
    out = buf.getvalue()
    assert "PRIOR acme/widget 2026-10-13 screened/REVISE" in out and "FRESH zz/fresh-repo-1" in out
    assert "PRIOR acme/other" in out and "3 unique repos = PRIOR 2 + FRESH 1 (duplicates in input: 1)" in out, out


def test_repo_key_handles_any_host_ssh_and_plain_names():
    from intake_ledger import _repo_key
    # github forms all collapse to owner/repo
    assert _repo_key("git@github.com:Acme/Widget.git") == "acme/widget"
    assert _repo_key("ssh://git@github.com/Acme/Widget.git") == "acme/widget"
    assert _repo_key("https://www.github.com/Acme/Widget/") == "acme/widget"
    assert _repo_key("github.com/acme/widget") == "acme/widget"
    # other hosts keep the host, so two hosts never collide
    assert _repo_key("https://gitlab.com/acme/widget") == "gitlab.com/acme/widget"
    assert _repo_key("git@gitlab.com:acme/widget.git") == "gitlab.com/acme/widget"
    assert _repo_key("https://gitlab.com/acme/sub/widget/-/tree/main") == "gitlab.com/acme/sub/widget"
    assert _repo_key("https://gitlab.com/acme/widget") != _repo_key("https://gitlab.com/acme/other")
    assert _repo_key("https://gitlab.com/acme/widget") != _repo_key("acme/widget")
    assert _repo_key("https://www.npmjs.com/package/left-pad") != _repo_key("https://www.npmjs.com/package/right-pad")
    # non-URL tools are keyed by the full string
    assert _repo_key("ripgrep") == "ripgrep"
    assert _repo_key("npm:left-pad") == "npm:left-pad"
    assert _repo_key("@scope/pkg") == "@scope/pkg"
    assert _repo_key("ripgrep") != _repo_key("ripgrep-all")


def test_lookup_word_boundary_in_docs_and_reason_printed():
    import contextlib
    import io
    d = tempfile.mkdtemp()
    note = os.path.join(d, "notes.md")
    open(note, "w", encoding="utf-8").write("we looked at zz-acme/zz-widget-pro today\nand zz-acme/zz-widget. Done\n")
    led = os.path.join(d, "ledger.jsonl")
    main(["--ledger", led, "record", "--source", "https://github.com/zz-acme/zz-widget", "--candidate", "c",
          "--verdict", "rejected", "--reason", "duplicates our router", "--next-path", "later"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["lookup", "--ledger", led, "zz-acme/zz-widget", "--search", note]) == 0  # --ledger after the command
    out = buf.getvalue()
    assert "reason: duplicates our router" in out
    assert "notes.md:2" in out and "notes.md:1" not in out, out  # widget-pro line (1) is not a hit


def test_malformed_ledger_lines_are_skipped_and_counted():
    import contextlib
    import io
    d = tempfile.mkdtemp()
    led = os.path.join(d, "ledger.jsonl")
    with open(led, "w", encoding="utf-8") as f:
        f.write('{"source": "https://github.com/a/b", "candidate": "c", "date": "2026-10-01"}\n')  # no verdict
        f.write("not json at all\n")
        f.write("[1, 2]\n")
        f.write('{"source": "https://github.com/a/c", "candidate": "d", "verdict": "rejected", "next_path": "x"}\n')
    from intake_ledger import load_counted
    recs, skipped = load_counted(led)
    assert len(recs) == 2 and skipped == 2
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        assert main(["--ledger", led, "stats"]) == 0  # record without a verdict must not crash
        assert main(["--ledger", led, "lookup", "a/b"]) == 0
        assert main(["--ledger", led, "split", "a/b", "a/c"]) == 0
    assert "skipped 2 malformed" in err.getvalue()
    assert "(no verdict)" in out.getvalue()


def test_no_python_311_only_imports():
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "intake_ledger.py"), encoding="utf-8").read()
    assert "import UTC" not in src and ", UTC" not in src


def test_review_tolerates_object_names_and_ignores_unusable_rows():
    import json

    from intake_ledger import review_rows
    home = tempfile.mkdtemp()
    p = os.path.join(home, "skills", "used", "SKILL.md")
    os.makedirs(os.path.dirname(p))
    open(p, "w", encoding="utf-8").write("x")
    inv = os.path.join(home, "inv")
    os.makedirs(inv)
    with open(os.path.join(inv, "2026-10.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"date": "2026-10-09", "source": "checkpoint", "skills": [{"skill": "used"}], "agents": []}) + "\n")
        f.write(json.dumps({"note": "no date"}) + "\n")
    recs = [{"source": "s", "candidate": "a", "verdict": "adopted", "date": "2026-09-05",
             "target_files": ["skills/used/SKILL.md"]}]
    rows = {r["candidate"]: r["status"] for r in review_rows(recs, today="2026-10-12", days=30, home=home, inv_dir=inv)}
    assert rows == {"a": "observed"}, rows


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
