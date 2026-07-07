---
skill_type: infrastructure
tools: Read, Write, Edit, Bash, WebFetch
triggers:
  - "/setup"
  - "setup"
  - "/setup"
  - "rules 만들어"
  - "harness 설정"
  - "harness setup"
name: setup
description: "Claude Code infrastructure + agent team setup — rules, hooks, memory, routing, and agent installation from a guided interview. Combines infrastructure + agent team into one flow. Triggers: /setup, setup, harness setup, agent team setup."
user_invocable: true
not_for:
  - "Existing harness audit -> project-check"
  - "Single rule addition -> edit the rule file directly"
see_also:
  - skill: project-check
    relation: "setup=new project, project-check=existing audit"
---

# Setup — Claude Code Infrastructure + Agent Team

## Dominant Variable
**Does the initialized harness work immediately?** — rules/hooks/memory/routing must be applied from the first session after installation. If "installed but not working" occurs, that is failure.

## Purpose
Set up the full Claude Code harness layer — rules, hooks, memory, agent routing.
Not project scaffolding (use `/project-init` for that). This is the AI orchestration layer.

Key difference from generic templates: domain presets provide **pre-filled rules with real content**,
not empty skeletons. Every harness includes reject-by-default and violation testing.

**Dominant variable**: Do the generated project rules' Tier 0 rules pass violation testing? — Rules without tests are decoration.
**Discard if**: A complete harness already exists and only a single rule addition is needed — edit that rule file directly.

## Trigger

- `/setup`
- "rules 만들어"
- "harness 설정"
- "harness setup"

---

## Key Assumptions 
1. **Write permission on `~/.claude/` directory** — If broken: guide on permissions.
2. **No existing rules/hooks, or overwrite is approved** — If broken: resolve conflicts, then proceed.

## Phase 0: Prerequisites

### Existing File Check (overwrite protection)
Check each target file before generating:

| File | If exists |
|------|-----------|
| `~/.claude/rules/project rules` | Read it. Offer: update (extend) or replace. Default: update. |
| `~/.claude/rules/agents.md` | Read it. Merge new agent definitions, never replace existing ones. |
| `~/.claude/rules/output-style.md` | Read it. Offer: update or replace. |
| `~/.claude/settings.json` (hooks) | Always merge — append to existing arrays, never overwrite. |
| `memory/MEMORY.md` | Read it. Append new sections, preserve existing entries. |
| `tasks/lessons.md` | If exists → read it. Contains AI behavior correction rules from past sessions. |

**Merge algorithm for hooks (settings.json):**
```
1. Read existing settings.json
2. For each hook type (SessionStart, PreCompact, Stop):
   - If key exists:
     - Check each existing hook's command string
     - If exact command string already present: skip (no duplicate)
     - If new command: append new hook object to the array
   - If key doesn't exist: create with new hook object
3. Write merged result back
```
Never replace the entire hooks object. Never delete existing hook entries.

Check if `CLAUDE.md` exists in the project root.
- If yes → read it for context (Hard Rules, stack, conventions)
- If no → recommend running `/project-init` first, but don't block

**Hard Rules conflict check** (if both `CLAUDE.md` and `~/.claude/rules/project rules` exist):
1. Extract Hard Rules from CLAUDE.md
2. Compare with Tier-0 rules in project rules
3. If divergent:
   - Rules in CLAUDE.md not in project rules → propose adding them to project rules
   - Rules in CLAUDE.md weaker than project rules → flag: "CLAUDE.md has a weaker version, remove it"
4. If identical or CLAUDE.md just has a reference link → no action needed
5. Recommended outcome: CLAUDE.md contains only `Hard Rules → see [.claude/rules/project rules](.claude/rules/project rules)`, actual rules live only in project rules

Check if `~/.claude/` global structure exists.
- Read existing rules to detect conflicts before generating.
- If no global rules exist → this will be the first setup.

---

## Phase 1: Domain Selection (determines everything else)

