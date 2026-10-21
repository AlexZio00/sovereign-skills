---
name: skill-ops
user-invocable: true
description: "Skill ops hub with 4 modes: snapshot/rollback, usage health, invocation frequency, and an operational quality score."
not_for:
  - "Creating/editing skills — this only manages existing skills, it doesn't author new ones"
  - "Deep review of whether a skill's content is good — Quality mode is only a usage-plus-structure signal"
see_also:
  []
depends_on:
  skills: []
  agents: []
  files:
    - "scripts/skill_health_bucket.py"
    - "scripts/skill_snapshot.py"
concurrency_profile:
  read_only: false
  concurrency_safe: false
---

# /skill-ops

> Skill/agent ops hub — 4 modes: snapshot, health (usage), invocations (frequency), quality (operational score).

`${CLAUDE_SKILL_DIR}` is this skill's folder; Claude Code fills it in. In other agents, replace it with the path where you installed the skill. Use `python` instead of `python3` where only that exists (common on Windows). If a script is missing or fails to start, say so: Snapshot mode falls back to the manual phases below; Health, Invocations and Quality modes stop with "scoring script unavailable" (Invariant 8: no scores by eye).

File formats (invocation log, lessons.md): https://github.com/AlexZio00/sovereign-skills/blob/master/docs/FILE-CONVENTIONS.md

## Dominant Variable
**Snapshot integrity + invocation log completeness** — if a snapshot doesn't match the original, rollback is meaningless. Without logs, usage analysis is impossible.

## Key Assumptions

1. **Permission to create `~/.claude/.harness/snapshots/`** — if broken: report permission issue + provide manual mkdir command.
2. **Target file is `~/.claude/skills/*/SKILL.md` or `~/.claude/agents/*.md`** — if broken: ask for the skill name directly.
3. **Retention policy: keep last 5** — 6th and older are flagged for deletion oldest-first (command printed, not auto-run — see Phase 4). If listing fails, skip cleanup reporting for that skill.
4. **Invocation logs: the session-checkpoint skill appends to `~/.claude/.harness/invocations/YYYY-MM.jsonl`** (Phase 1.6.5 is the primary writer, Phase 3.7 the fallback). Without that skill there is no writer, so there are no logs — if so, state "no logs".
5. **Skill list = the folders in `~/.claude/skills/*/SKILL.md`.** An inventory file (for example `SKILLS_INVENTORY.md`) is optional: use one if you keep it, otherwise scan the folders.

## Trigger
- `/skill-ops` (snapshot default)
- `/skill-ops health`
- `/skill-ops invocations`
- `/skill-ops quality` (or `--quality`)
- "skill version", "skill usage frequency"

## Discard If
- Target file is outside `~/.claude/skills/` or `~/.claude/agents/` (project code → git handles it)
- Target file doesn't exist (nothing to snapshot)
- A same-day snapshot with identical content already exists (duplicate is pointless; the script compares bytes, the manual path compares SHA-256 hashes)
- Health mode: `invocations/` directory itself doesn't exist → report "no logs"
- Health mode: 0 JSONL files within scan range → report "no logs in range"

## Mode
| Mode | Role | Trigger |
|------|------|--------|
| **snapshot** | Pre-change snapshot + regression-detection restore command | `/skill-ops` (default) |
| **health** | Usage/Dead/Unused/Discard report | `/skill-ops health` |
| **invocations** | Per-skill frequency rollup from session JSONL | `/skill-ops invocations` |
| **quality** | Per-skill S_Q operational score (structure + usage), bottom quartile flagged | `/skill-ops quality` |

---

## Snapshot Mode

**Script path (preferred)**: `python3 "${CLAUDE_SKILL_DIR}/scripts/skill_snapshot.py" snapshot <name|absolute-path> [--label L]` runs Phases 0-4 and 6 in one call: byte-for-byte comparison (MATCH/MISMATCH), a same-day identical-content check (DUPLICATE), delete commands for snapshots beyond the newest 5 (printed only, never run), the rollback command (printed only, with quoted paths), and a final `STATUS:` line. Layout: `<name>/<YYYY-MM-DD-HHMMSS>[-label]/<original file name>`. `python3 "${CLAUDE_SKILL_DIR}/scripts/skill_snapshot.py" audit` counts directories outside that layout, read-only (for example date-only labels or name directories with no timestamp subdirectory); with no snapshot folder it prints "no snapshots". Existing nonstandard entries are not moved. Follow the manual phases below only when the script cannot run.

