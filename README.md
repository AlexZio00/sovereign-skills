🌐 **English** | [한국어](docs/README.ko.md) | [日本語](docs/README.ja.md) | [中文](docs/README.zh.md) | [Español](docs/README.es.md)

# claude-code-skills v6.0

10 skills for the full Claude Code project lifecycle — from setup to daily workflow to session management. Each skill is useful standalone; the full sequence covers everything.

> **What changed in v6.0:** Consolidated from 13 to 10 skills. `harness-init` + `team-init` merged into `setup`. `brief` + `adr` merged into `scope`. `retro` absorbed into `session-checkpoint`. `token-audit` removed (use `npx ccusage` CLI). New: `goal-lock` — agent discipline engine that prevents scope drift and success masquerading.

---

## Quick Start

**New project (15 min):**
```
/project-init       →  CLAUDE.md + ROADMAP + .gitignore + .env.example
/setup              →  rules/ + hooks + memory/ + agent routing + team
then daily:
  /session-start      at the start of every session
  /scope              before each feature (define IN/OUT/exit criteria)
  /freeze             before implementation (declare editable zone)
  /goal-lock          lock the goal, enforce PLAN→DO→VERIFY loop
  /pre-push           before each push (secrets scan + agent review)
  /session-checkpoint at the end of every session
```

**Existing project (5 min):**
```
/project-check      →  Score across 4 dimensions + gap list by severity
/collab-audit       →  13-section AI collaboration diagnostic from your work patterns
```

---

## Skills

### Setup Phase

| Skill | What it does |
|-------|-------------|
| [project-init](project-init/) | Interview-based project scaffolding — generates CLAUDE.md, ROADMAP, .gitignore, .env.example from decisions, not templates |
| [setup](setup/) | Claude Code infrastructure + agent team — rules, hooks, memory, routing, and agent installation in one guided flow |

### Daily Workflow

| Skill | What it does |
|-------|-------------|
| [scope](scope/) | Define what's IN, what's OUT, and exit criteria before implementation. Quick mode (3 questions) or Full mode (layered spec) |
| [freeze](freeze/) | Declare the editable zone — everything outside is frozen. Prevents scope creep during implementation |
| [goal-lock](goal-lock/) | **New.** Agent discipline engine — locks the goal, enforces PLAN→DO→VERIFY→FINALIZE→OUTPUT loop, detects 11 success masquerading patterns |
| [pre-push](pre-push/) | Mandatory pre-push pipeline — secrets scan (12 patterns), build/test, lint, parallel AI code review. Blocks push on Critical/High findings |

### Session Management

| Skill | What it does |
|-------|-------------|
| [session-start](session-start/) | Load handoff from last session, review lessons, health check, output "ready" signal with priority action |
| [session-checkpoint](session-checkpoint/) | Save session context before compact — handoff file, memory updates, lesson extraction, reflexion (what went wrong, what to do differently) |

### Quality

| Skill | What it does |
|-------|-------------|
| [project-check](project-check/) | Scan existing project across 4 dimensions: Infrastructure, Security, Quality, Harness. Gaps ordered by severity |
| [collab-audit](collab-audit/) | 13-section AI collaboration audit — analyzes your actual work patterns (not surveys) to generate behavioral profile, blind spots, and growth direction |

---

## Lifecycle Flow

```
┌─────────────────── Setup (once) ───────────────────┐
│  /project-init  →  /setup                          │
└────────────────────────────────────────────────────┘
         ↓
┌─────────────────── Daily Loop ─────────────────────┐
│  /session-start                                     │
│       ↓                                             │
│  /scope → /freeze → /goal-lock → work → /pre-push  │
│       ↓                                             │
│  /session-checkpoint                                │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────── On Demand ──────────────────────┐
│  /project-check    (health audit)                   │
│  /collab-audit     (behavioral diagnostic)          │
└─────────────────────────────────────────────────────┘
```

---

## Installation

### Option A: Copy skills (simplest)

Each skill is a standalone directory with a `SKILL.md` file. Copy the ones you want:

