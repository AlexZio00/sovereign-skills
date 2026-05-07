# claude-code-skills v4.6

Audit what's broken. Scaffold what's missing. Wire the AI. Assemble the team. Lock scope. Record decisions. Open sessions right. Close sessions right. Ship with confidence. Diagnose how you work.

> **Scope:** The full lifecycle pipeline for Claude Code projects — from health check to daily push gate, session management, and an AI collaboration audit that turns your own work patterns into a diagnostic.
> Ten skills that build on each other. Each one is useful standalone; the full sequence covers setup to daily workflow to session lifecycle.

---

## Quick Start

**New project (15 min):**
```
/project-init    →  CLAUDE.md + ROADMAP + .gitignore + .env.example
/harness-init    →  rules/ + hooks + memory/ + agent routing
/team-init       →  orchestrator + reviewers + implementers
then:
  /session-start     at the start of every session
  /brief             before each feature
  /adr               after key design decisions
  /pre-push          before each push
  /session-checkpoint  at the end of every session
```

**Existing project (5 min):**
```
/project-check   →  Score N/10 + gap list ordered by severity
  gaps found     →  /project-init (Update mode) + /harness-init + /team-init
  score ≥ 8      →  fix ⚠ items only
then: /session-start + /session-checkpoint as daily session bookends
```

**Already set up, just want the daily loop:**
```
/session-start      →  load handoff, flag lessons, ready signal
/brief              →  before starting any feature
/adr                →  after any non-obvious design choice
/pre-push           →  before every git push
/session-checkpoint →  at session end, before /compact
/collab-audit       →  monthly to see what patterns have shifted
```

---

## Skills

### Project Setup

---

#### `/project-check` — Existing Project Health Scan

Read-only audit of an existing project across four dimensions: Infrastructure, Security, Quality, and Harness. Surfaces all gaps ordered by severity with a Score out of 10.

**What it checks:**
- **Security** (always first): hardcoded secrets, API keys, `.env` not in `.gitignore`
- **Infrastructure**: `CLAUDE.md`, `Hard Rules`, `Secrets Policy`, `ROADMAP`, `.gitignore`, `.env.example`, `docs/decisions/`
- **Quality**: test/source file ratio, debug remnants, open work markers (TODO/FIXME)
- **Harness**: `ai-constitution.md`, `agents.md`, hooks, installed agents, orchestrator type, `tasks/lessons.md`, SubagentStop hook

**Why it matters:**
Most projects have gaps they don't know about — missing Hard Rules, hardcoded credentials buried in a config, no test infrastructure, or a harness that was never wired up. This skill surfaces all of it in one scan before you make things worse.

**Scale-aware:** A 5-file script won't fail for missing ROADMAP. Warnings are calibrated to project size.

**In production:** Run before each sprint on a 200+ file codebase. Consistently surfaces: coverage gaps in new modules, missing .env.example entries, stale docs after refactors.

---

#### `/project-init` — New Project Setup Interview

Conversational interview that generates `CLAUDE.md` + `DEVELOPMENT_ROADMAP.md` before you write a single line of code.

**What it does:**
- Asks 8 focused questions (one at a time) to lock in stack, data layer, deployment, AI/LLM strategy, and Hard Rules
- Generates a `CLAUDE.md` with Hard Rules, Secrets Policy, and Dev Conventions tailored to your project
- Outputs a Phase-structured `DEVELOPMENT_ROADMAP.md`
- Generates `.gitignore` and `.env.example` matched to your stack
- Generates `docs/decisions/README.md` for Architecture Decision Records (if scope > 1 month)
- Suggests the right folder structure for your language (Python, TypeScript, Java/Kotlin, Go, Rust, Swift)

**Why it matters:**
Most projects skip the "invariants first" step. By the time you add Hard Rules, the codebase already violates them. This skill forces the conversation upfront.

**Supports:** Python · TypeScript (Next.js / API) · Java · Kotlin (Spring Boot / Android) · Go · Rust · Swift

**In production:** Initialized before the first line of domain code. The CLAUDE.md and .env.example structure generated here survived 4 months and 99K LOC with minimal changes.

---

#### `/harness-init` — Claude Code Agent Infrastructure Setup

Sets up the full Claude Code harness layer — rules, hooks, memory, agent routing — from a 6-question interview.

**What it does:**
- Determines agent complexity level (minimal → orchestrated multi-agent)
- Configures review gates (code review, security, verification)
- Sets up memory strategy (session-only → structured with handoff files)
- Generates lifecycle hooks (SessionStart, PreCompact, Stop)
- Creates tiered rule hierarchy (immutable hard rules → style preferences)
- Runs violation testing on generated rules before finalizing

