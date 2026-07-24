---
name: full-audit
description: "Exhaustive audit of an entire area (codebase, docs, memory, skills, DB, config). Triggers: '/full-audit', 'audit everything', 'full audit', 'find every gap'."
user_invocable: true
not_for:
  - "Single-file or single-question checks (use a code review instead)"
  - "Harness maturity scoring with a fixed checklist (that's a different, narrower tool)"
  - "A single docs-vs-code drift check (too narrow a scope for this)"
see_also:
  - skill: project-check
    relation: "project-check=fixed-checklist health score, full-audit=open-ended exhaustive sweep with a denominator"
---

# Full Audit — Exhaustive Area Review (v1.0)

## Dominant Variable
**Accuracy of the coverage claim** — the word "exhaustive" ships with a method label or it doesn't ship at all. The moment an unreviewed area gets reported as reviewed, this skill has failed its own purpose.

## Trigger
- `/full-audit [area]` · "audit everything" · "exhaustive audit" · "full audit" · "double-check everything"

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

## Phase 0: Agree Scope + Diff Against Prior Map
1. Declare the target areas as a table (e.g. codebase / docs / global skills / memory / DB / settings).
2. If a prior coverage map exists, read it and **queue its remaining gaps first**.
3. Areas the user explicitly excludes go on the map as "intentionally excluded" — never silently dropped.

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