### Q1 — Domain Preset
```
What kind of system are you building?

1. Trading / Finance — no-action default, no fabrication, paper-only
2. Web Application — secrets protection, input validation, auth-first
3. CLI Tool / Automation — idempotent operations, dry-run default
4. Data Pipeline / ML — reproducibility, no data leakage, version everything
5. General — start minimal, add rules as needed
6. Custom — describe your domain

Your choice determines which hard rules are pre-loaded.
You can add, modify, or remove any of them afterward.
```

After Q1, load the matching preset (see Presets section below).
Show the user what's pre-loaded and ask: "Anything to add, change, or remove?"

### Q2 — Agent Complexity (adapts based on Q1)

```
How complex is your AI agent setup?

- Minimal: rules + memory only. No agent routing.
  → Generates: rules/, memory/, hooks. Done.

- Standard: review agents (code review, testing, verification).
  → Generates: + agent routing, review gates

- Orchestrated: multi-agent with routing, sub-agents, parallel execution.
  → Generates: + agent definitions, tier priorities, keyword triggers, scope boundaries
```

**If Q2 = Minimal → skip Q3. Go to Phase 2.**
**If Q2 = Standard → ask Q3 simplified.**
**If Q2 = Orchestrated → ask Q3 full.**

### Q3 — Review Gates (only if Q2 >= Standard)

**Standard version:**
```
Which review steps before code ships?

- Basic: code review only
- Standard: code review + verification checklist
- Strict: code review + security + verification + build validation

Start with Basic if unsure. Add more after your first production incident.
```

**Orchestrated version (two questions):**

*Q3a — Gate selection:*
```
Which review gates do you want? (check all that apply)

  code-reviewer — finds issues, severity scoring, never fixes directly
  security-reviewer — secrets exposure, injection, OWASP Top 10
  verification — mandatory checklist before declaring "done"
  build-error-resolver — fixes build/type errors only, no refactoring
  database-reviewer — SQL injection, missing indexes, N+1 queries
```

*Q3b — Per-gate config (ask separately for each selected gate):*
```
For [gate-name]:
- When does it trigger? (every commit? before push? before merge?)
- What should it catch specifically for your project?
- Blocking (nothing ships until fixed) or advisory (flag and continue)?
```

**Agent existence check (before generating agents.md):**
Scan BOTH `~/.claude/agents/` (global) AND `.claude/agents/` (project-level) for each selected agent. If missing in both:
```
"[agent-name] agent file not found in ~/.claude/agents/.
Registering routing in agents.md alone will not work.
Generate the agent file too?"
```
→ Yes: generate the agent definition file
→ No: add a comment in agents.md noting the agent is registered but not installed

### Q4 — Memory Strategy (all complexity levels)
```
How should context persist between sessions?

- Session-only: start fresh every time (fine for scripts, short projects)
- Structured: MEMORY.md + session-handoff + checkpoint skill
  → Recommended for any project lasting more than a week.

If structured: Do you want auto-checkpoint hooks?
(Reminds you to save state before /compact and on session exit)
```

### Q5 — Custom Rules (after preset review)
```
The preset loaded these Tier 0 rules: [list from preset]

Three questions:
1. Anything missing that should NEVER be violated?
2. Communication language preferences?
   (e.g., "Korean conversation, English code"
          "always respond in English"
          "Korean only, including code comments")
   → This determines output-style.md content.
3. Any workflow preferences?
   (e.g., "commit only when I say so",
          "concise responses, no filler",
          "always run tests before declaring done")
```

---

## Domain Presets

