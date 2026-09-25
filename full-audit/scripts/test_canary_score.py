"""test_canary_score.py — regression tests for canary_score.py."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import canary_score as cs  # noqa: E402

results = []

MANIFEST = [
    {"kind": "clean", "path": "/canaries/clean/c1.py"},
    {"kind": "clean", "path": "/canaries/clean/c2.py"},
    {"kind": "seeded", "path": "/canaries/seeded/s1.py", "defect_id": "d1"},
    {"kind": "seeded", "path": "/canaries/seeded/s2.py", "defect_id": "d2"},
]
FINDINGS = [
    {"file": "/canaries/clean/c1.py", "verdict": "CONFIRMED"},   # false positive on a clean file
    {"file": "/canaries/seeded/s1.py", "verdict": "CONFIRMED"},  # seeded defect detected
    # s2.py: no finding -> missed
]

# 1) fp_on_clean is correct
result = cs.score(MANIFEST, FINDINGS)
results.append(("1 score fp_on_clean", [m["path"] for m in result["fp_on_clean"]] == ["/canaries/clean/c1.py"], result))

# 2) missed_seeded is correct
results.append(("2 score missed_seeded", [m["path"] for m in result["missed_seeded"]] == ["/canaries/seeded/s2.py"], result))

# 3) staged_path is preferred when present, and a reviewer-written relative/suffix path still matches
STAGED = [
    {"kind": "seeded", "path": "/pool/seeded/billing_client.py", "staged_path": "/run/bundle/billing_client.py",
     "defect_id": "d1"},
]
r = cs.score(STAGED, [{"file": "bundle/billing_client.py", "verdict": "CONFIRMED"}])
results.append(("3 staged_path + relative suffix match", r["missed_seeded"] == [], r))

# 4) when a finding has descriptive text, at least one expected keyword must appear to count as a detection
KW = [{"kind": "seeded", "path": "/p/s.py", "defect_id": "d1", "expected_finding_keywords": ["injection"]}]
r_wrong = cs.score(KW, [{"file": "/p/s.py", "verdict": "CONFIRMED", "summary": "missing type hints"}])
r_right = cs.score(KW, [{"file": "/p/s.py", "verdict": "CONFIRMED", "summary": "SQL Injection via concat"}])
r_bare = cs.score(KW, [{"file": "/p/s.py", "verdict": "CONFIRMED"}])
ok = len(r_wrong["missed_seeded"]) == 1 and r_right["missed_seeded"] == [] and r_bare["missed_seeded"] == []
results.append(("4 keyword match (only when descriptive text is present)", ok, (r_wrong, r_right, r_bare)))

# 5) a non-CONFIRMED finding (e.g. UNCERTAIN) counts neither as a detection nor a false positive
r = cs.score(MANIFEST, [{"file": "/canaries/clean/c2.py", "verdict": "UNCERTAIN"}])
results.append(("5 non-CONFIRMED findings ignored", r["fp_on_clean"] == [] and len(r["missed_seeded"]) == 2, r))

with tempfile.TemporaryDirectory() as td:
    manifest_path = pathlib.Path(td) / "manifest.json"
    findings_path = pathlib.Path(td) / "findings.json"
    manifest_path.write_text(json.dumps(MANIFEST), encoding="utf-8")
    findings_path.write_text(json.dumps(FINDINGS), encoding="utf-8")

    # 6) load round-trip
    ok = cs.load_manifest(manifest_path) == MANIFEST and cs.load_findings(findings_path) == FINDINGS
    results.append(("6 load_manifest/findings round-trip", ok, None))

    # 7) recall ledger is append-only
    ledger_path = pathlib.Path(td) / "recall_ledger.jsonl"
    cs.append_recall_ledger([{"date": "2026-09-25", "skill": "full-audit", "seeded_id": "d1", "detected": True}], ledger_path)
    cs.append_recall_ledger([{"date": "2026-09-25", "skill": "full-audit", "seeded_id": "d2", "detected": False}], ledger_path)
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    results.append(("7 append_recall_ledger is append-only", len(lines) == 2, lines))

    # 8) cmd_score end-to-end: records 2 seeded entries, returns 0
    ledger_path2 = pathlib.Path(td) / "recall_ledger2.jsonl"
    args = types.SimpleNamespace(manifest=str(manifest_path), findings=str(findings_path),
                                 skill="full-audit", recall_ledger=str(ledger_path2))
    rc = cs.cmd_score(args)
    recs = [json.loads(line) for line in ledger_path2.read_text(encoding="utf-8").strip().splitlines()]
    ok = (rc == 0 and len(recs) == 2
          and any(x["seeded_id"] == "d1" and x["detected"] is True for x in recs)
          and any(x["seeded_id"] == "d2" and x["detected"] is False for x in recs))
    results.append(("8 cmd_score e2e recall ledger", ok, recs))

    # 9) recall_summary: per-skill k/n, n<5 marks unmeasured
    summ = cs.recall_summary(ledger_path2, skill="full-audit")
    results.append(("9 recall_summary k/n + n<5 unmeasured",
                    summ == {"detected": 1, "total": 2, "unmeasured": True}, summ))

fails = [r for r in results if not r[1]]
for name, ok, detail in results:
    if not ok:
        print(f"FAIL {name}: {detail}")
print(f"\n{len(results) - len(fails)}/{len(results)} passed")
sys.exit(1 if fails else 0)
