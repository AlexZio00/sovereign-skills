---
name: full-audit
description: "Exhaustive, denominator-driven audit of an entire area (codebase, docs, memory, skills, DB, config). Runs a 6-phase pipeline: scope agreement + prior-map diff -> deterministic sweep (counts/versions/paths/parsing plus cross-index reconciliation) -> parallel read-only content review (citations forced, rule dry-run) -> judgment (false-positive/UNCERTAIN triage) -> fix-vs-addition split, gated by execution mode (AUDIT_ONLY default = read-only, PROPOSE = list only, APPLY_APPROVED = apply approved items only) -> coverage-map recording. A bare 'audit'/'analyze' request defaults to AUDIT_ONLY and never auto-advances to file writes. NOT for single-file or single-question checks (use a regular code review instead) or harness-maturity scoring against a fixed checklist (use a dedicated scoring tool instead). Triggers: '/full-audit', 'audit everything', 'full audit', 'find every gap'."
skill_type: audit-orchestrator
user-invocable: true
triggers:
  - "/full-audit"
  - "audit everything"
  - "exhaustive audit"
  - "full audit"
  - "double-check everything"
  - "find every gap"
depends_on:
  skills: []
  agents: []
  files:
    - "scripts/canary_mix.py"
    - "scripts/canary_score.py"
  # self-contained aside from the optional canary scripts: Phase 2 spawns ad-hoc
  # read-only reviewer subagents rather than calling a fixed named skill/agent.
concurrency_profile:
  parallel_safe: true
  parallel_phase: "Phase 2 content review only (read-only reviewers, unlimited fan-out)"
  serialized_phases: "Phase 1 sweep and Phase 4 fix-bucket edits run sequentially, not concurrently with Phase 2"
not_for:
  - "Single-file or single-question checks (use a code review instead)"
  - "Harness maturity scoring with a fixed checklist (that's a different, narrower tool)"
  - "A single docs-vs-code drift check (too narrow a scope for this)"
see_also:
  - skill: project-check
    relation: "project-check=fixed-checklist health score, full-audit=open-ended exhaustive sweep with a denominator"
---

# Full Audit — Exhaustive Area Review

## Dominant Variable
**Accuracy of the coverage claim** — the word "exhaustive" ships with a method label or it doesn't ship at all. The moment an unreviewed area gets reported as reviewed, this skill has failed its own purpose.

## Trigger
- `/full-audit [area]` · "audit everything" · "exhaustive audit" · "full audit" · "double-check everything"
- **Default mode on any of the above: `AUDIT_ONLY`.** These are analysis requests, not execution requests — see Execution Modes below. Advancing to `PROPOSE` or `APPLY_APPROVED` in the same invocation requires the user to say so explicitly (e.g. "audit everything and apply the fixes").

## Discard If
- Single file / single question needs checking → use a regular code review instead
- The goal is a harness-maturity score against a fixed checklist → use a fixed-checklist scoring tool instead
- The goal is a single docs-vs-code drift check → too narrow a scope for this
- An identical-scope full audit finished within the last 7 days and nothing has changed → just diff against the existing coverage map instead

---

## Key Assumptions
1. **Target area is agreed in Phase 0** — if not, don't start without an area table.
2. **Deterministic sweeping (scripts/grep) is available for the target** — if not, skip Phase 1 and never claim "exhaustive" from Phase 2 (LLM review) alone.
3. **A prior coverage map can shrink the scope via diff** — if not, do a full re-scan.

## Execution Modes: AUDIT_ONLY / PROPOSE / APPLY_APPROVED
This skill keeps **analysis** and **execution** in separate, explicitly-named modes. A trigger phrase like "audit everything" or "analyze this" selects a mode — it does not, by itself, authorize any file write.