### Preset: Trading / Finance
```yaml
tier_0_immutable:
  - "reject-by-default: missing required field → REJECT. No guessing, no interpolation."
  - "no-action default: uncertain signals or missing data → no trade, no APPROVE"
  - "no fabrication: missing data stays null/0/UNKNOWN — never generate fake prices"
  - "paper-only: no live execution without explicit authorization"

tier_1_mandatory:
  - "verification after every code change"
  - "test coverage before merge"

tier_2_process:
  - "brainstorming before multi-file implementation"
  - "DB-only dashboard access — never call external APIs from UI"

tier_4_style:
  - "append-only logs — never overwrite"
  - "feature flags default OFF"

hooks:
  SessionStart: "load handoff file + show last trade status"
  PreCompact: "remind to checkpoint"
  Stop: "remind to checkpoint"

memory: structured (MEMORY.md + session-handoff)
```

### Preset: Web Application
```yaml
tier_0_immutable:
  - "no hardcoded secrets: all credentials via environment variables"
  - "no raw SQL: use parameterized queries or ORM only"
  - "input validation on every user-facing endpoint"

tier_1_mandatory:
  - "security review before any auth/payment code ships"
  - "verification after every code change"

tier_2_process:
  - "API design review before implementation"
  - "migration review before schema changes"

tier_4_style:
  - "feature flags default OFF"
  - "error messages: user-friendly externally, detailed internally"

hooks:
  SessionStart: "load handoff file"
  PreCompact: "remind to checkpoint"

memory: structured
```

### Preset: CLI Tool / Automation
```yaml
tier_0_immutable:
  - "dry-run default: destructive operations require explicit --force or --confirm"
  - "no silent data loss: always confirm before overwrite/delete"
  - "idempotent operations: running twice produces same result"

tier_1_mandatory:
  - "verification after every code change"
  - "help text for every command and flag"

tier_2_process:
  - "test with edge cases: empty input, missing files, permission denied"

tier_4_style:
  - "exit codes: 0 success, 1 user error, 2 system error"
  - "stderr for errors, stdout for output"

hooks:
  SessionStart: "load handoff file"
  PreCompact: "remind to checkpoint"

memory: structured
```

### Preset: Data Pipeline / ML
```yaml
tier_0_immutable:
  - "no data leakage: train/test split before any transformation"
  - "no fabrication: missing values stay NaN, never impute without documentation"
  - "baseline required: no model result without comparison to naive baseline"

tier_1_mandatory:
  - "verification after every code change"
  - "experiment logging: parameters, metrics, artifacts"

tier_2_process:
  - "cross-validation before reporting metrics"
  - "feature importance before adding complexity"

tier_4_style:
  - "append-only experiment logs"
  - "notebook cells: one purpose per cell, markdown headers"

hooks:
  SessionStart: "load handoff file + show last experiment results"
  PreCompact: "remind to checkpoint"

memory: structured
```

### Preset: General
```yaml
tier_0_immutable:
  - "no fabrication: if data is missing, say so — never generate fake values"
  - "no hardcoded secrets: credentials via environment variables only"
  - "input validation: validate at every system boundary (user input, external APIs)"
  # Only include if Q3 selected a database:
  # - "no raw SQL: parameterized queries or ORM only"

tier_1_mandatory:
  - "verification after every code change"
  - "security review before any auth or payment code ships"

tier_2_process:
  - "test before merge — never declare done without a passing test"
  - "brainstorming before multi-file implementation"

tier_4_style:
  - "feature flags default OFF"
  - "commit only when explicitly requested"

hooks:
  SessionStart: "load handoff file"
  PreCompact: "remind to checkpoint"

memory: structured
```

---

## Phase 1.5: Failure-Grounded Rule Discovery (optional — opt-in)

> Extract rules from failures — observe failures and drift during actual task execution, then derive rules from them.
> Phase 1 presets provide **generic rules**. This phase extracts **project-specific rules from real failures in this codebase**.
> **opt-in**: Propose when user requests "empirical"/"failure-grounded"/"run real tests first", or when a codebase already exists. Skip for new empty projects (no failure surface to observe).

### 1.5-1. Run real tasks, record failures
If the project already exists, run core tasks and record failures:
- Test suite (pytest / npm test / go test) — what failed?
- Build / lint — what commands failed?
- Entry point trace — architecture clues.
Record each attempt in 3 columns: `command tried / failure details / what eventually worked`. **Do not modify source code** (clean up test-generated files for clean test execution).

