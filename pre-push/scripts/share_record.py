#!/usr/bin/env python3
"""share_record.py - count-only scan of the exact files a public-mirror push sends, plus a value-free record.

Idea from rlaope/oh-my-hermes (MIT) "data share review"; re-implemented here.
Used by pre-push Step 3.5 (d). WARN-only: it never blocks. It reports how many matches of each class sit in the
files the push carries (whole files, not only the added lines) and appends one JSONL line to a local log.
The record holds the remote, date, file count, a digest of the file contents and the per-class counts -
never a matched value (the log must not become the leak).

  python share_record.py --remote <url> --files-from <list.txt> [--log-dir <dir>]
  (list.txt has one repo-relative path per line; the default log dir is <git-dir>/pre-push-share-log,
   which git never tracks or pushes)

Exit: 0 for every scan result (WARN-only); 2 only when the file list cannot be read.
Prints "SHARE_SCAN: <class>=<n> ... files=<n> skipped=<n>" and "SHARE_RECORD: <path>".
Known misses: values split across lines, encoded/base64 content, binary files (skipped and counted).
Not counted on purpose: lines with a gitleaks:allow / scan-secrets: allow marker, placeholder mail domains
(example.*, *.invalid, git@github.com), key-shaped strings inside test files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CLASSES = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "user_home_path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]|(?<![\w.:~-])/(?:Users|home)/[^/\s]+/", re.I),
    "api_key_like": re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[bp]-[0-9A-Za-z-]{10,})"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[ -])?\(?\d{2,4}\)?[ -]\d{3,4}[ -]\d{4}\b"),
    "private_ip": re.compile(r"\b(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)\b"),
}
ALLOW_MARK = re.compile(r"gitleaks:allow|scan-secrets:\s*allow")
PLACEHOLDER_MAIL = re.compile(r"@(example\.[a-z]+|[a-z0-9.-]+\.invalid|github\.com|gitlab\.com)\b", re.I)
TEST_FILE = re.compile(r"(^|/)(tests?/|test_[^/]+$)|_test\.[a-z]+$")


def default_log_dir(root: Path) -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=root, capture_output=True, text=True, timeout=10)
        git_dir = Path(out.stdout.strip())
        if out.returncode == 0 and out.stdout.strip():
            return (git_dir if git_dir.is_absolute() else root / git_dir) / "pre-push-share-log"
    except (OSError, subprocess.SubprocessError):
        pass
    return root / ".git" / "pre-push-share-log"


def scan(paths: list[Path]) -> tuple[dict, str, int]:
    counts = {k: 0 for k in CLASSES}
    h = hashlib.sha256()
    skipped = 0
    for p in sorted(paths):
        try:
            data = p.read_bytes()
        except OSError:
            skipped += 1
            continue
        h.update(p.as_posix().encode() + b"\0" + hashlib.sha256(data).digest())
        if b"\0" in data[:4096]:
            skipped += 1
            continue
        is_test = bool(TEST_FILE.search(p.as_posix()))
        for line in data.decode("utf-8", errors="replace").splitlines():
            if ALLOW_MARK.search(line):  # same opt-out marker as scan_secrets.py
                continue
            for k, rx in CLASSES.items():
                if k == "api_key_like" and is_test:  # fake keys in fixtures; scan_secrets.py still checks the diff
                    continue
                hits = [m for m in rx.finditer(line)
                        if not (k == "email" and PLACEHOLDER_MAIL.search(m.group(0)))]
                counts[k] += len(hits)
    return counts, h.hexdigest(), skipped


def redact_remote(remote: str) -> str:
    """Keep scheme, host and path only: userinfo (even with / or @ in the password), query and fragment are dropped."""
    if "://" not in remote:  # scp form git@host:owner/repo carries no secret
        return remote
    scheme, rest = remote.split("://", 1)
    rest = rest.split("?", 1)[0].split("#", 1)[0]
    # cut at the LAST @: a password may hold / or @, so urlsplit's netloc is not safe here.
    # A path that contains @ is over-trimmed (host lost) - safe direction, never a leak.
    return f"{scheme}://{rest.rsplit('@', 1)[-1]}"


def record(remote: str, files: list[str], counts: dict, digest: str, skipped: int, log_dir: Path) -> Path:
    now = datetime.now(timezone.utc)
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{now:%Y-%m}.jsonl"
    remote = redact_remote(remote)  # drop user:token@ and ?token= from the URL before it is logged
    entry = {"ts": now.isoformat(timespec="seconds"), "remote": remote, "files": len(files), "binary_or_unreadable": skipped,
             "digest": digest, "counts": counts}
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--remote", required=True)
    ap.add_argument("--files-from", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args(argv)
    try:
        files = [x.strip() for x in Path(a.files_from).read_text(encoding="utf-8").splitlines() if x.strip()]
    except OSError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    root = Path(a.root)
    counts, digest, skipped = scan([root / f for f in files])
    print("SHARE_SCAN: " + " ".join(f"{k}={v}" for k, v in counts.items()) + f" files={len(files)} skipped={skipped}")
    if not a.no_record:
        log_dir = Path(a.log_dir) if a.log_dir else default_log_dir(root)
        print(f"SHARE_RECORD: {record(a.remote, files, counts, digest, skipped, log_dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