**What it generates:**
```
~/.claude/
├── rules/
│   ├── ai-constitution.md       # Tier 0 — immutable rules
│   ├── agents.md                # agent routing & priorities
│   ├── output-style.md          # response formatting
│   └── development-workflow.md  # review gate pipeline
├── settings.json                # hooks (merged, not overwritten)
│                                # includes SessionStart, PreCompact, Stop, SubagentStop
└── projects/[project]/
    └── memory/
        ├── MEMORY.md
        ├── session-handoff-LATEST.md
        └── tasks/lessons.md     # AI behavior correction log (Boris Cherny pattern)
```

**Why it matters:**
The harness layer determines how productive every Claude Code session will be. Building it manually takes weeks of trial-and-error. This skill captures that experience in a 5-minute conversation.

**Use this AFTER `/project-init`** — project-init scaffolds the codebase, harness-init scaffolds the AI orchestration layer on top.

**In production:** The project running on this infrastructure: 3 daily scheduled jobs, a monitoring bot, a multi-tab analytics dashboard, and a 12-agent pipeline — all coordinated through the rules/skills/agents structure harness-init establishes.

---

#### `/team-init` — Agent Team Assembly

Generates a complete coding team — orchestrator, reviewers, implementers — from a 3-question interview.

**What it does:**
- Determines team size (Solo 3 agents / Standard 6 / Full 9)
- Loads domain-specific review checks (Trading, Web, CLI, Data/ML, General)
- Generates an **orchestrator** with drift detection and correction loop
- Creates only missing agents — existing ones stay untouched
- Updates `agents.md` routing table (merged, not replaced)

**What it generates:**
```
~/.claude/agents/
├── orchestrator.md          # plan tracking + drift detection + gate enforcement
├── code-reviewer.md         # domain-aware review (if not exists)
├── verification.md          # completion checklist (if not exists)
├── brainstorming.md         # design-first gate (Standard+)
├── writing-plans.md         # atomic task planning (Standard+)
├── build-error-resolver.md  # build/type fixes (Standard+)
├── subagent-dev.md          # parallel implementation (Full)
├── systematic-debugging.md  # root-cause analysis (Full)
└── security-reviewer.md     # OWASP + secrets (Full)
```

**Why it matters:**
The orchestrator's correction loop catches implementation drift automatically — when code diverges from the plan, it corrects twice before escalating to you. Without it, you're manually comparing every subagent's output against the spec.

**Use this AFTER `/harness-init`** — harness-init sets the rules, team-init assembles the agents that work within those rules.

**In production:** Bootstrapped a 12-agent pipeline with specialized roles across data, analysis, alerting, and reporting. The AGENTS.md files generated here are still the source of truth after 4 months.

---

### Daily Workflow

---

#### `/brief` — Scope Locking Before Implementation

Converts a vague feature idea into a locked brief before any code is written. Forces explicit scope OUT before implementation starts.

**What it does:**
- Asks at most 3 clarifying questions, then generates the brief
- Produces: Goal / Scope IN / **Scope OUT** (mandatory, min 2 items) / Constraints / Exit Criteria / Risk Flags
- Scope OUT items must be plausible extensions someone would suggest — not far-fetched exclusions
- Exit Criteria require "observable action → measurable result" format. Vague criteria are auto-rejected and rewritten
- Saves to `BRIEF.md` only after explicit approval

**Why Scope OUT is mandatory:**
People specify what to build but rarely specify what NOT to build. The skill's core value is forcing that conversation upfront.

**Discard if:** bug fix, single-file change, or a spec is already written.

**In production:** Used before every feature addition on a complex multi-agent codebase. Has prevented at least 3 cases of "built the right thing wrong" by forcing non-goals and definition-of-done up front.

---

#### `/adr` — Architecture Decision Record

Records a design or architecture decision with its context, choice, alternatives rejected, and consequences. Prevents re-litigating settled decisions and keeps future AI sessions aware of constraints not visible in code.

**What it does:**
- Captures: Context (the forcing function) / Decision / Alternatives Considered / Consequences / Override Conditions
- Asks at most one clarifying question — gaps are filled with `[inferred]` annotation
- Generates `docs/decisions/YYYY-MM-DD-<title>.md` after explicit approval
- Does not fabricate alternatives — if none were seriously considered, it says so

**Why it matters:**
Future sessions — and future team members — need to understand what alternatives existed and why they were rejected, not just what was chosen. An ADR without "why" is a changelog entry.

**Pair with `/brief`:**
`/brief` locks scope before implementation. `/adr` records the non-obvious technical choices made during or after. Brief → implement → `/adr` for the decisions that aren't obvious from the code.

**In production:** 10+ decisions documented — each capturing a tradeoff that wasn't obvious months later. Most valuable in retrospect: why certain safety constraints are architectural rather than conventional.

---

#### `/pre-push` — Pre-Push Quality Gate

Mandatory pipeline that runs automatically before every `git push`. Blocks on secrets, test failures, and lint errors. Surfaces code review findings before they land in the remote.