## Phase 2: Content Review + Rule Dry-Run (Three-Layer Principle)
> **Structural checks (Phase 1) alone do NOT justify calling something "exhaustive"** — exhaustive = structure + content + rule dry-run, three layers. Rules and guards can't be confirmed as actually working just by reading their documentation — only running them against mock input fills in the third layer. The three layers are non-substitutable: structural checks can come back clean while the content is wrong, and the content can be correct while a rule still fails to fire at runtime.
- Fan out parallel review agents (unlimited breadth for coverage, read-only — never give reviewers edit access)
- **Force citations**: reviewers must attach a grep/ls output as proof when they claim something is missing — "I can't find it" from memory alone is invalid
- **Anti-false-positive 4-bucket** (enforce in the review dispatch's output-format instructions): classify every finding as `CONFIRMED / FALSE-POSITIVE (reviewed and dismissed, with a refuting citation) / UNCERTAIN (needs inference — keep it, don't discard, to avoid false negatives) / NIT`, each with a **reasoning note**. `CONFIRMED` at Critical/High needs 2+ of {condition, impact, reproduction} or it gets downgraded to Medium. `FALSE-POSITIVE` needs the discarded hypothesis + a refuting citation (command output or a line quote) — "no issue" in one line is not acceptable. An empty false-positive list is not a penalty (state "none dismissed" explicitly — this prevents over-suppression).
- **Kill-test** (enforce in the dispatch instructions): before reporting each finding, run one command that *tries to refute it*, include the output, and add one line: `(refutation check: output refutes the finding / output is unrelated and insufficient)`. If refuted, it moves to the false-positive bucket. "It's missing" claims must be backed by an exhaustive grep across the whole denominator (explicit regex and scope, `grep -rn <pattern> <root>` — substring matching alone doesn't count). Passing a mock test alone does not count as a refutation (remove the code and re-test instead). The conclusion needs one objective anchor: a rule/linter, an actual execution result, a direct two-point comparison within the reviewed content, or a grep-derived denominator — "it looks like" with no anchor is invalid (inference-requiring cases aren't invalid, they go to UNCERTAIN instead). **Anchor-inject the countables**: for anything a machine can count, hand reviewers Phase 1's deterministic values as a given anchor up front rather than asking them to re-derive it — this keeps reviewers out of the business of re-counting what a script already settled.
- **Rule dry-run (third layer)**: if the target area has rules or guards (linter configs, pre-commit hooks, validation scripts), build an actual mock input (a fixture) and run it through the rule to confirm by execution — not by reading — that it detects or blocks what its documentation claims. Static comparison (does the rule's documentation exist) and content review (does the rule's wording make sense) alone can't prove it fires at runtime — skip this layer and a dead guard (documented but inert) slips through unnoticed.

## Phase 3: Judgment — Dismissing False Positives
Personally re-verify every reviewer report before classifying. Common false-positive patterns to check for:
- **Training-cutoff confusion**: "this date/version can't exist yet" — re-check against the actual current date
- **"Already exists but reported missing"**: any reported "gap" must be re-confirmed to actually be missing via grep before being accepted
- **Historical notation mistaken for staleness**: an original-version marker or changelog entry is history, not staleness — don't "fix" it
- **Number conflicts**: reviewer's number vs. the Phase 1 deterministic number → deterministic wins
- **Composite-accumulation-gate (death-by-thousand-cuts guard)** ([borrowed from PHP-AIO, arXiv 2607.15944v1]): even when every individual finding is separately dismissed as FALSE-POSITIVE/UNCERTAIN/NIT, if the same area (same file/module/component) accumulates 3+ UNCERTAIN findings, or 5+ combined (UNCERTAIN+NIT) findings, flag it separately as an "individually-passed, cumulatively-risky" signal — passing each individual threshold does not mean the composite threshold is also safe (structurally identical to the CRITICAL hard-cap principle in `agents/code-reviewer.md`). A flagged area is not promoted to CONFIRMED, but must be listed at least once in the Phase 4 addition bucket so the user sees it. [The 3/5 thresholds are initial estimates, subject to recalibration once operational data accumulates.]

## Phase 4: Apply Fixes and Additions Separately
- **Fix bucket** (apply immediately): stale numbers, dead references, policy violations, broken parsing — plain factual corrections
- **Addition bucket** (propose only): new features, structural changes, deletions, upgrades — summarize and propose, execute only after user approval
- Re-verify after fixing: re-run any affected tests/checkers

## Phase 5: Record the Coverage Map
Create or update a coverage-map file (same-day re-run = append a pass section):
- Table: `Area | Method label | Findings/actions` — three method labels required: **[deterministic]** / **[LLM judgment]** / **[close read]**
- **State remaining gaps explicitly** (what wasn't reviewed, bounded checks, intentional exclusions) — a map with zero remaining gaps deserves suspicion
- **Assumption Ledger** ([borrowed from Uncertainty Ledger, arXiv 2607.16112], conditional addition): if a Phase 3 CONFIRMED verdict depends on an unverified assumption, add a separate table to the map — `Assumption/Parameter | Status | Evidence needed | Materiality (would it flip the verdict?) | Owner`. Five status values: **externally-anchored** (verified by a third party) / **author-calibrated-prior** (an adjusted assumption) / **assertion-only** (unsupported claim) / **open-proposal** (a TODO) / **open-question**. If one or more rows are assertion-only, open-proposal, or open-question AND materiality is High (flipping it changes the verdict), downgrade the final label to `PARTIAL` and name the owner who must resolve it (user / follow-up investigation / tooling). If the CONFIRMED conclusion does not depend on any unverified assumption, the Assumption Ledger may be omitted — if omitted, state "Assumption ledger: N/A (reason)" as one line.
- End with 1-3 lines on what methodology was established or fixed during this audit

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| Deterministic sweep (counts/versions/paths/parsing) | Compute a harness maturity score (a different tool's job) |
| Dispatch parallel content review (read-only) | Grant reviewers edit access |
| Apply fix-bucket edits immediately (stale/dead-refs/violations) | Execute addition-bucket changes without approval (propose-only) |
| Record the coverage map | Declare "100% done" while hiding remaining gaps |
| Read the prior coverage map and diff | Silently include areas the user excluded |

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Fix-bucket edit (existing file) | high (git) | L1 |
| Delete/move a file (addition bucket) | medium | L1+L3 (explicit user approval required) |
| Editing a protected config/rules path (deny-listed) | medium | L1+L2+L3 (temporarily lift the deny → edit → restore immediately) |

**Guard-degradation observability**: if a Phase 1 checker can't run, don't silently skip it — record `⚠️ check unavailable: [reason]` on the coverage map.

## Invariants (never violate)
1. **Three-layer exhaustiveness**: never report "exhaustive" from structural checks alone. Any area where content review or rule dry-run was skipped gets labeled "[deterministic] only — content/dry-run not executed" on the map. Violation → overstated coverage; the user trusts an area that was never actually reviewed or exercised.
2. **Deterministic wins**: when an LLM's count/existence claim conflicts with a script's result, the script wins. Violation → hallucinated numbers get written into the source of truth.
3. **Fixes and additions stay separate**: only apply plain factual corrections immediately; everything else is propose-only. Violation → scope creep, and the user's decision rights get bypassed.
4. **Coverage map is mandatory**: never declare completion without recording it. A map with zero remaining gaps needs re-review. Violation → nobody in a future session can tell how far the last audit actually went.

## Error Recovery
| Failure | Detection | Recovery |
|---------|-----------|----------|
| Checker script execution failure | Script errors out | Rewrite and retry once → on repeat failure, record "⚠️ check unavailable" on the map, never treat it as passed |
| Ambiguous scope ("everything" — but everything up to where?) | Scope unclear at Phase 0 | Make the area table explicit and confirm with the user |
| Reviewers disagree with each other, or disagree with the deterministic sweep | Contradictory reports | Deterministic wins → adversarial re-check → escalate to the user if still unresolved |

## Truthful Reporting
1. **No mock deception**: "clean" is reported only from an actually-run check's output. Never mark a check that wasn't run as passed.
2. **Bounded checks are labeled as bounded**: a sample-only or grep-only check gets its bound stated explicitly on the map.
3. **No silent brokenness**: final status is one of `WORKING` / `PARTIAL` / `BROKEN` + a bullet list of remaining gaps.

## Rationalization Table
| Rationalization | Counter |
|------------------|---------|
| "The grep came back clean, so this area is done" | A clean grep means "pattern not found," not "content is sound." Label it [deterministic] only until content review happens (Invariant 1) |
| "Three reviewers found the same thing, so it must be true" | Agreement from reviewers sharing the same blind spot is a false-consensus trap, not confirmation. Verify with citations before accepting |
| "I checked this area last week, skip it this time" | Diff-based scope reduction is fine; silently skipping with no label is coverage inflation |
| "It's a small addition, let's just fix it along the way" | Violates fix/addition separation (Invariant 3). Batch additions and propose them together |
| "I'll do the map later if there's time" | An audit with no map resets to zero for the next session (Invariant 4) |
| "A few UNCERTAINs here and there do not matter" | Individual passes do not hide accumulated risk — 3+ in the same area triggers the composite-accumulation-gate flag (Phase 3) |

## Output
- Updated **coverage map** file
- Chat report: list of applied fixes (with line anchors) / list of proposed additions / verification results (✅⚠️❌) / final status label / remaining gaps / Assumption ledger (if applicable)
