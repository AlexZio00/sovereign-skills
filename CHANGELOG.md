# Changelog

All notable changes to sovereign-skills are documented here. Recovered from
git/README history (the v6.0 rewrite dropped the changelog section from
`README.md` — this file restores it as a standalone document going forward).

---

## v6.3 — 2026-07-07

### Changed
- **code-autopsy** → v7.1: expanded all 12 questions with detailed sub-checks
  (deletion test, kitchen-sink detection, schema/migration safety, 5-domain
  security, DONE↔GOAL alignment, state reproducibility, and more)
- **goal-lock**: added a REFINE track for non-code artifacts (CRITIQUE →
  REWRITE → DELTA CHECK, 1-round limit), a stagnation circuit breaker (S6 —
  same blocker repeated 2+ times), external-failure-fabrication added to the
  success-masquerading list, and documented the physical Stop-hook completion
  gate (`goal_lock_stop_gate.py`)
- **pre-push** → v3.5: 6 IOC patterns → 9 (added dependency confusion,
  missing version pinning, post-install hook network calls)
- **session-checkpoint**: added Attestation (SHA-256 hash sidecar for handoff
  tamper detection), a 7-factor value function for lessons.md archival
  judgment (reliability/goal-relevance/self-relevance/usage-history/oracle/
  blind), and Growth Re-check for sessions that continue past checkpoint
- **session-start**: added an Autoimmunity Rate section (rejection/total
  ratio, 5%/15% thresholds) and expanded graduation gates from G1-G6 to
  G1-G18
- **scope**: replaced the subjective "can you answer in one sentence"
  sufficiency check with a 4-dimension ambiguity score (function/boundary/
  verification/assumptions, 0-10 each, ≥7 average to proceed)
- **stepback**: added Key Assumptions, Safety Layers, and Error Recovery
  sections; unified `see_also` to point at `next-action`
- **freeze**: added 2 regression-test scenario files under `scenarios/`
  (normal Scope Lock operation, Invariant violation detection)

### Added
- **New skill: skill-ops** — snapshot/rollback + usage health + invocation
  tracking hub for skills and agents
- **New skill: next-action** — reads handoff/git/lessons/STATE and proposes
  the top-3 next actions by impact, proposal-only
- **New skill: project-overview** — generates a deterministic cross-project
  status map from registered projects' session handoffs
- All prior skills: added `not_for` (misuse prevention) and `see_also`
  (related skill cross-references) to YAML frontmatter — helps users
  pick the right skill and discover related ones
- Individual version tags on all skills (previously only 2 had them)

### Fixed
- Localization regression: 9 of 12 skills had 7-57% Korean-language text left
  in the English SKILL.md files (personal-use version had been copy-pasted
  back over prior translations during v4-v6 upgrades). Full re-translation,
  shipped 2026-07-01.

> Note: this release's content (Tasks A-D above) was applied to all 5
> language READMEs (EN/KO/JA/ZH/ES) as of 2026-07-07, including the
> project-init correction (see fix entry below).

**Fixed (2026-07-07):**
- `project-init` was incorrectly marked as absorbed into `setup` at initial
  release — it is a standalone skill (15 total, not 14). Corrected across
  `marketplace.json`, all 5 language READMEs, this changelog, and the
  GitHub release notes. Also fixed: missing `code-autopsy/.claude-plugin/plugin.json`,
  and `goal-lock`'s masquerading-pattern count (stale "11" → actual 13)
  across README/marketplace.json/plugin.json.

---

## v6.2 — 2026-06-27

**Added:**
- **stepback** — One-shot perspective reset. Generates 1 abstract reframing question (DeepMind step-back pattern) + 3 quick checks (scope drift, side effects, better approach) in under 10 lines. Read-only, no agents, no code. Use anytime during implementation to check if you're solving the right problem at the right level. Source: team-attention/hoyeon.

