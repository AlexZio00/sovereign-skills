---
skill_type: analysis
tools: Read, Write, Glob, Grep
triggers:
  - "/doc-drift"
  - "문서 정합성"
  - "docs 체크"
name: doc-drift
context: fork
user_invocable: true
description: |
  Use this skill when the user wants to audit the memory and documents Claude
  Code loads into context — CLAUDE.md (user global + project + nested),
  MEMORY.md, @imports, .claude/skills, .claude/agents, .claude/commands,
  installed plugins — and detect three kinds of issues: outdated claims,
  mutually contradictory statements, and risky-or-ambiguous wording. Produces
  a prioritized improvement list at `.drift-reports/`. Zero config.
  Trigger phrases: "doc drift", "memory drift", "memory audit", "context drift",
  "docs audit", "문서 점검", "문서 감사", "메모리 감사", "메모리 점검",
  "outdated 문서", "문서 충돌".
  NOT for: exhaustive content audit of an entire area (→ full-audit) · harness
  maturity scoring (→ check-harness) · single-file verification (→ verification).
  doc-drift only covers drift (contradiction/staleness/risky wording) in
  already-loaded context.
depends_on:
  skills: []
  agents: []
  files:
    - CLAUDE.md
    - memory/MEMORY.md
concurrency_profile:
  read_only: false
  concurrency_safe: false
  destructive: low
not_for:
  - "Memory reorganization -> memory-dream"
  - "Skill audit -> forge --audit"
see_also:
  - skill: memory-dream
    relation: "doc-drift=document consistency, memory-dream=memory reorganization"
---

# doc-drift — Claude memory audit

## Purpose

Scan the memory and documents Claude loads for this project, and surface what's
stale, what contradicts something else, and what's risky or ambiguous — sorted
by priority.

**Memory verification**: the CLAUDE.md / MEMORY.md / rules files this skill reads
are past-point-in-time snapshots. Verify current state with Glob/Read before
acting — never assume "it's in memory, so it must still be true" (per
memory-discipline principles).

## Dominant Variable

**False-positive rate** — if a finding turns out to be wrong, the person stops
trusting the report and the tool itself gets abandoned. One false positive
outweighs one missed real issue.

## Trigger

- `/doc-drift`
- "문서 정합성"
- "docs 체크"

## Discard If

- The project has neither CLAUDE.md nor MEMORY.md (nothing to audit)
- The user just finished manual cleanup and wants an immediate re-audit (drift
  needs time to accumulate — recommend at least a 24h gap)
- The project has fewer than 10 files (audit cost exceeds the benefit)

---

## Key Assumptions

This skill runs on the following assumptions (per reasoning-standard principles):

1. **Filesystem access is available** — Read/Glob/Grep must work. If broken:
   fail-fast (report the missing tool).
