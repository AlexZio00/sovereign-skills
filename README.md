🌐 **English** | [한국어](docs/README.ko.md) | [日本語](docs/README.ja.md) | [中文](docs/README.zh.md) | [Español](docs/README.es.md)

# sovereign-skills v6.5.11

20 skills for the full Claude Code project lifecycle — from setup to daily workflow to code review to session management to governance. Each skill is useful standalone; the full sequence covers everything.

> **What changed in v6.5.11:** Bug-fix release driven by an independent third-party audit of the v6.5.9 snapshot — every one of the 20 skills received at least one fix, none added or removed. Two deployment blockers: Codex install docs were wrong (Codex actually discovers skills via `.agents/skills/<name>/SKILL.md`, not by appending `agents/openai.yaml` to `AGENTS.md` — fixed across all 5 READMEs and all 20 yaml files), and 7 plugin manifests failed `claude plugin validate` with an invalid `skills` field (now fixed, validates clean). Real bugs fixed with reproductions: `pre-push` (secrets scan now covers outgoing commits, not just staged diff), `project-overview` (corrupted AUTO-marker splice could delete manual text; one bad-encoding file no longer kills the whole run; PARTIAL status now actually fires), `session-checkpoint` (quarantined entries could reach memory promotion; attestation timing caused false TAMPERED reports), `scope` (input validation gaps let malformed scores pass), `code-autopsy` (a cheap-to-fix catastrophic bug could dodge the Critical gate), plus fixes across `setup`, `project-init`, `project-check`, `session-start`, `collab-audit`, `skill-ops`, `integration-intake`, `clean-room`, `eval-leakage-audit`, `doc-drift`, `goal-lock`, `full-audit` (new AUDIT_ONLY/PROPOSE/APPLY_APPROVED mode gate), `freeze`, `next-action`, and `stepback`. Full detail in CHANGELOG.md.
>
> **What changed in v6.5.10:** Refinement release — no skills added or removed; a delta port from the internal fork covering 11 of the 20 skills. `pre-push` → v3.9.0 (fixed a real regression where 9 spots used `cmd | tail -N; $?`, which silently swallowed lint/build/test failures instead of reporting them — switched to `PIPESTATUS`; added an opt-in test-count-floor warning; corrected a stale "12 patterns" claim to the actual 14), `eval-leakage-audit` (18→21-pattern taxonomy — adds success-provenance-gap, lenient-judge-mode non-disclosure, and hardest-category denominator exclusion), `doc-drift` (new 4th detection category, Session Leakage, backed by two new deterministic scripts), `goal-lock` (B5.2 Termination Handshake replaced with Ralph Mode for unattended autonomous loops; new mandatory Tier-0/Tier-1 self-attack step; verification upgraded from recommended to mandatory), `session-checkpoint` (new `kill_if` lesson field + Regression Detection step + a postmortem 3-condition gate on new lessons), `full-audit` → v1.1 (new "coverage caps intervention value" pre-audit step), `integration-intake` (field-level merge operators — SUM/REPLACE/IMMUTABLE/PATCH — for frontmatter grafts), `collab-audit` (psychological-framework sections now gate on evidence sufficiency instead of applying unconditionally), `setup` (new existing-governance-doc probe that generates a thin stub instead of a full duplicate template when a project already has compatible rules), `scope` (three Invariants — Scope OUT minimum, question-count cap, Risk Flags minimum — now allow a single stated exception each instead of being unconditional floors; a behavior change, not a bug fix), `session-start` (ships the `harness_observability.py` script this release had originally deferred, plus a new fast-path that reads `session-checkpoint`'s compact state-snapshot block instead of the full prose handoff). **Not ported this release**: `project-check` — investigated the internal fork's apparent routing change and found `/team-init` isn't a registered trigger anywhere, so it's a dead reference rather than a real upgrade; the public version is currently more complete on this skill than the internal fork.
>
> **What changed in v6.5.9:** Codex compatibility complete — all 20 skills now ship `agents/openai.yaml`. Previously 5 skills added in v6.3–v6.5 (`doc-drift`, `eval-leakage-audit`, `next-action`, `project-overview`, `skill-ops`) were missing Codex agent definitions. Installation section restructured (Option C: Codex/AGENTS.md, Option D: Cursor/other agents). No skill content changes — packaging-only release.
>
> **What changed in v6.5.8:** Refinement release — no skills added or removed; a targeted delta port from the internal fork since v6.5.7 (6 of the 20 skills changed upstream in that window, plus a hand-diffed `code-autopsy` port). `doc-drift` (new Derivability signal — a hardcoded-but-code-reconstructable fact is flagged as structurally drift-prone even when currently correct), `integration-intake` (new Analogy-trap check — an "X does it this way, so should we" value claim needs three answered questions before it counts as evidence), `session-start` (new Query-conditional load rule for on-demand memory files — load only after confirming the conversation is actually about that topic, not on keyword overlap alone), `goal-lock` (new optional EVAL TYPE field for tasks that measure a skill/hook/gate's own reliability, a Silent Self-Correction anti-pattern, a First-Attempt Ledger recording the raw pre-fix DONE EVIDENCE run before any changes, an Early Self-Doubt Boundary note against premature task abandonment from misjudged remaining budget), `pre-push` (code-reviewer unavailability now falls back to an inline abbreviated review instead of an outright skip; new Step 3.5 Public-Mirror Scrub — a WARN-only push-time backstop for repos that are curated public mirrors of a private source; new opt-in high-risk gap-sweep second pass and opt-in multi-angle parallel re-attack; skip-reason logging added to the Fix loop), `session-checkpoint` (new Stage 1, CT promotion queueing — `scripts/ct_promotion_queue.py`, opt-in via a marker file, pure deterministic token-overlap clustering with no LLM judgment and no writes to MEMORY.md/context-log.md itself, ships with a 35-case regression suite; invocation-log skip condition clarified to reuse only the activity-volume legs of the Triple Gate, deliberately not the 24h leg meant for a different auto-trigger), `code-autopsy` (7 more code-smell terms + explicit SOLID-principle naming for dependency-direction violations, a wrapper/proxy forwarding-correctness check, a governing-rules violation check quote-only with no inferred "intent", Q3 gained off-by-one/falsy-zero/copy-paste/unescaped-regex plus Python's mutable-default-argument and late-binding-closure traps, Q7's memory-leak check now names closure-captured-large-object as a pattern, STEP 0 gained a function-level contract check + explicit diff-scope pinning + governing-CLAUDE.md/rules discovery, a new re-established-invariant check for every deleted/replaced line, and a new [FAST MODE] `--fast` tier between the full pipeline and Quick Mode).
>
> **What changed in v6.5.7:** Refinement release — no skills added or removed; several gained working deterministic scripts in place of LLM self-scoring. `project-overview` (`generate_overview.py` is no longer a stub — fully implemented registry parsing, state-snapshot extraction, and AUTO-block render/replace, with untrusted-input table-cell escaping and malformed-marker recovery, backed by unit + integration tests), `scope` (Quick/Full ambiguity gating and BRIEF.md min-item validation now run through a ported `ambiguity_gate.py`, with a regression test locking a bold-text-as-header counting bug), `skill-ops` → v1.2 (Health Mode bucket classification and Quality Mode S/U/S_Q scoring now run through `skill_health_bucket.py` instead of manual arithmetic), `collab-audit` (Step 0.6 source-hygiene filtering now runs through `session_hygiene_scan.py`), `session-checkpoint` (new Discoverability Check step flagging memory writes with no index backlink, a timeout/kill partial-output guard, two Reflexion lesson-quality gates, a PII-redaction rule for raw observations, and Key Files verification moved to a `validate_memory_claims.py` script), `goal-lock` (scope-check surface widened to interface/API changes not just touched files, a benchmark-backed chain-length dominant-variable note, the Stop-hook order gate upgraded to a verified 4-condition implementation, a new Safety Layers section, enum-style VERIFY failure labels, a self-judgment caveat on REFINE's DELTA CHECK, and a background-task termination handshake), `code-autopsy` (a Rationalization Table of 8 common reviewer rationalizations + rebuttals, and a note recommending script-based severity arithmetic over mental math), `eval-leakage-audit` (17→18-pattern taxonomy — adds Goodhart co-evolution in self-improving loops — plus a Reviewer Independence Honest 4-Label check), `integration-intake` (read-only `tools:` frontmatter, redirect-style `not_for` entries, 7 fixed misjudgment-enum labels per phase), `pre-push` (explicit `depends_on`/`concurrency_profile` frontmatter, an Autonomy Boundary note distinguishing read-only git commands from the gated `git push`, an external security-catalog reference link), `session-start` (`depends_on`/`concurrency_profile` frontmatter, Phase 2.2-2.4 rewritten to deterministic commands with fixed stdout contracts, a new unnumbered L0 Inheritance section), `doc-drift` (new Step 0 deterministic pre-filter feeding the Risky/Ambiguous category as supporting evidence only), and `depends_on`/`concurrency_profile` frontmatter adopted across `full-audit`, `project-check`, `project-init`, `freeze`, `stepback`, `next-action`, and `clean-room`, several of which also gained tool-category-tagged Scope Boundary tables. **Known gap surfaced by this release**: `project-check` (and a few siblings) gained unnumbered "inherited principle" notes on Safety Layers/Error Recovery headers — a past release deliberately stripped numbered `(L0 §N)` citations from these same headers across all 10 skills; this version's notes are unnumbered/generic rather than the removed citations, but the header-annotation pattern itself is back. Worth a conscious call before the next release builds further on it.
>
> **What changed in v6.5.6:** Refinement release — no skills added or removed. `eval-leakage-audit` (13→17-pattern taxonomy — respawn masking, pseudo-replication, stimulus-calibration gap, unaudited cost-saving skips), `goal-lock` (an S7 stop rule that blocks forcing an implementation through when execution evidence contradicts an explicit instruction, a 5-tier evidence-rigor ladder + failure-first reporting order + banned hedge phrases, a "layer laundering" success-masquerade pattern, and an evidence-rigor pre-spec note), `full-audit` (a composite-accumulation-gate that flags death-by-thousand-cuts risk when UNCERTAIN/NIT findings pile up in one area even though each was individually dismissed, and an Assumption Ledger for CONFIRMED verdicts that rest on unverified assumptions), `session-checkpoint` (optional `regime`/`escalate_if` lesson fields, an optional `outcomes` field tracking first-attempt-pass/rework/resolvedBy, and a second lessons-archival OR-condition plus a mandatory cross-reference check before archiving), `code-autopsy` → v7.2 (a code-smell vocabulary for Q1, a concrete-failure-scenario requirement, object-level authorization under Q5, expanded network/DB/streaming/cache checks under Q7, a shallow-module + ADR-conflict check under Q8, a numeric confidence-threshold system, and an outcome-ceiling-to-process-metric switch for tied comparisons), `pre-push` → v3.8.0 (ships `scan_secrets.py` alongside the existing `scan_secrets.pl` — Python preferred when present, Perl as fallback — plus `LICENSE.txt` for upstream attribution; note: the two scanners' pattern coverage was found to differ in this release, e.g. the Python port adds an f13 Slack-webhook check absent from Perl, and several existing patterns cover a narrower or wider set of variants on each side — documented as a known gap, not yet reconciled).
>
> **What changed in v6.5.5:** Refinement release — no skills added or removed. `eval-leakage-audit` (8→13-pattern taxonomy — dual-fail-flag, asymmetric-baseline self-falsification, evidence-burn, an ungraded-grader 4-gate check, ceiling-task detection — plus a stratification-substantiation checklist and an honest reviewer-independence 4-label verdict), `goal-lock` (an order gate that blocks completion when no verification ran after the last edit, evidence-channel branching for non-exit-code deliverables, a comprehension check, and three new success-masquerade guards), `pre-push` → v3.7 (cross-bundle joint pass + a three-state false-positive gate), `integration-intake` (headroom pre-classification, trait-vs-procedure termination, triple-check effectiveness claims), `session-start` (added `claude-sonnet-5` to the model-ID allowlist — fixed a false "invalid model" warning), `setup` (removed a duplicate `/setup` trigger), `full-audit` (a rule-dry-run verification layer), `clean-room` (reconciled with upstream autobahn v0.14.0 — an N=1 cap on the independent re-sweep), `code-autopsy` (Q10 oracle-redefinition detection), plus smaller refinements to `session-checkpoint`, `skill-ops`, `collab-audit`, and `scope`.
>
> **What changed in v6.5:** New: `eval-leakage-audit` (audits whether an eval/metric/holdout actually secures independent external ground truth vs circular self-confirmation, via an 8-pattern taxonomy; read-only), `doc-drift` (audits the memory/docs Claude Code loads into context — CLAUDE.md/MEMORY.md/skills/agents/commands — for outdated claims, mutual contradictions, and risky/ambiguous wording, producing a prioritized fix list). Updated: `project-init` (fixed a `skill.md`→`SKILL.md` filename-casing bug that could break skill loading on case-sensitive filesystems, and moved the Phase 3 templates into `references/templates.md`), `pre-push` → v3.6 (two new secret-scanner patterns — f11 prompt-injection strings in diffs, f12 non-PyPI supply-chain index URLs — plus a Step 0 Hook Pipeline Health check), `scope` (added the Mid-Task Scope Drift 10x-Discovery Rule), `collab-audit` (added Step 0.6 Source Hygiene Filter to exclude auto-derived subagent/thread sessions), `full-audit` and `integration-intake` (both gained a Safety Layers section; `integration-intake` also added a Phase 1.8 M-axis surface-selection step — judge which surface (prompt/rule/hook/skill) a pattern should live on before routing), `goal-lock` (added a `migration` task template), `project-overview` (added a Rationalization Table), `stepback` (added a Dominant Variable section + frontmatter fields).
>
> **What changed in v6.4:** New: `full-audit` (exhaustive area audit — deterministic sweep + content review, persistent coverage map, anti-false-positive kill-test), `integration-intake` (5-item screening gate for adopting external skills/agents/rules/plugins, with a provenance/injection check), `clean-room` (carves safety-adjacent requests into a safe scope executed by a genuinely isolated fresh-context subagent, adapted from LilMGenius/paperthin's "autobahn" skill under MIT with a filesystem-isolation and ledger-timing upgrade). Updated: `goal-lock` (a constraint re-echo check at long-task checkpoints, so CONSTRAINTS/SCOPE-Exclude don't quietly fall out of view during extended work), `session-checkpoint` (a new Attestation phase — an evidence-chain receipt log with a bundled `handoff_attestation.py`, so the next session's SessionStart hook can detect handoff tampering).
>
> **What changed in v6.3:** New: `skill-ops` (snapshot/rollback + usage health + invocation tracking hub), `next-action` (reads handoff/git/lessons/STATE and proposes the top-3 next actions), `project-overview` (deterministic cross-project status map). `code-autopsy` → v7.1 (deeper sub-checks per question), `pre-push` → v3.5 (9 supply-chain IOC patterns), `goal-lock`/`session-checkpoint`/`session-start`/`scope`/`stepback`/`freeze` all strengthened. All 12 prior skills gained `not_for` and `see_also` frontmatter for better discoverability.

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
| [code-autopsy](code-autopsy/) | **Updated v7.2.** 12Q quantified code review — 4-axis scoring (Security/Stability/Robustness/Operability), severity anchors, deployment verdict (SHIP/FIX/RISKY/BLOCK), factuality gate. Backed by empirical evidence (Johnson 2019, Parnas 1972). Also works as a standalone prompt in any LLM |

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

### Governance

| Skill | What it does |
|-------|-------------|
| [full-audit](full-audit/) | **New.** Exhaustive audit of an entire area (codebase/docs/skills/memory/config) — deterministic sweep + content review two-layer method, anti-false-positive kill-test, persistent coverage map |
| [integration-intake](integration-intake/) | **New.** 5-item screening gate for adopting external patterns (skills/agents/rules/plugins/MCP) — redundancy check against your existing assets + a provenance/injection check for imported executable content |
| [clean-room](clean-room/) | **New.** Carves safety-adjacent requests into a safe scope, executed by a genuinely isolated fresh-context subagent — adversarial verify pass + descope ledger |
| [eval-leakage-audit](eval-leakage-audit/) | **New.** Audits whether an eval/metric/holdout actually secures independent external ground truth vs circular self-confirmation — 18-pattern taxonomy. Read-only |
| [doc-drift](doc-drift/) | **New.** Audits the memory/docs Claude Code loads into context (CLAUDE.md/MEMORY.md/skills/agents/commands) for outdated claims, mutual contradictions, and risky/ambiguous wording — produces a prioritized fix list |

---

## Lifecycle Flow

```
┌─────────────────── Setup (once) ───────────────────┐
│  /project-init  →  /setup                           │
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
│  /integration-intake (before adopting external work) │
│  /full-audit       (exhaustive area audit)           │
│  /clean-room       (safety-adjacent scope carve-out) │
│  /eval-leakage-audit (eval circular-logic check)     │
│  /doc-drift        (loaded-context drift audit)      │
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
- `pre-push` includes both `scan_secrets.py` (preferred) and `scan_secrets.pl` (Perl fallback)

---

## Agentic Design Patterns Coverage

These 17 of the 20 skills (the original lifecycle set, the v6.4 governance additions, and the v6.5 audit additions — the v6.3 operations additions aren't mapped here yet) implement 17 of the 25 known agentic design patterns ([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| Pattern | Implemented by | How |
|---------|---------------|-----|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | Full lifecycle chain |
| **Parallel Execution** | pre-push | Parallel AI code review agents |
| **Loop (Retry)** | goal-lock | VERIFY fail → PLAN re-entry, capped retries |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | Independent code-reviewer + security-reviewer; 12Q structured review; full-audit's Phase 2 fan-out reviewer pass; eval-leakage-audit critiques whether an eval secures independent ground truth vs circular self-confirmation |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE passes |
| **Coordinator/Router** | setup | Agent routing rules generation |
| **Plan-and-Execute** | goal-lock, scope | Plan reviewable before execution |
| **ReAct** | project-check | Investigate → score → recommend path |
| **Reflexion** | session-checkpoint | Phase 1.7: analyze failures → lessons for next session |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES, Critical/High blocks push; integration-intake's 5-item screening gate before adoption |
| **Custom Logic** | pre-push | Deterministic secrets scan (Perl) + AI review |
| **Event-Driven** | session-start | Triggered on session open, loads prior state |
| **Guardrails/Safety** | goal-lock, clean-room | 13 success masquerading patterns detected; clean-room isolates safety-adjacent scope into a carved-out subagent run |
| **Memory Management** | session-checkpoint, doc-drift | Handoff file + memory updates + lesson extraction; doc-drift audits the memory/docs loaded into context for outdated claims, contradictions, and risky wording |
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
| `integration-intake` | `full-audit` | integration-intake gates a single external adoption decision; full-audit sweeps an entire area (including your existing skill/agent inventory) for drift or gaps |
| `full-audit` | `code-autopsy`, `project-check` | full-audit is a broader, multi-area sweep with a persistent coverage map; code-autopsy stays per-file/12Q, project-check stays a 4-dimension score |
| `clean-room` | `goal-lock` | clean-room fires when a task's scope mixes safety-adjacent material with safe work, mid-execution; goal-lock is the surrounding PLAN→DO→VERIFY loop it interrupts |
| `doc-drift` | `full-audit` | doc-drift audits only the memory/docs loaded into context (CLAUDE.md/MEMORY.md/skills/agents) for drift and contradictions; full-audit sweeps an entire area with a coverage map |
| `eval-leakage-audit` | `full-audit`, `code-autopsy` | eval-leakage-audit checks whether an eval/metric/holdout is circular (measurement integrity); full-audit and code-autopsy review code/areas, not the eval's independence |

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
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift
                 (on-demand governance & audits, any stage)
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history (v3.0 → v6.5.8).

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. If you build a skill that fits the lifecycle, open a PR.

## Contact

DM [@AlexZio00](https://x.com/AlexZio00) for custom skill development.
