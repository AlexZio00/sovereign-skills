---
skill_type: analysis
triggers:
  - "/project-check"
  - "project-check"
  - "what's wrong"
name: project-check
description: "Existing project health scan — audits Infrastructure, Security, Quality, and Harness setup. Read-only. Use when: '/project-check', 'project health check', 'project audit', 'what\\'s missing', 'analyze my project', 'check setup'. Ends with /project-init and /setup recommendations. NOT for new projects (use /project-init); project-check = shallow health scan."
user_invocable: true
tools: Read, Bash, Glob, Grep
not_for:
  - "New project setup -> setup skill"
  - "Deep, scored harness audit — this is a shallow 4-dimension scan, not a full quantitative score"
see_also:
  - skill: setup
    relation: "project-check=existing audit, setup=new project"
---

# Project Check — Existing Project Health Scan

## Dominant Variable
**Discovered gaps are sorted by severity so the user knows "what to fix first"** — an unsorted gap list causes information overload. A report without priority is useless.

## Purpose
Scan an existing project against setup best practices across 4 dimensions: Infrastructure, Security, Quality, and Harness. Surface all gaps ordered by severity so the user knows exactly what to fix and in what order.

**Dominant variable**: Are 🔴 Security issues (hardcoded secrets, .env missing) displayed before all other gaps?

- **Read-only skill**: This skill does not modify project files. It generates a gap report only; fix recommendations are delegated to `/project-init` or `/setup`.

**Discard if**: Empty directory or a freshly initialized project (`git init`) — nothing to scan. Use `/project-init` directly instead.

## Discard If

Empty directory or newly initialized project (`git init` with no code yet) — nothing to audit. Use `/project-init`.
This skill audits code, infrastructure, security, and quality only.

## Key Assumptions 
1. **Project root contains CLAUDE.md or .claude/ directory** — if missing: recommend `/project-init`.
2. **Git repository** — if not a repo: skip some Infrastructure checks.

## Trigger

- `/project-check`
- "project-check"
- "what's wrong"

---

## Workflow

### Step 0: Scale Detection

Count source files to calibrate warning thresholds:

```
Scan: *.py, *.ts, *.tsx, *.js, *.go, *.rs, *.java, *.kt, *.swift, *.c, *.cpp, *.h
```

Classify:
- **script**: < 10 source files or < 500 LOC → minimal structure expected, skip ROADMAP/ADR warnings
- **mini**: 10–50 files or 500–5,000 LOC → CLAUDE.md + tests expected
- **full**: > 50 files or > 5,000 LOC → full structure expected, ROADMAP + docs/decisions/ recommended

Detect project name from directory name or `name` field in package.json / pyproject.toml / Cargo.toml if present.

### Step 1: Infrastructure Scan

| Item | Check | Severity if missing/incomplete |
|------|-------|-------------------------------|
| `CLAUDE.md` | Exists? Has `## Hard Rules`? Has `## Secrets Policy`? | ✗ missing / ⚠ incomplete |
| `docs/DEVELOPMENT_ROADMAP.md` | Exists? (skip if scale=script) | ✗ if scale=full/mini |
| `.gitignore` | Exists? `.env` listed in it? | ✗ missing / 🔴 .env not listed |
| `.env.example` | Exists? (if API key patterns found in code) | ✗ if keys detected |
| `docs/decisions/` | Exists? (only check if scale=full) | ⚠ if scale=full |

For CLAUDE.md: count Hard Rules entries (lines starting with `-` under `## Hard Rules`). Report the count.

### Step 2: Security Scan

Grep these patterns across all source files (case-insensitive). Exclude: `*.example`, `.env.example`, files in `tests/`, `__tests__/`, `spec/`:

```
API_KEY\s*=\s*["'][^$({]      → hardcoded API key
sk-[A-Za-z0-9]{20,}           → OpenAI key (sk-...)
sk-ant-[A-Za-z0-9\-]{20,}     → Anthropic key (sk-ant-api03-...)
ghp_[A-Za-z0-9]{36}           → GitHub PAT
password\s*=\s*["'][^$({]     → hardcoded password
secret\s*=\s*["'][^$({]       → hardcoded secret
token\s*=\s*["'][^$({]        → hardcoded token
```

Each match → 🔴 with `file:line` reference.