| Mode | When active | What runs | Writable scope |
|------|---|---|---|
| `AUDIT_ONLY` (**default**) | Any bare audit/analysis trigger, with no separate execution request | Phase 0-3 (scope, deterministic sweep, content review, judgment) + Phase 5 (coverage map) | None — audited files are read-only. No Edit/Write to any target file, protected or not. Only audit artifacts may be written (scratch scripts, canary staging, coverage map, recall ledger). |
| `PROPOSE` | User asks for fix proposals (after an `AUDIT_ONLY` pass, or up front) | `AUDIT_ONLY` output + a listed fix/addition bucket (Phase 4 framing, nothing applied) | None — still read-only, output is a proposal list |
| `APPLY_APPROVED` | User explicitly approves specific items or the fix bucket as a whole ("apply these items", "apply the fix bucket") | Applies only the items the user named as approved | Limited to the approved items. A protected path (see "Protected paths" under Safety Layers) is reachable **only** here, only for that one named item, and only by drafting the edit plus an apply script for the user to run themselves — the model has no path to lift a deny rule (the deny rule lives in the same settings file it protects). |

**One-way per pass**: `AUDIT_ONLY` never auto-advances into `PROPOSE` or `APPLY_APPROVED` within the same invocation. Advancing needs a new, explicit user statement. This closes the gap where "audit everything" silently walked all the way to Phase 4 fix-bucket execution — including a protected file changing — without the user ever approving execution, not just analysis.

**Delegated runs**: in a run with no user present (a subagent, a scheduled task), approval for `PROPOSE` or `APPLY_APPROVED` counts only when the caller passes the user's own approving words verbatim. A paraphrase or "the user approved" is not approval: stay in `AUDIT_ONLY` and return `NEEDS_INPUT` listing the items that need approval.

## Phase 0: Agree Scope + Diff Against Prior Map
1. **Declare the execution mode for this run** in the first line of the response (e.g. "Mode: AUDIT_ONLY — read-only, no files will change"). Default `AUDIT_ONLY` unless the request explicitly names `PROPOSE`/`APPLY_APPROVED` or explicitly approves specific items up front.
2. Declare the target areas as a table (e.g. codebase / docs / global skills / memory / DB / settings). For code and docs areas, build the file list as the union of `git ls-files` and `git ls-files --others --exclude-standard` - a tracked-only list drops uncommitted files, which are the ones most in need of review. (If the area is not a git repository, build the list with `find` and say so on the map.)
3. If a prior coverage map exists, read it and **queue its remaining gaps first**. Default map location: `<repo root>/.audit/coverage-map.md` (for a non-git area: `<area root>/.audit/coverage-map.md`); use the project's own location if it already has one. If no map exists, say "no prior map" and do a full scan.
4. Areas the user explicitly excludes go on the map as "intentionally excluded" — never silently dropped.

## Phase 1: Deterministic Sweep
Whatever a machine can count, a script counts — never eyeball it:
- Counts (test count, DB rows, file count) / version stamps (single source of truth in N places) / path and reference existence (dead links)
- Parsing (YAML frontmatter, JSON settings) / stale-number greps (old numbers still lingering) / expiry (TTL, aging)
- **No inline throwaway scripts** — write a script to a file, run it, then delete it (guards against quoting/escaping mistakes)
- Reuse existing checkers first (test suites, project-specific validation scripts, linters)

**Cross-index contract sweep (mandatory sub-step — this is the layer most exhaustive audits skip)**:
The layer most easily missed in "exhaustive" audits is *"does the index/routing doc match the real files?"* — careful reading of individual files alone will never catch this. Sweep deterministically:
- **Index vs. reality reconciliation**: names listed in an inventory/index file vs. the actual directory/file listing — check both directions (ghost entries with no backing file, and real files missing from the index)
- **Routing vs. reality reconciliation**: names a routing table points to vs. whether those targets actually exist (dead routes to archived/renamed targets)
- **Declared-dependency sweep**: for each unit's declared dependencies (other files/skills/agents it depends on), do all of them actually exist? (including malformed declarations, e.g. a flag where a name was expected)
- **Frontmatter parsing integrity**: duplicate YAML keys in frontmatter (the later one silently wins — a safety profile could flip silently)
- Rationale: in comparable audits, most of the gap came not from "reading more carefully" but from "did we actually sweep these specific things deterministically" — a model-independent, reproducible methodology improvement.