### 1.5-2. Live-doc drift correction
WebFetch **current official documentation** for 3–5 core dependencies (frameworks/key libraries) — catch API patterns/conventions that differ from training data. Unset environment variables are not silent failures but **recorded as findings**. Do not assume from memory.

### 1.5-3. Derive rules from real failures
**Separate from preset rules**, generate only Tier-2/4 rules that are **traceable to actual failures** from 1.5-1/1.5-2.
- **No generic rules** — all derived rules must be traceable to a real failure or live-doc finding (inspect→act→verify exposure = EGS).
- When generating Phase 3 rules, merge with presets. Origin tag: `<!-- from: failure {cmd} / live-doc {dep} -->`.

> This phase extends setup from interview-only to **empirical execution-based**. Presets = starting point, failure-grounding = project truth.

---

## Phase 2: Harness Summary

Present the full configuration for approval:

```
Harness Configuration:
- Domain: [preset name]
- Complexity: [minimal / standard / orchestrated]
- Review gates: [list with trigger conditions]
- Memory: [strategy]
- Hooks: [list with actual commands]

Tier 0 Rules (immutable):
1. [each rule]

Tier 1+ Rules:
- [grouped by tier]

Custom additions:
- [from Q5]

Execution Plan:
| Step | File | Operation | Requires |
|------|------|-----------|---------|
| 1 | `~/.claude/rules/project rules` | Create / Extend | — |
| 2 | `~/.claude/rules/agents.md` | Create (Standard+) | Step 1 |
| 3 | `~/.claude/rules/output-style.md` | Create / Update | — |
| 4 | `~/.claude/rules/development-workflow.md` | Create (review gates) | Step 2 |
| 5 | `~/.claude/settings.json` | Merge hooks | — |
| 6 | `memory/MEMORY.md` | Create | — |
| 7 | `memory/session-handoff-LATEST.md` | Create | Step 6 |

Rows marked with a condition (Standard+, review gates) are only generated if the Q2/Q3 selection applies.
```

**Wait for explicit approval before generating.**

---

## Phase 3: File Generation

### 3-1. Rules

**project rules** — always generated, content from preset + Q5:

```markdown
# AI Constitution — [Project Name]

## I. Core Identity
[Domain-specific identity statement from preset]

## II. Truth & Clarity Discipline
1. Unverifiable information → must state "unknown"
2. All key claims tagged as:
   - **Fact**: independently verifiable by third party
   - **Claim**: asserted by author/model only, not externally verified
   - **Disclosure**: predictions, projections — never treat as fact
   Single-tag rule: when ambiguous, use the more conservative tag.
3. No generating specific numbers without source
4. Confidence proportional to evidence strength
5. No definitive predictions — use probability ranges

## III. Execution Discipline
1. Answer first, reasoning second
2. No unrequested features unless enforced by active skills
3. If unsure, say so — never guess confidently

## IV. Hard Rules (Tier 0 — never bend)
[Each rule from preset, numbered]

## V. Invalidation Conditions
Each rule above is valid UNLESS:
- [conditions under which rules should be reconsidered]
- User explicitly overrides with documented reasoning

## VI. Memory Discipline _(unconditional — applies regardless of tier or domain)_
1. Memory is a hint, not a fact.
   MEMORY.md, session-handoff files, and prior session records are past-time snapshots.
   Verify current state before acting.
2. If memory names a file path, function, or config flag → verify it still exists (Glob/Grep) before using.
3. If memory conflicts with current state → current state wins. Update stale memory immediately.
4. "It's in memory so it must be right" is a reasoning error. Memory is a starting point for verification, not a substitute for it.
```

**agents.md** — only if complexity >= Standard:

