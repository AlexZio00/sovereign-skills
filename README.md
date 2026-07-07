🌐 **English** | [한국어](docs/README.ko.md) | [日本語](docs/README.ja.md) | [中文](docs/README.zh.md) | [Español](docs/README.es.md)

# sovereign-skills v6.3

14 skills for the full Claude Code project lifecycle — from setup to daily workflow to code review to session management. Each skill is useful standalone; the full sequence covers everything.

> **What changed in v6.3:** New: `skill-ops` (snapshot/rollback + usage health + invocation tracking hub), `next-action` (reads handoff/git/lessons/STATE and proposes the top-3 next actions), `project-overview` (deterministic cross-project status map). `code-autopsy` → v7.1 (deeper sub-checks per question), `pre-push` → v3.5 (9 supply-chain IOC patterns), `goal-lock`/`session-checkpoint`/`session-start`/`scope`/`stepback`/`freeze` all strengthened. `project-init` removed — absorbed into `setup`, which now combines infrastructure setup with interview-based project scaffolding in one guided flow. All prior skills gained `not_for` and `see_also` frontmatter for better discoverability.

---

## Quick Start

**New project (15 min):**
```
/setup              →  CLAUDE.md + ROADMAP + .gitignore/.env.example + rules/ + hooks + memory/ + agent routing + team
then daily:
  /session-start      at the start of every session
  /scope              before each feature (define IN/OUT/exit criteria)
  /freeze             before implementation (declare editable zone)
  /goal-lock          lock the goal, enforce PLAN→DO→VERIFY loop
  /stepback           anytime — zoom out, check direction, 10 lines
  /next-action        anytime — reads current state, proposes top-3 next actions
  /code-autopsy       12Q code review with severity scoring + verdict
  /pre-push           before each push (secrets scan + agent review)
  /session-checkpoint at the end of every session
```

**Existing project (5 min):**
```
/project-check      →  Score across 4 dimensions + gap list by severity
/collab-audit       →  14-section AI collaboration diagnostic from your work patterns
```

---

## Skills

### Setup Phase

| Skill | What it does |
|-------|-------------|
| [setup](setup/) | Combines infrastructure setup (rules, hooks, memory, routing, agent team) with interview-based project scaffolding (CLAUDE.md, ROADMAP, .gitignore, .env.example) into one guided flow |

### Daily Workflow

| Skill | What it does |
|-------|-------------|
| [scope](scope/) | Define what's IN, what's OUT, and exit criteria before implementation. Quick mode (3 questions) or Full mode (layered spec) |
| [freeze](freeze/) | Declare the editable zone — everything outside is frozen. Prevents scope creep during implementation |
| [goal-lock](goal-lock/) | Agent discipline engine — locks the goal, enforces PLAN→DO→VERIFY→FINALIZE→OUTPUT loop, detects 13 success masquerading patterns |
| [pre-push](pre-push/) | Mandatory pre-push pipeline — secrets scan (12 patterns), build/test, lint, parallel AI code review. Blocks push on Critical/High findings |

### Perspective

| Skill | What it does |
|-------|-------------|
| [stepback](stepback/) | **Updated.** One-shot perspective reset — generates 1 abstract reframing question + 3 quick checks (scope drift, side effects, better approach) in under 10 lines. Use anytime during work |
| [next-action](next-action/) | **New.** Reads handoff/git/lessons/STATE and proposes the top-3 next actions by impact. Proposes only, never executes. Use anytime |

### Session Management

| Skill | What it does |
|-------|-------------|
| [session-start](session-start/) | Load handoff from last session, review lessons, health check, output "ready" signal with priority action |
| [session-checkpoint](session-checkpoint/) | Save session context before compact — handoff file, memory updates, lesson extraction, reflexion (what went wrong, what to do differently) |

### Code Review

| Skill | What it does |
|-------|-------------|
| [code-autopsy](code-autopsy/) | **Updated v7.1.** 12Q quantified code review — 4-axis scoring (Security/Stability/Robustness/Operability), severity anchors, deployment verdict (SHIP/FIX/RISKY/BLOCK), factuality gate. Backed by empirical evidence (Johnson 2019, Parnas 1972). Also works as a standalone prompt in any LLM |

### Quality

| Skill | What it does |
|-------|-------------|
| [project-check](project-check/) | Scan existing project across 4 dimensions: Infrastructure, Security, Quality, Harness. Gaps ordered by severity |
| [collab-audit](collab-audit/) | 14-section AI collaboration audit — analyzes your actual work patterns (not surveys) to generate behavioral profile, blind spots, and growth direction |

### Operations

| Skill | What it does |
|-------|-------------|
| [skill-ops](skill-ops/) | **New.** Skill/agent ops hub — snapshot/rollback + usage health + invocation tracking, 3 modes |
| [project-overview](project-overview/) | **New.** Generates a deterministic cross-project status map from registered projects' session handoffs |

---

## Lifecycle Flow

```
┌─────────────────── Setup (once) ───────────────────┐
│  /setup                                             │
└────────────────────────────────────────────────────┘
         ↓
┌─────────────────── Daily Loop ─────────────────────┐
│  /session-start                                     │
│       ↓                                             │
│  /scope → /freeze → /goal-lock → work                │
│       → /stepback (anytime) → /code-autopsy           │
│       → /pre-push                                     │
│       ↓                                             │
│  /session-checkpoint                                │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────── On Demand ──────────────────────┐
│  /stepback         (perspective reset — anytime)      │
│  /project-check    (health audit)                    │
│  /code-autopsy     (12Q code review — any LLM)       │
│  /collab-audit     (behavioral diagnostic)           │
└─────────────────────────────────────────────────────┘
```