### Phase 0: Parse Input
1. Extract target file path from user input (absolute path > skill name > user question)
2. Extract skill name: `~/.claude/skills/<name>/SKILL.md` or `~/.claude/agents/<name>.md`

### Phase 1: Read Original
- `[READ] {TARGET_FILE}` → compute its SHA-256 content hash (ORIGINAL_HASH; `shasum -a 256` on macOS, `sha256sum` on Linux/Git Bash)
- Failure (file missing) → "target file not found" + end with BROKEN status

### Phase 2: Prepare Directory + Same-Day Duplicate Check
```bash
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
SKILL_SNAP_DIR=~/.claude/.harness/snapshots/{skill-name}
ORIGINAL_HASH=$( (shasum -a 256 "${TARGET_FILE}" 2>/dev/null || sha256sum "${TARGET_FILE}") | cut -d' ' -f1)
mkdir -p "${SKILL_SNAP_DIR}/${TIMESTAMP}"
```
- Same-day snapshot exists + its SHA-256 hash equals `ORIGINAL_HASH` → "identical-content snapshot already exists" → go to Phase 6 (equal line counts alone do NOT count as identical — always compare hashes)

### Phase 3: Save + Verify (Invariant #2)
- `[WRITE]` snapshot → `[READ]` re-verify → compare its SHA-256 hash against `ORIGINAL_HASH`
- Mismatch → `⚠️ Snapshot verification failed` + end with PARTIAL

### Phase 4: Clean Up Old Snapshots (list + print delete commands beyond 5 — never deletes automatically)
```bash
SNAP_DIR=~/.claude/.harness/snapshots/{skill-name}
COUNT=$(find "${SNAP_DIR}" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
if [ "${COUNT}" -gt 5 ]; then
  echo "Cleanup candidates (oldest first, beyond the 5 kept) — run these yourself:"
  find "${SNAP_DIR}" -mindepth 1 -maxdepth 1 -type d | sort | head -n "$((COUNT-5))" | while IFS= read -r path; do
    [ -n "${path}" ] && echo "rm -rf -- \"${path}\""
  done
fi
```
- Cleanup is skipped entirely when `COUNT` ≤ 5, so `head -n` never receives a zero or negative argument.
- The `while IFS= read -r path` loop handles snapshot paths that contain spaces.
- **This phase never runs `rm -rf` itself** — it only lists candidates and prints the exact command; running it is the user's call (same propose-then-user-executes pattern as Phase 6's rollback command). A skill silently deleting a user's files in bulk is a worse failure mode than asking them to paste one line.

