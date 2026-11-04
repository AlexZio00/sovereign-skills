---
skill_type: analysis
triggers:
  - "/project-check"
  - "project-check"
name: project-check
description: "Existing project health scan — audits Infrastructure, Security, Quality, and Harness setup. Read-only. Use when: '/project-check', 'project health check', 'project audit', 'what\\'s missing', 'analyze my project', 'check setup'. Ends with /project-init and /setup recommendations. NOT for new projects (use /project-init); project-check = shallow health scan."
user-invocable: true
tools: Read, Bash, Glob, Grep
disallowed-tools: Edit, Write, NotebookEdit  # descriptive metadata: read-only discipline is a rule in the body (Invariant 1), not enforced by this field
depends_on:
  skills: []
  agents: []
  files:
    - CLAUDE.md
    - .claude/rules/*.md
    - .project-check-history.json
concurrency_profile:
  read_only: true
  concurrency_safe: true
  destructive: none
not_for:
  - "New project scaffolding -> project-init; harness/agent-team setup -> setup"
  - "Deep, scored harness-maturity audit against a fixed multi-axis checklist -> check-harness (optional, not included in this repo; project-check is a shallow one-pass scan, not a maturity score)"
see_also:
  - skill: setup
    relation: "project-check=existing audit, setup=new harness setup (project-init is a separate skill for project scaffolding)"
  - skill: check-harness
    relation: "optional, not included in this repo. project-check=shallow one-time 4-dimension scan with no persistent scoring model, check-harness=deep multi-axis maturity scoring with trend tracking"
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
Need a persistent, weighted maturity score with cross-axis trend tracking instead of a one-time 4-dimension pass/fail scan — use `/check-harness` (optional, not included in this repo; without it, this report is the available scan), not this skill.

## Key Assumptions 

1. **Project root contains CLAUDE.md or .claude/ directory** — if missing: recommend `/project-init`.
2. **Git repository** — if not a repo: skip some Infrastructure checks.

## Trigger

- `/project-check`
- "project-check"

---

## Workflow

### Step 0: Scale Detection

Count source files to calibrate warning thresholds:

```
Scan: *.py, *.ts, *.tsx, *.js, *.go, *.rs, *.java, *.kt, *.swift, *.c, *.cpp, *.h
Exclude dirs: node_modules/, .venv/, venv/, __pycache__/, vendor/, dist/, build/, .git/, .next/, target/
```
(Without this exclusion, dependency/build directories get swept into the file/LOC count and skew the Step 0 scale classification.)

Classify (if the file count and the LOC point to different classes, take the **larger** class — for example 5 files with 3,000 LOC is mini):
- **script**: < 10 source files or < 500 LOC → minimal structure expected, skip ROADMAP/ADR warnings
- **mini**: 10–50 files or 500–5,000 LOC → CLAUDE.md + tests expected
- **full**: > 50 files or > 5,000 LOC → full structure expected, ROADMAP + docs/decisions/ recommended

Detect project name from directory name or `name` field in package.json / pyproject.toml / Cargo.toml if present.

### Step 1: Infrastructure Scan

| Item | Check | Severity if missing/incomplete |
|------|-------|-------------------------------|
| `CLAUDE.md` | Exists? Has `## Hard Rules`? Has `## Secrets Policy`? | ✗ missing / ⚠ incomplete |
| `docs/DEVELOPMENT_ROADMAP.md` | Exists? (skip if scale=script) | ✗ if scale=full/mini |
| `.gitignore` | Exists? `.env` actually ignored — verified via `git check-ignore -v .env` (see Step 2), not just string presence in the file | ✗ missing / 🔴 not ignored or already tracked (see Step 2) |
| `.env.example` | Exists? (if API key patterns found in code) | ✗ if keys detected |
| `docs/decisions/` | Exists? (only check if scale=full) | ⚠ if scale=full |

For CLAUDE.md: count Hard Rules entries (lines starting with `-` under `## Hard Rules`). Report the count.

**CLAUDE.md size and structure** (read-only, `wc -l`): if the project `CLAUDE.md` (root or `.claude/CLAUDE.md`) is longer than 200 lines, report ⚠. Anthropic's memory documentation (code.claude.com/docs/en/memory) recommends under 200 lines per file, because longer files use more context and are followed less reliably. `@import` files are loaded at launch too, so imports do not reduce the line count. In the report, give the line count and name instructions that apply only to some files or directories as candidates to move into `.claude/rules/<topic>.md` with `paths:` frontmatter. Keep Hard Rules and always-on rules in a file without `paths:`: a `paths:` rule loads only after a matching file is read, so an invariant placed there is not in force before then. 200 lines or fewer is ✓.

### Step 2: Security Scan

Grep these patterns across all source files. Run the `sk-` patterns and the vendor-prefixed patterns case-sensitive and every other pattern case-insensitive. Exclude: `*.example`, `.env.example`, files in `tests/`, `__tests__/`, `spec/`, and dependency/build directories (`node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `vendor/`, `dist/`, `build/`, `.git/`, `.next/`, `target/` — same list as Step 0):

```
API_KEY\s*=\s*["'`][^$({]     → hardcoded API key
(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}      → OpenAI/Anthropic key (sk-..., sk-ant-..., sk-proj-... — includes hyphens and underscores; a pattern without them misses keys that contain a hyphen)
(^|[^A-Za-z0-9])sk-ant-[A-Za-z0-9\-]{20,}  → Anthropic key (sk-ant-api03-...)
ghp_[A-Za-z0-9]{36}           → GitHub PAT
github_pat_[A-Za-z0-9_]{22,}  → GitHub fine-grained PAT
AKIA[0-9A-Z]{16}              → AWS access key id
xox[baprs]-[A-Za-z0-9-]{10,}  → Slack token
AIza[0-9A-Za-z_-]{35}         → Google API key
password\s*=\s*["'`][^$({]    → hardcoded password
secret\s*=\s*["'`][^$({]      → hardcoded secret
token\s*=\s*["'`][^$({]       → hardcoded token
```

The quote character class includes the backtick so that JS/TS template literals such as `` `sk-...` `` match too. The vendor-prefixed patterns (`ghp_`, `github_pat_`, `AKIA`, `xox`, `AIza`) have unique prefixes, so run them case-sensitive.

The `sk-` patterns need a non-alphanumeric character (or line start) before `sk-` and must not be case-insensitive. Without that, ordinary identifiers such as `task-queue-worker-configuration` (the `sk-queue-...` inside `task-queue-...`), `risk-assessment-...` or `disk-usage-...` match and produce false 🔴 findings; they must not match.

Each match → 🔴 with `file:line` reference. Read the matched line before judging: a placeholder value (`your_key_here`, `xxx`, `changeme`, `<...>`) is ℹ info, not 🔴. Never print the found value — report `file:line` and the pattern name only.

Additional check — permission scope: if `permissions.allow` in the project `.claude/settings.json` or `.claude/settings.local.json` contains an entry that allows every command, such as `Bash(*)` or a bare `Bash`, report ⚠. Report the file and the entry only.

Additional checks — `.env` protection (skip entirely if not a git repo, per Key Assumption 2):

A string match for `.env` inside `.gitignore` is not proof of protection — the pattern can be malformed (wrong path, typo, wrong glob syntax) and never actually match, or the file can already be tracked in git, in which case `.gitignore` has no effect on it at all. Verify both:
1. `git check-ignore -v .env` — confirms the pattern actually matches the file. No output / non-zero exit → the listed pattern doesn't cover `.env` → 🔴 "`.env` present in `.gitignore` text but the pattern doesn't actually match (git check-ignore reports it as not ignored)". If the command is denied or fails (e.g. the target is outside the worktree), report "⚠️ cannot verify — string presence only" instead of a red finding.
2. `git ls-files --error-unmatch .env` (exit 0 means tracked) — if `.env` is already tracked, → 🔴 "`.env` is already tracked in git — `.gitignore` cannot retroactively untrack it. Needs `git rm --cached .env` (manual step; this skill does not run it)".
- `.env` missing from `.gitignore` entirely (no string match) → 🔴 as before.
- `.env.local`, `.env.*.local` in `.gitignore` → ⚠ if missing (TypeScript/Next.js projects). Apply the same `git check-ignore -v` verification when a matching line is present.

### Step 3: Quality Scan

Apply the same exclusion list as Step 0 (`node_modules/`, `.venv/`, `__pycache__/`, `vendor/`, `dist/`, `build/`, `.git/`, etc.) to every file count and grep below.

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

**Profile detection (run first — determines whether orchestrator/agent-team absence is a gap at all):**

Check whether the project shows any sign of agent-routing adoption:
- `.claude/agents/*.md` (project-level) — any files present?
- `~/.claude/agents/*.md` (global) — any files present?
- CLAUDE.md or project rules mention agent routing (e.g., "orchestrator", "Tier 1/2/3", "subagent-dev", "brainstorming → writing-plans")?

If **none** of the above are present, infer **Minimal profile** — per the `setup` skill's own Q2 ("Minimal: rules + memory only. No agent routing" is a first-class, intentional choice, not a defect). Under Minimal profile, orchestrator/agent-team absence is a configuration choice, not a gap — do not score it as ⚠.

If **any** of the above are present, the project has adopted Standard/Orchestrated routing at least partially — a missing orchestrator or key agents at that point is a real gap (routing infrastructure exists without the piece that coordinates it), and stays ⚠.

Check Claude Code infrastructure:

| Item | Check | Severity |
|------|-------|----------|
| Project rules file: `.claude/rules/*.md` (what `/setup` writes: `.claude/rules/project-rules.md`) | Any file present? | ⚠ if none |
| `~/.claude/rules/agents.md` (global; `/setup` writes it only for the Standard and Orchestrated profiles) | Exists? | ⚠ if missing and **not** Minimal profile; skip if Minimal profile |
| `.claude/settings.json` or `~/.claude/settings.json` | hooks section present? | ⚠ if no hooks |
| CLAUDE.md Hard Rules format | Inline text vs project rules reference link (`Hard Rules → see .claude/rules/...`) | ⚠ if both (duplication) |
| `~/.claude/agents/` | Any .md agent files installed? (global) | ⚠ if empty and **not** Minimal profile; ℹ (no score) if empty and Minimal profile |
| `.claude/agents/` | Any .md agent files installed? (project-level) | ℹ if present (report separately) |
| `~/.claude/agents/orchestrator.md` (optional agent, not included in this repo) | Exists? | ⚠ if missing and **not** Minimal profile; skip (no flag) if Minimal profile |
| `tasks/lessons.md` (created by `/setup` when structured memory is chosen; format: FILE-CONVENTIONS link below) | Exists? (skip if scale=script) | ℹ if missing and scale=full/mini; no score deduction |
| SubagentStop hook | SubagentStop included in `settings.json` hooks? | ⚠ if missing and **not** Minimal profile (a Minimal setup has no subagents to stop) |

**Worktree hygiene** (only in a git repository where `git worktree list` shows 2 or more worktrees; read-only commands only): every finding below is ⚠ or ℹ, and this skill never deletes or creates anything.
- `git worktree list --porcelain`: report `prunable` entries and the number of long-abandoned `.claude/worktrees/*` directories as ⚠. Cleaning up is the user's job. Do not count a worktree as stale if it is `locked`, is the current session's working directory, or has a branch named like `claude/<adjective-name-hash>`: the app or session manages those, and an app-managed worktree may have no lock.
- Missing local data: if the main worktree has gitignored `*.db` files, `config/local/`, or `.env*` files and a worktree lacks them, report ⚠ `missing_local`. Tests then fail in that worktree and the failures look like code regressions. A missing `.worktreeinclude` file is ℹ: suggest it, do not create it.
- Permission rule paths: if a `permissions.deny` or `permissions.allow` rule uses a relative glob that starts with `**/` to protect a sensitive file, report ⚠. In a worktree session such a rule resolves against the worktree and may not block the file in the main checkout. Absolute-path rules on Windows need the form `//d/...` (lowercase drive letter, no colon); this follows the Claude Code permissions documentation and this skill does not re-verify it.
- If a past incident caused by a worktree (for example a test run against a stale database copy in a worktree) is recorded only in `tasks/lessons.md` and not in `CLAUDE.md` or the rules, report ℹ and suggest a one-line worktree rule in the root `CLAUDE.md`.