**What it does (8 steps):**

1. **Secrets scan** — runs `scan_secrets.pl` against staged diff only. Covers 12 patterns: AWS/GCP/Azure keys, private keys, connection string passwords, hardcoded credential assignments (quoted + unquoted YAML), platform tokens (GitHub 6 types, Slack, Stripe live), Dockerfile ENV secrets, Google/Gemini API keys, npm auth tokens, LLM provider keys (Anthropic/OpenAI/HuggingFace/Replicate/Groq), Azure Storage/SAS. Scans only `+` lines — never blocks a commit that *removes* a secret.

2. **Routing & remediation** — secrets found → BLOCK with per-pattern remediation instructions. Only `*.md` / `docs/**` changed → fast exit, skip remaining steps.

3. **Supply chain check** — lists all added dependencies from `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, etc. Flags misspelled or unfamiliar package names as potential typosquats. Runs `pip-audit` when Python requirement files changed (WARN-only, install: `pip install pip-audit`). Never blocks — warns only.

4. **Build & test** — language-aware, runs only what changed:
   - Python (`.py` changed + `pyproject.toml`/`setup.py`/`requirements.txt` present): `pytest -q`
   - Go (`.go` changed + `go.mod` present): `go test ./...`
   - JS/TS (`.ts`/`.tsx`/`.js`/`.jsx` changed + `package.json`): `npm run build` then `npm test`

5. **Lint gate** — direct lint first, AI lint second:
   - Python: `ruff check` (preferred) → `flake8` fallback
   - Go: `go vet ./...`
   - JS/TS: `eslint` (if config file present)
   - Then **quick-validator** (haiku) for type errors and logical issues static tools miss — skipped if diff < 50 lines

6. **Parallel AI review** — spawns applicable agents in one turn:
   - `code-reviewer` (sonnet) — always
   - `security-reviewer` (opus) — triggered by auth files, API routes, infra, dangerous patterns (`eval`, `exec`, `child_process`, `dangerouslySetInnerHTML`), or new packages
   - `database-reviewer` (sonnet) — triggered by migrations, SQL, `prisma/**`
   - `refactor-cleaner` (sonnet) — triggered when 10+ files changed

7. **Gate check** — Critical/High findings block push. Medium: fix if < 5 min or add `// TODO(security):`. Low: report only.

8. **Report & push** — structured summary with elapsed time per step. Executes `git push` only when all gates pass.

**Extra safeguards:**
- Pushes to `main`/`master` require explicit confirmation
- Test files (`__tests__/**`, `*.test.*`, `*.spec.*`) — secret findings downgraded to Medium
- Emergency override: user says "skip review" → pipeline bypassed with warning printed

**Installation note:** `scripts/scan_secrets.pl` must be co-located with `SKILL.md`. The scanner is called via `find ~/.claude -name "scan_secrets.pl"` so it works regardless of where you install the skill.

**In production:** Running on a 99K LOC Python project, 1,326 tests, 200+ files. Every push goes through this gate — catches credential leaks, dependency drift, and logic errors before they reach main. 4+ months in production.

---

### Session Management

---

#### `/session-start` — Session Open

Loads saved session state and produces a concrete starting point within 60 seconds of invoking.

**What it does:**
- Reads `memory/session-handoff-LATEST.md` (auto-loaded via frontmatter) — extracts Priority 1, open decisions, blockers, context notes
- Reads `tasks/lessons.md` — flags any correction rules relevant to today's work
- Spot-checks `memory/MEMORY.md` for 1–2 stale references (file paths, function names mentioned in handoff)
- Promotes any `[ref:N≥3]` items from `memory/context-log.md` to MEMORY.md

**Output format:**
```
## Session Ready
Priority 1: [concrete next action]
Priority 2: [if present]
Open decisions: [list or "none"]
Lessons flagged: [applicable rules or "none"]
Memory alerts: [stale refs or "none"]
```

**Auto-trigger (Triple Gate):** ≥5,000 tokens accumulated AND ≥3 tool calls AND ≥24h since last session → high-value context is at risk. Run this skill before starting new work.

**Dominant variable:** Does the handoff contain "what to do next" or "what was done"? If it reads like a completion log, it was written wrong — flag this before proceeding.

**Discard if:** first session on the project (no handoff file), user says "start fresh."

**In production:** Managing context across 50+ sessions on a 12-agent system. Past 200 files, loading the handoff takes under 60 seconds — without it, the same time goes to reconstructing "where was I."

---

#### `/session-checkpoint` — Session Close

Saves session state before context compaction, task switching, or ending a session. Five-phase pipeline.

**What it does:**
- **Phase 1**: Extracts what context compression could destroy — 9 categories: pending tasks, current state, session intent, key technical concepts, critical file snippets, active errors, important user messages, next steps, and problem-solving process
- **Phase 1.5 (Entity Extraction)**: Classifies session content into four types: permanent facts (→ MEMORY.md), episode entries (→ context-log.md with TTL), raw observations (→ lessons.md candidates), stale detections (→ immediate MEMORY.md update)
- **Phase 2**: Rewrites `memory/session-handoff-LATEST.md` — removes completed items, adds new items, forward-looking only (max 200 lines)
- **Phase 3**: Saves classified entities to their respective memory files
- **Phase 4**: Preservation checklist — 5 items, any NO blocks compact guidance
- **Phase 5**: Warns that `/compact` disables ALL tools during compression — state must be saved before compaction, not during. Then tells user to run `/compact`.

> **NO_TOOLS warning:** `/compact` runs with no tool access. Any state not written to disk before this phase is lost. Phases 2–3 are the save gates.

**TTL system for context log:**
- `ttl:permanent` — decisions, architecture changes
- `ttl:90d` — completions, plans, external events
- `ttl:30d` — temporary states, short-lived issues

**Why the handoff stays small:**
Completed items are deleted, not archived. Git history preserves them. A handoff that lists "what was done" is a changelog — not a starting point.

**Discard if:** no code changes and no open decisions this session. `/compact` is a Claude Code CLI built-in — this skill cannot call it directly.

**In production:** Running across 50+ sessions on a 12-agent codebase. The handoff file is the single artifact that survives `/compact` — every session that skips writing it costs the next session 15–20 minutes of reconstruction.

---

### Quality & Reflection

---

#### `/collab-audit` — AI Collaboration Audit

Analyzes your conversation history and work patterns across 13 sections to generate a behavioral diagnosis report. No surveys. Observation only.

**What it does:**
- Reads actual conversation history — message patterns, artifact production, decision style, delegation habits
- Profiles psychological tendencies (perfectionism, avoidance, context-switching, dependency patterns)
- Identifies blind spots and collaboration anti-patterns with specific evidence
- Delivers behavioral correction feedback integrated with the analysis

**Why it's bundled:**
Psychological analysis and behavioral feedback are intentionally combined. Separated, users read one and skip the other.

**Compare mode:**
```
/collab-audit compare    # diff latest two audits — shows what shifted
```

**Constraints:**
- Requires 2+ sessions or 100+ messages (or 1 high-density session: 50+ messages with substantial artifacts or deep technical dialogue)
- No self-report: does not ask you how you work — observes what you actually did
- Output saved to `~/.claude/collab-audits/YYYY-MM-DD.md`

**Why it matters:**
AI amplifies your existing work patterns — good and bad. Most people don't know which patterns are costing them until they see them documented with evidence.

**In production:** Run periodically on a project where Claude Code has touched 200+ files over 4 months. Catches pattern drift — where early architectural decisions get quietly undermined as scale grows.

---

## Installation

```bash
# macOS / Linux
SKILLS_DIR=~/.claude/skills

mkdir -p $SKILLS_DIR/{brief,adr,project-check,project-init,harness-init,team-init,pre-push/scripts,collab-audit,session-start,session-checkpoint}

cp brief/SKILL.md                $SKILLS_DIR/brief/SKILL.md
cp adr/SKILL.md                  $SKILLS_DIR/adr/SKILL.md
cp project-check/SKILL.md        $SKILLS_DIR/project-check/SKILL.md
cp project-init/SKILL.md         $SKILLS_DIR/project-init/SKILL.md
cp harness-init/SKILL.md         $SKILLS_DIR/harness-init/SKILL.md
cp team-init/SKILL.md            $SKILLS_DIR/team-init/SKILL.md
cp pre-push/SKILL.md             $SKILLS_DIR/pre-push/SKILL.md
cp pre-push/scripts/scan_secrets.pl $SKILLS_DIR/pre-push/scripts/scan_secrets.pl
cp collab-audit/SKILL.md         $SKILLS_DIR/collab-audit/SKILL.md
cp session-start/SKILL.md        $SKILLS_DIR/session-start/SKILL.md
cp session-checkpoint/SKILL.md   $SKILLS_DIR/session-checkpoint/SKILL.md
```

```bat
:: Windows
set SKILLS=%USERPROFILE%\.claude\skills
for %d in (brief adr project-check project-init harness-init team-init pre-push collab-audit session-start session-checkpoint) do mkdir "%SKILLS%\%d" 2>nul
for %d in (brief adr project-check project-init harness-init team-init pre-push collab-audit session-start session-checkpoint) do copy %d\SKILL.md "%SKILLS%\%d\SKILL.md"
mkdir "%SKILLS%\pre-push\scripts" 2>nul
copy pre-push\scripts\scan_secrets.pl "%SKILLS%\pre-push\scripts\scan_secrets.pl"
```

Invoke in any Claude Code session:

```
/brief                # lock scope before implementation
/adr                  # record a design decision (after it's made)
/project-check        # audit an existing project (read-only)
/project-init         # scaffold a new project
/harness-init         # set up Claude Code agent infrastructure
/team-init            # assemble your coding agent team
/pre-push             # run before git push
/collab-audit         # diagnose your AI collaboration patterns
/session-start        # open a session — load handoff + lessons
/session-checkpoint   # close a session — save state before /compact
```

---

## Recommended Flow

**Existing project — start here:**
```
/project-check → Score N/10 + gap list
  ├─ gaps found → /project-init (Update mode) + /harness-init + /team-init
  └─ score ≥ 8  → only fix the ⚠ items
then: session-start + session-checkpoint as daily bookends
```

**New project — start here:**
```
/project-init    → CLAUDE.md + ROADMAP + .gitignore + .env.example
/harness-init    → rules/ + hooks + memory/ + agent routing
/team-init       → orchestrator + code-reviewer + verification + ...
/project-check   → verify everything landed correctly
```

**Daily session loop:**
```
/session-start       → load context, flag lessons, ready signal
/brief               → before each feature (scope OUT mandatory)
  implement
/adr                 → after non-obvious design choices
/pre-push            → before every git push
/session-checkpoint  → at session end, before /compact
```

The ten skills map to the full project lifecycle:

| Phase | Category | Skill | Frequency | Benefit |
|-------|----------|-------|-----------|---------|
| Diagnose | Setup | `/project-check` | On-demand | Know exactly what's broken before you touch anything |
| Bootstrap | Setup | `/project-init` | Once | Hard Rules locked before the first line of code |
| Wire AI | Setup | `/harness-init` | Once | Every future session starts with full context |
| Build team | Setup | `/team-init` | Once | Implementation drift caught automatically |
| **Lock scope** | **Workflow** | **`/brief`** | **Before each feature** | **Scope OUT defined before code starts** |
| **Record decisions** | **Workflow** | **`/adr`** | **After key choices** | **Future sessions know why, not just what** |
| **Ship daily** | **Workflow** | **`/pre-push`** | **Every push** | **Secrets, tests, critical findings blocked before remote** |
| **Open session** | **Session** | **`/session-start`** | **Every session** | **Priority 1 in 60 seconds, lessons loaded** |
| **Close session** | **Session** | **`/session-checkpoint`** | **Every session** | **Nothing lost to context compression** |
| Reflect | Quality | `/collab-audit` | Periodic | Work pattern blind spots surfaced with evidence |

> **Standalone use:** Each skill works independently. `/pre-push` works on any project — it auto-detects the language and only runs relevant checks. `/session-start` and `/session-checkpoint` work on any project that has `memory/session-handoff-LATEST.md` (generated by `/harness-init`).

---

## When to Use Each Skill

| Skill | Use when… |
|-------|-----------|
| `/brief` | You're about to implement a feature and requirements feel open-ended. Also: when a previous feature grew mid-sprint — run brief before the next one. |
| `/adr` | A design decision was just made and it's not obvious from the code why. Also: when you find yourself explaining the same choice repeatedly to AI sessions. |
| `/project-check` | You inherited a repo and want to know the setup state. Or: run periodically when something keeps breaking at the infrastructure level. |
| `/project-init` | Starting a new codebase. Or: you have code but no `CLAUDE.md`, no `ROADMAP`, no `.gitignore`. |
| `/harness-init` | First Claude Code session on a project. Or: you keep re-explaining conventions at every session start. |
| `/team-init` | You want drift detection without reviewing every subagent output yourself. |
| `/pre-push` | Before every `git push`. Set it as a habit trigger — "I type `git push`, I run this first." |
| `/collab-audit` | After 2+ weeks of active use. Or: sessions are getting less productive and you can't pinpoint why. |
| `/session-start` | At the start of every session where prior work exists. Especially: after a break, after switching tasks, after a long session the day before. |
| `/session-checkpoint` | Before running `/compact`, switching major tasks, or ending a session. Whenever you want the next session to start with full context. |

---

## v4 Design Principles

Every skill in v4 encodes three things:

- **Dominant variable** — the single factor that most determines whether the skill output is useful. Named explicitly so you know what to optimize for.
- **Discard condition** — when NOT to use the skill. A skill that runs itself when it shouldn't is worse than useless.
- **Invariants with consequences** — rules that cannot be overridden, with explicit failure mode documented for each one.

**Added in v4.1 — Prompt rules are advisory. Physical constraints are mandatory:**

Four new patterns applied across all skills in v4.1:

- **`tools:` frontmatter** — read-only skills and agents now declare `tools: Read, Bash, Glob, Grep` (or similar) in frontmatter. Claude Code physically removes Edit/Write from the tool list. Prompt-level "don't modify files" can be rationalized away; tool absence cannot.
- **STATIC/DYNAMIC boundary** — each workflow step is tagged as static (cacheable project structure, query templates) or dynamic (user input, live data). Separating these tells Claude Code what to preserve across sessions vs. what to re-run.
- **MagicDocs pattern** — output files written by skills use `# MAGIC DOC: [title]` as their heading. Claude Code recognizes this and auto-updates the file content during conversations without being explicitly asked.
- **YOLO classifier** — read-only operations (`git diff`, `git status`, file reads) are explicitly marked as auto-approvable. Reduces permission prompts for operations with no side-effects.

**New in v4 — Session lifecycle as a first-class concern:**

The session open/close pair (`/session-start` + `/session-checkpoint`) addresses the single biggest productivity leak in AI-assisted development: context loss. Each session starts cold — you re-explain conventions, re-locate where you left off, and lose the first 10 minutes rebuilding mental model. The session lifecycle skills eliminate this by making handoff and context loading a structured habit rather than an afterthought.

**The memory layer (used by session skills):**

```
memory/MEMORY.md              ← permanent facts (file paths, architecture decisions)
memory/session-handoff-LATEST.md     ← current session incomplete items (forward-looking only)
memory/context-log.md         ← dated events with TTL (completions, plans, decisions)
tasks/lessons.md              ← AI behavior correction rules (Boris Cherny pattern)
```

Each file has a specific role. `/session-checkpoint` writes to all four. `/session-start` reads from three and writes to one (MEMORY.md, on stale detection only).

---

## Roadmap

- [x] `/project-check` — health scan for existing projects
- [x] `/project-init` — project scaffolding
- [x] `/harness-init` — agent infrastructure setup
- [x] `/team-init` — agent team assembly
- [x] `/pre-push` — pre-push quality gate (secrets + tests + lint + AI review)
- [x] `/collab-audit` — AI collaboration pattern diagnosis (13 sections, observation-only)
- [x] `/brief` — scope locking before implementation (Scope OUT mandatory, Exit Criteria action+result format)
- [x] `/adr` — architecture decision record (context mandatory, no fabricated alternatives, override conditions required)
- [x] `/session-start` — session open (load handoff + lessons + memory spot-check → ready signal)
- [x] `/session-checkpoint` — session close (entity extraction + handoff rewrite + memory save + preservation check)

---

## Changelog

### v4.7 — Pre-push resilience + session improvements + internal ref cleanup (2026-05-07)

**`pre-push`** upgraded to v3.2.0:

- **Agent failure recovery**: if a review agent times out or errors, retry once — still failing → report `⚠️ SKIPPED (agent unavailable — {agent})` in the push summary and continue. Never silently treat a failed agent as PASS.
- **Conflict resolution**: when agents give opposing verdicts on the same file — security-reviewer Critical + any non-critical → Critical wins (weakest-link principle). Fully opposing verdicts (one PASS, one Critical FAIL) → report both to user, do not push.
- Action tags added to Scope Boundary (`[BASH]`, `[AGENT]`).

**`session-checkpoint`** improvements:

- **Phase 1.5 ⑤ Snapshot Cleanup**: checks `~/.claude/.harness/snapshots/` for entries older than 90 days and notifies the user. Not auto-deleted — manual review required.
- **Phase 3 step 5**: `~/.claude/STATE.md` update — resolved blockers → remove row, completed PENDING → remove row, major milestones → add to change log. Skip if no state change.
- Phase 4 checklist: `□ STATE.md reviewed?` added.
- Safety Layers and Truthful Reporting sections added.

**`session-start`** improvements:

- **Phase 4.1 Selective Load**: tag-based MEMORY.md filtering. `<!-- #always -->` sections → load in full. `<!-- #on-demand -->` sections → extract headers as TOC only (Grep when needed). No tags → load in full (backward compatible). Reduces context load for large MEMORY.md files.

**All 10 skills**: removed internal framework references (`(L0 XIII/XIV/XV 상속)`, `(L0 II.7 상속)`, etc.) from Safety Layers and Truthful Reporting section headers. Behavior unchanged — labels removed only.

---

### v4.6 — Lessons.md confidence/decay metadata (2026-04-28)

Two session lifecycle skills upgraded to track lesson health over time, not just lesson content.

- **`session-checkpoint`**: Phase 1.5 ③ + Phase 3 step 3 — when adding a new entry to `tasks/lessons.md`, attach a metadata line `> conf: 0.5 · seen: today · obs: 1` below the header. On re-observation, increment `obs` and bump `conf` after thresholds (3/6/9, max 0.9). On violation + user correction, lower `conf` by 0.1 (min 0.3). Quarterly cleanup: `conf < 0.4 AND (today − seen) > 90 days` → move to `tasks/_archive/lessons-pre-YYYY-MM.md`.
- **`session-start`**: Phase 2 — utilize the `> conf · seen · obs` metadata to prioritize which lessons surface in the ready signal. `conf ≥ 0.7` shows rule body, `conf 0.5` title only, `conf < 0.5` TOC or skip. Lessons without v2 metadata are handled normally (backward compatible).

**Origin:** ECC [`continuous-learning-v2`](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2) (instinct + confidence scoring). Concept absorbed; the full package (homunculus directory + background Haiku agent + 6 slash commands) was not adopted — the metadata pattern transfers cleanly into existing `lessons.md` without new infrastructure dependencies.

### v4.5 — Safety Layers and Truthful Reporting (2026-04-27)

Five skills now include explicit safety and reporting contracts — Safety Layers document which actions are risky and what defense layers apply; Truthful Reporting defines what counts as a complete vs. partial result.

- **`pre-push`**: Python CVE scan via `pip-audit` added to Step 3 (WARN-only, never blocks). Preferred over osv-scanner for Python-native projects. Also adds **Safety Layers** mapping each push action to its reversibility tier, and **Truthful Reporting** clarifying what "READY TO PUSH" actually means.
- **`collab-audit`**, **`brief`**: **Truthful Reporting** — explicit criteria for what counts as a complete audit vs. inference-padded output; and what counts as a locked scope vs. a draft.
- **`harness-init`**, **`project-init`**: **Safety Layers** + **Truthful Reporting** — maps file-creation actions to reversibility tiers and defense layers. Prohibitions explicit: no `.env` generation, no `settings.json` overwrite.

### v4.4 — In production reference cases (2026-04-20)

All 10 SKILL.md files and README now include **"In production"** sections — concrete production context showing scale, duration, and what each skill actually catches in a real codebase. No new behavior changes; documentation only.

### v4.3 — Task-to-Skill Crystallization (2026-04-18)

- **Phase 1.6: Task-to-Skill Crystallization** (`session-checkpoint`): new phase detects repeated workflow signatures (Intent + Tool Sequence + Output Shape) and proposes promoting them into a new skill. Triggers: same signature ≥3 times within session, or `[ref:N]` ≥5 in `context-log.md`. Origin: GenericAgent crystallization pattern.
- **Invariant 4: Propose-only** (`session-checkpoint`): Phase 1.6 never authors the skill automatically — only suggests the candidate. User judgment required before promotion. Prevents one-off explorations from polluting the skill library.
- **Rationalization Table +2 entries** (`session-checkpoint`): closes two loopholes — "just auto-promote the repeated workflow" (Invariant 4 violation) and "signature is too trivial, skip it" (dismissing 3+ reps as trivial is measurement laziness → log to `[ref:N]` instead).
- **Non-trigger conditions** (`session-checkpoint`): explicit skip rules — one-off exploration, duplicate of an existing skill (scans `~/.claude/skills/*/SKILL.md`), or overly generic signatures that would collide with already-established skills.

### v4.2 — Handoff filename unification + bilingual triggers (2026-04-17)

- **Handoff file renamed** (`session-start`, `session-checkpoint`, `harness-init`, README): `memory/session-handoff.md` → `memory/session-handoff-LATEST.md`. Explicit `-LATEST` suffix prevents confusion when users also git-tag historical snapshots (`session-handoff-2026-04-07.md`, etc.). Breaking change — rename existing handoff files on upgrade.
- **Bilingual trigger keywords** (`session-start`, `session-checkpoint`): descriptions now include Korean triggers alongside English (`'세션 시작'`, `'체크포인트'`, `'핸드오프 저장'`, etc.) so both language prompts route correctly. Body content remains English.
- **Phase 3: Global State Check** (`session-start`): new phase reads `~/.claude/STATE.md` (cross-project blockers/decisions) so session-open surfaces global items that are resolvable in the current project. Skip if STATE.md missing.
- **checkpoint-compact removed**: functionality fully consolidated into `session-checkpoint`. If you had a separate `/checkpoint-compact` command bound, remap to `/session-checkpoint`.

### v4.1 — Physical constraints + Prompt architecture patterns (2026-04-16)

Four patterns from Claude Code internals applied across the full skill suite:

- **`tools:` frontmatter** (`project-check`): physical tool scope enforcement — read-only skills declare allowed tools in frontmatter. Edit/Write are absent from the tool list entirely, not just prohibited by prompt instruction.
- **STATIC/DYNAMIC boundary** (`brief`): project structure scan in Step 1 is explicitly marked as static/cacheable context. Steps 2–5 are dynamic. Reduces redundant re-scanning across sessions.
- **Triple Gate auto-trigger** (`session-start`): added auto-trigger signal — ≥5,000 tokens AND ≥3 tool calls AND ≥24h since last session → run session-start before new work. Prevents silent context loss.
- **NO_TOOLS warning + 9-item expansion** (`session-checkpoint`): Phase 1 extraction expanded to 9 items (was 5). Phase 5 now explicitly warns that `/compact` disables all tools — state must be written before compaction begins, not during.
- **YOLO classifier** (`pre-push`): read-only git ops (`git diff`, `git status`, `git log`) explicitly marked as auto-approvable without permission prompt. Write ops still gated.
- **Second-opinion review gate** (`harness-init`): generated harness now includes a multi-model review gate — routes high-stakes decisions to a stronger model for confirmation before finalizing.
- **MagicDocs** (`adr`, `collab-audit`): generated output files now use `# MAGIC DOC: [title]` heading. Claude Code auto-updates these files during conversations.

