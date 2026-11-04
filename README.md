🌐 **English** | [한국어](docs/README.ko.md) | [日本語](docs/README.ja.md) | [中文](docs/README.zh.md) | [Español](docs/README.es.md)

# sovereign-skills v6.6.0

22 skills for the full Claude Code project lifecycle — from setup to daily workflow to code review to session management to governance. Each skill is useful standalone; the full sequence covers everything.

> **What changed in v6.6.0:** 20 of the 22 skills updated. `eval-leakage-audit` grows from 28 to 31 patterns (trivial-cue baseline, per-condition grader error in A-vs-B comparisons, undisclosed fallback scoring). `skill-trigger-auditor` scores trigger tests per split (tuning / heldout / review / real). Two new helper scripts with tests: `doc-drift/scripts/stale_numbers.py` (counts and versions in docs that no longer match the files) and `pre-push/scripts/share_record.py` (per-class counts of e-mails, home paths and key-shaped strings in what a public push carries, recorded without values). `integration-intake` checks how to leave a connector or memory provider before you adopt it. Fixes: `pre-push` no longer reads font URLs such as `family=…:wght@400` as a password in a connection string; `project-check` detects GitHub fine-grained tokens and uses the larger size class when file count and LOC disagree; `session-start` runs its health check even when the rest is skipped. See [CHANGELOG.md](CHANGELOG.md).

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

**Governance & audits (as needed):**
```
/integration-intake →  before adopting an external skill/agent/rule/plugin — 5-item screening gate
/full-audit         →  exhaustive area audit (codebase/docs/skills/memory/config) with a coverage map
/clean-room         →  when a task mixes safety-adjacent material with genuinely safe work
/eval-leakage-audit →  before trusting an eval/metric/holdout — check for circular self-confirmation
/doc-drift          →  audit loaded context (CLAUDE.md/MEMORY.md/skills) for outdated/contradictory wording
/ssot-audit         →  one fact in many files — find the source of truth, then consolidate
```

**If you write your own skills:**
```
/skill-trigger-auditor →  before changing a skill description — catch routing collisions and misfires
/skill-ops             →  snapshot/rollback a skill before editing, check which skills are actually used
/project-overview      →  one status map across several projects
```

---

## Skills

### Setup Phase

| Skill | What it does |
|-------|-------------|
| [project-init](project-init/) | Interview-based project scaffolding — generates CLAUDE.md, ROADMAP, .gitignore, and .env.example from decisions, not templates |
| [setup](setup/) | Claude Code infrastructure and agent team — rules, hooks, memory, routing, and agent installation in one guided flow |

### Daily Workflow

| Skill | What it does |
|-------|-------------|
| [scope](scope/) | Define what's IN, what's OUT, and exit criteria before implementation. Quick mode (3 questions) or Full mode (layered spec). Full mode ships `coverage_check.py` (requirement ↔ task check) |
| [freeze](freeze/) | Declare the editable zone — everything outside is frozen. Prevents scope creep during implementation |
| [goal-lock](goal-lock/) | Agent discipline engine — locks the goal, enforces PLAN→DO→VERIFY→FINALIZE→OUTPUT loop, detects 16 success masquerading patterns |
| [pre-push](pre-push/) | Mandatory pre-push pipeline — secrets scan (14 patterns), build/test, lint, parallel AI code review. Checks what the push actually carries (staged + outgoing commits). Blocks push on Critical/High findings. Pushes to a public mirror also get a value-free share record (`share_record.py`) |

### Perspective

| Skill | What it does |
|-------|-------------|
| [stepback](stepback/) | One-shot perspective reset — 1 abstract reframing question + 3 quick checks (scope drift, side effects, better approach) and a continue/stop verdict, in under 10 lines. Use anytime during work |
| [next-action](next-action/) | Reads handoff/git/lessons/STATE and proposes the top-3 next actions by impact. Proposes only, never executes. Use anytime |

### Session Management

| Skill | What it does |
|-------|-------------|
| [session-start](session-start/) | Load handoff from last session, review lessons, health check, output "ready" signal with priority action. Flags handoff items whose date has already passed |
| [session-checkpoint](session-checkpoint/) | Save session context before compact — handoff file, memory updates, lesson extraction, reflexion (what went wrong, what to do differently). Keeps future-dated items in a separate "Scheduled checks" list |

