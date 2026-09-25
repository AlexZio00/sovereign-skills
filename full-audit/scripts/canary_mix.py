#!/usr/bin/env python3
"""canary_mix.py — selects canaries (a known-clean control file plus a file with a
planted defect) to mix into a full-audit review bundle.

Why: "zero findings" from a review pass could mean the area is actually clean, or
it could mean the reviewer missed something. Mixing in a control pair and scoring
the reviewer's verdicts against it afterward (see canary_score.py) turns that
ambiguity into a measured number.

Pool layout: <canaries-dir>/{clean,seeded}/. Each seeded file has a matching
sidecar of the same name with a .json extension, holding defect_id,
expected_finding_keywords, and category. The reviewer-visible file name and body
must never contain anything that gives away that it's a planted defect.

Selection is deterministic (sorted, then take the first n) — the same pool always
produces the same manifest. Pass --stage-dir to copy the selected files into that
directory and record their staged_path in the manifest. Put staged_path (not the
original canaries-dir path) into the actual review bundle — if the reviewer sees
a path like ".../canaries/seeded/...", it gives away which file is the control.

This only stages files into the review set; it never changes any verdict. Scoring
happens separately in canary_score.py.

Usage:
  python canary_mix.py select --pool both --n-clean 1 --n-seeded 1 --out <manifest.json> \
      [--stage-dir <review bundle dir>] [--canaries-dir <pool dir>]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil

# Default pool ships inside this skill (scripts/canaries/) so the feature works
# out of the box with no environment-specific setup. Override with --canaries-dir
# to point at a larger, project-specific pool.
DEFAULT_CANARIES_DIR = pathlib.Path(__file__).resolve().parent / "canaries"


def load_canary_pool(canaries_dir: pathlib.Path) -> dict:
    pool = {"clean": [], "seeded": []}
    for kind in ("clean", "seeded"):
        d = canaries_dir / kind
        if d.is_dir():
            pool[kind] = sorted(p for p in d.iterdir() if p.is_file() and p.suffix != ".json")
    return pool


def select_canaries(pool: dict, n_clean: int = 1, n_seeded: int = 1) -> list:
    selected = []
    for kind, n in (("clean", n_clean), ("seeded", n_seeded)):
        for f in pool.get(kind, [])[:n]:
            entry = {"kind": kind, "path": str(f)}
            if kind == "seeded":
                sidecar = f.with_suffix(".json")
                if sidecar.is_file():
                    entry.update(json.loads(sidecar.read_text(encoding="utf-8")))
            selected.append(entry)
    return selected


def stage_canaries(selected: list, stage_dir: pathlib.Path) -> list:
    """Copy the selected files into stage_dir under their original file name and
    attach staged_path to each entry. Assumes file names don't collide within the
    pool — if they do, this raises ValueError instead of silently overwriting."""
    stage_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for entry in selected:
        src = pathlib.Path(entry["path"])
        dst = stage_dir / src.name
        if dst.exists():
            raise ValueError(f"stage target already exists: {dst}")
        shutil.copyfile(src, dst)
        out.append({**entry, "staged_path": str(dst)})
    return out


def write_manifest(selected: list, out_path: pathlib.Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_select(args) -> int:
    pool = load_canary_pool(pathlib.Path(args.canaries_dir))
    n_clean = 0 if args.pool == "seeded" else args.n_clean
    n_seeded = 0 if args.pool == "clean" else args.n_seeded
    selected = select_canaries(pool, n_clean=n_clean, n_seeded=n_seeded)
    if not selected:
        print(f"[CANARY-MIX] selected 0 -- pool is empty: {args.canaries_dir}")
        return 2
    if args.stage_dir:
        selected = stage_canaries(selected, pathlib.Path(args.stage_dir))
    write_manifest(selected, pathlib.Path(args.out))
    print(f"[CANARY-MIX] selected {len(selected)} (clean={n_clean} seeded={n_seeded}) -> {args.out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Select canaries for a full-audit review bundle")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_select = sub.add_parser("select")
    p_select.add_argument("--pool", default="both", choices=["both", "clean", "seeded"])
    p_select.add_argument("--n-clean", type=int, default=1, dest="n_clean")
    p_select.add_argument("--n-seeded", type=int, default=1, dest="n_seeded")
    p_select.add_argument("--out", required=True)
    p_select.add_argument("--stage-dir", default=None, dest="stage_dir")
    p_select.add_argument("--canaries-dir", default=str(DEFAULT_CANARIES_DIR), dest="canaries_dir")
    p_select.set_defaults(func=cmd_select)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