Count total agent files across both locations. Report global vs project-level split.
Report which key agents are installed (orchestrator, code-reviewer, verification, brainstorming, security-reviewer; all optional, none are included in this repo — `/setup` can generate review agents). If Minimal profile was inferred, report "0 agents — consistent with Minimal setup profile (rules + memory only)" instead of counting it toward gaps.

If CLAUDE.md has inline Hard Rules AND a project rules file with Tier-0 rules exists in `.claude/rules/*.md` → ⚠ "Hard Rules duplication: directly in CLAUDE.md AND project rules file present. Recommend consolidating to the project rules file with a reference link in CLAUDE.md."

File formats: https://github.com/AlexZio00/sovereign-skills/blob/master/docs/FILE-CONVENTIONS.md (a missing `tasks/lessons.md` or history file is never an error here: report ℹ and move on).

### Step 5: Build Report

Sort all findings by severity within each section: 🔴 → ✗ → ⚠ → ℹ → ✓

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
Status: WORKING | PARTIAL (what was not scanned and why) | BROKEN (scan could not run)
```

### Step 6: Recommendations

Always end with next steps:

- 🔴 Security → "🔴 First: Remove secrets at [file:line] and move to .env (manual edit required)"
- Infrastructure ✗ → "→ Use `/project-init` — if CLAUDE.md exists, choose its Update option"
- Harness rules ✗/⚠ (rules, agents, hooks) → "→ Use `/setup` to configure Claude Code infrastructure"
- **Verify before recommending (required)**: before recommending any slash command or skill below, confirm it exists with Glob: `~/.claude/commands/<name>.md`, `~/.claude/skills/<name>/SKILL.md`, the project's `.claude/commands/` and `.claude/skills/`, and plugin installs under `~/.claude/plugins/` (for example `~/.claude/plugins/**/skills/<name>/SKILL.md`). The skill list shown in the current session also counts as proof that it exists. If none of these shows it, drop that recommendation and write "recommended `/X` is not installed" instead. A dead reference to a command that was never installed is a known failure of this report.
- Harness agents ✗/⚠ (no agents, no orchestrator) AND agent-routing infra already exists elsewhere (Step 4 profile detection = not Minimal) → "→ Use `/setup` to install agent team (orchestrator + reviewer + implementer)"
- No agents anywhere AND no orchestrator, Minimal profile inferred (Step 4) → do not recommend an agent team as a fix; instead: "ℹ No agent-routing layer detected — consistent with a Minimal setup (rules + memory only). No action needed if intentional; run `/setup` if you want review agents or orchestration."
- Quality only → "→ Recommend adding tests"
- Score ≥ 8 → "✓ Already well configured. Optionally address ⚠ items."

**Recommended loop (new users):**
```
/project-check → discover gaps
  → /project-init  (CLAUDE.md + ROADMAP + .gitignore)
  → /setup  (rules + hooks + memory + optional agent team)
  → /project-check (re-scan → verify score improvement)