### Code Review

| Skill | What it does |
|-------|-------------|
| [code-autopsy](code-autopsy/) | 12Q quantified code review (v7.3) — 4-axis scoring (Security/Stability/Robustness/Operability), severity anchors, deployment verdict (SHIP/FIX/RISKY/BLOCK), factuality gate. Each finding is marked NEW or PRE-EXISTING and carries an evidence tier. Backed by empirical evidence (Johnson 2019, Parnas 1972). Also works as a standalone prompt in any LLM |

### Quality

| Skill | What it does |
|-------|-------------|
| [project-check](project-check/) | Scan existing project across 4 dimensions: Infrastructure, Security, Quality, Harness. Gaps ordered by severity |
| [collab-audit](collab-audit/) | 14-section AI collaboration audit — analyzes your actual work patterns (not surveys) to generate behavioral profile, blind spots, and growth direction. `extract_session_meta.py` builds the session data it needs |

### Operations

| Skill | What it does |
|-------|-------------|
| [skill-ops](skill-ops/) | Skill/agent ops hub — snapshot/rollback + usage health + invocation tracking + quality score, 4 modes. Ships `skill_snapshot.py` and `skill_health_bucket.py` |
| [project-overview](project-overview/) | Generates a deterministic cross-project status map from registered projects' session handoffs, and reports snapshots older than 7 days |
| [skill-trigger-auditor](skill-trigger-auditor/) | Audits skill, agent and slash-command routing for collisions and misfires, and gates description changes behind holdout trigger tests scored per split (tuning / heldout / review / real). Optional probe measures real Skill tool calls |

### Governance

| Skill | What it does |
|-------|-------------|
| [full-audit](full-audit/) | Exhaustive audit of an entire area (codebase/docs/skills/memory/config) — deterministic sweep + content review two-layer method, anti-false-positive kill-test, seeded canaries, persistent coverage map |
| [integration-intake](integration-intake/) | 5-item screening gate for adopting external patterns (skills/agents/rules/plugins/MCP) — redundancy check against your existing assets, a provenance/injection check for imported executable content, a license line, a ledger lookup of earlier verdicts, and an exit-path check for connectors and memory providers |
| [clean-room](clean-room/) | Carves safety-adjacent requests into a safe scope, executed by a genuinely isolated fresh-context subagent — adversarial verify pass + descope ledger |
| [eval-leakage-audit](eval-leakage-audit/) | Audits whether an eval/metric/holdout actually secures independent external ground truth vs circular self-confirmation — 31-pattern taxonomy, two golden cases. Read-only |
| [doc-drift](doc-drift/) | Audits the memory/docs Claude Code loads into context (CLAUDE.md/MEMORY.md/skills/agents/commands) for outdated claims, mutual contradictions, and risky/ambiguous wording — produces a prioritized fix list. `stale_numbers.py` flags counts and versions that no longer match |
| [ssot-audit](ssot-audit/) | Finds every copy of one fact, value or decision across a repo or notes folder, names the source of truth (read-only), and consolidates the duplicates only after you approve |

---

## Lifecycle Flow