### Phase 5 (optional): Show Prior Score Store Score
- Only applies if a separate tool writes `~/.claude/.harness/scores/*.json` (for example a check-harness skill, optional, not included in this repo). This skill never writes those files.
- If the folder has files: extract `harness_score` (0-100 scale, written by that tool; a different scale from this skill's own 0-10 `S_Q` metric in Quality Mode below) + `date` from the latest file.
- If there are none: skip this phase and say "no score store".

### Phase 6: Output Rollback Command
Print the command only; never run it. `{ORIGINAL_FILE_NAME}` is `SKILL.md` for a skill and `<name>.md` for an agent; quote the paths.
```
Rollback: cp "~/.claude/.harness/snapshots/{skill-name}/{TIMESTAMP}/{ORIGINAL_FILE_NAME}" "{TARGET_FILE}"
List: ls ~/.claude/.harness/snapshots/{skill-name}/
```

---

## Health Mode

### Phase 0: Verify
- Confirm `invocations/` directory exists
- Load the skill list (see Key Assumption 5); an inventory file is optional

### Phase 1: Parse Invocation Logs + Correction History
**The script does the rollup**: `python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" report [--days 30] [--out ~/.claude/.harness/reports/skill-health-{date}.md]` produces the Phase 1-3 per-skill count, last_seen, discard_rate, and status label in one pass. It counts records from every `source` in the log, accepts `discarded` entries as plain strings or `{"skill": ..., "reason": ...}` objects, and prints a denominator line. Without `--out` it creates no file; with `--out` it creates missing parent folders. If the skills folder is missing it prints an error naming it and exits 2 (pass `--skills-dir`). Keep this as the single rollup implementation: if the log rules change, change this script first. The manual description below explains how to read its output.
Per-skill rollup from JSONL over the last 30 days (default):
- `skills[]` → invocation count
- `discarded[]` → Discard If trigger count
- `last_seen` → last invocation date
- **Retained snapshot count**: number of snapshot directories currently under `~/.claude/.harness/snapshots/{skill}/` — NOT the skill's true cumulative edit count, since Invariant 4 caps retention at 5 (a skill edited more than 5 times still shows at most 5 here). A count at or near the 5-snapshot cap is a stability-watch signal (frequent recent edits)

### Phase 2: Classify Status (deterministic)

Don't eyeball this against the criteria table — call the bucket classifier per skill instead:
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" bucket --count {invocation_count_30d} --last-seen {last_seen_date} --discard-rate {discard_rate}
```
`--last-seen` and `--discard-rate` come from the Phase 1 rollup. The script is the source of truth for the label; the table below is reference only, for reading the output — not for manually re-deriving it.

| Status | Criterion | Label |
|------|------|------|
| Active | ≥ threshold (2x/30d) within range | 🟢 |
| Low | ≥1x, below threshold | 🟡 |
| Unused | 0x in range (logs exist, skill never invoked), under 90 days since last use | 🔴 |
| Dead | 0x, 90+ days | 💀 |
| Discarded | Discard If triggered only | ⚪ |
| Unknown | No logs (or no records in range) | ❓ |

Unused + no recent edits is a retire-candidate signal.

**Skill-bank alignment signal**: a skill bank that has drifted out of alignment with your current goals or workflow can underperform having no skill bank at all. Treat Unused *and* clearly-misaligned skills as a stronger retire-candidate signal than either alone.

**Retirement-judge audit gate**: before wiring Health mode's Dead/Unused/Discard classifications into any automated delete/archive pipeline, validate the classifier itself — deliberately include a few known-good (still-needed) skills in the candidate pool and check whether the classifier still flags them (false positives). A high false-positive rate means the retirement mechanism looks like it's working but silently isn't. Until that validation exists, this mode stays report-only — deletion is always the user's call (Invariant 5).

### Phase 3: Generate + Save Report
```
📊 Skill Health — {YYYY-MM-DD}
🟢 Active {N} | 🟡 Low {N} | 🔴 Unused {N} | 💀 Dead {N}

[Full status table]
[💀 Dead — recommend immediate review]
[⚪ Discard ratio >30% warning]
```
Save: `~/.claude/.harness/reports/skill-health-{date}.md`

---

## Invocations Mode

### Phase 7: Invocation Frequency Scan
Measure per-skill monthly invocation frequency from the invocation log.
- **Single source**: run `python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" report --days 30` (the same rollup as Health mode) and take Top 5 and zero-invocation from its table. Use `--days 90` or `365` for longer windows. No log folder: state "no logs".
- **Names only**: the log holds skill names and dates, never prompt text.
- **Windows**: use `python`/`python3` on PATH; if neither resolves, check common install locations before failing.
- **Read-only**: this mode creates no new file.

Output:
```
📊 Skill Invocation Report (YYYY-MM)
Top 5: [most invoked]
Zero-invocation: [never-invoked list — SHARPEN candidates]
```

---

## Quality Mode

> Trigger: `/skill-ops quality` or `/skill-ops --quality`

### Purpose
Calculate a per-skill quality score (S_Q, 0-10 scale — distinct from the 0-100 `harness_score` in Snapshot Mode's Score Store) and identify the bottom quartile as optimization targets.

> ⚠️ Boundary: S_Q is an **operational signal** for "keep vs. retire this skill" — not a quality oracle. It measures usage plus a handful of structural checklist items, not whether the skill's content is actually good. Don't read a low S_Q as "this skill is badly written" — it may simply be under-used. Deep content-quality review of a skill's actual reasoning/instructions is a separate activity outside this skill's scope (see `not_for` above).

### Phase 8: Quality Score Scan (deterministic)

Structure score, usage score, and their sum are computed by the script — never re-derive them by reading the checklist and eyeballing points. The bullets below are what each score *means*, not steps to apply by hand.

1. **Load skill list**: `~/.claude/skills/*/SKILL.md` (an inventory file is optional)
2. **Structure score (0-5)**:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" structural --file <path to SKILL.md>
   ```
   Output is JSON: `{"structural_score": N.N}`. Checks, +1 each: Dominant Variable present · Discard If present · Invariants has a violation-consequence clause · Scope Boundary has 2+ rows on each side · Rationalization Table has 3+ rows.
3. **Usage score (0-5)**:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" usage --invocation-count-30d {N} --discard-rate {F} \
       --days-since-modified {N} [--has-related-lesson]
   ```
   `{N}` for invocations and `{F}` come from the Health rollup; `--days-since-modified` is the days since the SKILL.md file's modification time; pass `--has-related-lesson` only if a lessons file (`tasks/lessons.md`, if you keep one) has an entry that names this skill, otherwise omit it.
   Output is JSON: `{"usage_score": N.N}`. Weights: 5+ invocations in 30 days (+2) / 1-4 (+1) / 0 (0) · Discard If trigger rate < 30% (+1, only when invocations ≥ 1 — with 0 calls the rate has no denominator) · last modified within 30 days (+1) or within 90 days (+0.5) · related lesson exists (correction history = usage evidence) (+0.5).
4. **S_Q = structure + usage (0-10)** — the `sq` subcommand takes `--structural`/`--usage` as plain floats, so piping step 2/3's JSON straight in fails argparse. Extract the numeric field first:
   ```bash
   S=$(python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" structural --file <path to SKILL.md> | python3 -c "import json,sys; print(json.load(sys.stdin)['structural_score'])")
   U=$(python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" usage --invocation-count-30d {N} --discard-rate {F} --days-since-modified {N} | python3 -c "import json,sys; print(json.load(sys.stdin)['usage_score'])")
   python3 "${CLAUDE_SKILL_DIR}/scripts/skill_health_bucket.py" sq --structural "$S" --usage "$U"
   ```
5. **OPTIMIZE = the bottom 25% by S_Q** (ties at the cut-off are included). Everything above it = keep as-is. The score bands below are for reading the table only; they do not define OPTIMIZE.

### Output
```
📊 Skill Quality Report (YYYY-MM-DD)
Bands (half-open): STRONG 7 <= S_Q <= 10: {N} | ADEQUATE 4 <= S_Q < 7: {N} | WEAK 0 <= S_Q < 4: {N}
(the highest reachable S_Q is 9.5: structure 5 + usage 4.5)
OPTIMIZE (bottom quartile by S_Q): {N}

[OPTIMIZE target table: skill name | structure | usage | S_Q | 1-line improvement direction]
```
Save: `~/.claude/.harness/reports/skill-quality-{date}.md`

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Read the original snapshot target file | Directly modify skill/agent files |
| [WRITE] Save timestamped snapshot file | Execute automatic restoration (proposal only) |
| [BASH] List old snapshots beyond 5 + print the delete command | Directly delete a snapshot (execution is the user's job) / Upload to external storage/cloud |
| [READ] Check prior Score Store score (optional, only if another tool writes it) | Write the Score Store or run a quality audit itself |
| [READ] Parse invocations JSONL (tool_use only) | Read session prompt text |
| [WRITE] health report (invocations mode writes nothing) | Judge skill quality or decide deletion |
| [BASH] Scan session JSONL for frequency rollup | Access project code or databases |
| [BASH] Call `skill_health_bucket.py` for bucket/structural/usage/S_Q scoring | Manually re-derive those scores by eye |

> Targets only `~/.claude/` global skills/agents. Project code version control is git's job.

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Clean up old snapshots (list + print `rm -rf`, user runs it) | medium | L1+L3 |
| Roll back a skill file (this skill only prints the `cp` command; the user runs it) | medium | L1+L3 |

- **L1 (Invariants)**: mandatory re-verification after save (byte comparison in the script, SHA-256 on the manual path). No automatic restoration.
- **L3 (User Approval)**: deletion only after explicit user request. Before the user runs a rollback, state "current → rollback" and get their confirmation.

## Error Recovery

| Failure Type | Detection | Recovery |
|---------|---------|--------|
| `tool_failure` | Write/Read failure | State "snapshot save failed". Never proceed with comparison without a snapshot |
| `logic_inconsistency` | Only if Phase 5 ran: `harness_score` DELTA (0-100 scale, from the optional Score Store, not the 0-10 `S_Q` scale) ≤ -5 but content actually improved | State "possible false positive" + ask user to re-review |
| `missing_data` | Target file missing / invocations log missing | Discard that mode + state the reason |
| `input_error` | Target skill unclear | Snapshot mode: ask for the skill name (1 question). Health, Invocations and Quality modes: default to the full-list scan |

## Invariants (never violate)

1. **Confirm original exists before snapshotting**: Write only after successful Read. Abort if original is missing. Violation → empty snapshot.
2. **Re-verify Read after Write**: content mismatch (byte comparison, or SHA-256 on the manual path) → PARTIAL. Violation → reporting a corrupted snapshot as "done".
3. **No automatic restoration**: only output the restore `cp` command. Execution is the user's job. Violation → unintended file overwrite.
4. **Keep last 5**: 6th-and-beyond are listed as cleanup candidates with the delete command printed for the user to run — this phase never calls `rm -rf` itself (same propose-then-user-executes pattern as Phase 6's rollback). Violation → unreported cleanup targets let the directory grow unbounded.
5. **No automatic deletion (Health)**: never delete/move files even at 0 usage. Report only. Violation → No Action default violation.
6. **No logs ≠ unused (Health)**: sessions that skipped session-checkpoint may still have been used despite missing logs. Treat as Unknown. Violation → truthful-reporting violation.
7. **Below threshold ≠ Dead (Health)**: Low (below threshold) and Dead (0x for 90+ days) are distinct. Violation → misclassifying an in-use skill.
8. **Bucket/structure/usage/S_Q scores are computed via `skill_health_bucket.py` (in this skill's `scripts/` folder), never eyeballed**: counting is a job for the script, judgment (retire or not) stays with the user/LLM. Violation → scores drift silently between runs and stop being comparable.

## Truthful Reporting

1. **no mock deception**: never say "save complete" without a post-Write Read re-verification. Never assume "used" from absent logs.
2. **no test façade**: content mismatch after saving = PARTIAL. Never assume "it probably worked".
3. **no silent brokenness**: final status must be labeled `WORKING` / `PARTIAL` / `BROKEN`.

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "Skipping the re-verify after Write is fine if it succeeded" | Violates Invariant 2. A silent Write failure means rollback is attempted without a real snapshot |
| "Auto-restore would be more convenient" | Violates Invariant 3. If the user restores without understanding the regression cause, the root cause remains |
| "Old snapshots can just stay" | The folder grows without bound. The keep-5 rule prints delete commands; the user decides when to run them |
| "Skills at 0 usage can be auto-deleted" | Violates Invariant 5. Could be emergency-only, seasonal, or recently added. User decides |
| "Months with no logs can just be treated as 0 invocations" | Violates Invariant 6. Must be treated as Unknown |
| "High Discard If ratio → recommend immediate retirement" | Related to Invariant 7. The safeguard may simply be working correctly. Propose re-review only |
| "The criteria table is simple enough to just eyeball" | Violates Invariant 8. Manual application drifts from the script's exact thresholds and regex logic — the same skill can score differently run to run |