**Coverage caps intervention value**: before starting Phase 2 content review, count how many items this audit could actually affect (e.g., "N files this rule change would apply to"). That count **caps the maximum value of the intervention before you've even seen the results** — if only 3 items are in scope, no amount of review sophistication can produce more improvement than those 3 items allow. Computing this cap up front prevents over-investing deep-review time in low-cap areas, and gives a concrete basis for shifting review effort toward higher-cap areas instead.

**Canary mixing** (a control group for telling "clean" apart from "the reviewer missed it"): when reviewing a code area, stage one known-clean file and one file with a planted defect from this skill's bundled example pool (`scripts/canaries/{clean,seeded}/`) using `python3 "${CLAUDE_SKILL_DIR}/scripts/canary_mix.py" select --pool both --n-clean 1 --n-seeded 1 --stage-dir <scratch>/<run>/bundle --out <scratch>/<run>/canary-manifest.json`, then mix the staged files into one or two real review bundles. Don't tell the reviewer dispatch that a control exists or which file it is, and don't count canaries in the Phase 1 denominator. The bundled pool ships with only 2 clean / 2 seeded example files — build a project-owned pool with pairs representative of the actual codebase before treating a recall number as meaningful, keep it in the project (not in the install folder, so a skill update does not erase it), and select from it with `--canaries-dir <your pool>` (layout: `<pool>/clean/` and `<pool>/seeded/` with one `.json` sidecar per seeded file; see `scripts/canaries/README.md`). For a docs/rules area, add `.md` pairs to the pool (one clean, one seeded with a numeric contradiction inside the body) and pass `--ext .md` to the same command; the bundled pool has none, so without your own `.md` pairs the script exits with "no files with suffix .md". The leading dot in `--ext` is optional. Put the clean and the seeded doc into different review bundles - their bodies look alike, and seeing both together gives away that they are controls. If the pool has no file with the requested suffix, or Python is unavailable, skip the step and note "canary not applied (no pool for this area / no Python)" on the map. Scoring uses the same `canary_score.py`.

`${CLAUDE_SKILL_DIR}` is this skill's folder; Claude Code fills it in. In other agents, replace it with the path where you installed the skill. Use `python` instead of `python3` where only that exists (common on Windows). If a script fails to start, record `⚠️ check unavailable: <script>` on the map instead of skipping silently.