```

### Step 6.5: Score Delta Tracking

Look for a previous check result in two places, project-root first:
1. `.project-check-history.json` in project root.
2. If that's absent, fall back to the user-level persistent cache before concluding there's no prior result: `~/.claude/.harness/project-check/<project-name>.json` (keyed by the detected project name from Step 0). This survives the project-root file being gone after a fresh clone or a `.gitignore`'d local file getting wiped.

If either is found, compare against it:

```
── Score Delta ──
Previous: [N]/10 (YYYY-MM-DD) → Current: [M]/10
Change: [+X / -X / no change]

By category — Previous → Current:
  🔴 Critical: [N] → [N]
  ✗ Fail:      [N] → [N]
  ⚠ Warn:      [N] → [N]
```

**Honesty limit**: the history file stores only the total score and per-category counts (see JSON schema below) — it does not store *which* items failed. Item-level claims like "X went from ✗ to ✓" or "Y is a new gap" are not supported by this data and must never be shown — showing them would be a guess dressed as a fact. Report only the aggregate score and per-category count deltas above (e.g., "2 fewer ⚠ items than last run," not which ones resolved). Per-item history tracking is out of scope for this skill by design (a persistent, item-level maturity trend is `check-harness`'s job — see `see_also`), not a missing feature to add here.

If neither exists, suggest saving current result — project-root file by default, user-level cache path as the fallback option if the project doesn't want history checked into (or gitignored within) the repo:
```json
{"date":"YYYY-MM-DD","score":N,"gaps":{"critical":N,"fail":N,"warn":N}}
```
`"Next /project-check will show score delta."` — one line.

**No auto-save — this skill never writes it, period.** The JSON snippet above is printed to the chat as text only. Actually creating or appending to `.project-check-history.json` is something the user does themselves — it is outside this skill's execution scope (this skill is read-only by rule; see Invariant 1).

---

## Rationalization Table

| Excuse | Rebuttal |
|--------|----------|
| "It's a new project, so gaps are normal" | If gaps are normal, the score is meaningless. Gaps are action items. |
| "Security scans have too many false positives" | That judgment is on you. A scan surfaces suspicious patterns. Better to ask. |
| "ROADMAP is unnecessary for small projects" | If scale=script, warnings are auto-skipped. Don't manually skip — let calibration work. |
| "Harness checks only apply to Claude Code users" | Missing agent infrastructure = re-explaining context every session. Costs accumulate. |
| "The score is low, but we can't fix it right now" | The score is priority information. Deferring is different from ignoring. |
| "`.gitignore` contains `.env`, so it is protected" | String presence is not proof. Step 2 verifies the real match and tracked status with `git check-ignore -v` and `git ls-files --error-unmatch`. |
| "0 agents means a setup deduction" | Check the project profile first. Under a Minimal profile, no agents is an intended choice, not a gap. |
| "Just delete the secret" | Invariant 1 — read-only. Report the location only; never remove it directly. |

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Scan file existence (Glob) | Modify, create, or delete any file |
| [READ] Grep code patterns (read-only) | Execute tests (pytest, jest, go test, etc.) |
| [READ] Run read-only git inspection (`git check-ignore -v`, `git ls-files --error-unmatch`, `git worktree list`) to verify `.gitignore` actually protects secret files | Run any git command that mutates state (commit, push, add, rm, checkout, etc.) |
| [READ] Output gap report | — |
| [READ] Recommend /project-init, /setup | Remove secrets directly |
| [READ] Analyze CLAUDE.md content | Refactor code or fix bugs |

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| File modification, deletion | medium | L1 (BLOCK) |
| Direct secret removal | none | L1 (BLOCK) |
| Test execution (`pytest`, `jest`, etc.) | medium | L1 (BLOCK) |

- **L1 (Invariants)**: Invariant 1 — read-only. When secrets are found, report location only; never remove directly. Invariant 4 — never run test runners (prevents DB writes, API calls, network side effects).
- ⚠️ **No tool-level enforcement**: the `tools:` and `disallowed-tools:` frontmatter fields are descriptive metadata. Read-only behavior rests on this skill's rules (Invariant 1) alone, and the `Bash` tool could still write (e.g. `echo x > file`, `git commit`) if the rule were ignored. A host project can add its own PreToolUse hook to intercept write-shaped Bash commands.

---

## Error Recovery 

On failure: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure Type | Detection | Recovery Path |
|---------|---------|--------|
| `tool_failure` | File read fails (permission/path error) | Narrow scan scope to accessible files only; state scope reduction. |
| `missing_data` | CLAUDE.md missing / project root unclear | State "CLAUDE.md not found". Never guess content of missing files. Recommend `/setup` and keep scanning the remaining steps. |
| `input_error` | Unclear which project to check | Auto-scan from current directory. If that fails, ask one clarifying question. |

---

## Invariants (never violate)

1. **Read-only**: Never write, edit, delete, or execute any file. Use Glob, Grep, and read-only inspection commands only (e.g., `git check-ignore -v`, `git ls-files --error-unmatch`, `git worktree list`, `wc -l`) — never a Bash command that writes, deletes, mutates git state, or executes project code. Violation → scan tool gains unintended side effects; user trust in a diagnostic tool erodes.
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
- **File existence as proxy** — test file count is a structural signal; running tests is out of scope

---

## Truthful Reporting

When reporting completion, this skill:
1. **no mock deception**: Confirm results from actual execution. Never report completion based on assumption.
2. **no test façade**: Don't hide failures with skip/xfail. If skipped, mark as `⚠️ SKIPPED: reason`.
3. **no silent brokenness**: Always label final state as `WORKING` / `PARTIAL` / `BROKEN`. For PARTIAL/BROKEN, list specific failures.
