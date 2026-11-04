#!/usr/bin/env python3
"""scan_secrets.py -- deterministic secrets scanner for git diffs.

Usage: git diff --staged | python scan_secrets.py   (run from the skill's scripts/ folder or by full path)
Exit code: 0 = clean, 1 = issues found

Design: scans ONLY added (+) lines to avoid blocking secret removal commits.
Exception: merge conflict markers are checked on all lines (added + context).

Ported from scan_secrets.pl (coinangel/claude-pre-push-skill, MIT). Regex patterns and
anti-evasion defenses are preserved 1:1 from the Perl original; the regression suite
(test_scan_secrets.py) re-verifies parity.

Hardening notes (internal revision history, not a version table):
- STDIN is decoded as UTF-8 and every line is normalized (zero-width characters, smart quotes,
  homoglyphs) before any rule runs.
- A whole-line-reversed copy is re-scanned with the unanchored tight-form rules, and
  "A" + "B" quote concatenation is collapsed into one literal before matching.
- Not fixed on purpose: cross-line credential splitting, and a looser f4b prefix-tolerant anchor
  (both need their own design and a calibration corpus).
- Same-line allow marker: an added line that carries `scan-secrets: allow` or
  `gitleaks:allow` after a comment leader (`#`, `//`, `/*`, `--`, `;`) skips credential
  checks for that one line only (merge-conflict detection is never suppressible). Every skip is
  counted and printed to stderr as `[ALLOW] N added line(s) skipped ...`, so a marker cannot
  silently swallow a finding.
"""
from __future__ import annotations

import re
import sys
from collections.abc import Iterable

# ── Normalization (defangs zero-width / smart-quote / homoglyph evasion) ──
_ZERO_WIDTH_RE = re.compile("[​‌‍﻿]")
_CURLY_QUOTES = str.maketrans({
    "‘": "'", "’": "'", "“": '"', "”": '"',
})
_CYRILLIC_HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p",
    "с": "c", "у": "y", "х": "x", "і": "i",
    "ј": "j", "ѕ": "s",
})
# collapse "A" + "B" (+ "C" ...) quote+operator concatenation into one literal
_CONCAT_RE = re.compile(r"""(["'])([^"']*)\1(\s*\+\s*)(["'])([^"']*)\4""")


def _collapse_concat(line: str) -> str:
    while True:
        new_line, n = _CONCAT_RE.subn(r"\1\2\5\1", line)
        if n == 0:
            return line
        line = new_line


def _normalize(line: str) -> str:
    line = _ZERO_WIDTH_RE.sub("", line)
    line = line.translate(_CURLY_QUOTES)
    line = line.translate(_CYRILLIC_HOMOGLYPHS)
    return _collapse_concat(line)


# ── Merge conflict markers — checked on ALL lines (added + unchanged context) ──
_MERGE_RE = re.compile(r"^[+ ](<{7} |={7}\s*$|>{7} )")

# ── Same-line allow marker: skips credential checks for that one added line
# only. Merge-conflict detection above still applies (never suppressible).
# Skips are counted and reported by main() so a silent bypass isn't possible. ──
_ALLOW_RE = re.compile(r"(?:#|//|/\*|--|;)\s*(?:scan-secrets:\s*allow|gitleaks:allow)\b")
LAST_ALLOWED_COUNT = 0

# ── f1: AWS Access Key ID (AKIA=long-term, ASIA=STS/temporary) ──
_F1_RE = re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}")

# ── f2: Private key header — RSA/EC/DSA/OpenSSH/generic/PKCS8-ENCRYPTED, PGP
# block, and the 4-dash SSH2/Tectia export variant ──
_F2_RE = re.compile(
    r"-{4,5}\s?BEGIN\s+(?:[A-Z0-9]+\s+){0,3}PRIVATE\s+KEY(?:\s+BLOCK)?\s?-{4,5}"
)

# ── f3: Password embedded in connection/DSN string (skip ${VAR}/$(cmd)
# templates — scoped to the matched credential substring only) ──
# userinfo cannot hold / ? # (RFC 3986) - without this a URL path/query (e.g. a Google Fonts
# "family=JetBrains+Mono:wght@400") reads as user:password@host. An empty user (redis://:pw@h) is allowed.
_F3_RE = re.compile(r"""(://[^\s:@/?#]*:[^\s@]{4,}@)""")
_F3_TEMPLATE_RE = re.compile(r"\$\{|\$\(")

# ── f4a: Hardcoded credential assignment — quoted value (6+ chars) ──
_F4A_RE = re.compile(
    r"""(password|passwd|pwd|secret|api_key|apikey|access_token|auth_token"""
    r"""|bearer_token|jwt_secret|github_token|gh_token)\s*[=:]\s*"""
    r"""['"][^'"]{6,}['"]""",
    re.IGNORECASE,
)

