# Canary pool

Example control pool for `canary_mix.py` / `canary_score.py` (see the "Canary
mixing" step in `SKILL.md`). Ships with 2 clean files and 2 files with a
planted defect — enough to smoke-test the mechanism, not enough for a
meaningful recall number. Extend it with pairs representative of your own
codebase before treating `canary_score.py --summary`'s recall line as
signal.

## Layout

```
canaries/
  clean/<name>.py            # a real, unremarkable file — nothing wrong with it
  seeded/<name>.py            # a file with exactly one planted defect
  seeded/<name>.json          # sidecar: {"defect_id", "expected_finding_keywords", "category", "note"}
  recall_ledger.jsonl          # written by canary_score.py — append-only, safe to delete to reset history
```

Rules for adding a pair:
- The clean file must be something a reviewer could plausibly flag by mistake (real logic, not a stub) — otherwise it's too easy to pass and the false-positive rate it measures is meaningless.
- The seeded file's name and body must give no hint that it's a planted defect (no `_bad`, `_vuln`, comments admitting the bug, etc.) — a reviewer who can tell which files are canaries isn't being measured under normal conditions.
- `expected_finding_keywords` should describe the defect's *nature* (e.g. `"hardcoded"`, `"injection"`), never a variable/function name from the source — a keyword copied from the code lets any finding that merely quotes that name count as a "hit" for the wrong reason (see the note in `canary_score.py`).
- Keep file names unique across the whole pool, not just within `clean/`/`seeded/` — `canary_mix.py --stage-dir` copies by file name and refuses to silently overwrite a collision.
