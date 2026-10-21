#!/usr/bin/env python3
"""skill_snapshot.py - deterministic implementation of skill-ops Snapshot mode (Phases 0-4 and 6).

Usage:
  python skill_snapshot.py snapshot <skill-or-agent-name|absolute-path> [--label L] [--root ~/.claude] [--snap-root DIR]
  python skill_snapshot.py audit [--snap-root DIR]     # list entries outside the layout (read-only)

Layout: <snap-root>/<name>/<YYYY-MM-DD-HHMMSS>[-label]/<original file name>. The original and the
snapshot are compared byte for byte (filecmp).
It never deletes anything - snapshots beyond the newest 5 are only printed as delete commands for you to run.
The last output line is STATUS: WORKING | PARTIAL | BROKEN | DUPLICATE.
Known limit: the same-day identical-content check only looks inside the same name directory.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import filecmp
import os
import re
import shlex
import shutil
import sys

KEEP = 5
STD = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}(-[A-Za-z0-9_-]+)?$")


def resolve_target(arg: str, root: str):
    """(name, absolute path) - skill name -> skills/<n>/SKILL.md, agent name -> agents/<n>.md, or an absolute path."""
    if os.path.isabs(arg):
        p = os.path.abspath(arg)
        parent = os.path.basename(os.path.dirname(p))
        name = parent if os.path.basename(p) == "SKILL.md" else os.path.splitext(os.path.basename(p))[0]
        return name, p
    sk = os.path.join(root, "skills", arg, "SKILL.md")
    ag = os.path.join(root, "agents", arg + ".md")
    if os.path.isfile(sk):
        return arg, sk
    if os.path.isfile(ag):
        return arg, ag
    return arg, sk


def _in_scope(path: str, root: str) -> bool:
    p = os.path.normcase(os.path.abspath(path))
    return any(p.startswith(os.path.normcase(os.path.join(root, d)) + os.sep) for d in ("skills", "agents"))


def prune_command(target: str) -> str:
    """Delete command to print for one snapshot directory; the path is quoted for the target shell."""
    if os.name == "nt":
        return "Remove-Item -Recurse -Force -LiteralPath '%s'" % target.replace("'", "''")
    return "rm -rf -- " + shlex.quote(target)


def prune_candidates(name_dir: str, keep: int = KEEP):
    subs = sorted(d for d in os.listdir(name_dir) if os.path.isdir(os.path.join(name_dir, d)))
    return subs[: max(0, len(subs) - keep)]


def snapshot(arg: str, root: str, snap_root: str, label: str | None = None, now=None) -> dict:
    now = now or _dt.datetime.now()
    name, src = resolve_target(arg, root)
    res = {"name": name, "source": src, "status": "BROKEN", "snapshot": None, "msgs": []}
    if not os.path.isfile(src):
        res["msgs"].append(f"Source not found: {src}")
        return res
    if not _in_scope(src, root):
        res["msgs"].append(f"Outside skills/ and agents/ (use git for this file): {src}")
        return res
    if label and not re.fullmatch(r"[A-Za-z0-9_-]+", label):
        res["msgs"].append(f"label may contain only letters, digits, _ and -: {label}")
        return res
    name_dir = os.path.join(snap_root, name)
    base = os.path.basename(src)
    today = now.strftime("%Y-%m-%d")
    if os.path.isdir(name_dir):
        for d in sorted(os.listdir(name_dir)):
            cand = os.path.join(name_dir, d, base)
            if d.startswith(today) and os.path.isfile(cand) and filecmp.cmp(src, cand, shallow=False):
                res.update(status="DUPLICATE", snapshot=os.path.join(name_dir, d))
                res["msgs"].append("Identical snapshot from today already exists (byte match) - not creating a new one")
                res["rollback"] = f"cp {shlex.quote(cand)} {shlex.quote(src)}"
                return res
    stamp = now.strftime("%Y-%m-%d-%H%M%S") + (f"-{label}" if label else "")
    dest_dir = os.path.join(name_dir, stamp)
    os.makedirs(dest_dir, exist_ok=False)
    dest = os.path.join(dest_dir, base)
    shutil.copyfile(src, dest)
    res["snapshot"] = dest_dir
    if not filecmp.cmp(src, dest, shallow=False):
        res["status"] = "PARTIAL"
        res["msgs"].append("Snapshot verification failed (byte mismatch)")
        return res
    res["status"] = "WORKING"
    res["verified"] = "MATCH"
    res["prune"] = prune_candidates(name_dir)
    res["rollback"] = f"cp {shlex.quote(dest)} {shlex.quote(src)}"
    return res


def audit(snap_root: str) -> dict:
    """Entries outside the layout: a subdirectory that does not match STD, or a name directory with no timestamp subdirectory."""
    bad, total = [], 0
    if not os.path.isdir(snap_root):
        return {"total_dirs": 0, "nonstandard_count": 0, "nonstandard": [], "no_snapshots": True}
    for name in sorted(os.listdir(snap_root)):
        nd = os.path.join(snap_root, name)
        if not os.path.isdir(nd):
            continue
        total += 1
        kids = os.listdir(nd)
        subdirs = [k for k in kids if os.path.isdir(os.path.join(nd, k))]
        if not subdirs or any(not STD.match(k) for k in subdirs):
            bad.append({"name": name, "children": sorted(kids)[:6],
                        "nonstandard": [k for k in subdirs if not STD.match(k)] or ["(no timestamp subdirectory)"]})
    return {"total_dirs": total, "nonstandard_count": len(bad), "nonstandard": bad}


def main(argv=None) -> int:
    home = os.path.join(os.path.expanduser("~"), ".claude")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("snapshot")
    a.add_argument("target")
    a.add_argument("--label", default=None)
    a.add_argument("--root", default=home)
    a.add_argument("--snap-root", default=None)
    b = sub.add_parser("audit")
    b.add_argument("--snap-root", default=os.path.join(home, ".harness", "snapshots"))
    args = ap.parse_args(argv)
    if args.cmd == "audit":
        r = audit(args.snap_root)
        if r.get("no_snapshots") or r["total_dirs"] == 0:
            print(f"no snapshots: nothing found under {args.snap_root}")
            return 0
        print(f"Denominator: {r['nonstandard_count']} of {r['total_dirs']} snapshot name directories are outside the layout")
        for x in r["nonstandard"]:
            print(f"  {x['name']}: {x['nonstandard']}")
        return 0
    snap_root = args.snap_root or os.path.join(args.root, ".harness", "snapshots")
    r = snapshot(args.target, args.root, snap_root, args.label)
    for m in r["msgs"]:
        print(m)
    if r.get("snapshot"):
        print(f"Snapshot: {r['snapshot']}")
    if r.get("verified"):
        print(f"cmp: {r['verified']}")
    for p in r.get("prune", []):
        target = os.path.join(snap_root, r["name"], p)
        cmd = prune_command(target)
        print(f"Cleanup candidate (run it yourself): {cmd}")
    if r.get("rollback"):
        print(f"Rollback: {r['rollback']}")
    print(f"STATUS: {r['status']}")
    return 0 if r["status"] in ("WORKING", "DUPLICATE") else 1


if __name__ == "__main__":
    sys.exit(main())
