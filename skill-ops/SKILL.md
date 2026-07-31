---
name: skill-ops
user_invocable: true
description: "Skill ops hub: snapshot/rollback + usage health + invocations."
not_for:
  - "Creating/editing skills — this only manages existing skills, it doesn't author new ones"
  - "Deep quality scoring/audit of a skill's content — this tracks usage, not quality"
see_also:
  []
depends_on:
  skills: []
  agents: []
  files:
    - "scripts/skill_health_bucket.py"
concurrency_profile:
  read_only: false
  concurrency_safe: false
---

# /skill-ops v1.2

> Skill/agent ops hub — 3 modes: snapshot, usage, frequency. Merges skill-versioning + skill-health-report.

## Dominant Variable
**Snapshot integrity + invocation log completeness** — if a snapshot doesn't match the original, rollback is meaningless. Without logs, usage analysis is impossible.

## Key Assumptions

1. **Permission to create `~/.claude/.harness/snapshots/`** — if broken: report permission issue + provide manual mkdir command.
2. **Target file is `~/.claude/skills/*/SKILL.md` or `~/.claude/agents/*.md`** — if broken: ask for the skill name directly.
3. **Retention policy: keep last 5** — 6th and older are deleted oldest-first. Ignore if deletion fails.
4. **Invocation logs: session-checkpoint Phase 3.7 appends to `invocations/YYYY-MM.jsonl`** — if broken: state "no logs".
5. **SKILLS/AGENTS_INVENTORY.md is the source of truth** — if broken: analyze from log-derived names only (mark incomplete).

## Trigger
- `/skill-ops` (snapshot default)
- `/skill-ops health`
- `/skill-ops invocations`
- "skill version", "skill usage frequency", "harness score"

## Discard If
- Target file is outside `~/.claude/skills/` or `~/.claude/agents/` (project code → git handles it)
- Target file doesn't exist (nothing to snapshot)
- A same-day snapshot with identical content (line count) already exists (duplicate is pointless)
- Health mode: `invocations/` directory itself doesn't exist → report "no logs"
- Health mode: 0 JSONL files within scan range → report "no logs in range"

## Mode
| Mode | Role | Trigger |
|------|------|--------|
| **snapshot** | Pre-change snapshot + regression-detection restore command | `/skill-ops` (default) |
| **health** | Usage/Dead/Unused/Discard report | `/skill-ops health` |
| **invocations** | Per-skill frequency rollup from session JSONL | `/skill-ops invocations` |

---

## Snapshot Mode

### Phase 0: Parse Input
1. Extract target file path from user input (absolute path > skill name > user question)
2. Extract skill name: `~/.claude/skills/<name>/SKILL.md` or `~/.claude/agents/<name>.md`

### Phase 1: Read Original
- `[READ] {TARGET_FILE}` → record line count (ORIGINAL_LINES)
- Failure (file missing) → "target file not found" + end with BROKEN status

### Phase 2: Prepare Directory + Same-Day Duplicate Check
```bash
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
SKILL_SNAP_DIR=~/.claude/.harness/snapshots/{skill-name}
mkdir -p ${SKILL_SNAP_DIR}/${TIMESTAMP}
```
- Same-day snapshot exists + identical line count → "identical-content snapshot already exists" → go to Phase 6

### Phase 3: Save + Verify (Invariant #2)
- `[WRITE]` snapshot → `[READ]` re-verify → compare line count
- Mismatch → `⚠️ Snapshot verification failed` + end with PARTIAL

### Phase 4: Clean Up Old Snapshots (delete beyond 5)
```bash
ls -d ~/.claude/.harness/snapshots/{skill-name}/*/ | sort | head -$((COUNT-5)) | xargs rm -rf
```

### Phase 5: Show Prior Score Store Score
- Extract `harness_score` + `date` from the latest `~/.claude/.harness/scores/*.json` file
- If none: "No Score Store — run a quality audit first to have something to compare against"

### Phase 6: Output Rollback Command
```
Rollback: cp ~/.claude/.harness/snapshots/{skill-name}/{TIMESTAMP}/SKILL.md {TARGET_FILE}
List: ls ~/.claude/.harness/snapshots/{skill-name}/
```

