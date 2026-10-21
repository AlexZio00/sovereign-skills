"""test_canary_mix.py — regression tests for canary_mix.py."""
from __future__ import annotations

import json
import pathlib
import re
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
                  == pathlib.Path(s["path"]).read_text(encoding="utf-8") for s in staged)
          # the original file name is hidden too - the same name would let a reviewer grep
          # for it and find the pool original, revealing that the file is a control
          # check the whole staged name against the neutral pattern; a substring test on short
          # stems like "c1" fails at random whenever the random hex happens to contain them
          and all(re.fullmatch(r"module_[0-9a-f]{8}", pathlib.Path(s["staged_path"]).stem) for s in staged)
          and all(pathlib.Path(s["staged_path"]).suffix == pathlib.Path(s["path"]).suffix for s in staged))
    results.append(("5 stage_canaries path-neutral + content identical", ok, staged))

# 6) --ext filter: separate pools per suffix (docs-area canaries)
with tempfile.TemporaryDirectory() as td2:
    cd = pathlib.Path(td2) / "audit-canaries"
    (cd / "clean").mkdir(parents=True)
    (cd / "seeded").mkdir()
    (cd / "clean" / "a.md").write_text("# clean doc", encoding="utf-8")
    (cd / "clean" / "b.py").write_text("# clean code", encoding="utf-8")
    (cd / "seeded" / "d.md").write_text("# seeded doc", encoding="utf-8")
    (cd / "seeded" / "d.json").write_text(
        json.dumps({"defect_id": "dd", "expected_finding_keywords": ["k"], "category": "doc"}), encoding="utf-8")
    (cd / "seeded" / "e.py").write_text("# seeded code", encoding="utf-8")
    pm = cm.load_canary_pool(cd, ext=".md")
    pall = cm.load_canary_pool(cd)
    ok = ([f.name for f in pm["clean"]] == ["a.md"] and [f.name for f in pm["seeded"]] == ["d.md"]
          and len(pall["clean"]) == 2 and len(pall["seeded"]) == 2)
    results.append(("6 load_canary_pool --ext filter", ok, (pm, pall)))
    mo = pathlib.Path(td2) / "m.json"
    rc = cm.main(["select", "--ext", ".md", "--canaries-dir", str(cd), "--out", str(mo),
                  "--stage-dir", str(pathlib.Path(td2) / "bundle")])
    man = json.loads(mo.read_text(encoding="utf-8"))
    ok = rc == 0 and len(man) == 2 and all(m["staged_path"].endswith(".md") for m in man)
    results.append(("7 select --ext .md CLI: stages docs canaries only", ok, man))

# 8) --ext without a leading dot works; missing suffix reports "no files with suffix"; message shows actual counts
import contextlib  # noqa: E402
import io  # noqa: E402

with tempfile.TemporaryDirectory() as td3:
    cd = pathlib.Path(td3) / "pool"
    (cd / "clean").mkdir(parents=True)
    (cd / "seeded").mkdir()
    (cd / "clean" / "a.md").write_text("# clean doc", encoding="utf-8")
    (cd / "seeded" / "d.md").write_text("# seeded doc", encoding="utf-8")
    (cd / "seeded" / "d.json").write_text(json.dumps({"defect_id": "dd"}), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc1 = cm.main(["select", "--ext", "md", "--n-clean", "3", "--n-seeded", "3", "--canaries-dir", str(cd),
                       "--out", str(pathlib.Path(td3) / "m1.json")])
    out1 = buf.getvalue()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc2 = cm.main(["select", "--ext", "rs", "--canaries-dir", str(cd), "--out", str(pathlib.Path(td3) / "m2.json")])
    out2 = buf.getvalue()
    results.append(("8 --ext without dot selects", rc1 == 0 and "clean=1 seeded=1" in out1, out1))
    results.append(("9 message shows actual counts + shortfall warning", "WARN" in out1 and "requested clean=3" in out1, out1))
    results.append(("10 missing suffix message", rc2 == 2 and "no files with suffix .rs" in out2, out2))

fails = [r for r in results if not r[1]]


def test_all_cases():
    """pytest entry point: this file uses its own runner, so without this wrapper `pytest` collects
    0 tests and exits 0 (looks like a pass)."""
    assert not fails, fails


if __name__ == "__main__":
    for name, ok, detail in results:
        if not ok:
            print(f"FAIL {name}: {detail}")
    print(f"\n{len(results) - len(fails)}/{len(results)} passed")
    sys.exit(1 if fails else 0)