```
┌─────────────────── Setup (once) ────────────────────┐
│  /project-init  →  /setup                           │
└─────────────────────────────────────────────────────┘
         ↓
┌──────────────────── Daily Loop ─────────────────────┐
│  /session-start                                     │
│       ↓                                             │
│  /scope → /freeze → /goal-lock → work               │
│       → /stepback (anytime) → /code-autopsy         │
│       → /pre-push                                   │
│       ↓                                             │
│  /session-checkpoint                                │
└─────────────────────────────────────────────────────┘
         ↓
┌───────────────────── On Demand ─────────────────────┐
│  /stepback         (perspective reset — anytime)    │
│  /next-action      (top-3 next actions from state)  │
│  /project-check    (health audit)                   │
│  /code-autopsy     (12Q code review — any LLM)      │
│  /collab-audit     (behavioral diagnostic)          │
│  /integration-intake (before adopting external work)│
│  /full-audit       (exhaustive area audit)          │
│  /clean-room       (safety-adjacent scope carve-out)│
│  /eval-leakage-audit (eval circular-logic check)    │
│  /doc-drift        (loaded-context drift audit)     │
│  /ssot-audit       (one fact, many copies)          │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────── Skill authors / multi-project ───────────┐
│  /skill-ops        (snapshot, rollback, usage)      │
│  /skill-trigger-auditor (routing collisions)        │
│  /project-overview (cross-project status map)       │
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

This repo is a Claude Code plugin marketplace named `sovereign-plugins`. Add it once, then install the skills you want. Inside a Claude Code session:

```
/plugin marketplace add AlexZio00/sovereign-skills
/plugin install goal-lock@sovereign-plugins
```

From a shell, the same two steps are:

```bash
claude plugin marketplace add AlexZio00/sovereign-skills
claude plugin install goal-lock@sovereign-plugins
```

In the desktop app, add the marketplace with one of the commands above, then pick skills from the plugin browser (**+** next to the prompt box → **Add plugins**). Third-party marketplaces do not auto-update by default. See the [official plugin install guide](https://code.claude.com/docs/en/plugins/install.md).

Each skill also includes standalone `.claude-plugin/plugin.json` metadata.

Skills are invoked by typing the trigger command (e.g., `/goal-lock`) in Claude Code. Claude reads the SKILL.md and follows the instructions.

### Option C: Codex

Codex discovers skills by scanning `.agents/skills/<skill-name>/SKILL.md` at the repository, user (`$HOME/.agents/skills`), admin, and system levels — no separate agent definition is required. Install a skill for Codex the same way you would for Claude Code, just under the `.agents/skills/` path:

```bash
# User-level (available in every project)
cp -r goal-lock ~/.agents/skills/goal-lock/