---

## Health Mode

### Phase 0: Verify
- Confirm `invocations/` directory exists
- Load SKILLS_INVENTORY.md / AGENTS_INVENTORY.md

### Phase 1: Parse Invocation Logs + Correction History
Per-skill rollup from JSONL over the last 30 days (default):
- `skills[]` → invocation count
- `discarded[]` → Discard If trigger count
- `last_seen` → last invocation date
- **Correction count**: number of snapshots under `~/.claude/.harness/snapshots/{skill}/` = cumulative edit count for that skill. High edit frequency is a stability-watch signal

### Phase 2: Classify Status (deterministic)

Don't eyeball this against the criteria table — call the bucket classifier per skill instead:
```bash
python scripts/skill_health_bucket.py bucket --count {invocation_count_30d} --last-seen {last_seen_date} --discard-rate {discard_rate}
```
`--last-seen` and `--discard-rate` come from the Phase 1 rollup. The script is the source of truth for the label; the table below is reference only, for reading the output — not for manually re-deriving it.

| Status | Criterion | Label |
|------|------|------|
| Active | ≥ threshold (2x/30d) within range | 🟢 |
| Low | ≥1x, below threshold | 🟡 |
| Unused | 0x, under 90 days | 🔴 |
| Dead | 0x, 90+ days | 💀 |
| Discarded | Discard If triggered only | ⚪ |
| Unknown | No logs | ❓ |

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
Aggregate `Skill` tool calls from session JSONL to measure per-skill monthly invocation frequency.
- **tool_use metadata only** — never read prompt text
- **Windows**: prefer `D:/Python313/python.exe`, fallback to `python`/`python3`
- Save: `~/.claude/.harness/invocations/YYYY-MM.json`

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
Calculate a per-skill quality score (S_Q) and identify the bottom quartile as optimization targets.

> ⚠️ Boundary: S_Q is an **operational signal** for "keep vs. retire this skill" — not a quality oracle. It measures usage plus a handful of structural checklist items, not whether the skill's content is actually good. Don't read a low S_Q as "this skill is badly written" — it may simply be under-used. Deep content-quality review of a skill's actual reasoning/instructions is a separate activity outside this skill's scope (see `not_for` above).

### Phase 8: Quality Score Scan (deterministic)

Structure score, usage score, and their sum are computed by the script — never re-derive them by reading the checklist and eyeballing points. The bullets below are what each score *means*, not steps to apply by hand.

1. **Load skill list**: `~/.claude/skills/*/SKILL.md` + `SKILLS_INVENTORY.md`
2. **Structure score (0-5)**:
   ```bash
   python scripts/skill_health_bucket.py structural --file <path to SKILL.md>
   ```
   Checks, +1 each: Dominant Variable present · Discard If present · Invariants has a violation-consequence clause · Scope Boundary has 2+ rows on each side · Rationalization Table has 3+ rows.
3. **Usage score (0-5)**:
   ```bash
   python scripts/skill_health_bucket.py usage --invocation-count-30d {N} --discard-rate {F} \
       --days-since-modified {N} [--has-related-lesson]
   ```
   Weights: 5+ invocations in 30 days (+2) / 1-4 (+1) / 0 (0) · Discard If trigger rate < 30% (+1) · last modified within 30 days (+1) or within 90 days (+0.5) · related lesson exists (correction history = usage evidence) (+0.5).
4. **S_Q = structure + usage (0-10)**:
   ```bash
   python scripts/skill_health_bucket.py sq --structural {F} --usage {F}
   ```
5. **Bottom 25%** = optimization targets. Top 75% = keep as-is.

