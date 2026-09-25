"""test_canary_mix.py — regression tests for canary_mix.py."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import canary_mix as cm  # noqa: E402

results = []

with tempfile.TemporaryDirectory() as td:
    canaries_dir = pathlib.Path(td) / "canaries"
    (canaries_dir / "clean").mkdir(parents=True)
    (canaries_dir / "seeded").mkdir()
    (canaries_dir / "clean" / "c1.py").write_text("# clean 1", encoding="utf-8")
    (canaries_dir / "clean" / "c2.py").write_text("# clean 2", encoding="utf-8")
    (canaries_dir / "seeded" / "s1.py").write_text("# seeded 1", encoding="utf-8")
    (canaries_dir / "seeded" / "s1.json").write_text(
        json.dumps({"defect_id": "d1", "expected_finding_keywords": ["kw1"], "category": "cat1"}), encoding="utf-8")
    (canaries_dir / "seeded" / "s2.py").write_text("# seeded 2", encoding="utf-8")
    (canaries_dir / "seeded" / "s2.json").write_text(
        json.dumps({"defect_id": "d2", "expected_finding_keywords": ["kw2"], "category": "cat2"}), encoding="utf-8")

    # 1) load_canary_pool: correct clean/seeded counts (the .json sidecar is excluded from the pool)
    pool = cm.load_canary_pool(canaries_dir)
    results.append(("1 load_canary_pool counts", len(pool["clean"]) == 2 and len(pool["seeded"]) == 2, pool))

    # 2) select_canaries: honors n_clean/n_seeded
    selected = cm.select_canaries(pool, n_clean=1, n_seeded=2)
    kinds = [s["kind"] for s in selected]
    ok = kinds.count("clean") == 1 and kinds.count("seeded") == 2
    results.append(("2 select_canaries counts honored", ok, selected))

    # 3) seeded entries get sidecar metadata merged in
    seeded_entries = [s for s in selected if s["kind"] == "seeded"]
    ok = all("defect_id" in s and "expected_finding_keywords" in s for s in seeded_entries)
    results.append(("3 select_canaries sidecar metadata merged", ok, seeded_entries))

    # 4) write_manifest round-trips
    out_path = pathlib.Path(td) / "manifest.json"
    cm.write_manifest(selected, out_path)
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    results.append(("4 write_manifest round-trip", loaded == selected, loaded))

    # 5) stage_canaries: the reviewer-visible path never leaks the canary directory names
    stage_dir = pathlib.Path(td) / "bundle"
    staged = cm.stage_canaries(selected, stage_dir)
    ok = (all(pathlib.Path(s["staged_path"]).is_file() for s in staged)
          and not any(w in s["staged_path"] for s in staged for w in ("canaries", "clean", "seeded"))
          and all(pathlib.Path(s["staged_path"]).read_text(encoding="utf-8")
                  == pathlib.Path(s["path"]).read_text(encoding="utf-8") for s in staged))
    results.append(("5 stage_canaries path-neutral + content identical", ok, staged))

fails = [r for r in results if not r[1]]
for name, ok, detail in results:
    if not ok:
        print(f"FAIL {name}: {detail}")
print(f"\n{len(results) - len(fails)}/{len(results)} passed")
sys.exit(1 if fails else 0)