# ── f4b: Hardcoded credential assignment — unquoted YAML/ENV value
# Anchored to start of added line to avoid matching inside string/comments ──
_F4B_RE = re.compile(
    r"""^\+\s*(PASSWORD|PASSWD|PWD|SECRET|API_KEY|APIKEY|ACCESS_TOKEN"""
    r"""|AUTH_TOKEN|BEARER_TOKEN|JWT_SECRET|GITHUB_TOKEN|GH_TOKEN)[_A-Z0-9]*"""
    r"""\s*[=:]\s*[^\s'"#$\{]{6,}""",
    re.IGNORECASE,
)

# ── f5: Platform tokens — Slack / GitHub (5 types) / Stripe live ──
_F5_RE = re.compile(
    r"xox[baprs]-[0-9A-Za-z\-]+|gh[poushr]_[0-9A-Za-z]{20,}"
    r"|github_pat_[A-Za-z0-9_]{50,}|sk_live_[0-9A-Za-z]+|pk_live_[0-9A-Za-z]+"
)

# ── f6: Secret in Dockerfile ENV/ARG directive — anchored so ENV/ARG must be
# the leading instruction token, not a substring of ordinary prose ──
_F6_RE = re.compile(
    r"^\+\s*(?:ENV|ARG)\s+\w*(?:PASSWORD|SECRET|KEY|TOKEN)\w*[\s=]",
    re.IGNORECASE,
)

# ── f7: Google / Gemini API Key (AIza + 35 alphanumeric chars) ──
_F7_RE = re.compile(r"AIza[0-9A-Za-z\-_]{35}")

# ── f8: npm registry auth token (.npmrc) — whitespace-around-'=' tolerant ──
_F8_RE = re.compile(r"_authToken\s*=\s*[A-Za-z0-9\-_]{20,}")

# ── f9: LLM provider API keys (Anthropic/OpenAI/HuggingFace/Replicate/Groq/xAI) ──
_F9_RE = re.compile(
    r"sk-ant-[A-Za-z0-9_\-]{20,}|sk-proj-[A-Za-z0-9_\-]{20,}"
    r"|sk-svcacct-[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9]{48}(?![a-z])"
    r"|hf_[A-Za-z0-9]{30,}|r8_[A-Za-z0-9]{30,}|gsk_[A-Za-z0-9]{40,}"
    r"|xai-[A-Za-z0-9]{20,}"
)

# ── f10: Azure credentials — Storage Account Key / SAS token sig / conn string ──
_F10_RE = re.compile(
    r"AccountKey=[A-Za-z0-9+/]{86}==|(?:[?&]|&amp;)sig=[A-Za-z0-9%+/]{30,}"
    r"|DefaultEndpointsProtocol=https;AccountName=",
    re.IGNORECASE,
)

# ── f11: Prompt injection strings embedded in code (supply-chain prompt attack) ──
_F11_RE = re.compile(
    r"""["'](?:[^"']*?)(?:ignore\s+(?:previous|all\s+previous)\s+instructions"""
    r"""|disregard\s+(?:your\s+)?(?:instructions|guidelines|system\s+prompt)"""
    r"""|you\s+are\s+now\s+(?:a|an)\s+\w+\s+without\s+(?:restrictions|limits)"""
    r"""|forget\s+(?:everything|your\s+previous|all\s+previous)"""
    r"""|system\s+prompt\s+override|jailbreak\s+mode\s+enabled)"""
    r"""(?:[^"']*?)["']""",
    re.IGNORECASE,
)

# ── f12: Supply-chain risk — non-standard package sources ──
_F12_EXTRA_INDEX_RE = re.compile(
    r"--extra-index-url\s+(?!https?://(?:pypi\.org|files\.pythonhosted\.org))",
    re.IGNORECASE,
)
_F12_INDEX_RE = re.compile(
    r"--index-url\s+(?!https?://(?:pypi\.org|files\.pythonhosted\.org))",
    re.IGNORECASE,
)
_F12_GIT_HTTP_RE = re.compile(r"git\+http://", re.IGNORECASE)

# ── f13: Slack Incoming Webhook URL ──
_F13_RE = re.compile(r"hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+")

# Reversed-line defense: applied only to unanchored/tight-form rules. Anchored
# or keyword-proximity rules (f3/f4a/f4b/f6/f11/f12) are excluded — reversal
# breaks their intended semantics and would just add false-positive surface.
_REVERSED_PATTERNS = (_F1_RE, _F2_RE, _F5_RE, _F7_RE, _F8_RE, _F9_RE, _F10_RE, _F13_RE)
_REVERSED_KEYS = ("f1", "f2", "f5", "f7", "f8", "f9", "f10", "f13")