### Output
```
📊 Skill Quality Report (YYYY-MM-DD)
S_Q ≥ 7: {N} (STRONG)
S_Q 4-6: {N} (ADEQUATE)
S_Q < 4: {N} (OPTIMIZE) ← bottom quartile

[OPTIMIZE target table: skill name | structure | usage | S_Q | 1-line improvement direction]
```
Save: `~/.claude/.harness/reports/skill-quality-{date}.md`

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Read the original snapshot target file | Directly modify skill/agent files |
| [WRITE] Save timestamped snapshot file | Execute automatic restoration (proposal only) |
| [BASH] Delete old snapshots (beyond 5) | Upload to external storage/cloud |
| [READ] Check prior Score Store score | Run a quality audit itself |
| [READ] Parse invocations JSONL (tool_use only) | Read session prompt text |
| [WRITE] health report / invocations JSON | Judge skill quality or decide deletion |
| [BASH] Scan session JSONL for frequency rollup | Access project code or databases |
| [BASH] Call `scripts/skill_health_bucket.py` for bucket/structural/usage/S_Q scoring | Manually re-derive those scores by eye |

> Targets only `~/.claude/` global skills/agents. Project code version control is git's job.

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Delete old snapshots (`rm -rf`) | medium | L1+L3 |
| Roll back a skill file (Write overwrite) | medium | L1+L3 |

- **L1 (Invariants)**: mandatory line-count re-verification after save. No automatic restoration.
- **L3 (User Approval)**: deletion only after explicit user request. Rollback only after stating "current→rollback" and getting user confirmation.

## Error Recovery

| Failure Type | Detection | Recovery |
|---------|---------|--------|
| `tool_failure` | Write/Read failure | State "snapshot save failed". Never proceed with comparison without a snapshot |
| `logic_inconsistency` | Score DELTA ≤ -5 but content actually improved | State "possible false positive" + ask user to re-review |
| `missing_data` | Target file missing / invocations log missing | Discard that mode + state the reason |
| `input_error` | Target skill unclear | Default to full-list scan. If specific target intended, ask 1 clarifying question |

## Invariants (never violate)

1. **Confirm original exists before snapshotting**: Write only after successful Read. Abort if original is missing. Violation → empty snapshot.
2. **Re-verify Read after Write**: line-count mismatch → PARTIAL. Violation → reporting a corrupted snapshot as "done".
3. **No automatic restoration**: only output the restore `cp` command. Execution is the user's job. Violation → unintended file overwrite.
4. **Keep last 5**: delete 6th and beyond. Violation → unbounded directory growth.
5. **No automatic deletion (Health)**: never delete/move files even at 0 usage. Report only. Violation → No Action default violation.
6. **No logs ≠ unused (Health)**: sessions that skipped session-checkpoint may still have been used despite missing logs. Treat as Unknown. Violation → truthful-reporting violation.
7. **Below threshold ≠ Dead (Health)**: Low (below threshold) and Dead (0x for 90+ days) are distinct. Violation → misclassifying an in-use skill.
8. **Bucket/structure/usage/S_Q scores are computed via `scripts/skill_health_bucket.py`, never eyeballed**: counting is a job for the script, judgment (retire or not) stays with the user/LLM. Violation → scores drift silently between runs and stop being comparable.

## Truthful Reporting

1. **no mock deception**: never say "save complete" without a post-Write Read re-verification. Never assume "used" from absent logs.
2. **no test façade**: line-count mismatch = PARTIAL. Never assume "it probably worked".
3. **no silent brokenness**: final status must be labeled `WORKING` / `PARTIAL` / `BROKEN`.

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "Skipping the re-verify after Write is fine if it succeeded" | Violates Invariant 2. A silent Write failure means rollback is attempted without a real snapshot |
| "Auto-restore would be more convenient" | Violates Invariant 3. If the user restores without understanding the regression cause, the root cause remains |
| "Snapshots older than 90 days can just stay" | Slows Glob traversal + wastes space. 90-day cleanup happens via session-checkpoint guidance, after user approval |
| "Skills at 0 usage can be auto-deleted" | Violates Invariant 5. Could be emergency-only, seasonal, or recently added. User decides |
| "Months with no logs can just be treated as 0 invocations" | Violates Invariant 6. Must be treated as Unknown |
| "High Discard If ratio → recommend immediate retirement" | Related to Invariant 7. The safeguard may simply be working correctly. Propose re-review only |
| "The criteria table is simple enough to just eyeball" | Violates Invariant 8. Manual application drifts from the script's exact thresholds and regex logic — the same skill can score differently run to run |