# Repo-level (this project only)
cp -r goal-lock .agents/skills/goal-lock/
```

Each skill also ships an **optional** `agents/openai.yaml` — UI/policy metadata for the ChatGPT desktop app (display name, description, icon/branding color, and the `allow_implicit_invocation` flag, `true` by default). It is not needed for Codex to find or run the skill; copy it along with `SKILL.md` only if you want that metadata applied:

```bash
cp -r goal-lock/agents .agents/skills/goal-lock/agents/
```

See the [official Codex skills documentation](https://learn.chatgpt.com/docs/build-skills) for the full discovery and metadata spec.

### Option D: Cursor / Other Agents

The SKILL.md content is universal markdown — it works with any LLM that reads markdown instructions. Copy `SKILL.md` into your agent's instruction path.

### Requirements

- **Claude Code**: CLI, desktop app, or web app ([claude.ai/code](https://claude.ai/code))
- **Codex**: OpenAI Codex — reads `SKILL.md` directly from `.agents/skills/`; `agents/openai.yaml` is optional UI metadata
- **Cursor / Other**: Any agent that reads markdown instructions
- Skills directory: `~/.claude/skills/` (Claude Code) or agent-specific path
- Python 3.9+ for the bundled helper scripts (`scripts/*.py` inside several skills). Skills call them as `${CLAUDE_SKILL_DIR}/scripts/<name>.py`, which Claude Code fills in with the skill's own folder; in other agents, replace it with the folder where you installed the skill. When a script cannot run, each skill says whether it falls back to a manual step or stops
- `pre-push` includes both `scan_secrets.py` (preferred) and `scan_secrets.pl` (Perl fallback). Optional: `ruff` (changed-line lint) and `gitleaks` (second secret-scan engine, warning only)

### Files the session skills read and write

`session-start`, `session-checkpoint`, `next-action`, `project-overview`, `skill-ops` and `collab-audit` share a few plain-text files: a session handoff, `tasks/lessons.md`, `~/.claude/STATE.md`, `memory/MEMORY.md`, a context log and an invocation log. None of them is required — a skill skips the step when the file is missing. Formats: [docs/FILE-CONVENTIONS.md](docs/FILE-CONVENTIONS.md).

### Optional agents and skills not included here

Some skills can hand work to agents or skills that this repo does **not** ship. Each mention in a SKILL.md is labeled optional and has a fallback, so nothing breaks without them:

| Name | Used by | Without it |
|------|---------|------------|
| `code-reviewer`, `security-reviewer`, `database-reviewer`, `build-error-resolver` | pre-push | `/setup` can generate these agents; otherwise pre-push runs an inline review (code-autopsy FAST MODE) and marks agent steps SKIPPED |
| `refactor-cleaner` | pre-push | step skipped |
| `doubt-reviewer` | scope (Full mode), goal-lock | a general-purpose subagent with an adversarial prompt, or SKIPPED in the report |
| `verification`, `brainstorming`, `check-harness`, `memory-dream`, `forge` | various see-also / routing notes | pointers only — the skill works without them |

---

## Agentic Design Patterns Coverage

The skills map to 18 agentic design patterns from the published catalogs ([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| Pattern | Implemented by | How |
|---------|---------------|-----|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | Full lifecycle chain |
| **Parallel Execution** | pre-push | Parallel AI code review agents |
| **Loop (Retry)** | goal-lock | VERIFY fail → PLAN re-entry, capped retries |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | Independent reviewer subagents (optional — see above) or an inline review; 12Q structured review; full-audit's Phase 2 fan-out reviewer pass; eval-leakage-audit critiques whether an eval secures independent ground truth vs circular self-confirmation |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE passes |
| **Coordinator/Router** | setup | Agent routing rules generation |
| **Plan-and-Execute** | goal-lock, scope | Plan reviewable before execution |
| **ReAct** | project-check | Investigate → score → recommend path |
| **Reflexion** | session-checkpoint | Phase 1.7: analyze failures → lessons for next session |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES, Critical/High blocks push; integration-intake's 5-item screening gate before adoption |
| **Custom Logic** | pre-push | Deterministic secrets scan (Python, Perl fallback) + AI review |
| **Event-Driven** | session-start | Triggered on session open, loads prior state |
| **Guardrails/Safety** | goal-lock, clean-room | 16 success masquerading patterns detected; clean-room isolates safety-adjacent scope into a carved-out subagent run |
| **Memory Management** | session-checkpoint, doc-drift | Handoff file + memory updates + lesson extraction; doc-drift audits the memory/docs loaded into context for outdated claims, contradictions, and risky wording |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE input sheet |
| **Step-Back Abstraction** | stepback | DeepMind step-back: concrete → abstract principle |
| **Prioritization** | next-action | Ranks candidate actions from handoff/git/lessons/STATE by impact |
| **Evaluation & Monitoring** | skill-ops, skill-trigger-auditor, project-overview | Usage health per skill; routing precision/recall on holdout prompts; stale-snapshot report across projects |

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
| `integration-intake` | `full-audit` | integration-intake gates a single external adoption decision; full-audit sweeps an entire area (including your existing skill/agent inventory) for drift or gaps |
| `full-audit` | `code-autopsy`, `project-check` | full-audit is a broader, multi-area sweep with a persistent coverage map; code-autopsy stays per-file/12Q, project-check stays a 4-dimension score |
| `clean-room` | `goal-lock` | clean-room fires when a task's scope mixes safety-adjacent material with safe work, mid-execution; goal-lock is the surrounding PLAN→DO→VERIFY loop it interrupts |
| `doc-drift` | `full-audit` | doc-drift audits only the memory/docs loaded into context (CLAUDE.md/MEMORY.md/skills/agents) for drift and contradictions; full-audit sweeps an entire area with a coverage map |
| `eval-leakage-audit` | `full-audit`, `code-autopsy` | eval-leakage-audit checks whether an eval/metric/holdout is circular (measurement integrity); full-audit and code-autopsy review code/areas, not the eval's independence |
| `ssot-audit` | `doc-drift`, `full-audit` | ssot-audit follows one fact across files and picks the source of truth; doc-drift checks loaded context for drift; full-audit sweeps a whole area |
| `skill-trigger-auditor` | `skill-ops`, `doc-drift` | skill-trigger-auditor checks whether skills fire on the right prompts; skill-ops tracks whether they are used and rolls them back; doc-drift checks their text for outdated claims |
| `project-check` | `setup`, `collab-audit` | project-check scores a repo's setup and lists gaps (setup fills them); collab-audit looks at how you work with the AI, not at the repo |

Diagram (arrows = "hands off to" / "informs"):

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (anytime, any stage)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (reads state, recommends)
                                   │
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift / ssot-audit
                 (on-demand governance & audits, any stage)
                                   │
         skill-ops / skill-trigger-auditor / project-overview
                 (for skill authors and multi-project setups)
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history (v3.0 → latest).

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. If you build a skill that fits the lifecycle, open a PR.

## Contact

DM [@AlexZio00](https://x.com/AlexZio00) for custom skill development.