---

## Installation

### Option A: Copy skills (simplest)

Each skill is a standalone directory with a `SKILL.md` file. Copy the ones you want:

```bash
# Install all skills
git clone https://github.com/AlexZio00/sovereign-skills.git
cd sovereign-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# Or install one skill
cp -r goal-lock ~/.claude/skills/
```

### Option B: Marketplace (sovereign-plugins)

This repo is a Claude Code marketplace. Register it once and browse/install skills:

```bash
# Add sovereign-plugins marketplace in Claude Code
# Settings → Plugins → Add Marketplace → https://github.com/AlexZio00/sovereign-skills.git
```

Each skill also includes standalone `.claude-plugin/plugin.json` metadata.

Skills are invoked by typing the trigger command (e.g., `/goal-lock`) in Claude Code. Claude reads the SKILL.md and follows the instructions.

### Option C: Codex / Cursor (npx)

Each skill includes `agents/openai.yaml` for Codex compatibility:

```bash
# Install a skill for Codex
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent codex -g -y

# Install a skill for Cursor
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent cursor -g -y

# Install a skill for Claude Code (alternative to Option A)
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent claude-code -g -y
```

The SKILL.md content is universal — it works with any LLM that reads markdown instructions.

### Requirements

- **Claude Code**: CLI, desktop app, or web app ([claude.ai/code](https://claude.ai/code))
- **Codex**: OpenAI Codex with `npx skills` support
- **Cursor**: Cursor IDE with skill plugin support
- Skills directory: `~/.claude/skills/` (Claude Code) or agent-specific path
- `pre-push` requires Perl (for `scan_secrets.pl` — included)

---

## Agentic Design Patterns Coverage

These 12 of the 14 skills (the original lifecycle set — the v6.3 operations additions aren't mapped here yet) implement 17 of the 25 known agentic design patterns ([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| Pattern | Implemented by | How |
|---------|---------------|-----|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | Full lifecycle chain |
| **Parallel Execution** | pre-push | Parallel AI code review agents |
| **Loop (Retry)** | goal-lock | VERIFY fail → PLAN re-entry, capped retries |
| **Review & Critique** | pre-push, code-autopsy | Independent code-reviewer + security-reviewer; 12Q structured review |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE passes |
| **Coordinator/Router** | setup | Agent routing rules generation |
| **Plan-and-Execute** | goal-lock, scope | Plan reviewable before execution |
| **ReAct** | project-check | Investigate → score → recommend path |
| **Reflexion** | session-checkpoint | Phase 1.7: analyze failures → lessons for next session |
| **Human-in-the-Loop** | goal-lock, pre-push | STOP RULES, Critical/High blocks push |
| **Custom Logic** | pre-push | Deterministic secrets scan (Perl) + AI review |
| **Event-Driven** | session-start | Triggered on session open, loads prior state |
| **Guardrails/Safety** | goal-lock | 13 success masquerading patterns detected |
| **Memory Management** | session-checkpoint | Handoff file + memory updates + lesson extraction |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE input sheet |
| **Step-Back Abstraction** | stepback | DeepMind step-back: concrete → abstract principle |

---

## Design Principles

1. **Interview over template** — Skills ask questions and generate filled content, not empty skeletons
2. **Verification over trust** — DONE EVIDENCE must be executed, not assumed. "It should pass" is not verification
3. **Scope before code** — Define IN/OUT/exit criteria before touching files. Freeze what you're not changing
4. **Honest reporting** — WORKING / PARTIAL / BROKEN labels. No silent brokenness, no mock deception
5. **Session continuity** — Start with handoff, end with checkpoint. Context survives across sessions

---

## How Skills Connect

Skills declare relationships via `see_also` (related) and `not_for`
(misuse guardrails) in their frontmatter. Key relationships:

| Skill | Connects to | Relationship |
|-------|-------------|---------------|
| `scope` | `goal-lock`, `freeze` | scope defines what to build; freeze locks the editable zone; goal-lock enforces the execution loop |
| `freeze` | `scope`, `goal-lock` | freeze is the manual zone-lock companion to scope's planning and goal-lock's loop enforcement |
| `goal-lock` | `scope`, `freeze` | goal-lock is the execution-time discipline layer that scope/freeze set boundaries for |
| `stepback` | `next-action` | stepback checks direction ("am I solving the right problem"), next-action recommends what to do ("what's next by impact") |
| `next-action` | `session-start`, `stepback` | next-action reads current state for recommendations; session-start restores prior-session state |
| `session-start` | `session-checkpoint` | lifecycle pair — open and close a session |
| `session-checkpoint` | `session-start`, `setup` | closes a session; setup opens a new project |
| `code-autopsy` | `pre-push` | code-autopsy is a deep, on-demand 12Q review; pre-push runs a faster automated pipeline before every push |
| `skill-ops` | `project-overview` | skill-ops manages skill/agent lifecycle (snapshot/rollback/usage); project-overview aggregates status across multiple projects |

Diagram (arrows = "hands off to" / "informs"):

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (anytime, any stage)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (reads state, recommends)
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history (v3.0 → v6.3).

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. If you build a skill that fits the lifecycle, open a PR.

## Contact

DM [@AlexZio00](https://x.com/AlexZio00) for custom skill development.