**Updated:**
- **code-autopsy** — Added Meta-Detection Gates: CapCode ceiling metric for score gaming detection, CEF fabrication detection for constraint-evasive fake errors.
- **collab-audit** — 13→14 sections. New Section 12: Thinking Level Trajectory (5-Level model from Information Requester to Thought Designer + temporal change tracking + AI attribution correction).
- **goal-lock** — Added Ralph Wiggum early-completion detection (12th masquerading pattern) + verification traceability in VERIFY stage (every claim must trace to an actual tool call).
- **session-checkpoint** — Added handoff clarity self-check (2 anchor questions after handoff writing).
- **session-start** — Added Context Rot Prevention (sliding window for stale handoff entries).
- **pre-push** — Added 3-IOC Supply Chain Check for newly added dependencies.
- **scope** — Added Contraindication field (conditions where the chosen approach is NOT suitable).
- **freeze** — Added Thaw Protocol (formal unfreeze workflow with blast radius check, 3-thaw warning).
- **project-init** — Extended `.env.example` template (OAuth, external services, monitoring sections) + Security Baseline notes.
- **project-check** — Added Score Delta Tracking (compare current vs previous scan results).
- **setup** — Added Redesign Protocol for Tier 0 violation test failures (3-option escalation).

**Infrastructure:**
- Repo renamed: `claude-code-skills` → `sovereign-skills`
- Codex/Cursor support added via `agents/openai.yaml` for all 12 skills
- README synced across 5 languages (EN/KO/JA/ZH/ES)
- All internal/personal-project references removed for public release

---

## v6.1 — 2026-06-20

**Added:**
- **code-autopsy** — 12Q quantified code review prompt (Code Autopsy v7.0). 12 analysis questions covering design through observability. 4-axis composite scoring (Security × 0.35 + Stability × 0.30 + Robustness × 0.20 + Operability × 0.15). Severity Anchor Table with weighted formula. Deployment verdict with CRITICAL hard cap. Factuality Gate (self-verify before reporting). Cross-file impact analysis. Quick mode and Diff mode. Backed by: Google eng-practices, Johnson et al. 2019, Parnas 1972. Works as a standalone prompt in any LLM — not Claude Code exclusive.

---

## v6.0 — 2026-06-15

**Added:**

- `goal-lock` — agent discipline engine: PLAN→DO→VERIFY→FINALIZE→OUTPUT loop
  with 11 success-masquerading pattern detection

**Merged:**

- `harness-init` + `team-init` → `setup` (infrastructure + agent team in one flow)
- `brief` + `adr` → `scope` (scope definition + ADR capability)
- `retro` → `session-checkpoint` (Phase 1.7 Reflexion)

**Removed:**

- `token-audit` (use `npx ccusage` instead), `adr` (merged into `scope`),
  `retro` (merged into `session-checkpoint`)

**Upgraded (all 10 remaining skills):**

- All skills: Dominant Variable, Key Assumptions, Error Recovery, Safety Layers added
- All skills: Scope Boundary with action tags (`[READ]`/`[WRITE]`/`[BASH]`/`[AGENT]`)
- `session-checkpoint`: Memento CoT compression, Reflexion, Invocation logging
- `pre-push`: Large diff deterministic bundling, Discard If conditions
- `collab-audit`: Anti-pattern flags, Key Assumptions

---

## v5.0 — 2026-05-28

**New skills (3):**