_MESSAGES = (
    ("f_merge", "CRITICAL", "Unresolved merge conflict markers detected"),
    ("f1", "CRITICAL", "AWS Access Key ID detected"),
    ("f2", "CRITICAL", "Private key detected"),
    ("f3", "CRITICAL", "Password in connection string detected"),
    ("f4a", "HIGH", "Hardcoded credential assignment (quoted value) detected"),
    ("f4b", "HIGH", "Hardcoded credential assignment (unquoted YAML/ENV) detected"),
    ("f5", "CRITICAL", "Platform token detected (Slack / GitHub / Stripe)"),
    ("f6", "CRITICAL", "Secret in Dockerfile ENV directive"),
    ("f7", "CRITICAL", "Google / Gemini API Key detected"),
    ("f8", "HIGH", "npm registry auth token detected"),
    ("f9", "CRITICAL", "LLM provider API key detected (Anthropic / OpenAI / HuggingFace / Replicate / Groq)"),
    ("f10", "CRITICAL", "Azure credential detected (Storage Key / SAS token / connection string)"),
    ("f11", "HIGH", "Prompt injection string detected in code (LLM supply-chain attack risk)"),
    ("f12", "HIGH", "Supply-chain risk detected (non-PyPI index URL or HTTP git install)"),
    ("f13", "HIGH", "Slack Incoming Webhook URL detected"),
)


assert len(_REVERSED_KEYS) == len(_REVERSED_PATTERNS)  # zip() without strict= (Python 3.9)


def scan_lines(lines: Iterable[str]) -> dict:
    """Pure decision function: scan an already-split sequence of diff lines and return the flag dict.
    No file or STDIN I/O, so tests can call it directly (no subprocess or perl needed)."""
    global LAST_ALLOWED_COUNT
    flags = {key: False for key, _, _ in _MESSAGES}
    allowed = 0

    for raw_line in lines:
        line = _normalize(raw_line)

        if _MERGE_RE.search(line):
            flags["f_merge"] = True

        if not line.startswith("+"):
            continue
        if line.startswith("+++"):
            continue
        if _ALLOW_RE.search(line):
            allowed += 1
            continue

        # Runtime-reversal defense: a value written backwards in source
        # contains the real secret as a contiguous substring once the WHOLE
        # LINE is reversed. Only unanchored, tight-form rules are re-checked.
        reversed_line = line[::-1]
        for key, pattern in zip(_REVERSED_KEYS, _REVERSED_PATTERNS):
            if pattern.search(reversed_line):
                flags[key] = True

        if _F1_RE.search(line):
            flags["f1"] = True
        if _F2_RE.search(line):
            flags["f2"] = True

        m3 = _F3_RE.search(line)
        if m3 and not _F3_TEMPLATE_RE.search(m3.group(1)):
            flags["f3"] = True

        if _F4A_RE.search(line):
            flags["f4a"] = True
        if _F4B_RE.search(line):
            flags["f4b"] = True
        if _F5_RE.search(line):
            flags["f5"] = True
        if _F6_RE.search(line):
            flags["f6"] = True
        if _F7_RE.search(line):
            flags["f7"] = True
        if _F8_RE.search(line):
            flags["f8"] = True
        if _F9_RE.search(line):
            flags["f9"] = True
        if _F10_RE.search(line):
            flags["f10"] = True
        if _F11_RE.search(line):
            flags["f11"] = True
        if (_F12_EXTRA_INDEX_RE.search(line) or _F12_INDEX_RE.search(line)
                or _F12_GIT_HTTP_RE.search(line)):
            flags["f12"] = True
        if _F13_RE.search(line):
            flags["f13"] = True

    LAST_ALLOWED_COUNT = allowed
    return flags


def format_report(flags: dict) -> str:
    out = []
    for key, severity, text in _MESSAGES:
        if flags.get(key):
            out.append(f"\U0001f6a8 {severity}: {text}")
    return "\n".join(out)


def main() -> int:
    # Diffs are UTF-8 and the report contains emoji; the console default (cp949, cp1252, ...) would
    # crash on either, so force UTF-8 and never fail on an undecodable byte.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    lines = [line.rstrip("\r\n") for line in sys.stdin]
    flags = scan_lines(lines)
    if LAST_ALLOWED_COUNT:
        print(
            f"[ALLOW] {LAST_ALLOWED_COUNT} added line(s) skipped by an allow marker "
            "(scan-secrets: allow / gitleaks:allow) - review them in the diff",
            file=sys.stderr,
        )
    if any(flags.values()):
        print(format_report(flags))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
