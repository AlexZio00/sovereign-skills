"""Golden-text tests for claude_md_lint.py (run: python -m pytest scripts -q)."""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claude_md_lint as cl  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VAGUE_KO = "\uc801\ub2f9\ud788 \uc54c\uc544\uc11c \ud558\uc138\uc694"  # three Korean vague phrases
MIXED = ("# Rules\n- Never edit src/app.py\n- Always run pytest tests/\n```bash\npytest -q\n```\n"
         "Use your judgment, as needed.\n" + VAGUE_KO + "\n")
STRONG = ("# Rules\n- Never edit src/app.py\n- Always run pytest -q\n- Use black\n- Avoid globals\n- Prefer pathlib\n"
          "```bash\npytest -q\n```\nSee docs/guide.md and config/app.yaml.\n")


def test_golden_mixed_text_is_weak():
    r = cl.lint_text(MIXED)
    assert (r["reward_total"], r["penalty_total"], r["net"], r["line_count"], r["verdict"]) == (8, 8, 0, 9, "WEAK")
    assert [(h["category"], h["match"]) for h in r["penalty_hits"]] == [
        ("vague_directive", "Use your judgment"),
        ("vague_directive", "as needed"),
        ("vague_directive", "\uc801\ub2f9\ud788"),
        ("vague_directive", "\uc54c\uc544\uc11c"),
    ]
    assert [h["category"] for h in r["reward_hits"]] == [
        "code_fence", "code_fence", "file_path", "shell_command", "imperative_line", "imperative_line"]


def test_golden_strong_text_and_verdict_bands():
    r = cl.lint_text(STRONG)
    assert r["verdict"] == "STRONG" and r["penalty_total"] == 0 and r["net"] >= 8, r
    assert cl.lint_text("Just some prose.\n")["verdict"] == "WEAK"


def test_line_budget_penalty():
    text = "- Never x\n" * 200
    r = cl.lint_text(text)
    over = r["line_count"] - cl.LINE_BUDGET
    assert r["line_count"] == 201 and over == 51
    assert r["penalty_hits"][-1] == {"category": "over_line_budget", "weight": 5, "match": "201 lines (budget 150)"}


def test_cli_output_and_gate():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "CLAUDE.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(MIXED)
        out = subprocess.run([sys.executable, os.path.join(HERE, "claude_md_lint.py"), p],
                             capture_output=True, text=True, encoding="utf-8")
        assert out.returncode == 0
        assert out.stdout.splitlines()[0] == f"{p}: net=0 (reward=8 penalty=8) lines=9 verdict=WEAK"
        gated = subprocess.run([sys.executable, os.path.join(HERE, "claude_md_lint.py"), p, "--min", "3"],
                               capture_output=True, text=True, encoding="utf-8")
        assert gated.returncode == 1
        js = subprocess.run([sys.executable, os.path.join(HERE, "claude_md_lint.py"), p, "--json"],
                            capture_output=True, text=True, encoding="utf-8")
        assert json.loads(js.stdout)["verdict"] == "WEAK"


def test_korean_hit_prints_on_an_ascii_console():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "CLAUDE.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(MIXED)
        env = dict(os.environ, PYTHONIOENCODING="ascii", PYTHONUTF8="0")
        out = subprocess.run([sys.executable, os.path.join(HERE, "claude_md_lint.py"), p], capture_output=True, env=env)
        assert out.returncode == 0, out.stderr
        assert "\uc801\ub2f9\ud788" in out.stdout.decode("utf-8")


def test_no_hangul_in_script_source():
    import re
    src = open(os.path.join(HERE, "claude_md_lint.py"), encoding="utf-8").read()
    assert not re.search("[\uac00-\ud7a3]", src)
