#!/usr/bin/env python3
"""Regression tests for scan_secrets.py.

Calls scan_lines() directly (no subprocess/perl dependency — sidesteps the
"python3 resolves to a Windows Store stub" PATH gotcha this harness already
tracks, per environment-first). Fixtures ported 1:1 from the Perl-era test
suite, itself built from the adversarial evasion probe
(~/.claude/.harness/evasion-corpus/pre-push-scan-secrets.md, 2026-07-16) —
every EVASION_NOW_FIXED case used to evade (exit 0) before the v2.2.0
hardening pass and must now be caught (exit 1). KNOWN_GAP cases are
deliberately left unfixed (see scan_secrets.py header comment) and must
stay documented rather than silently regress further.

Run: python test_scan_secrets.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scan_secrets import scan_lines  # noqa: E402


def run(fixture: str) -> int:
    """fixture may contain an embedded '\\n' representing multiple diff
    lines fed via stdin (Perl read them as separate <STDIN> iterations)."""
    flags = scan_lines(fixture.split("\n"))
    return 1 if any(flags.values()) else 0


# name -> (diff_line, expected_exit_code)
CASES = {
    # --- f1: AWS Access Key ID ---
    "f1_control_akia_still_caught": (
        '+aws_key = "AKIAABCDEFGHIJKLMNOP"', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f1_evasion_now_fixed_asia_prefix": (
        '+aws_access_key_id = "ASIATESTFAKEKEY12345"', 1),

    # --- f2: Private key header ---
    "f2_control_rsa_still_caught": (
        '+-----BEGIN RSA PRIVATE KEY-----', 1),
    "f2_control_generic_still_caught": (
        '+-----BEGIN PRIVATE KEY-----', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f2_evasion_now_fixed_pgp_block": (
        '+-----BEGIN PGP PRIVATE KEY BLOCK-----', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f2_evasion_now_fixed_pkcs8_encrypted": (
        '+CONFIG_BLOB = "-----BEGIN ENCRYPTED PRIVATE KEY-----MIIFDjBABgkqhkiG9w0BBQ0w"', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f2_evasion_now_fixed_ssh2_4dash": (
        '+---- BEGIN SSH2 ENCRYPTED PRIVATE KEY ----', 1),

    # --- f3: Password in connection string (scoped ${}/$() exception) ---
    "f3_control_hardcoded_still_caught": (
        '+  DSN = "mysql://admin:Passw0rd123!@db.internal:3306/app"', 1),
    "f3_evasion_now_fixed_trailing_var_no_longer_suppresses": (
        '+  DSN = "mysql://admin:Passw0rd123!@db.internal:3306/app"  # fallback default ${DB_DSN_OVERRIDE}', 1),
    "f3_negative_legit_template_stays_clean": (
        '+  DSN = "mysql://${DB_USER}:${DB_PASS}@db.internal:3306/app"', 0),

    # --- f4a: quoted credential assignment ---
    "f4a_control_password_still_caught": (
        '+password = "abcdef123456"', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f4a_evasion_now_fixed_pwd_keyword": (
        '+db_pwd = "Tr0ub4dor&3xyz9Q"', 1),
    "f4a_evasion_now_fixed_bearer_token_keyword": (
        '+BEARER_TOKEN="7f3a9c2e8b1d4f6a9e0c3b5d8f2a1c4e"', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f4a_evasion_now_fixed_curly_quotes": (
        '+    cfg.password = “SuperSecretPass123”', 1),

    # --- f4b: unquoted credential assignment ---
    "f4b_control_secret_key_still_caught": (
        '+SECRET_KEY=abc123def456', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f4b_evasion_now_fixed_github_token_keyword": (
        '+GITHUB_TOKEN=1234567890abcdef1234567890abcdef12345678', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f4b_known_gap_prefix_anchor_still_evades": (
        # Deliberately deferred (Lane B): loosening the anchor to tolerate
        # a "MY_"-style prefix risks false-positiving on unrelated names
        # like SECRET_ROTATION_ID. Documented as still-evading, not fixed.
        '+  MY_SECRET_KEY=zK9pL3mQ8xT2vB7nR4wY6hJ1cF5dS0aG', 0),  # gitleaks:allow (합성 테스트 픽스처)

    # --- f5: Platform tokens (ZWSP normalization) ---
    "f5_control_slack_token_still_caught": (
        '+SLACK_TOKEN = "' + 'xoxb-' + '123456789012-1234567890123-abcdefghijklmnopqrstuvwxyz' + '"', 1),  # split literal: avoids GitHub push-protection false-positive on this synthetic fixture
    "f5_evasion_now_fixed_zwsp": (
        '+    SLACK_TOKEN = "xoxb​-123456789012-1234567890123-abcdefghijklmnopqrstuvwxyz"', 1),

    # --- f6: Dockerfile ENV/ARG (case-insensitive) ---
    "f6_control_env_uppercase_still_caught": (
        '+ENV SECRET_KEY=abc123def456', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f6_evasion_now_fixed_env_lowercase": (
        '+env SECRET_KEY=abc123def456', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f6_evasion_now_fixed_arg_vs_env": (
        '+ARG DB_PASSWORD=hunter2ULTRA9x', 1),  # gitleaks:allow (합성 테스트 픽스처)

    # --- f8: npm auth token (whitespace tolerant) ---
    "f8_control_no_whitespace_still_caught": (
        '+//registry.npmjs.org/:_authToken=npm_abcdefghijklmnopqrstuvwxyzABCDEFGH12', 1),
    "f8_evasion_now_fixed_whitespace_padding": (
        '+//registry.npmjs.org/:_authToken = npm_abcdefghijklmnopqrstuvwxyzABCDEFGH12', 1),

    # --- f9: LLM provider keys (homoglyph normalization, widened alternation) ---
    "f9_control_sk_ant_still_caught": (
        '+    ANTHROPIC_KEY = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF"', 1),
    "f9_evasion_now_fixed_homoglyph": (
        '+    ANTHROPIC_KEY = "sk-аnt-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF"', 1),
    "f9_evasion_now_fixed_lookbehind_removed": (
        '+  curl -H "Authorization: Bearer confsk-UvgAf1EDQZCJHbVL4EHEBv5d180pmfsTdqrJ1nXYnfIG15iH"', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f9_evasion_now_fixed_sk_svcacct": (
        '+OPENAI_SVC_KEY = "sk-svcacct-A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2W3x4Y5z6"', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "f9_evasion_now_fixed_xai_prefix": (
        '+    -H "Authorization: Bearer xai-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMN" \\', 1),

    # --- f10: Azure credentials (case-insensitive, HTML-entity tolerant) ---
    "f10_control_accountkey_properkey_still_caught": (
        '+AccountKey=FakeAzureStorageAccountKeyForTestingPurposesOnlyNotReal0123456789ABCDEFGHIJKLMNOPQRSTU==;EndpointSuffix=core.windows.net', 1),
    "f10_evasion_now_fixed_case_insensitive": (
        '+accountkey=FakeAzureStorageAccountKeyForTestingPurposesOnlyNotReal0123456789ABCDEFGHIJKLMNOPQRSTU==;EndpointSuffix=core.windows.net', 1),
    "f10_evasion_now_fixed_html_entity_sas": (
        '+  <a href="https://mystorageacct.blob.core.windows.net/container/file.txt?sv=2023-01-01&amp;sig=Xk9pQ7mR2vT4wY6zA8bC1dE3fG5hJ0kLmN7oPqRsTuVwXyZ12345%3D&amp;se=2027-01-01">Download</a>', 1),

    # --- f13: Slack Incoming Webhook URL (new rule) ---
    "f13_evasion_now_fixed_webhook_new_rule": (
        '+SLACK_WEBHOOK_URL = "' + 'https://hooks.slack.com/services/' + 'T012ABCDEF/B012GHIJKL/9f8e7d6c5b4a3f2e1d0c9b8a' + '"', 1),  # split literal: avoids GitHub push-protection false-positive on this synthetic fixture

    # --- Lane B, item 2 only: deliberately NOT fixed (needs narrow 2-line
    # lookback design — see brainstorming notes, separate task) ---
    "known_gap_cross_line_split": (
        '+AWS_KEY = ("AKIA1234567"\n+           "890ABCDEF")', 0),

    # --- Lane B, items 1+3: now fixed (whole-line-reversed re-scan + repeated
    # quote+operator concatenation collapse, both stateless single-line fixes) ---
    "laneb_evasion_now_fixed_runtime_string_reversal": (
        '+    token = "9876543210ZYXWVUTSRQPONMLKJIHGFEDCBA_phg"[::-1]  # reversed at runtime', 1),  # gitleaks:allow (합성 테스트 픽스처)
    "laneb_evasion_now_fixed_string_concat_split": (
        '+    aws_key = "AKIA" + "IOSFODNN7EXAMPLE"  # split to dodge contiguous regex', 1),
    "laneb_evasion_now_fixed_string_concat_chain_3way": (
        '+    token = "ghp_" + "ABCDEFGHIJKLMNOPQRST" + "UVWXYZ01234"', 1),
    "laneb_negative_concat_with_variable_not_merged": (
        # One side is a variable, not a quoted literal — must NOT merge/match.
        '+  msg = "Hello, " + user_name', 0),

    # --- Sanity: removed lines and benign content stay clean ---
    "sanity_removed_line_not_scanned": (
        '-aws_key = "AKIAABCDEFGHIJKLMNOP"', 0),  # gitleaks:allow (합성 테스트 픽스처)
    "sanity_benign_line_stays_clean": (
        '+  print("hello world")', 0),

    # --- Regression: false-positive probes (independent verification, 2026-07-16) ---
    # f6's /i addition without a line-start anchor matched the ordinary English
    # word "env"/"arg" anywhere in a comment/prose line. Fixed by anchoring
    # ENV/ARG to the leading instruction token (^\+\s*). These fixtures pin
    # that fix and its adjacent probes so it can't silently regress again.
    "fp_probe_llm_token_count_var_stays_clean": (
        '+MAX_TOKENS = 100000', 0),
    "fp_probe_password_policy_short_value_stays_clean": (
        '+PASSWORD_POLICY_VERSION=2', 0),
    "fp_probe_docstring_mentioning_password_stays_clean": (
        '+  # docstring example: the password field must be at least 8 characters', 0),
    "fp_probe_legit_cyrillic_text_stays_clean": (
        '+  welcome_message = "Добро пожаловать"', 0),
    "fp_probe_korean_text_stays_clean": (
        '+  greeting = "안녕하세요"', 0),
    "fp_probe_zwsp_typo_in_normal_word_stays_clean": (
        '+  na​me = "test"', 0),
    "fp_regression_env_word_in_comment_now_fixed": (
        # Confirmed regression (independent verification): before this anchor
        # fix, f6's /i flag made this ordinary comment CRITICAL (exit 1).
        '+    # env API_KEY_ROTATION_DAYS is set to 30', 0),
    "fp_preexisting_uppercase_env_in_comment_now_also_fixed": (
        # Pre-existing gap (matched even before v2.2.0, uppercase ENV with no
        # anchor) — incidentally also fixed by the same anchor change.
        '+# ENV VARIABLE_TOKEN_COUNT is set separately', 0),
    "fp_preexisting_known_gap_secret_rotation_id_compound_name": (
        # Pre-existing false-positive-prone design in f4b (predates this
        # session's changes): any UPPER_SNAKE name starting with a listed
        # keyword plus a 6+ char unquoted value triggers, even when the name
        # doesn't actually hold a secret. Not fixed here — same family as the
        # deferred f4b prefix-anchor item (see f4b_known_gap_* above).
        # Documented so it isn't mistaken for a new regression later.
        '+SECRET_ROTATION_ID=abc123def456', 1),  # gitleaks:allow (합성 테스트 픽스처)
}


def main():
    failures = []
    for name, (line, expected) in CASES.items():
        actual = run(line)
        status = "PASS" if actual == expected else "FAIL"
        if actual != expected:
            failures.append((name, expected, actual))
        print(f"[{status}] {name}: expected={expected} actual={actual}")

    print(f"\n{len(CASES) - len(failures)}/{len(CASES)} passed")
    if failures:
        print("\nFAILURES:")
        for name, expected, actual in failures:
            print(f"  {name}: expected exit {expected}, got {actual}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