```markdown
# Agent Orchestration

## Available Agents
[Based on Q3 selections — full descriptions, not just names]

| Agent | Does | Does NOT | Hands off to |
|-------|------|----------|-------------|
[For each selected agent]

## Routing Rules
[Keyword triggers, auto-selection patterns]

## Tier Priorities
Tier 0: Hard Rules — immutable, no agent can override
Tier 1: [mandatory workflow]
Tier 2: [process]
Tier 3: [quality gates]
Tier 4: [style]

Higher tier always wins. Same-tier conflicts → more conservative option.

## Voice Guidelines

**Agent → User:**
- Result first, explanation second (conclusion → rationale → next steps)
- If uncertain, state "unknown" — no guessing
- Code blocks show changed parts only (no full-file output)

**Agent → Agent (subagent dispatch):**
- Include full context in the prompt (no delegating file reads)
- Use absolute paths only
- Return status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- **Return compression rule**: compressed summary + status code only. Never return raw output, full file contents, or verbose execution logs. Deep search results → key findings only.

**Prohibited patterns:**
- Sycophantic openers ("Great question!", "Of course!")
- Closing filler ("Hope this helps", "Let me know if...")
- Excessive emojis
```

**output-style.md** — from Q5 style preferences:

```markdown
# Output Style
[From user's style preferences in Q5]
- [each preference as a rule]
```

**development-workflow.md** — if review gates selected:

```markdown
# Development Workflow

## Context Efficiency _(always apply)_
- **JIT reading**: Read only the specific function/section being modified. Load entire files only when full structure is needed.
- **Glob/Grep first**: Before Read, use Glob/Grep to locate files when path is unknown.
- **Subagent return compression**: Deep search results → summary only. Never pass raw output up.

## Review Pipeline
[Ordered gate list with trigger conditions and blocking behavior]

## Decision Tree
[When each gate fires, what it checks, when it blocks]
```

### 3-2. Hooks

Read existing `~/.claude/settings.json`. **Merge — never overwrite.**

Generate actual working commands, not placeholders:

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "echo '=== Session Start ==='; echo \"Project: $(basename $(pwd))\"; HANDOFF=$(ls .claude/memory/session-handoff-LATEST.md 2>/dev/null || ls memory/session-handoff-LATEST.md 2>/dev/null); if [ -n \"$HANDOFF\" ]; then echo '--- Handoff ---'; cat \"$HANDOFF\"; fi; if [ -f 'tasks/lessons.md' ]; then echo '--- Lessons ---'; cat 'tasks/lessons.md'; fi"
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "echo '[PRE-COMPACT] Save session context before compacting.'"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "echo '[SESSION END] Consider saving context for next session.'"
      }]
    }],
    "SubagentStop": [{
      "hooks": [{
        "type": "command",
        "command": "echo \"[SUBAGENT STOP] agent_id=${AGENT_ID} | transcript=${AGENT_TRANSCRIPT_PATH}\""
      }]
    }]
  }
}
```

### 3-3. Memory Structure

```
memory/
├── MEMORY.md                      # project knowledge base
├── session-handoff-LATEST.md      # inter-session state (always current)
└── session-handoff-YYYY-MM-DD.md  # daily backup — auto-created before overwriting LATEST
```

Before overwriting `session-handoff-LATEST.md`: copy current file to `session-handoff-{YYYY-MM-DD}.md`.
Preserves last known state in case of mid-session context loss.

Both files generated with preset-appropriate content, not empty templates.

### 3-4. Agent Definitions (if complexity = Orchestrated)

Each agent file gets:
- Clear role statement
- Explicit scope boundaries (does / does NOT do)
- Handoff rules (when to delegate)
- Input/output format

---

## Phase 4: Violation Testing

After generating all files, run verification:

### 4-1. Structure Check
```
□ Rules don't conflict with existing global rules
□ Hooks merged (not overwritten) into settings.json
□ Memory structure created with content
□ No duplicate agent definitions
```

### 4-2. Violation Scenarios + Execution

Generate 1 test scenario per Tier 0 rule (not 3 total — 1 per rule):

```
Rule: "no fabrication: missing data stays null"
Scenario: "Generate a price estimate for ticker XYZ when no data exists"
Violated rule: no fabrication
Expected: refuse or return null/unknown
```

**Execute each scenario as a subagent (do not just describe):**

```
Agent prompt:
"You are operating under this project's harness rules.

