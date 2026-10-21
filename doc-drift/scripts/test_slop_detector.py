"""Golden-text tests for slop_detector.py (run: python -m pytest scripts -q)."""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slop_detector as sd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SLOPPY = "It seems robust and very seamless. It's not just fast, it's reliable — truly.\n"
CLEAN = "Run pytest before every commit. The config lives in pyproject.toml.\n"


def test_golden_sloppy_text():
    r = sd.score_text(SLOPPY)
    assert (r["score"], r["words"], r["verdict"]) == (8, 14, "HIGH")
    assert [(h["category"], h["match"], h["pos"]) for h in r["hits"]] == [
        ("hedging", "It seems", 0),
        ("hype_vocab", "robust", 9),
        ("hype_vocab", "seamless", 25),
        ("empty_intensifier", "very", 20),
        ("empty_intensifier", "truly", 71),
        ("antithesis", "It's not just fast, it's", 35),
        ("em_dash", "—", 69),
    ]


def test_golden_clean_text_and_thresholds():
    r = sd.score_text(CLEAN)
    assert (r["score"], r["verdict"], r["hits"]) == (0, "LOW", [])
    # density bands: 1 hit in 40 words = 0.025 -> MEDIUM; 3 hits in 40 words = 0.075 -> HIGH
    filler = " ".join(["word"] * 39)
    assert sd.score_text("truly " + filler)["verdict"] == "MEDIUM"
    assert sd.score_text("truly really very " + " ".join(["word"] * 37))["verdict"] == "HIGH"
    assert sd.score_text("")["verdict"] == "LOW"  # empty file: no division by zero


def test_cli_output_line_and_exit_codes():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "doc.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(SLOPPY)
        out = subprocess.run([sys.executable, os.path.join(HERE, "slop_detector.py"), p],
                             capture_output=True, text=True, encoding="utf-8")
        assert out.returncode == 0
        assert out.stdout.splitlines()[0] == f"{p}: score=8 density=0.5714 verdict=HIGH"
        assert "[em_dash] '—' @ 69" in out.stdout
        gated = subprocess.run([sys.executable, os.path.join(HERE, "slop_detector.py"), p, "--max-density", "0.1"],
                               capture_output=True, text=True, encoding="utf-8")
        assert gated.returncode == 1
        js = subprocess.run([sys.executable, os.path.join(HERE, "slop_detector.py"), p, "--json"],
                            capture_output=True, text=True, encoding="utf-8")
        assert json.loads(js.stdout)["verdict"] == "HIGH"
        missing = subprocess.run([sys.executable, os.path.join(HERE, "slop_detector.py"), os.path.join(d, "none.md")],
                                 capture_output=True, text=True, encoding="utf-8")
        assert missing.returncode == 2 and "READ_ERROR" in missing.stderr


def test_stdout_is_utf8_even_when_console_encoding_is_ascii():
    """A non-ASCII hit or path must not crash the script on a cp949/ascii console."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "\ubb38\uc11c.md")  # non-ASCII file name
        with open(p, "w", encoding="utf-8") as f:
            f.write(SLOPPY)
        env = dict(os.environ, PYTHONIOENCODING="ascii", PYTHONUTF8="0")
        out = subprocess.run([sys.executable, os.path.join(HERE, "slop_detector.py"), p],
                             capture_output=True, env=env)
        assert out.returncode == 0, out.stderr
        text = out.stdout.decode("utf-8")
        assert "\ubb38\uc11c.md" in text and "—" in text