```bash
# Install all skills
git clone https://github.com/AlexZio00/claude-code-skills.git
cd claude-code-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# Or install one skill
cp -r goal-lock ~/.claude/skills/
```

### Option B: Plugin (marketplace-ready)

Each skill includes `.claude-plugin/plugin.json` metadata. If your marketplace supports git-based plugins, point it to this repo.

Skills are invoked by typing the trigger command (e.g., `/goal-lock`) in Claude Code. Claude reads the SKILL.md and follows the instructions.

### Requirements

- [Claude Code](https://claude.ai/code) CLI, desktop app, or web app (claude.ai/code)
- Skills directory: `~/.claude/skills/` (created automatically by Claude Code)
- `pre-push` requires Perl (for `scan_secrets.pl` — included)

---

## What's New in v6.0

### Added
- **goal-lock** — Agent discipline engine with PLAN→DO→VERIFY→FINALIZE→OUTPUT loop. Detects 11 success masquerading patterns (test deletion, mock wrapping, threshold relaxation, etc.). Quick mode (3 fields) for small changes, Full mode (7 fields) for everything else.

### Merged
- `harness-init` + `team-init` → **setup** — Infrastructure and agent team in one flow
- `brief` + `adr` → **scope** — Scope definition with ADR capability built in
- `retro` → **session-checkpoint** — Retrospection is now Phase 1.7 Reflexion inside session-checkpoint

### Removed
- `token-audit` — Use `npx ccusage` directly, or build a ccusage skill from the pattern
- `adr` (standalone) — Absorbed into scope
- `retro` (standalone) — Absorbed into session-checkpoint

### Upgraded
- All skills: Dominant Variable, Key Assumptions, Error Recovery, Safety Layers added
- All skills: Scope Boundary with action tags ([READ]/[WRITE]/[BASH]/[AGENT])
- `session-checkpoint`: Memento CoT compression, Reflexion, Invocation logging
- `pre-push`: Large diff deterministic bundling, Discard If conditions
- `collab-audit`: Anti-pattern flags, Key Assumptions

---

## Agentic Design Patterns Coverage

These 10 skills implement 15 of the 25 known agentic design patterns ([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| Pattern | Implemented by | How |
|---------|---------------|-----|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | Full lifecycle chain |
| **Parallel Execution** | pre-push | Parallel AI code review agents |
| **Loop (Retry)** | goal-lock | VERIFY fail → PLAN re-entry, capped retries |
| **Review & Critique** | pre-push | Independent code-reviewer + security-reviewer |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE passes |
| **Coordinator/Router** | setup | Agent routing rules generation |
| **Plan-and-Execute** | goal-lock, scope | Plan reviewable before execution |
| **ReAct** | project-check | Investigate → score → recommend path |
| **Reflexion** | session-checkpoint | Phase 1.7: analyze failures → lessons for next session |
| **Human-in-the-Loop** | goal-lock, pre-push | STOP RULES, Critical/High blocks push |
| **Custom Logic** | pre-push | Deterministic secrets scan (Perl) + AI review |
| **Event-Driven** | session-start | Triggered on session open, loads prior state |
| **Guardrails/Safety** | goal-lock | 11 success masquerading patterns detected |
| **Memory Management** | session-checkpoint | Handoff file + memory updates + lesson extraction |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE input sheet |

---

## Design Principles

1. **Interview over template** — Skills ask questions and generate filled content, not empty skeletons
2. **Verification over trust** — DONE EVIDENCE must be executed, not assumed. "It should pass" is not verification
3. **Scope before code** — Define IN/OUT/exit criteria before touching files. Freeze what you're not changing
4. **Honest reporting** — WORKING / PARTIAL / BROKEN labels. No silent brokenness, no mock deception
5. **Session continuity** — Start with handoff, end with checkpoint. Context survives across sessions

---

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. If you build a skill that fits the lifecycle, open a PR.

## Contact

DM [@AlexZio00](https://x.com/AlexZio00) for custom skill development.