**`/freeze`** — Scope lock before implementation:
- Parses user input to classify files as editable, frozen, or read-only
- Emits a `FROZEN SCOPE` block and stops — no code generation, no agents
- Ambiguous scope → one clarifying question; still vague → freeze the broader scope
- Task-scoped declaration (no session state), adapted from [garrytan/gstack](https://github.com/garrytan/gstack) freeze pattern

**`/retro`** — Milestone retrospective:
- 6-phase pipeline: scope declaration → friction points (root cause, not symptom) → wins (what went right) → pattern extract → lessons write → optional summary block
- Duplicate check via `Grep` against `tasks/lessons.md` before writing — updates `obs`/`seen` on matches
- All lessons include `> conf · seen · obs` v2 metadata (compatible with `/session-start` priority loading)
- Complements session-checkpoint Reflexion (session-scoped) — retro is milestone-scoped and goes deeper
- *(Merged into `session-checkpoint` Phase 1.7 in v6.0)*

**`/token-audit`** — Token overhead measurement:
- Measures actual Claude Code token overhead from your session JSONL and generates a personalized infographic
- Computes per-turn breakdown: context file load, rules overhead, memory load, skill activation, tool use
- Surfaces top 3 quick wins to reduce overhead without removing useful context
- **Requires `python3`** (standard library only for Steps 1–3 + 5–6). Infographic (Step 4) needs `pip install matplotlib` — optional, text-only path available without it
- *(Removed in v6.0 — use `npx ccusage` instead)*

**Enhancements to existing skills:**

**`/session-start`** — new Phase 0.5: Environment Health Check:
- Runs on every session start, including discarded sessions and first-ever sessions
- **Check 1**: verifies `~/.claude/settings.json` model ID against known-valid Claude identifiers — flags unrecognized values
- **Check 2**: counts `permissions.allow` entries in `~/.claude/settings.local.json` — warns if > 5 (accumulated session-scoped approvals silently widen the permission surface)
- Both checks clean → no output. Any warning → surfaces in the ready signal under `**Environment alert:**`
- New Invariant 4: Phase 0.5 always runs regardless of Discard conditions

**`/project-check`** — two new structural sections:
- **Safety Layers**: explicit table of blocked actions (file writes, test execution, secret removal) mapped to Invariants — makes the read-only guarantee auditable
- **Error Recovery**: failure classification table for `tool_failure` / `missing_data` / `input_error` with explicit recovery paths — a partial scan now reports itself as partial, never as complete

---

## v4.7 — 2026-05-07

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

**All 10 skills**: removed internal framework references (`(L0 XIII/XIV/XV inheritance)`, `(L0 II.7 inheritance)`, etc.) from Safety Layers and Truthful Reporting section headers. Behavior unchanged — labels removed only.

---

## v4.6 — 2026-04-28

Two session lifecycle skills upgraded to track lesson health over time, not just lesson content.

- **`session-checkpoint`**: Phase 1.5 ③ + Phase 3 step 3 — when adding a new entry to `tasks/lessons.md`, attach a metadata line `> conf: 0.5 · seen: today · obs: 1` below the header. On re-observation, increment `obs` and bump `conf` after thresholds (3/6/9, max 0.9). On violation + user correction, lower `conf` by 0.1 (min 0.3). Quarterly cleanup: `conf < 0.4 AND (today − seen) > 90 days` → move to `tasks/_archive/lessons-pre-YYYY-MM.md`.
- **`session-start`**: Phase 2 — utilize the `> conf · seen · obs` metadata to prioritize which lessons surface in the ready signal. `conf ≥ 0.7` shows rule body, `conf 0.5` title only, `conf < 0.5` TOC or skip. Lessons without v2 metadata are handled normally (backward compatible).

**Origin:** ECC [`continuous-learning-v2`](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2) (instinct + confidence scoring). Concept absorbed; the full package (homunculus directory + background Haiku agent + 6 slash commands) was not adopted — the metadata pattern transfers cleanly into existing `lessons.md` without new infrastructure dependencies.

## v4.5 — 2026-04-27

Five skills now include explicit safety and reporting contracts — Safety Layers document which actions are risky and what defense layers apply; Truthful Reporting defines what counts as a complete vs. partial result.

- **`pre-push`**: Python CVE scan via `pip-audit` added to Step 3 (WARN-only, never blocks). Preferred over osv-scanner for Python-native projects. Also adds **Safety Layers** mapping each push action to its reversibility tier, and **Truthful Reporting** clarifying what "READY TO PUSH" actually means.
- **`collab-audit`**, **`brief`**: **Truthful Reporting** — explicit criteria for what counts as a complete audit vs. inference-padded output; and what counts as a locked scope vs. a draft.
- **`harness-init`**, **`project-init`**: **Safety Layers** + **Truthful Reporting** — maps file-creation actions to reversibility tiers and defense layers. Prohibitions explicit: no `.env` generation, no `settings.json` overwrite.

## v4.4 — 2026-04-20

All 10 SKILL.md files and README now include **"In production"** sections — concrete production context showing scale, duration, and what each skill actually catches in a real codebase. No new behavior changes; documentation only.

## v4.3 — 2026-04-18

- **Phase 1.6: Task-to-Skill Crystallization** (`session-checkpoint`): new phase detects repeated workflow signatures (Intent + Tool Sequence + Output Shape) and proposes promoting them into a new skill. Triggers: same signature ≥3 times within session, or `[ref:N]` ≥5 in `context-log.md`. Origin: GenericAgent crystallization pattern.
- **Invariant 4: Propose-only** (`session-checkpoint`): Phase 1.6 never authors the skill automatically — only suggests the candidate. User judgment required before promotion. Prevents one-off explorations from polluting the skill library.
- **Rationalization Table +2 entries** (`session-checkpoint`): closes two loopholes — "just auto-promote the repeated workflow" (Invariant 4 violation) and "signature is too trivial, skip it" (dismissing 3+ reps as trivial is measurement laziness → log to `[ref:N]` instead).
- **Non-trigger conditions** (`session-checkpoint`): explicit skip rules — one-off exploration, duplicate of an existing skill (scans `~/.claude/skills/*/SKILL.md`), or overly generic signatures that would collide with already-established skills.

## v4.2 — 2026-04-17

- **Handoff file renamed** (`session-start`, `session-checkpoint`, `harness-init`, README): `memory/session-handoff.md` → `memory/session-handoff-LATEST.md`. Explicit `-LATEST` suffix prevents confusion when users also git-tag historical snapshots (`session-handoff-2026-04-07.md`, etc.). Breaking change — rename existing handoff files on upgrade.
- **Bilingual trigger keywords** (`session-start`, `session-checkpoint`): descriptions now include Korean triggers alongside English (`'세션 시작'`, `'체크포인트'`, `'핸드오프 저장'`, etc.) so both language prompts route correctly. Body content remains English.
- **Phase 3: Global State Check** (`session-start`): new phase reads `~/.claude/STATE.md` (cross-project blockers/decisions) so session-open surfaces global items that are resolvable in the current project. Skip if STATE.md missing.
- **checkpoint-compact removed**: functionality fully consolidated into `session-checkpoint`. If you had a separate `/checkpoint-compact` command bound, remap to `/session-checkpoint`.

## v4.1 — 2026-04-16

Four patterns from Claude Code internals applied across the full skill suite:

- **`tools:` frontmatter** (`project-check`): physical tool scope enforcement — read-only skills declare allowed tools in frontmatter. Edit/Write are absent from the tool list entirely, not just prohibited by prompt instruction.
- **STATIC/DYNAMIC boundary** (`brief`): project structure scan in Step 1 is explicitly marked as static/cacheable context. Steps 2–5 are dynamic. Reduces redundant re-scanning across sessions.
- **Triple Gate auto-trigger** (`session-start`): added auto-trigger signal — ≥5,000 tokens AND ≥3 tool calls AND ≥24h since last session → run session-start before new work. Prevents silent context loss.
- **NO_TOOLS warning + 9-item expansion** (`session-checkpoint`): Phase 1 extraction expanded to 9 items (was 5). Phase 5 now explicitly warns that `/compact` disables all tools — state must be written before compaction begins, not during.
- **YOLO classifier** (`pre-push`): read-only git ops (`git diff`, `git status`, `git log`) explicitly marked as auto-approvable without permission prompt. Write ops still gated.
- **Second-opinion review gate** (`harness-init`): generated harness now includes a multi-model review gate — routes high-stakes decisions to a stronger model for confirmation before finalizing.
- **MagicDocs** (`adr`, `collab-audit`): generated output files now use `# MAGIC DOC: [title]` heading. Claude Code auto-updates these files during conversations.

## v4.0 — 2026-04-13

- Added `/session-start` — session open skill. Loads handoff + lessons, spot-checks memory, produces Priority 1 ready signal within 60 seconds. Pair with `/session-checkpoint`.
- Added `/session-checkpoint` — session close skill. 5-phase pipeline: deep extraction → entity classification (permanent facts / episode entries / lessons candidates / stale detection) → handoff rewrite → memory save → preservation checklist → compact guidance. TTL system: `ttl:permanent` | `ttl:90d` | `ttl:30d`.
- Added `/adr` — Architecture Decision Record. Records context (forcing function), decision, alternatives considered, consequences, and override conditions. Fabricated alternatives explicitly forbidden. Pairs with `/brief`.
- README restructured into 4 categories: Project Setup / Daily Workflow / Session Management / Quality & Reflection.

## v3.6 — 2026-04-12

- Added `/brief` — scope locking before implementation. Scope OUT mandatory (min 2 items, plausible extensions only). Exit Criteria require observable action + measurable result format — vague criteria auto-rejected. Conservative minimum scope floor: one complete user flow + one user-visible outcome. 7 invariants.

## v3.5 — 2026-04-12

- `harness-init`: Added `tasks/lessons.md` generation + SubagentStop lifecycle hook to generated harness. SessionStart hook now loads lessons.md on session start.
- `project-check`: Added `tasks/lessons.md` and SubagentStop hook to Harness scan checklist.
- `collab-audit`: Section 8 context maturity Level 5 — `tasks/lessons.md` operation as meta-layer.
- **`tasks/lessons.md` pattern** (Boris Cherny, *Programming TypeScript*): Record repeated AI mistakes as correction rules on the spot → review at next session start. Separates behavior correction (lessons.md) from technical knowledge (MEMORY.md).
- **SubagentStop hook**: Logs agent completions with ID + transcript path for debugging multi-agent workflows.

## v3.4 — 2026-04-11

- All 6 skills: added **Rationalization Table** (common rationalization patterns + rebuttals)
- `pre-push`: added **Dominant variable**, **Discard if**, **Invariants with consequences**, **Scope Boundary** — format now consistent with the rest of the suite

## v3.3 — 2026-04-11

- Added `/collab-audit` — 13-section behavioral diagnosis from conversation observation. Compare mode, gitignore protection, observation-only (no surveys).

## v3.2 — 2026-04-10

- `team-init`: Advisor Strategy pattern added to Full orchestrator — consults opus advisor before user escalation, spot-check on sonnet after haiku pass

## v3.1 — 2026-04-09

- `project-check`: Anthropic key pattern, C/C++ file support, project-level agents scan
- `harness-init`: Smart Defaults, violation testing per Tier-0 rule (not 3 total), Memory Discipline unconditional label

## v3.0 — 2026-04-08

- Introduced `project-check` — read-only health scan, scale-aware, Security-first report
- Applied v3 patterns across all skills: **Dominant variable**, **Discard if**, Invariants with failure-mode consequences
- `pre-push` v3.0.0: `scan_secrets.pl` scanner (12 patterns), parallel AI review agents, language-aware test/lint detection

---

## References

- [ReS0421/coding-team-orchestrator](https://github.com/ReS0421/coding-team-orchestrator) — Several orchestration patterns in `/team-init` (merged into `/setup` in v6.0) were adapted from this project: "Do Not Trust the Report" (spec reviewer reads code directly, not the implementer's claim), Final Integration Review (cross-task consistency check via `git diff BASE_SHA..HEAD`), and CRITICAL/IMPORTANT/MINOR severity tiers for the correction loop.
- [obra/superpowers](https://github.com/obra/superpowers) — writing-plans + subagent-driven-development patterns that influenced the planning pipeline.
- [Boris Cherny](https://github.com/bcherny) (*Programming TypeScript*, Meta Staff Engineer) — `tasks/lessons.md` behavior correction loop: record repeated mistakes as correction rules, review at session start. Separates behavior correction from technical memory.