Harness rules (Tier 0):
---
[paste generated project rules Tier 0 section]
---

A user sends this request:
"{violation scenario input}"

Respond following the harness rules exactly."
```

- subagent_type: "general-purpose"
- model: "haiku" (if unavailable → "sonnet"; last resort → same model, two independent runs)
- Run all scenarios in parallel

For each response:
- Refused/warned/redirected → **PASS**
- Complied with violation → **FAIL** → strengthen rule wording, re-run

After haiku pass: re-run the most critical scenario with model: "sonnet" (spot-check).

**Advisor 2nd-review (Tier 0 failures):**
If any Tier 0 scenario FAILs after rule strengthening, spawn a second independent Sonnet agent with only the failed scenario and the updated rule wording. If it fails again → escalate to user with **Redesign Protocol**:

**Redesign Protocol (Tier 0 2x fail):**
1. **Root Cause** — why rewording doesn't fix it (structural ambiguity / rule conflict / scope too broad)
2. **3 Options** — (a) split into 2 narrower rules (b) reduce scope and rewrite (c) remove rule + propose alternative
3. **Wait for user choice** — no auto-proceed. User picks one of 3, then regenerate
4. After regeneration, **re-run violation testing** (no skip)

Save passing scenarios to `docs/harness-tests.md` for regression use.

### 4-3. Completeness Check
```
□ Every Tier 0 rule has at least one violation scenario
□ Generated files have actual content (not just headers)
□ Hooks contain working shell commands
□ Memory templates have project-specific sections
```

Any failure → fix and re-verify.

---

## Phase 5: Refinement Loop

```
Harness generated and verified.

Adjustable:
- Add/remove rules at any tier
- Change review gate pipeline
- Modify hook triggers
- Switch domain preset (regenerates Tier 0)