## Phase 2: Content Review + Rule Dry-Run (Three-Layer Principle)
> **Structural checks (Phase 1) alone do NOT justify calling something "exhaustive"** — exhaustive = structure + content + rule dry-run, three layers. Rules and guards can't be confirmed as actually working just by reading their documentation — only running them against mock input fills in the third layer. The three layers are non-substitutable: structural checks can come back clean while the content is wrong, and the content can be correct while a rule still fails to fire at runtime.
- Fan out parallel review agents (unlimited breadth for coverage, read-only — never give reviewers edit access)
- **Neutral framing**: phrase the review dispatch's goal as "judge whether this bundle satisfies policy P — with equal rigor whether it does or doesn't," not "find problems in this code." An instruction to find problems pulls something out of a clean file too.
- **Single-reviewer batch size cap** (reported in one controlled study of paper review: recall that held at 50–60% for 1–10 papers collapsed to 2.8% at 48 papers in a single batch — treat the figures as an illustration, not a calibrated threshold): the line above is about how many parallel agents you fan out; this is a separate axis — how many files/documents one reviewer call scans at once. Even when nominal context capacity looks sufficient, the more items you put in one call, the more likely "no findings" stops being an honest negative and becomes a confident fabrication. For large scopes, lean toward splitting bundles small (the exact cap is domain-dependent, so no number is fixed here).
- **Force citations**: reviewers must attach a grep/ls output as proof when they claim something is missing — "I can't find it" from memory alone is invalid
- **Anti-false-positive 4-bucket** (enforce in the review dispatch's output-format instructions): classify every finding as `CONFIRMED / FALSE-POSITIVE (reviewed and dismissed, with a refuting citation) / UNCERTAIN (needs inference — keep it, don't discard, to avoid false negatives) / NIT`, each with a **reasoning note**. `CONFIRMED` at Critical/High needs 2+ of {condition, impact, reproduction} or it gets downgraded to Medium. `FALSE-POSITIVE` needs the discarded hypothesis + a refuting citation (command output or a line quote) — "no issue" in one line is not acceptable. An empty false-positive list is not a penalty (state "none dismissed" explicitly — this prevents over-suppression).
- **Kill-test** (enforce in the dispatch instructions): before reporting each finding, run one command that *tries to refute it*, include the output, and add one line: `(refutation check: output refutes the finding / output is unrelated and insufficient)`. If refuted, it moves to the false-positive bucket. "It's missing" claims must be backed by an exhaustive grep across the whole denominator (explicit regex and scope, `grep -rn <pattern> <root>` — substring matching alone doesn't count). Passing a mock test alone does not count as a refutation (remove the code and re-test instead). The conclusion needs one objective anchor: a rule/linter, an actual execution result, a direct two-point comparison within the reviewed content, or a grep-derived denominator — "it looks like" with no anchor is invalid (inference-requiring cases aren't invalid, they go to UNCERTAIN instead). **Anchor-inject the countables**: for anything a machine can count, hand reviewers Phase 1's deterministic values as a given anchor up front rather than asking them to re-derive it — this keeps reviewers out of the business of re-counting what a script already settled.
- **Reverse dry-run for guard/lint scripts**: seeded-error injection only checks that a rule catches what it should. In the opposite direction, map every check in a guard, linter, or check script to the rule clause (`file:line`) that justifies it. Report any check with no mapped clause as a false-positive source candidate - checks left without a basis are what block legitimate work.
- **Rule dry-run (third layer)**: if the target area has rules or guards (linter configs, pre-commit hooks, validation scripts), build an actual mock input (a fixture) and run it through the rule to confirm by execution — not by reading — that it detects or blocks what its documentation claims. Static comparison (does the rule's documentation exist) and content review (does the rule's wording make sense) alone can't prove it fires at runtime — skip this layer and a dead guard (documented but inert) slips through unnoticed.

## Phase 3: Judgment — Dismissing False Positives
Personally re-verify every reviewer report before classifying. Common false-positive patterns to check for:
- **Training-cutoff confusion**: "this date/version can't exist yet" — re-check against the actual current date
- **"Already exists but reported missing"**: any reported "gap" must be re-confirmed to actually be missing via grep before being accepted
- **Historical notation mistaken for staleness**: an original-version marker or changelog entry is history, not staleness — don't "fix" it
- **Number conflicts**: reviewer's number vs. the Phase 1 deterministic number → deterministic wins
- **Composite-accumulation-gate (death-by-thousand-cuts guard)** : even when every individual finding is separately dismissed as FALSE-POSITIVE/UNCERTAIN/NIT, if the same area (same file/module/component) accumulates 3+ UNCERTAIN findings, or 5+ combined (UNCERTAIN+NIT) findings, flag it separately as an "individually-passed, cumulatively-risky" signal — passing each individual threshold does not mean the composite threshold is also safe (the same idea as a hard cap on a review verdict: one CRITICAL finding is never averaged away by many small ones). A flagged area is not promoted to CONFIRMED, but must be listed at least once in the Phase 4 addition bucket so the user sees it. [The 3/5 thresholds are initial estimates; recalibrate them once you have data from your own audits.]
- **Read the source before dismissing a CONFIRMED finding**: before flipping a reviewer's CONFIRMED to FALSE-POSITIVE or REFUTED, the orchestrator reads the `file:line` source itself (with Read, not a script or grep result) and quotes the refuting text. A regex refutation is supporting evidence only, never the sole reason for dismissal - a regex kill-test has dismissed real defects. A dismissal made without reading the source is marked `dismissed-unread` on the map and the item goes back to UNCERTAIN. The duty applies only to CONFIRMED -> dismissed, because that is the direction that tells the user "no problem".
- **Second pass for CONFIRMED High findings, with a different model**: after Phase 3, only final CONFIRMED findings of severity High or above (Critical included) go to a second pass. (1) Dispatch the reviewer with a different model tier than the first pass (set the Agent `model` parameter differently), in a fresh context. (2) Give it evidence only (`file:line` source, grep output); leave out the first pass's conclusion, severity and expected answer, and phrase the claim as a neutral question. (3) Output the 4 buckets plus one refuting command. (4) If the passes disagree, do not pick one: re-read the source, leave the item UNCERTAIN and escalate it to the user. (5) Label the vendor honestly on the map: if both passes are Claude models, `same_vendor` (only the tier differs, so this is not independent verification); `independent` only if a different vendor was used; `unverified` if the vendor cannot be shown. Items already UNCERTAIN after the first pass and Medium-or-lower findings are out of scope.
- **Canary scoring** (only for a run that mixed in canaries): save this run's verdicts as `[{"file": <path>, "verdict": <final bucket>, "summary": <one line>}]` JSON and run `python3 "${CLAUDE_SKILL_DIR}/scripts/canary_score.py" --manifest <canary-manifest.json> --findings <that JSON>`. A trailing `:line` or `:line:col` on `file` and the letter case of `verdict` are tolerated. Scoring the same manifest twice does not double-count in the recall ledger (records are keyed by manifest hash plus seeded id). If a clean control file comes back CONFIRMED, mark every CONFIRMED finding from this run as "needs re-verification" on the coverage map — this does not auto-downgrade them. Drop any finding on a canary file from the fix/addition buckets.

## Phase 4: Fix/Addition Split — Gated by Execution Mode
- **Runs only in `PROPOSE` or `APPLY_APPROVED`.** In `AUDIT_ONLY` (the default for a bare audit/analysis request), stop after Phase 3 — the coverage map may still *list* what would land in each bucket, but nothing here executes.
- **Fix bucket** (stale numbers, dead references, policy violations, broken parsing — plain factual corrections): listed under `PROPOSE`; applied only under `APPLY_APPROVED`, and only for items the user approved (a blanket "apply the fix bucket" covers non-protected paths — a protected path always needs its own explicit approval, see Safety Layers)
- **Addition bucket** (new features, structural changes, deletions, upgrades): listed under `PROPOSE`; executed under `APPLY_APPROVED` only per-item after explicit approval — never covered by a blanket approval
- Re-verify after fixing: re-run any affected tests/checkers

## Phase 5: Record the Coverage Map
Create or update the coverage-map file (default `<repo root>/.audit/coverage-map.md`, see Phase 0; same-day re-run = append a pass section):
- Table: `Area | Method label | Findings/actions` — three method labels required: **[deterministic]** / **[LLM judgment]** / **[close read]**
- **State remaining gaps explicitly** (what wasn't reviewed, bounded checks, intentional exclusions) — a map with zero remaining gaps deserves suspicion
- **Assumption Ledger** (conditional addition): if a Phase 3 CONFIRMED verdict depends on an unverified assumption, add a separate table to the map — `Assumption/Parameter | Status | Evidence needed | Materiality (would it flip the verdict?) | Owner`. Five status values: **externally-anchored** (verified by a third party) / **author-calibrated-prior** (an adjusted assumption) / **assertion-only** (unsupported claim) / **open-proposal** (a TODO) / **open-question**. If one or more rows are assertion-only, open-proposal, or open-question AND materiality is High (flipping it changes the verdict), downgrade the final label to `PARTIAL` and name the owner who must resolve it (user / follow-up investigation / tooling). If the CONFIRMED conclusion does not depend on any unverified assumption, the Assumption Ledger may be omitted — if omitted, state "Assumption ledger: N/A (reason)" as one line.
- **Recall line** (only if this run used canaries): append the output of `python3 "${CLAUDE_SKILL_DIR}/scripts/canary_score.py" --summary --skill full-audit` (`recall: k/n (seeded)`, `RECALL_UNMEASURED` while n<5) to the map verbatim. The recall ledger defaults to `~/.claude/full-audit/recall_ledger.jsonl` (outside the install folder, so updates keep it); override it with `--recall-ledger <path>` or the `FULL_AUDIT_RECALL_LEDGER` environment variable.
- End with 1-3 lines on what methodology was established or fixed during this audit

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [BASH] Deterministic sweep (counts/versions/paths/parsing) | Compute a harness maturity score (a different tool's job) |
| [AGENT] Dispatch parallel content review (read-only) | Grant reviewers edit access |
| [EDIT] Apply fix-bucket edits (stale/dead-refs/violations) — **only in `APPLY_APPROVED` mode** | Apply any edit while in `AUDIT_ONLY` or `PROPOSE` mode; execute addition-bucket changes without per-item approval (propose-only) |
| [WRITE] Record the coverage map | Declare "100% done" while hiding remaining gaps |
| [READ] Read the prior coverage map and diff | Silently include areas the user excluded |

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Fix-bucket edit (existing file) | high (git) | L1+L3 (the mode-gate itself is the L3 confirmation — switching to `APPLY_APPROVED` is the approval) |
| Delete/move a file (addition bucket) | medium | L1+L3 (explicit per-item user approval required) + mode-gate (`APPLY_APPROVED` only) |
| Editing a protected config/rules path | medium | L2 (deny — the model cannot edit it directly, if a deny rule exists) + L3 (the user runs the apply script themselves) + mode-gate: reachable **only** in `APPLY_APPROVED`, and only for the specific item the user named, by drafting an edit plus an apply script. There is no path for the model to lift the deny. |

**Layer key**: L1 = written instructions the model is asked to follow (this file); L2 = a physical block outside the model's control (a permission deny rule or a hook); L3 = confirmation by the user (a prompt or the user running the command). The mode-gate counts as L3 only when the user's request names the mode explicitly.

**Protected paths** are the rules, agent-instruction and settings files of the audited project (for example `CLAUDE.md`, a rules folder, settings files). Many setups also keep a **deny-list**: an optional user setting (for example permission deny rules in Claude Code settings) that blocks edits to those paths. If you have no deny-list, this skill still treats those paths as protected by rule: edits only in `APPLY_APPROVED`, only for the named item, and by apply script.

**Guard-degradation observability**: if a Phase 1 checker can't run, don't silently skip it — record `⚠️ check unavailable: [reason]` on the coverage map.

## Invariants (never violate)
1. **Three-layer exhaustiveness**: never report "exhaustive" from structural checks alone. Any area where content review or rule dry-run was skipped gets labeled "[deterministic] only — content/dry-run not executed" on the map. Violation → overstated coverage; the user trusts an area that was never actually reviewed or exercised.
2. **Deterministic wins**: when an LLM's count/existence claim conflicts with a script's result, the script wins. Violation → hallucinated numbers get written into the source of truth.
3. **Fixes and additions stay separate**: plain factual corrections (the fix bucket) are applied only in `APPLY_APPROVED` and only for approved items; additions (new features, structural changes, deletions) are applied only per item after explicit approval. In `AUDIT_ONLY` and `PROPOSE` nothing is applied. Violation → scope creep, and the user's decision rights get bypassed.
4. **Coverage map is mandatory**: never declare completion without recording it. A map with zero remaining gaps needs re-review. Violation → nobody in a future session can tell how far the last audit actually went.
5. **Analysis and execution stay in separate modes**: a bare audit/analysis request defaults to `AUDIT_ONLY` and never auto-advances into Phase 4 execution, and a protected path is never touched outside `APPLY_APPROVED` with that specific item named. Violation → a request to "look at X" silently becomes a request that changed X, including a file protected by a deny rule.

## Error Recovery
| Failure | Detection | Recovery |
|---------|-----------|----------|
| Checker script execution failure | Script errors out | Rewrite and retry once → on repeat failure, record "⚠️ check unavailable" on the map, never treat it as passed |
| Ambiguous scope ("everything" — but everything up to where?) | Scope unclear at Phase 0 | Make the area table explicit and confirm with the user |
| Reviewers disagree with each other, or disagree with the deterministic sweep | Contradictory reports | Deterministic wins → adversarial re-check → escalate to the user if still unresolved |

## Truthful Reporting
1. **No mock deception**: "clean" is reported only from an actually-run check's output. Never mark a check that wasn't run as passed.
2. **Bounded checks are labeled as bounded**: a sample-only or grep-only check gets its bound stated explicitly on the map.
3. **No silent brokenness**: final status is one of `WORKING` / `PARTIAL` / `BROKEN` / `BLOCKED` (stalled on an external unresolved dependency or pending approval) + a bullet list of remaining gaps or blockers.

## Rationalization Table
| Rationalization | Counter |
|------------------|---------|
| "The grep came back clean, so this area is done" | A clean grep means "pattern not found," not "content is sound." Label it [deterministic] only until content review happens (Invariant 1) |
| "Three reviewers found the same thing, so it must be true" | Agreement from reviewers sharing the same blind spot is a false-consensus trap, not confirmation. Verify with citations before accepting |
| "I checked this area last week, skip it this time" | Diff-based scope reduction is fine; silently skipping with no label is coverage inflation |
| "It's a small addition, let's just fix it along the way" | Violates fix/addition separation (Invariant 3). Batch additions and propose them together |
| "I'll do the map later if there's time" | An audit with no map resets to zero for the next session (Invariant 4) |
| "A few UNCERTAINs here and there do not matter" | Individual passes do not hide accumulated risk — 3+ in the same area triggers the composite-accumulation-gate flag (Phase 3) |
| "The user said 'audit', so finding an issue and just fixing it right there is helpful" | An audit/analysis trigger defaults to `AUDIT_ONLY` — fixing without an explicit mode-advance conflates analysis with execution (Invariant 5). Report it in the coverage map instead and wait for `PROPOSE`/`APPLY_APPROVED` |

## Output
- Updated **coverage map** file
- Chat report: **execution mode used, stated first** (`AUDIT_ONLY`/`PROPOSE`/`APPLY_APPROVED`) / list of applied fixes with line anchors (`APPLY_APPROVED` only) / list of proposed fixes and additions (`PROPOSE`/`APPLY_APPROVED`) / verification results (✅⚠️❌) / final status label / remaining gaps / Assumption ledger (if applicable)

> Internal revision history (the plugin's release version is in `.claude-plugin/plugin.json`): r1 (initial release) → r2 (added the coverage-caps-intervention-value step to Phase 1) → r3 (added the AUDIT_ONLY/PROPOSE/APPLY_APPROVED execution-mode gate — a bare audit/analysis trigger now defaults to read-only and never auto-advances to Phase 4 fix-bucket execution or a deny-lift on a protected file; those now require an explicit mode-advance from the user) → r4 (added the single-reviewer batch-size cap to Phase 2 — batch size is a separate axis from parallel-agent count) → r5 (added an opt-in canary-mixing step to Phase 1/2/3/5 — a known-clean and a known-defective file from a bundled example pool are mixed unlabeled into a review bundle, then scored after the fact, as a control for whether "zero findings" means clean or means the reviewer missed it; corrected the deny-lift claim — the model drafts an edit plus an apply script for the user to run, it never lifts a deny itself; added `BLOCKED` to the Truthful Reporting status enum)