2. **The CLAUDE.md `@import` token convention is honored** — `@path` syntax
   resolves per the standard spec. If broken: graceful degrade (warn + flag
   any import it couldn't resolve).
3. **`.drift-reports/` is writable** — create it if missing. If broken:
   fall back to `/tmp` or stdout.

---

## Workflow

### Step 1 — Gather what gets loaded

Collect every file Claude Code actually loads or can reference in this
project's context. No scripts — use Read/Glob/Grep directly.

**Starting points**
- `~/.claude/CLAUDE.md` (if present)
- `<cwd>/CLAUDE.md` + nested `**/CLAUDE.md`
- `~/.claude/projects/<encoded-cwd>/memory/MEMORY.md`
  - Encoding: replace `/` in the cwd's absolute path with `-`.
    Example: `/foo/bar` → `-foo-bar`
  - **Windows**: also replace the drive colon and `\` with `-`.
    Example: `C:\project` → `C--project` (one colon + one backslash = two
    hyphens). If unsure, `Glob ~/.claude/projects/*` to check the actual
    directory name.
- `<cwd>/.claude/skills/**/SKILL.md`
- `<cwd>/.claude/agents/*.md`
- `<cwd>/.claude/commands/*.md`
- `~/.claude/plugins/**` (skills/agents/commands of installed plugins)

**Expansion**
From each file, extract and recursively follow:
- `@import` tokens (resolve user-global ones relative to `~/.claude/`, others
  relative to the file's directory or the project root)
- Relative markdown links `[text](./path.md)`
- File paths mentioned inside backticks (only if they actually exist)

Keep collecting until no new nodes appear. **Verify current state** — re-check
with Glob that existing referenced paths still exist (per memory-discipline
principles).

### Step 2 — Detect three things

Read every audited file and look for **only** these three things:

| Kind | Criterion |
|------|-----------|
| **Outdated** | A claim that no longer matches the actual code/config (paths, commands, numbers, policy, versions, etc.) |
| **Conflict** | Two documents describe the same topic differently |
| **Risky / Ambiguous** | An instruction that's open to multiple readings, or dangerous if followed the wrong way (e.g. "use your judgment", "depending on the situation", delete/override instructions with no explicit scope) |

Every finding needs **evidence**: where the claim was made (`file:line`) and
the counter-evidence (`file:line` or a quote of the current code).

**If confidence is low, drop it. False positives are this tool's biggest
enemy.**

### Step 3 — Prioritize and propose fixes

Sort the report by:

1. **Blast radius** — files loaded into every conversation (`CLAUDE.md` /
   `MEMORY.md`) rank highest
2. **Severity** — HIGH (following the wrong instruction breaks something),
   MED (confusing but easy to recover from), LOW (minor inconsistency)
3. **Fix difficulty** — clearest fixes first

Include a **proposed fix** for every finding, specific enough that a human can
judge it with a single OK/NO.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Audit CLAUDE.md/MEMORY.md/rules/skills/agents/commands | Auto-edit file contents (proposals only) |
| [READ] Classify into Outdated/Conflict/Ambiguous | Report other kinds of issues (style, typos) |
| [WRITE] Write reports to `.drift-reports/` | Auto-add the report dir to `.gitignore` |
| [READ] Optional auto-fix PR (Outdated items with a clear fix only) | Auto-fix Conflict/Risky items (human judgment required) |
| [READ] Recursively trace `@import` | Fetch external URLs (offline only) |

---

## Rationalization Table

| Rationalization | Counter |
|-----------------|---------|
| "This finding's confidence is a bit low, but I'll include it anyway" | One false positive permanently damages this tool's credibility. Violates the Dominant Variable. Confidence < 80% → exclude. |
| "I can auto-fix Conflicts too" | Only a human knows which side of a Conflict is correct. Auto-fixing risks locking in the wrong side as the standard. |
| "A longer report is more valuable" | Long reports don't get read. 5 HIGH findings beat 50 LOW ones. Keep the signal-to-noise ratio high. |
| "It's fine to run this every day" | Drift accumulates over time. Re-audit only after at least 24h. An immediate re-audit just reproduces the same result. |

---

## Error Recovery

On failure: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure type | Detection condition | Recovery path |
|---------|---------|--------|
| `tool_failure` | Failed to read a document file | State the analysis scope as limited to accessible files only, then continue |
| `missing_data` | No docs/ directory, or zero documents | State "nothing to analyze". Never fabricate findings |
| `input_error` | Unclear which documents to analyze | Ask one clarifying question — default to a full scan |

---

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Write `.drift-reports/YYYY-MM-DD.md` | high | L1 |

- **L1 (Invariants)**: only saves the drift report. Never directly edits
  CLAUDE.md, rules, or MEMORY.md (diagnostic only, read-only).

---

## Invariants (never violate)

1. **Evidence required**: every finding cites both sides — `file:line` for the
   claim and `file:line` for the counter-evidence. No finding without
   evidence. Violation → impossible to trace what the tool actually based its
   judgment on, so a human can't decide whether to fix it.

2. **Exclude confidence < 80%**: items that are merely suspected, not
   confirmed, are left out of the report. Violation → false positives
   accumulate → the report gets ignored → the tool gets abandoned.

3. **Auto-fix requires all 3 conditions AND**: Outdated + a clear fix +
   explicit user approval. Auto-fixing Conflict/Risky items is never allowed.
   No file edits without user approval. Violation → a bad auto-fix can make
   the drift worse or break the document system.

---

## Output

Saved to `.drift-reports/` (create if missing, never add it to `.gitignore` —
its history should be visible in PRs):

- `.drift-reports/<YYYY-MM-DD-HHMM>.md` — timestamped report
- `.drift-reports/latest.md` — a copy of the latest one

**Report template:**

```markdown
# Memory Audit — {timestamp}

**Scanned:** {n} files reachable from CLAUDE.md / MEMORY.md / skills / agents
**Findings:** HIGH {h} / MED {m} / LOW {l}

## Top priority
1. **[HIGH] `path:line`** — {one-line summary}
   - Claim: "..."
   - Reality: `other/path:line` — ...
   - Proposed fix: ...
2. ...

## Medium
...

## Low
...

## Needs a human decision
- Conflicts where it's unclear which side is correct
- Ambiguous items where the intent is unclear

## Next step
Want an auto-fix PR? (Outdated items with a clear fix only)
```

### Auto-fix (optional)

Only ask after printing the report summary:

> "Found {h} HIGH items. What would you like to do?
> 1) Generate a PR for the ones with a clear fix
> 2) Report only"

If chosen, commit one atomic commit per finding on a
`docs/drift-fix-<timestamp>` branch, then `gh pr create`.

**Always excluded**: Conflict (needs a human to say which side is right),
Risky/Ambiguous (needs intent confirmation).

---

## Arguments

| Input | Behavior |
|------|------|
| `/doc-drift` | Full audit (default) |
| `/doc-drift recent` / `recent 50` | Only areas changed in the last N commits |
| `/doc-drift path <glob>` | A specific path only |

---

## Principles

- **Minimize false positives** — drop it if you're not confident. The report
  only survives if people trust it.
- **Evidence required** — every finding cites both sides (`file:line`).
- **Respect the summary-and-link pattern** — it's normal for `CLAUDE.md` to
  summarize/link to other documents. Only flag it when the meaning has
  actually drifted.

## Truthful Reporting

When reporting completion, this skill:
1. **no mock deception**: confirm actual execution results before reporting.
   No completion claims based on guesswork.
2. **no test façade**: never hide failures behind skip/xfail. Mark skips as
   `⚠️ SKIPPED: reason`.
3. **no silent brokenness**: final state must be labeled `WORKING` /
   `PARTIAL` / `BROKEN`. PARTIAL/BROKEN must list the concrete defects.
- **Prioritize files loaded every conversation** — drift in `CLAUDE.md` /
  `MEMORY.md` is more dangerous than drift in any other file.
