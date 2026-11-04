"""share_record.py - counts only, never values."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import share_record as sr  # noqa: E402


def test_counts_classes_and_record_has_no_values(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("mail me at someone@acme-mail.co\npath C:\\Users\\bob\\x\nkey sk-ABCDEFGHIJKLMNOPQRST\n", encoding="utf-8")  # scan-secrets: allow
    b = tmp_path / "b.bin"
    b.write_bytes(b"\x00\x01binary")
    counts, digest, skipped = sr.scan([a, b])
    assert counts["email"] == 1 and counts["user_home_path"] == 1 and counts["api_key_like"] == 1
    assert skipped == 1 and len(digest) == 64
    log = sr.record("https://github.com/x/sovereign-skills", ["a.md", "b.bin"], counts, digest, skipped, tmp_path / "log")
    line = log.read_text(encoding="utf-8")
    assert "someone@acme-mail.co" not in line and "sk-ABC" not in line and "bob" not in line
    assert json.loads(line)["counts"]["email"] == 1


def test_posix_home_paths_counted_but_tilde_and_relative_are_not(tmp_path):
    f = tmp_path / "p.md"
    f.write_text("see /home/alice/notes and /Users/bob/dev\nuse ~/.config/tool and ./docs/home/x\n", encoding="utf-8")
    counts, _, _ = sr.scan([f])
    assert counts["user_home_path"] == 2


def test_credentials_in_remote_url_are_not_logged(tmp_path):
    log = sr.record("https://user:ghp_secrettoken@github.com/x/y.git", [], {}, "d" * 64, 0, tmp_path / "log")  # scan-secrets: allow - synthetic fixture, not a real token
    line = log.read_text(encoding="utf-8")
    assert "ghp_secrettoken" not in line and "user:" not in line and "github.com/x/y.git" in line


def test_clean_file_all_zero_and_digest_changes_with_content(tmp_path):
    f = tmp_path / "c.md"
    f.write_text("plain text\n", encoding="utf-8")
    c1, d1, _ = sr.scan([f])
    f.write_text("plain text!\n", encoding="utf-8")
    _, d2, _ = sr.scan([f])
    assert all(v == 0 for v in c1.values()) and d1 != d2


def test_allow_marker_placeholder_mail_and_test_fixtures_not_counted(tmp_path):
    t = tmp_path / "tests"
    t.mkdir()
    f = t / "test_x.py"
    f.write_text('k = "AKIAABCDEFGHIJKLMNOP"\nm = "t@example.invalid"\n', encoding="utf-8")  # gitleaks:allow
    g = tmp_path / "a.md"
    g.write_text('k = "AKIAABCDEFGHIJKLMNOP"  # gitleaks:allow\nclone git@github.com:a/b\n', encoding="utf-8")
    counts, _, _ = sr.scan([f, g])
    assert counts["api_key_like"] == 0 and counts["email"] == 0


def test_cli_writes_record_to_log_dir_and_missing_list_exits_2(tmp_path, capsys):
    (tmp_path / "x.md").write_text("hello\n", encoding="utf-8")
    lst = tmp_path / "list.txt"
    lst.write_text("x.md\n", encoding="utf-8")
    rc = sr.main(["--remote", "https://example.org/r.git", "--files-from", str(lst), "--root", str(tmp_path),
                  "--log-dir", str(tmp_path / "log")])
    out = capsys.readouterr().out
    assert rc == 0 and "SHARE_SCAN:" in out and "SHARE_RECORD:" in out and (tmp_path / "log").is_dir()
    assert sr.main(["--remote", "r", "--files-from", str(tmp_path / "nope.txt")]) == 2


def test_redact_remote_drops_userinfo_query_and_fragment():
    # synthetic fake credentials - not real values
    cases = {
        "https://user:pa/ss@host/x.git": "https://host/x.git",  # scan-secrets: allow
        "https://user:pa@ss@host/x.git": "https://host/x.git",  # scan-secrets: allow
        "https://host/x.git?token=abc123#frag": "https://host/x.git",
        "https://host/x.git": "https://host/x.git",
        "git@github.com:owner/repo.git": "git@github.com:owner/repo.git",
    }
    for raw, want in cases.items():
        assert sr.redact_remote(raw) == want, raw