### v4.0 — Session lifecycle + Decision records (2026-04-13)
- Added `/session-start` — session open skill. Loads handoff + lessons, spot-checks memory, produces Priority 1 ready signal within 60 seconds. Pair with `/session-checkpoint`.
- Added `/session-checkpoint` — session close skill. 5-phase pipeline: deep extraction → entity classification (permanent facts / episode entries / lessons candidates / stale detection) → handoff rewrite → memory save → preservation checklist → compact guidance. TTL system: `ttl:permanent` | `ttl:90d` | `ttl:30d`.
- Added `/adr` — Architecture Decision Record. Records context (forcing function), decision, alternatives considered, consequences, and override conditions. Fabricated alternatives explicitly forbidden. Pairs with `/brief`.
- README restructured into 4 categories: Project Setup / Daily Workflow / Session Management / Quality & Reflection.

### v3.6 — Scope locking (2026-04-12)
- Added `/brief` — scope locking before implementation. Scope OUT mandatory (min 2 items, plausible extensions only). Exit Criteria require observable action + measurable result format — vague criteria auto-rejected. Conservative minimum scope floor: one complete user flow + one user-visible outcome. 7 invariants.

### v3.5 — Harness Engineering patterns (2026-04-12)
- `harness-init`: Added `tasks/lessons.md` generation + SubagentStop lifecycle hook to generated harness. SessionStart hook now loads lessons.md on session start.
- `project-check`: Added `tasks/lessons.md` and SubagentStop hook to Harness scan checklist.
- `collab-audit`: Section 8 context maturity Level 5 — `tasks/lessons.md` operation as meta-layer.
- **`tasks/lessons.md` pattern** (Boris Cherny, *Programming TypeScript*): Record repeated AI mistakes as correction rules on the spot → review at next session start. Separates behavior correction (lessons.md) from technical knowledge (MEMORY.md).
- **SubagentStop hook**: Logs agent completions with ID + transcript path for debugging multi-agent workflows.