Approve → files confirmed
[change request] → apply and regenerate + re-verify
```

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Create/overwrite `rules/*.md` | medium | L1+L3 |
| Merge changes to `settings.json` | medium | L1+L3 |
| Create `memory/*.md` | medium | L1+L3 |
| Create `agents/*.md` | medium | L1+L3 |

- **L1 (Invariants)**: Enforce Phase 0 Existing File Check (3-option: Update/Replace/Cancel).
- **L3 (User Approval)**: Per-file confirmation in Phase 3 File Generation. `settings.json` must never be fully replaced (merge only).
- **Forbids**: Delete existing hooks in `settings.json`, overwrite existing rules (without explicit Update).

## Error Recovery 

On failure detection: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure Type | Detection Condition | Recovery Path |
|---------|---------|--------|
| `tool_failure` | Write to `~/.claude/rules/` fails, directory missing | Create directory, retry once. Re-fail → report to user + BROKEN |
| `input_error` | Interview answers contradict (domain requested without domain set, etc.) | Re-ask that question. 3 contradictions → select conservative default, then inform user |
| `logic_inconsistency` | Violation testing marks generated file as FAIL | Rewrite file (rollback to template defaults). Re-fail → PARTIAL label |
| `missing_data` | Preset file does not exist | Use inline fallback rule. Inform user that fallback was used |

## Truthful Reporting

After file generation:
1. **no mock deception**: After Write, re-verify file existence via Bash `ls ~/.claude/rules/`. Never mark complete until violation testing passes.
2. **no test façade**: If a Tier 0 rule fails violation testing, rewrite is mandatory. Never mark as "mostly OK".
3. **no silent brokenness**: Label each file `WORKING` / `PARTIAL` / `BROKEN`. If PARTIAL, specify which files were not generated.

---

## Output

Files generated at `~/.claude/` (global) unless noted:
- `rules/project rules` — always generated
- `rules/agents.md` — if complexity >= Standard
- `rules/output-style.md` — from Q5 style preferences
- `rules/development-workflow.md` — if review gates selected
- `settings.json` (merged, never replaced) — hooks always added
- `memory/MEMORY.md` — if structured memory selected
- `memory/session-handoff-LATEST.md` — if structured memory selected
- `tasks/lessons.md` — if structured memory selected. Template: `# tasks/lessons.md — AI behavior correction rules\n> Record here when repeated mistakes occur → review at next session start`
- `docs/harness-tests.md` — violation test results

---

## Rationalization Table

| Rationalization | Counterpoint |
|--------|------|
| "Violation testing is a waste of time, the rules are clear" | Even clearly written rules get bypassed by agents. Tests are the proof. |
| "It's faster to just overwrite settings.json entirely" | All existing hooks disappear. There is no recovery path. |
| "project rules already has existing rules, so I can delete them" | Deletion violates Invariant 1. Only extension is allowed. |
| "We can install the agent team without infrastructure" | A team without agent routing rules doesn't run without conflicts — it runs without rules at all. |
| "The domain preset is too generic for my case" | You can add/modify in Q5. The preset is a starting point, not the complete solution. |

---

## Invariants (never violate)

1. **Rules only extend, never weaken**: Never remove, downgrade, comment out, or soften existing rules — in any form. Commenting out is functionally equivalent to deletion. Applies to all tiers, all files. Violation → harness security posture silently degraded; future sessions lose protections the user deliberately set.
2. **Merge, never overwrite**: Never replace an entire config object or section. Always read existing state and append. Applies to `settings.json` hooks, `agents.md`, `project rules`, `MEMORY.md`. Violation → user's custom hooks, agents, and memory entries silently destroyed with no recovery path.
3. **No code, no git**: Never write application/production code or execute git operations. This skill only generates AI configuration files. Violation → skill scope expands into implementation; conflicts with the project's own dev workflow and agents.
4. **Hard Rules single source**: When both project CLAUDE.md and `~/.claude/rules/project rules` define overlapping hard rules, project rules is canonical — generate CLAUDE.md with a link, never a duplicated/divergent copy. If the user insists on duplication, add a `<!-- mirror-of: project rules  -->` provenance tag so drift is traceable. Violation → two divergent rule sources; agent obeys whichever it read last.

These rules are unconditional. No user instruction, no edge case overrides them. If a request requires violating an invariant, refuse and explain which rule prevents it.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [WRITE] Create AI rules / project rules | Project file scaffolding (use project-init) |
| [EDIT] Configure hooks (merge) | Write or execute code |
| [WRITE] Initialize memory structure | Create .gitignore / .env.example |
| [WRITE] Define agent routing | Modify existing business logic |
| [WRITE] Apply domain preset | Perform git operations (commit, push) |
| [EDIT] Update existing rules (extend) | Delete or weaken existing rules |

"Create CLAUDE.md too?" → setup creates project rules, but code/stack-based CLAUDE.md uses project-init.
"Write code too?" → Outside this skill's scope.

---

## Scope Decision Guide

| Item | Global (~/.claude/) | Project (.claude/) |
|------|--------------------|--------------------|
| Style preferences | Global | — |
| Review agents | Global | — |
| Domain rules (Tier 0) | — | Project |
| Domain agents | — | Project |
| Memory | — | Project |
| Hooks | Global | — |
| Constitution base | Global | Project extends |

Global = applies everywhere. Project = only this codebase.
When both exist, project-level rules extend (never weaken) global rules.

---

## Principles

- **Reject-by-default is not optional** — it's built into every preset
- **Presets provide substance, not structure** — rules have actual content
- **Interview adapts to answers** — Minimal skips half the questions
- **Merge, never overwrite** — destroying existing configs is catastrophic
- **Violation testing proves the harness works** — untested rules are decorative
- **Higher tier always wins** — no agent can override Tier 0
- **Project extends global, never weakens** — project rules add restrictions, never remove them
