"""secret_redact.py — masks secrets in this skill's own observability logs
(interventions/receipts and similar append-only JSONL/DB records).

Background: a tool-input secrets guard can catch a secret *used in code*,
but text a script like harness_observability.py captures and persists into
its own local JSONL/DB logs is a separate exposure surface — this module
closes that gap for anything written through it.

Pattern credit: adapted from fivetaku/fablize's scripts/gate/ledger.py
redact() (MIT license), with a few additional key-value shapes added below.

API:
  scrub(text)          — substitute secrets only (no truncation/flattening).
                          Use for anything meant to preserve an audit trail
                          (e.g. a receipts.raw_json column).
  redact(text, limit)  — scrub + flatten newlines + length-cap. Use for
                          free-text log fields (e.g. interventions.context).
"""
from __future__ import annotations

import re
from typing import Any

# Secret shapes covered:
#  - key/value pairs: api_key/token/secret/password, plus app(_)key/app(_)secret
#    and access_token/refresh_token (covers common "APPKEY=..."/"*_API_KEY=..."
#    environment-variable-assignment shapes some vendor/brokerage APIs use)
#  - sk-*: OpenAI/Anthropic (sk-ant-)/OpenRouter (sk-or-) style keys, all
#    absorbed by one hyphen-inclusive pattern
#  - gh*_ / xox*: GitHub / Slack tokens
SECRET_PATTERNS = [
    re.compile(
        r"(?i)(api[_-]?key|token|secret|password|app[_-]?key|app[_-]?secret|"
        r"access[_-]?token|refresh[_-]?token)\s*[:=]\s*['\"]?[^'\"\s]{6,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{12,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{12,}"),
]


def scrub(text: Any) -> str:
    """Replace secret patterns with [REDACTED] only — preserves original
    structure/length (for audit-trail fields)."""
    value = "" if text is None else str(text)
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value


def redact(text: Any, limit: int = 500) -> str:
    """scrub + flatten newlines + length-cap — for free-text log fields."""
    value = "" if text is None else str(text)
    value = value.replace("\r", " ").replace("\n", " ").strip()
    value = scrub(value)
    if len(value) > limit:
        return value[: limit - 3] + "..."
    return value


def _self_test() -> int:
    """Deterministic self-test: verify synthetic secrets are actually removed."""
    cases = [
        ("openai key", "api_key: sk-abc123DEF456ghi789", "sk-abc123"),  # gitleaks:allow (synthetic self-test fixture)
        ("anthropic key", "ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx", "sk-ant-api03"),
        ("generic appkey kv", "appkey: PS1a2b3c4d5e6f7g8h9i", "PS1a2b3c"),  # gitleaks:allow (synthetic self-test fixture)
        ("github token", "token=ghp_ABCdef123456ghijkl", "ghp_ABC"),
        ("kv password", "password: hunter2secret", "hunter2"),
    ]
    fails = []
    for name, raw, leak in cases:
        out = scrub(raw)
        if leak in out or "[REDACTED]" not in out:
            fails.append(f"{name}: leak still present or not redacted -> {out!r}")
    # negative case: clean text with no secrets passes through unchanged
    if scrub("gate fired for session xyz") != "gate fired for session xyz":
        fails.append("negative: clean text was altered")
    for f in fails:
        print("FAIL ::", f)
    print(f"RESULT: {len(cases) + 1 - len(fails)}/{len(cases) + 1} PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