### v3.4 — Defense structure upgrade (2026-04-11)
- All 6 skills: added **Rationalization Table** (common rationalization patterns + rebuttals)
- `pre-push`: added **Dominant variable**, **Discard if**, **Invariants with consequences**, **Scope Boundary** — format now consistent with the rest of the suite

### v3.3 — AI Collaboration Audit (2026-04-11)
- Added `/collab-audit` — 13-section behavioral diagnosis from conversation observation. Compare mode, gitignore protection, observation-only (no surveys).

### v3.2 — Orchestrator upgrade (2026-04-10)
- `team-init`: Advisor Strategy pattern added to Full orchestrator — consults opus advisor before user escalation, spot-check on sonnet after haiku pass

### v3.1 — Harness + project-check polish (2026-04-09)
- `project-check`: Anthropic key pattern, C/C++ file support, project-level agents scan
- `harness-init`: Smart Defaults, violation testing per Tier-0 rule (not 3 total), Memory Discipline unconditional label

### v3.0 — v3 rewrite (2026-04-08)
- Introduced `project-check` — read-only health scan, scale-aware, Security-first report
- Applied v3 patterns across all skills: **Dominant variable**, **Discard if**, Invariants with failure-mode consequences
- `pre-push` v3.0.0: `scan_secrets.pl` scanner (12 patterns), parallel AI review agents, language-aware test/lint detection

---

## References

- [ReS0421/coding-team-orchestrator](https://github.com/ReS0421/coding-team-orchestrator) — Several orchestration patterns in `/team-init` were adapted from this project: "Do Not Trust the Report" (spec reviewer reads code directly, not the implementer's claim), Final Integration Review (cross-task consistency check via `git diff BASE_SHA..HEAD`), and CRITICAL/IMPORTANT/MINOR severity tiers for the correction loop.
- [obra/superpowers](https://github.com/obra/superpowers) — writing-plans + subagent-driven-development patterns that influenced the planning pipeline.
- [Boris Cherny](https://github.com/bcherny) (*Programming TypeScript*, Meta Staff Engineer) — `tasks/lessons.md` behavior correction loop: record repeated mistakes as correction rules, review at session start. Separates behavior correction from technical memory.

---

## License

MIT