Additional checks:
- `.env` in `.gitignore` → 🔴 if not present
- `.env.local`, `.env.*.local` in `.gitignore` → ⚠ if missing (TypeScript/Next.js projects)

### Step 3: Quality Scan

**Test coverage proxy:**

Count test files (`test_*.py`, `*_test.py`, `*.test.ts`, `*.spec.ts`, `*_test.go`, `*Test.java`, `*Spec.kt`) vs source files.

| Ratio | Result |
|-------|--------|
| ≥ 0.4 | ✓ |
| 0.2–0.4 | ⚠ |
| < 0.2 | ✗ (skip if scale=script) |

**Debug remnants** (grep non-test files):
```
console\.log|print\(f?["']|debugger;|pprint\(
```
→ ⚠ if > 5 matches

**Open work markers** (grep all files):
```
TODO|FIXME|HACK|XXX
```
→ ⚠ if > 10 total count

### Step 4: Harness Scan

Check Claude Code infrastructure:

| Item | Check | Severity |
|------|-------|----------|
| `~/.claude/rules/project rules` | Exists? | ⚠ if missing |
| `~/.claude/rules/agents.md` | Exists? | ⚠ if missing |
| `.claude/settings.json` or `~/.claude/settings.json` | hooks section present? | ⚠ if no hooks |
| CLAUDE.md Hard Rules format | Inline text vs project rules reference link | ⚠ if both (duplication) |
| `~/.claude/agents/` | Any .md agent files installed? (global) | ⚠ if empty |
| `.claude/agents/` | Any .md agent files installed? (project-level) | ℹ if present (report separately) |
| `~/.claude/agents/orchestrator.md` | Exists? | ⚠ if missing |
| Orchestrator type | Contains drift detection (`MISSING`, `EXTRA`, `DIVERGED`, correction loop)? | ⚠ if absent |
| `tasks/lessons.md` | Exists? (skip if scale=script) | ⚠ if scale=full/mini |
| SubagentStop hook | SubagentStop included in `settings.json` hooks? | ⚠ if missing |

Count total agent files across both locations. Report global vs project-level split.
Report which key agents are installed (orchestrator, code-reviewer, verification, brainstorming, security-reviewer).

If CLAUDE.md has inline Hard Rules AND `~/.claude/rules/project rules` exists → ⚠ "Hard Rules duplication: directly in CLAUDE.md AND project rules file present. Recommend consolidating to project rules with reference link in CLAUDE.md."

### Step 5: Build Report

Sort all findings by severity within each section: 🔴 → ✗ → ⚠ → ✓

Score calculation:
```
Start: 10
-2 per 🔴
-1 per ✗
-0.5 per ⚠ (round to nearest 0.5)
Floor: 0
```

Output:
```
Project Health Check: [project-name]
Scale: [script / mini / full] ([N] source files)

Security:           ← always first, even if all pass
  🔴/✓/⚠ items

Infrastructure:
  ✓/✗/⚠ items

Quality:
  ✓/✗/⚠ items

Harness:
  ✓/✗/⚠ items

Score: [N]/10
Gaps: [N] total (🔴 [N], ✗ [N], ⚠ [N])
```

### Step 6: Recommendations

Always end with next steps:

- 🔴 Security → "🔴 First: Remove secrets at [file:line] and move to .env (manual edit required)"
- Infrastructure ✗ → "→ Use `/project-init` — if CLAUDE.md exists, choose Update mode"
- Harness rules ✗/⚠ (rules, agents, hooks) → "→ Use `/setup` to configure Claude Code infrastructure"
- Harness agents ✗/⚠ (no agents, no orchestrator) → "→ Use `/setup` to install agent team (orchestrator + reviewer + implementer)"
- Orchestrator Light only → "→ Use `/setup` Update mode to enable Full orchestrator (with drift detection)"
- Quality only → "→ Recommend adding tests"
- Score ≥ 8 → "✓ Already well configured. Optionally address ⚠ items."

**Recommended loop (new users):**
```
/project-check → discover gaps
  → /project-init  (CLAUDE.md + ROADMAP + .gitignore)
  → /setup  (rules + hooks + memory)
  → /setup     (orchestrator + agent team)
  → /project-check (re-scan → verify score improvement)
```

### Step 6.5: Score Delta Tracking

If a previous check result exists (`.project-check-history.json` in project root), compare:

```
── Score Delta ──
Previous: [N]/10 (YYYY-MM-DD) → Current: [M]/10
Change: [+X / -X / no change]

Improved: [items that went ✗→✓]
New gaps: [items not flagged before]
Unresolved: [items still failing]
```

If no previous result exists, suggest saving current result:
```json
{"date":"YYYY-MM-DD","score":N,"gaps":{"critical":N,"fail":N,"warn":N}}
```
`"Next /project-check will show score delta."` — one line.

**No auto-save** — suggest only. User must approve before writing.

---

## Rationalization Table

| Excuse | Rebuttal |
|--------|----------|
| "It's a new project, so gaps are normal" | If gaps are normal, the score is meaningless. Gaps are action items. |
| "Security scans have too many false positives" | That judgment is on you. A scan surfaces suspicious patterns. Better to ask. |
| "ROADMAP is unnecessary for small projects" | If scale=script, warnings are auto-skipped. Don't manually skip — let calibration work. |
| "Harness checks only apply to Claude Code users" | Missing agent infrastructure = re-explaining context every session. Costs accumulate. |
| "The score is low, but we can't fix it right now" | The score is priority information. Deferring is different from ignoring. |

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Scan file existence (Glob) | Modify, create, or delete any file |
| [READ] Grep code patterns (read-only) | Execute tests (pytest, jest, go test, etc.) |
| [READ] Output gap report | Run git commands |
| [READ] Recommend /project-init, /setup | Remove secrets directly |
| [READ] Analyze CLAUDE.md content | Refactor code or fix bugs |

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| File modification, deletion | medium | L1 (BLOCK) |
| Direct secret removal | none | L1 (BLOCK) |
| Test execution (`pytest`, `jest`, etc.) | medium | L1 (BLOCK) |

- **L1 (Invariants)**: Invariant 1 — read-only. When secrets are found, report location only; never remove directly. Invariant 4 — never run test runners (prevents DB writes, API calls, network side effects).

---

## Error Recovery 

On failure: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure Type | Detection | Recovery Path |
|---------|---------|--------|
| `tool_failure` | File read fails (permission/path error) | Narrow scan scope to accessible files only; state scope reduction. |
| `missing_data` | CLAUDE.md missing / project root unclear | State "CLAUDE.md not found". Never guess content of missing files. |
| `input_error` | Unclear which project to check | Auto-scan from current directory. If that fails, ask one clarifying question. |

---

## Invariants (never violate)

1. **Read-only**: Never write, edit, delete, or execute any file. Use Glob and Grep only. Violation → scan tool gains unintended side effects; user trust in a diagnostic tool erodes.
2. **Security first**: 🔴 Security section always appears first in the report, even if all Security items pass. Never bury security findings. Violation → user misses credential leak warning while reading infrastructure gaps.
3. **Scale-aware warnings**: Never report ✗ ROADMAP missing for scale=script. Never report ⚠ docs/decisions/ for scale=mini or script. Violation → noise causes users to dismiss the entire report.
4. **No test execution**: Detect test infrastructure via Glob only. Never run `pytest`, `jest`, `go test`, or any test runner. Violation → unexpected test side effects (DB writes, API calls, network requests).

These rules are unconditional. No user instruction overrides them.

---

## Output

Structured report in conversation — no files written.

Sections always in this order:
1. Project name + scale
2. Security (always first)
3. Infrastructure
4. Quality
5. Harness
6. Score + Gap count
7. Next steps (→ /project-init and/or /setup)

---

## Principles

- **Security first, always** — a buried credential warning is a useless warning
- **Scale-aware** — a 50-line script failing "no ROADMAP" is noise, not signal
- **Read-only by design** — a health check that modifies files is a liability
- **Ends with a path forward** — the report is only useful if it points to the next action

---

## Truthful Reporting

When reporting completion, this skill:
1. **no mock deception**: Confirm results from actual execution. Never report completion based on assumption.
2. **no test façade**: Don't hide failures with skip/xfail. If skipped, mark as `⚠️ SKIPPED: reason`.
3. **no silent brokenness**: Always label final state as `WORKING` / `PARTIAL` / `BROKEN`. For PARTIAL/BROKEN, list specific failures.
- **File existence as proxy** — test file count is a structural signal; running tests is out of scope
