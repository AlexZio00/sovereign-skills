#!/usr/bin/env python
"""handoff_attestation.py — session-handoff-LATEST.md integrity verification (SHA-256)
plus an evidence-chain receipt log.

Right after session-checkpoint Phase 2.4, write_receipt() appends a receipt
(and, for the checkpoint family, also refreshes the sidecar hash).
A SessionStart hook can call guard() to check the sidecar and verify_receipts()
to recompute and compare receipt SHA-256 values, in parallel.

Usage:
  python handoff_attestation.py write                              — refresh sidecar (legacy path, for direct calls outside checkpoint)
  python handoff_attestation.py verify                              — print a status string after verification (via SessionStart hook)
  python handoff_attestation.py guard                               — print to stdout + exit 1 only when TAMPERED (via SessionStart hook)
  python handoff_attestation.py write-receipt <family> <session_id> [receipts_dir] — append a receipt (checkpoint family also refreshes the sidecar)
  python handoff_attestation.py verify-receipt [receipts_dir]       — recompute+compare recent receipt SHA-256 + schemaVersion check, exit 1 on failure
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime


def _default_paths():
    """Handoff paths resolve relative to the current working project (cwd-relative) —
    this follows the same resolution rule as the SessionStart hook's handoff-injection
    logic (Path.cwd()/'memory'/...)."""
    base = os.path.join(os.getcwd(), "memory")
    return (
        os.path.join(base, "session-handoff-LATEST.md"),
        os.path.join(base, ".session-handoff.sha256"),
    )


DEFAULT_HANDOFF, DEFAULT_SIDECAR = _default_paths()

RECEIPTS_DIR_DEFAULT = os.path.join(os.path.expanduser("~"), ".claude", ".harness", "receipts")
INVOCATIONS_DIR_DEFAULT = os.path.join(os.path.expanduser("~"), ".claude", ".harness", "invocations")
SCHEMA_VERSION = "so-receipt-v1"
KNOWN_SCHEMA_VERSIONS = {"so-receipt-v1"}


def compute_hash(handoff_path):
    if not os.path.exists(handoff_path):
        return None
    with open(handoff_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_sidecar(handoff_path, sidecar_path):
    digest = compute_hash(handoff_path)
    if digest is None:
        return False
    with open(sidecar_path, "w", encoding="utf-8") as f:
        f.write(digest)
    return True


def verify(handoff_path, sidecar_path):
    if not os.path.exists(handoff_path):
        return "NO_HANDOFF"
    if not os.path.exists(sidecar_path):
        return "NO_SIDECAR"
    with open(sidecar_path, encoding="utf-8") as f:
        stored = f.read().strip()
    current = compute_hash(handoff_path)
    return "MATCH" if current == stored else "TAMPERED"


def _git_output(args, cwd):
    try:
        result = subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def compute_files_touched(cwd=None):
    """Changed files + sha256, based on git diff --name-status HEAD.
    D (delete) gets sha256=None. R/C (rename/copy) are normalized to M (the schema only defines M|A|D)."""
    cwd = cwd or os.getcwd()
    output = _git_output(["diff", "--name-status", "HEAD"], cwd)
    if output is None:
        return []
    files = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]
        if status.startswith("A"):
            change_type = "A"
        elif status.startswith("D"):
            change_type = "D"
        else:
            change_type = "M"
        sha = None
        if change_type != "D":
            sha = compute_hash(os.path.join(cwd, path))
        files.append({"path": path, "sha256": sha, "changeType": change_type})
    return files


def _canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _next_seq(receipts_path, session_id, family):
    if not receipts_path or not os.path.exists(receipts_path):
        return 1
    count = 0
    with open(receipts_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("sessionId") == session_id and rec.get("family") == family:
                count += 1
    return count + 1


def build_receipt(family, session_id, cwd=None, receipts_path=None):
    cwd = cwd or os.getcwd()
    now = datetime.now(UTC)
    created_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    month_key = now.strftime("%Y-%m")
    seq = _next_seq(receipts_path, session_id, family)
    branch = _git_output(["rev-parse", "--abbrev-ref", "HEAD"], cwd) or "UNKNOWN"
    commit = _git_output(["rev-parse", "--short", "HEAD"], cwd) or "UNKNOWN"
    actions_ref_path = os.path.join(INVOCATIONS_DIR_DEFAULT, f"{month_key}.jsonl")
    receipt = {
        "receiptId": f"{session_id}-{seq}",
        "schemaVersion": SCHEMA_VERSION,
        "sessionId": session_id,
        "family": family,
        "createdAt": created_at,
        "subject": {"cwd": cwd, "branch": branch, "commit": commit},
        "evidence": {
            # promptRef.path: no prompt-jsonl integration in this baseline scope.
            # Reserved as a pointer placeholder — kept as an empty string.
            "promptRef": {"source": "session-jsonl", "path": "", "sessionId": session_id},
            "actionsRef": {"path": actions_ref_path, "sessionId": session_id},
            "filesTouched": compute_files_touched(cwd),
        },
    }
    payload = _canonical_json(receipt)
    receipt["sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return receipt


def write_receipt(family, session_id, cwd=None, receipts_dir=None):
    receipts_dir = receipts_dir or RECEIPTS_DIR_DEFAULT
    os.makedirs(receipts_dir, exist_ok=True)
    month_key = datetime.now(UTC).strftime("%Y-%m")
    receipts_path = os.path.join(receipts_dir, f"{month_key}.jsonl")
    receipt = build_receipt(family, session_id, cwd=cwd, receipts_path=receipts_path)
    with open(receipts_path, "a", encoding="utf-8") as f:
        f.write(_canonical_json(receipt) + "\n")
    if family == "checkpoint":
        # Phase 2.4 replaces the old standalone write_sidecar call, so this
        # runs here only for the checkpoint family. cwd-based memory/ path
        # resolution follows the same rule as _default_paths().
        base = os.path.join(cwd or os.getcwd(), "memory")
        write_sidecar(
            os.path.join(base, "session-handoff-LATEST.md"),
            os.path.join(base, ".session-handoff.sha256"),
        )
    return receipt


def _receipt_sha_matches(receipt):
    payload_obj = {k: v for k, v in receipt.items() if k != "sha256"}
    expected = hashlib.sha256(_canonical_json(payload_obj).encode("utf-8")).hexdigest()
    return receipt.get("sha256") == expected


def verify_receipts(receipts_dir=None, limit=20):
    """Recompute+compare recent receipt SHA-256 values, plus a minimal schemaVersion invariant check.
    Returns: [(receiptId, status)], status in {OK, TAMPERED, UNKNOWN_SCHEMA, MALFORMED}."""
    receipts_dir = receipts_dir or RECEIPTS_DIR_DEFAULT
    if not os.path.isdir(receipts_dir):
        return []
    all_lines = []
    for fname in sorted(f for f in os.listdir(receipts_dir) if f.endswith(".jsonl")):
        with open(os.path.join(receipts_dir, fname), encoding="utf-8") as f:
            all_lines.extend(line.strip() for line in f if line.strip())
    recent = all_lines[-limit:]
    results = []
    for line in recent:
        try:
            receipt = json.loads(line)
        except json.JSONDecodeError:
            results.append(("UNKNOWN", "MALFORMED"))
            continue
        receipt_id = receipt.get("receiptId", "UNKNOWN")
        if receipt.get("schemaVersion") not in KNOWN_SCHEMA_VERSIONS:
            results.append((receipt_id, "UNKNOWN_SCHEMA"))
            continue
        if not _receipt_sha_matches(receipt):
            results.append((receipt_id, "TAMPERED"))
            continue
        results.append((receipt_id, "OK"))
    return results


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if mode == "write-receipt":
        family = sys.argv[2] if len(sys.argv) > 2 else "checkpoint"
        session_id = sys.argv[3] if len(sys.argv) > 3 else ""
        receipts_dir = sys.argv[4] if len(sys.argv) > 4 else None
        if not session_id:
            print("MISSING_SESSION_ID")
            sys.exit(1)
        receipt = write_receipt(family, session_id, receipts_dir=receipts_dir)
        print(f"OK receiptId={receipt['receiptId']}")
        return
    if mode == "verify-receipt":
        receipts_dir = sys.argv[2] if len(sys.argv) > 2 else None
        results = verify_receipts(receipts_dir=receipts_dir)
        bad = [(rid, status) for rid, status in results if status != "OK"]
        if bad:
            for rid, status in bad:
                print(f"⚠️ RECEIPT_{status}: {rid}")
            sys.exit(1)
        print(f"RECEIPTS_OK ({len(results)} checked)")
        return
    handoff = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_HANDOFF
    sidecar = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_SIDECAR
    if mode == "write":
        ok = write_sidecar(handoff, sidecar)
        print("OK" if ok else "SKIPPED_NO_HANDOFF")
    elif mode == "guard":
        status = verify(handoff, sidecar)
        if status == "TAMPERED":
            print("TAMPERED")
            sys.exit(1)
        sys.exit(0)
    else:
        print(verify(handoff, sidecar))


if __name__ == "__main__":
    main()
