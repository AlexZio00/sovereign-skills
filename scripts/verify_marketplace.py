#!/usr/bin/env python3
"""Structural integrity check for the sovereign-skills marketplace.

Verifies that marketplace.json, each skill's plugin.json, and each skill's
directory/SKILL.md agree on the same set of skills. This is the check that
would have caught the 2026-07 project-init misclassification incident
(marketplace.json claimed 14 skills while 15 directories existed).

Exit code 0 = all checks pass. Exit code 1 = at least one check failed
(prints every failure, not just the first).
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# Directories that are not skills even though they live at repo root.
NON_SKILL_DIRS = {"docs", ".claude-plugin", ".git", ".github", "scripts", "node_modules"}


def find_skill_dirs():
    return sorted(
        p.name
        for p in REPO_ROOT.iterdir()
        if p.is_dir() and p.name not in NON_SKILL_DIRS and not p.name.startswith(".")
    )


def load_marketplace():
    with open(MARKETPLACE_JSON, encoding="utf-8") as f:
        return json.load(f)


def main():
    errors = []

    if not MARKETPLACE_JSON.exists():
        print(f"FAIL: marketplace.json not found at {MARKETPLACE_JSON}")
        return 1

    marketplace = load_marketplace()
    plugins = marketplace.get("plugins", [])
    skill_dirs = find_skill_dirs()

    # Check 1: count match (marketplace entries vs actual directories)
    plugin_names = sorted(p["name"] for p in plugins)
    if plugin_names != skill_dirs:
        errors.append(
            f"COUNT/SET MISMATCH: marketplace.json lists {len(plugin_names)} plugins "
            f"{plugin_names}, but {len(skill_dirs)} skill directories exist {skill_dirs}. "
            f"Only in marketplace: {sorted(set(plugin_names) - set(skill_dirs))}. "
            f"Only on disk: {sorted(set(skill_dirs) - set(plugin_names))}."
        )

    # Check 2 + 3: per-plugin pair existence + 3-way name match
    for plugin in plugins:
        name = plugin.get("name", "<missing name>")
        source = plugin.get("source", "")
        dirname = source.lstrip("./").rstrip("/")

        if not dirname:
            errors.append(f"{name}: marketplace.json entry has no/invalid 'source' field")
            continue

        skill_dir = REPO_ROOT / dirname
        skill_md = skill_dir / "SKILL.md"
        plugin_json_path = skill_dir / ".claude-plugin" / "plugin.json"

        if not skill_dir.is_dir():
            errors.append(f"{name}: source directory '{dirname}' does not exist")
            continue

        if not skill_md.exists():
            errors.append(f"{name}: missing {dirname}/SKILL.md")

        if not plugin_json_path.exists():
            errors.append(f"{name}: missing {dirname}/.claude-plugin/plugin.json")
            continue

        with open(plugin_json_path, encoding="utf-8") as f:
            plugin_json = json.load(f)

        plugin_json_name = plugin_json.get("name", "<missing name>")
        if not (name == plugin_json_name == dirname):
            errors.append(
                f"3-WAY NAME MISMATCH: marketplace.json name='{name}', "
                f"plugin.json name='{plugin_json_name}', directory='{dirname}' -- must all match"
            )

    if errors:
        print(f"FAIL: {len(errors)} issue(s) found\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS: {len(plugins)} skills verified (marketplace.json <-> plugin.json <-> directory <-> SKILL.md all consistent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
