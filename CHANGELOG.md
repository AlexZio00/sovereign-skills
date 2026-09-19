# Changelog

All notable changes to sovereign-skills are documented here. Recovered from
git/README history (the v6.0 rewrite dropped the changelog section from
`README.md` — this file restores it as a standalone document going forward).

---

## v6.5.12 — 2026-09-19

Refinement release — no skills added or removed; a delta port from the internal fork covering 5 of the 20 skills. `pre-push` also changed upstream, but only in internal-only steps (harness regression-scan wiring, the public-mirror scrub step), so nothing was ported; 13 other skills had no upstream change since v6.5.11, and `code-autopsy` has no internal skill counterpart to diff.

### Changed — per skill
- **integration-intake**: Phase 1.6 gains a conflict-of-interest check and two new checks — (d) plugin lifecycle-hook supply chain and (e) MCP tool-description injection sanitization (now "five checks"). Phase 2.5 item 8's four-axis status is replaced by a seven-stage deployment pipeline (DRAFTED → REGISTERED → DISCOVERABLE → ROUTED → INVOKED → ENFORCED → OBSERVED) with a per-claim Capability Map (unconfirmed claims default to UNCONFIRMED), a descent principle, and a check-coverage caveat. The report template gains a Capability Map line.
- **session-checkpoint**: pending decisions and causal/architectural conclusions carry a `basis: run|doc|dialogue` tag (arXiv 2609.03407, "narrative captivity"). 2+ user interventions on the same topic force `basis` to `dialogue` and raise urgency to at least M. Handoff decisions and the compact state-snapshot `decide` items carry `basis`.
- **doc-drift**: two new sub-signals — CLI interface sync (`[cli-drift]`, arXiv 2608.28497) and invariant erosion (`[invariant-erosion]`, arXiv 2608.17597) — each with an explicit "not checked (N)" report line instead of silent narrowing when the scope is large.
- **goal-lock**: the PLAN GATE runs the single cheapest discriminating check before declaring root-cause uncertainty (S5 now fires only afterwards). S6 asks whether a repeated blocker is an execution error or an input-sheet design error before escalating.
- **full-audit** → v1.3: Phase 2 gains a single-reviewer batch-size cap (arXiv 2609.09696) — batch size per reviewer call is a separate axis from parallel-agent count.

### Docs
- `README.md` and the four translations (`docs/README.{ko,ja,zh,es}.md`) now keep only the latest release note; earlier notes live here. `v6.5.10`, which had existed only in the README, is added below.

## v6.5.11 — 2026-09-06

Bug-fix release driven by an independent third-party audit of the v6.5.9 snapshot (read-only static review + test execution + boundary-input reproduction + official-doc cross-check). No skills added or removed; every one of the 20 skills received at least one fix. Full audit report available on request — this entry summarizes the applied fixes.

### Fixed — deployment blockers
- **Codex compatibility was documented incorrectly.** Per Codex's official skills doc (learn.chatgpt.com/docs/build-skills), Codex discovers skills by scanning `.agents/skills/<name>/SKILL.md` at repo/user/admin/system level — it does not read `agents/openai.yaml` as skill content. README (all 5 languages) previously instructed `cat <skill>/agents/openai.yaml >> .codex/AGENTS.md`; install instructions are now `cp -r <skill> ~/.agents/skills/<skill>/` (or a project-local `.agents/skills/`). All 20 `agents/openai.yaml` files had their non-schema `instructions: "../SKILL.md"` field removed and `allow_implicit_invocation: true` added, matching the actual optional-metadata schema (UI display, icons, invocation policy) rather than duplicating SKILL.md.
- **7 plugin manifests failed `claude plugin validate`** (`code-autopsy`, `doc-drift`, `eval-leakage-audit`, `next-action`, `project-overview`, `skill-ops`, `stepback`) with `skills: Invalid input` — each `.claude-plugin/plugin.json` carried an unsupported `"skills": [{...}]` array field that the 13 passing plugins don't have. Removed the field and brought all 7 up to the same `author`/`homepage`/`repository`/`license` shape as the rest of the repo. `claude plugin validate` now passes clean with zero warnings across all 20.

### Fixed — per skill
- **pre-push** → v3.10.0: the staged-diff secrets scan now also covers the outgoing-commit range (upstream/merge-base..`HEAD`), since `git push` sends already-committed commits, not just staged changes — a secret committed but never staged in this session previously slipped past the scanner entirely. Scanner-script discovery no longer hardcodes `~/.claude`; it now falls back through `~/.claude` → project `.claude/` → the working-tree root. The Autonomy Boundary section's "read-only" claim about test/build runners was corrected — they write local, non-git state (`.harness/test-count-floor.json`, build artifacts).
- **project-overview**: fixed three real bugs in `generate_overview.py` — a corrupted AUTO-block marker pair (orphan START, or END before START) no longer triggers silent auto-splice, which could delete manually-written text or grow a duplicate marker pair on every re-run (now raises and reports `BLOCKED` instead); a single non-UTF-8 handoff file no longer aborts the entire cross-project aggregation (now isolated and flagged, the rest still aggregate); the final status line now actually prints `PARTIAL` when a project is missing a snapshot instead of always printing `WORKING`.
- **session-checkpoint**: `ct_promotion_queue.py` now excludes `[QUARANTINE]`-tagged context-log entries from CT promotion candidacy entirely (filtered before clustering) — previously a quarantined entry could reach the promotion threshold under a `clean:internal` source tag. Moved handoff attestation from Phase 2.4 to a new Phase 4.5, since later phases (3.9, 4) can legitimately rewrite the handoff after the old attestation point, which was causing false `TAMPERED` reports on the next session's guard check. The Key-Files STALE check no longer auto-deletes a MEMORY.md line on the heuristic path-checker's say-so — it now surfaces the finding and waits for confirmation. Fixed a hardcoded personal script path.
- **setup**: normalized all project-rules file path references to `.claude/rules/project-rules.md` (was inconsistently `~/.claude/rules/project rules` / `rules/project rules`, missing the extension). The SubagentStop hook example now parses `agent_id`/`agent_transcript_path` from stdin JSON instead of referencing nonexistent environment variables. Phase 4-2's violation test now verifies the rule is actually installed and auto-loaded from disk rather than testing a rule string pasted directly into the prompt.
- **project-init**: added the missing `.md` extension to a template path reference, resolved a duplicate "Hard Rules change" regeneration-table row that gave two different instructions for the same trigger, and fixed a `.gitignore` template where an inline `# comment` after `Cargo.lock` was silently becoming part of the ignore pattern instead of a comment (`.gitignore` has no inline-comment syntax).
- **project-check**: the `.gitignore`-protection check now runs `git check-ignore -v` and `git ls-files --error-unmatch` instead of trusting string presence in `.gitignore` alone — catches an already-tracked secret file that `.gitignore` can no longer protect. Orchestrator/agent-team absence is no longer penalized when a project shows no agent-routing adoption anywhere (an inferred Minimal profile, by design, per `setup`'s own flow). The score-history feature's claimed per-item Improved/New/Unresolved tracking was corrected to match what it actually stores (aggregate score + category counts only). Fixed an `agents/openai.yaml` description that had wrongly quoted `check-harness`'s "6 axes, 58 items" instead of describing project-check's own 4-dimension scan.
- **code-autopsy**: added a hard-anchor override so a catastrophic-but-cheap-to-fix defect (e.g. data loss, Impact=10/Probability≥8) can no longer be pushed below the Critical gate by a low FixCost score — the Severity formula's weights are unchanged, but this class of finding now bypasses the composite score entirely. Downgraded the "95th percentile of prior reviews" ceiling from an absolute quality bound to an advisory-only signal, since it has no stated comparison group, sample size, or normalization.
- **scope**: `ambiguity_gate.py`'s `quick` subcommand now actually validates its input (all 4 required keys present, numeric type, 0–10 inclusive range) — a single-key JSON, an out-of-range value of 100, and a string value all previously passed silently. Script invocations in SKILL.md now resolve via `find ~/.claude -path "*/scope/scripts/*"` instead of a cwd-relative path that only worked from one specific directory. Removed a circular dependency in Quick Mode's approval gate (the min-items script needed a file that Invariant 5 said couldn't exist yet) via a `.scope-draft.md` scratch file.
- **session-start**: the Autoimmunity Rate metric previously equated "user declined" with "false positive"; it's now labeled as a rejection-rate proxy (upper bound) until a real false-positive signal exists. Context-Rot age checks now use each context-log entry's own `[DATE]` tag instead of the append-only file's mtime (which only reflects the latest write, not any individual entry's date). Split the frontmatter's blanket `read_only`/`concurrency_safe: true` into a `default` profile and a separate `promotion_write` profile, since the MEMORY.md promotion step is neither.
- **collab-audit**: closed an unfalsifiable rebuttal rule where both "disagreement with no counter-evidence" and "no rebuttal at all" were being recorded as confirming a blind-spot claim — both now yield an honest "observation unavailable" instead. `session_hygiene_scan.py` no longer crashes on a malformed session-metadata root (array, non-numeric count field) and no longer auto-classifies a fully empty object as organic. The `.gitignore`-protection check gained the same `git ls-files`-based verification as project-check. The cwd automation-harness heuristic no longer auto-excludes any project with "pipeline" in its name — only stronger multi-signal matches do, "pipeline" alone now routes to a new `uncertain` bucket for manual review.
- **skill-ops**: snapshot duplicate/integrity checks now compare SHA-256 hashes instead of line counts (equal line counts previously masked differing content). The cleanup script now defines its `COUNT` variable, no-ops when retention is under the cap instead of risking a negative argument, and replaces `xargs` with a space-safe read loop. Renamed a "cumulative edit count" label to "retained snapshot count" to match what it actually measures (capped at 5 by the retention policy). Annotated the two distinct scoring scales (`harness_score` 0–100 vs. per-skill `S_Q` 0–10) everywhere a threshold is referenced.
- **integration-intake**: the Provenance & Injection Gate now also covers constraint text destined for rule files and MCP server configs, not just executable skill/agent bodies. Relabeled a same-session/same-model re-read from "independent verification" to "manual re-check" — real independence requires a different vendor or a genuinely separate context. The 90%-redundancy check now requires fixing an explicit numbered list of the candidate's functional claims first, then reporting covered/total, instead of an ungrounded percentage.
- **clean-room**: the fresh-context executor now receives a mandatory minimum safety envelope (one line stating the safe purpose, one line stating the prohibited scope) instead of zero context, closing a "safety-laundering" gap where a fully blind executor could drift back across a boundary it couldn't perceive. Corrected "filesystem isolation" language — the executor shares the same filesystem as the main session; the only real barrier is an instructed restriction on what it may consult. Removed a reference to a "fixed risk catalog" that doesn't exist anywhere in this repo.
- **eval-leakage-audit**: vendor/model-family diversity alone no longer qualifies a reviewer as `independent` — evidence and methodology must also be independent, or the label falls back to `same_vendor`/`unverified`. A single-trial (k=1) result showing both arms ≥95% now yields `ceiling_suspected` rather than a confirmed ceiling, requiring an additional branching probe first.
- **doc-drift**: the 24-hour re-audit cooldown and the <10-file skip are now overridable defaults (`--force-after-change`, or a documented high-risk-small-repo judgment call) instead of hard bans that blocked legitimate immediate regression checks. Evidence-backed findings below the 80% confidence threshold are now preserved under a new `UNCERTAIN` section instead of silently dropped. Personal/global-memory citations are now redacted before being written into a report.
- **goal-lock**: the Stop-hook section now states plainly that the hook script, `settings.json` wiring, and tests are a reference design, not shipped code — adopters must build and test their own. The "production behavior change" masquerading pattern is now scoped to changes that contradict the actual spec, so it no longer flags ordinary TDD RED→GREEN cycles. The DONE EVIDENCE field now branches by artifact type (executable command for code, reviewer sign-off for non-code deliverables). Added `BLOCKED` to the final-status enum for tasks stalled on an external dependency or pending approval.
- **full-audit** → v1.2: added an `AUDIT_ONLY` (default) / `PROPOSE` / `APPLY_APPROVED` execution-mode gate — a bare "audit/analyze" request no longer auto-advances into Phase 4 fix execution or a Protect-Hooks deny-lift; applying anything now requires the user to explicitly name approved items.
- **freeze**: downgraded an "physical block" claim to "instruction-level block," since enforcement is a declared-scope convention, not a sandbox or hook.
- **next-action**: freshness is now checked per candidate's specific underlying source (a lesson entry, a commit) rather than only the handoff file's overall age.
- **stepback**: merged a contradictory "ask once if unclear" / "never ask" pair into a single rule.

### Not this release
The two remaining reported items (project-overview corruption-handling scope beyond what's listed above, and a small number of "upgrade" suggestions — new fixture corpora, dual-gate scoring systems) were treated as out of scope for a bug-fix release and left for a future pass.

Refinement release — no skills added or removed; a delta port from the internal fork covering 11 of the 20 skills.

### Fixed
- **pre-push** → v3.9.0: a real regression — 9 spots across Steps 0/3/4/5a used the `cmd | tail -N; VAR=$?` pattern, which (with no `pipefail` in this shell) captures `tail`'s exit code instead of the underlying command's, so lint, build, and test failures were silently swallowed and reported as passing. Switched each to `${PIPESTATUS[0]}`, or (for the pip-audit case, already routed through `$(...)`) split the exit-code capture from the truncation step so the exit code is read before `tail` runs. Step 4's Python path also gained an opt-in test-count-floor check (WARN-only, pattern credited to CopilotKit/openbot's `scripts/test-ci.ts`): it compares the current pytest passed-count against the previous run's count (a local, gitignored state file) and warns on a sharp drop, catching a file that silently dropped out of collection (e.g. an import-time exception) while still exiting 0. Also corrected a stale pattern count — `scan_secrets.py` already implements 14 patterns (f1–f13 plus the merge-conflict marker check), but the frontmatter and Step 1 body still said 12.

### Changed
- **eval-leakage-audit**: 18→21-pattern taxonomy — adds pattern #19, "Success provenance gap" (distinguishes an agent following authorized-context reasoning from one that simply acquired the target value in transit, via CLEAN/GOLD/SHAM re-scoring to measure the GOLD–SHAM gap); pattern #20, "Lenient-judge-mode non-disclosure" (a self-LLM judge defaulting to lenient grading without disclosing it in the headline number); and pattern #21, "Hardest-category denominator exclusion" (quietly dropping the hardest category from the denominator before computing headline accuracy).
- **doc-drift**: new fourth detection category, Session Leakage (`skills/*/SKILL.md`, `agents/*.md`, `commands/*.md` only) — flags sentences a future reader without this session's transcript couldn't resolve or verify (e.g. "in the previous session", "(decision 3)", unexplained PR/issue references), excluding intentional historical-record annotations kept as an audit trail. Step 0's deterministic pre-filter is now backed by two real scripts, `scripts/slop_detector.py` (AI-tell/hedge-phrase density scorer) and `scripts/claude_md_lint.py` (CLAUDE.md-as-machine-prompt linter), replacing the earlier prose-only description of the same scan. `tools:` frontmatter gained `Bash` to run them.
- **goal-lock**: B5.2 Termination Handshake replaced with Ralph Mode — a context-isolation alternative for unattended/long-running autonomous loops, where each round starts with zero inherited context and state crosses rounds only through the shared workspace plus a single bounded structured handoff (`status/summary/evidence/next_steps/blocker`); it interacts with the existing stagnation circuit-breaker so repeated blockers still escalate to a human even with no memory carried forward. New ATTACK sub-step in the DO phase — a mandatory Tier-0 self-attack that escalates to a new STOP rule under Tier-1 when the change hits one of six conditions (branch/module-boundary change, an unverifiable type-system property, irreversible blast radius, a core-parameter change, a data-collection logic change, or unwarranted confidence), deferring to `doubt-reviewer` instead of self-judging further. The verification relationship is upgraded from a recommendation to a mandatory requirement for any non-trivial code change.
- **session-checkpoint**: added a `kill_if` optional lesson field, the inverse of `escalate_if` — instead of promoting a lesson upward, it names the condition that retires it. A new Regression Detection step cross-checks `kill_if` fields against detected corrections/rejections and flags (never auto-deletes) a matching lesson as `[REGRESSION_CANDIDATE]` pending a later review pass. The Reflexion gate gained a third check, a postmortem 3-condition gate (subtle + systemic + costly-to-rediscover) — a lesson clearing the existing generality/diagnosis gates still needs to clear this before landing in `lessons.md`; the gate exempts the existing success-lesson item.
- **full-audit** → v1.1: new "coverage caps intervention value" step in Phase 1 — before content review begins, the audit counts how many items are actually in scope for the change under review, since that count caps the maximum possible improvement regardless of review depth. Directs reviewer time away from low-cap areas and toward areas where the cap is higher.
- **integration-intake**: Phase 2.5's Graft step gains field-level merge operators for frontmatter/metadata grafts — set-valued fields (`tags`, `depends_on`) use SUM (union), single-value fields (`model`, `description`) use REPLACE (latest wins), immutable identity fields (`name`, `created`) use IMMUTABLE (conflict-flagged, never silently overwritten), and structural body edits use PATCH (positioned insertion). Prevents a graft from collapsing every field into a single latest-wins overwrite.
- **collab-audit**: the four psychological-framework sub-sections (MBTI, DiSC, Enneagram, Big Five) now gate on evidence sufficiency — each is applied only when observation data actually supports it, and when evidence is weak that axis is marked unavailable/low and may be skipped, instead of being applied unconditionally.
- **setup**: Phase 0's Hard Rules conflict check gained an existing-governance-doc probe — before generating the project rules file, scan for a rules file that already covers Fact/Claim/Disclosure-style truth-tagging and voice/prohibited-patterns conventions. If found, generate those sections as a thin stub (pointer to the existing file plus only the project-specific delta) instead of re-typing the full text; true-greenfield projects keep the full template unchanged.
- **scope**: relax three Invariants with justified-exception clauses (behavior change, not a bug fix) — Invariant 2 (Scope OUT ≥ 2), Invariant 4 (question limit 3), and Invariant 7 (Risk Flags ≥ 1) previously had no escape hatch. They now allow a single named exception each when the deviation is explicitly stated: a self-evidently single-item scope may ship with 1 Scope OUT item plus a reason, a 4th clarifying question is allowed once when there's clear evidence it would change direction, and Risk Flags may read "no risk: `<reason>`" when there truly is none. This is a shift from "always enforce the floor" to "enforce the floor unless the model states why it doesn't apply" — a lazy reason still defeats the point, so it shifts scrutiny to review rather than removing the floor. (Note: the deterministic `ambiguity_gate.py` min-items check still hardcodes the unconditional floor with no exception flag — this relaxation is prose-only guidance for now, matching the internal fork's own current state.)
- **session-start**: ships the `harness_observability.py` dependency this release had originally deferred — Phase 2.2 (Model Difference Analysis Reminder) now sources its intervention-log model-tag count from `scripts/harness_observability.py model-tag-count` instead of a per-file `grep -c` sum, and Phase 2.4 (Autoimmunity Rate) now sources `rejections=N total=M rate=X%` from `... rejection-rate --period 30d` instead of a `find` + summed `grep -c` pass; both fall back to a flagged skip if the script fails to run. New Phase 1 Step 0, the state-snapshot v1 fast path — when the handoff carries `session-checkpoint`'s `<!-- state-snapshot v1 -->` compact block, parse `next`/`blocked`/`ctx`/`diff` first and only selectively read the prose sections below, closing the produce/consume gap between the two paired skills (`session-checkpoint` already writes this block; `session-start` couldn't read it until now). Ships `scripts/harness_observability.py`, `scripts/secret_redact.py` (a small secrets-masking helper the former imports), and `scripts/test_harness_observability.py` (11/11 passing). `tools:` frontmatter gains `Bash`.

### Not ported this release
- **project-check**: investigated the internal fork's apparent routing change (merging `/project-init`+`/setup` and adding a `/team-init` step) and found it isn't a real upgrade — `/team-init` isn't a registered trigger anywhere internally (checked `setup`'s own trigger list), so the internal `project-check` is recommending a command that doesn't resolve to anything. The internal copy also dropped a user-level persistent-cache fallback for `Step 6.5: Score Delta Tracking` that the public version already has, and has an empty `depends_on.files` where the public version correctly declares three. On this skill, the public repo is currently more complete than the internal fork, not behind it — nothing ported.

---

## v6.5.10 — 2026-09-06

Refinement release — no skills added or removed; a delta port from the internal fork covering 11 of the 20 skills. (Recovered from the README release note, which was the only place this release had been recorded.)

### Changed — per skill
- **pre-push** → v3.9.0: fixed a real regression where 9 spots used `cmd | tail -N; $?`, which silently swallowed lint/build/test failures instead of reporting them — switched to `PIPESTATUS`; added an opt-in test-count-floor warning; corrected a stale "12 patterns" claim to the actual 14.
- **eval-leakage-audit**: 18→21-pattern taxonomy — adds success-provenance-gap, lenient-judge-mode non-disclosure, and hardest-category denominator exclusion.
- **doc-drift**: new 4th detection category, Session Leakage, backed by two new deterministic scripts.
- **goal-lock**: B5.2 Termination Handshake replaced with Ralph Mode for unattended autonomous loops; new mandatory Tier-0/Tier-1 self-attack step; verification upgraded from recommended to mandatory.
- **session-checkpoint**: new `kill_if` lesson field, a Regression Detection step, and a postmortem 3-condition gate on new lessons.
- **full-audit** → v1.1: new "coverage caps intervention value" pre-audit step.
- **integration-intake**: field-level merge operators — SUM/REPLACE/IMMUTABLE/PATCH — for frontmatter grafts.
- **collab-audit**: psychological-framework sections now gate on evidence sufficiency instead of applying unconditionally.
- **setup**: new existing-governance-doc probe that generates a thin stub instead of a full duplicate template when a project already has compatible rules.
- **scope**: three Invariants — Scope OUT minimum, question-count cap, Risk Flags minimum — now allow a single stated exception each instead of being unconditional floors (a behavior change, not a bug fix).
- **session-start**: ships the `harness_observability.py` script this release had originally deferred, plus a new fast-path that reads `session-checkpoint`'s compact state-snapshot block instead of the full prose handoff.

### Not ported
- **project-check**: investigated the internal fork's apparent routing change and found `/team-init` isn't a registered trigger anywhere, so it's a dead reference rather than a real upgrade; the public version is currently more complete on this skill than the internal fork.

## v6.5.9 — 2026-08-11

Codex/Cursor compatibility complete — packaging-only release, no skill content changes.

### Added
- **agents/openai.yaml** for 5 skills missing Codex agent definitions: `doc-drift`, `eval-leakage-audit`, `next-action`, `project-overview`, `skill-ops`. All 20 skills now ship Codex-compatible agent YAML.

### Changed
- **README.md**: Installation section restructured — Option C now explains Codex `AGENTS.md` integration with `openai.yaml`, Option D covers Cursor and other markdown-reading agents. Requirements updated (scan_secrets.py preferred over .pl).

---

## v6.5.8 — 2026-08-05

Refinement release — no skills added or removed; targeted delta port from the
internal fork since v6.5.7 (6 of 20 skills changed upstream in that window).

### Changed
- **doc-drift**: new "Derivability signal" sub-signal under the Outdated category — a CLAUDE.md/rules line hardcoding a fact that's mechanically reconstructable from the code is structurally drift-prone even when currently correct. Tag such findings `[derivable]` as supporting priority evidence; not a new taxonomy category.
- **integration-intake**: new "Analogy trap check" — a value claim shaped like "X does it this way, so should we" requires three answers (what problem was X solving / is our problem identical on every relevant dimension / what constraints differ) before it counts as evidence; unanswered, treat as insufficient.
- **session-start**: new "Query-conditional load" rule for On-Demand Reference fact files — load only after confirming the conversation actually concerns that topic, not on header/keyword overlap alone.
- **goal-lock**: new optional GOAL field 8, EVAL TYPE (for tasks measuring a skill/hook/gate's own reliability); a Silent Self-Correction row in the Success Masquerading Blocklist (quietly re-running DONE EVIDENCE off the record and reporting only the final pass); a First-Attempt Ledger (record the raw, unmodified first DONE EVIDENCE run before making any changes, report it alongside the final result); an Early Self-Doubt Boundary note (long-reasoning models misjudge remaining budget by up to 24%, causing premature abandonment — trust a hard counter over felt pressure).
- **pre-push**: Key Assumption 3 revised — when the code-reviewer subagent is unavailable, fall back to an inline abbreviated review instead of skipping outright. New Step 3.5, Public-Mirror Scrub (WARN-only push-time backstop for repos that are curated public mirrors of a private source — configurable trigger pattern, org-identifier/section-number sweep, binary-file sweep, branch-name sweep). New opt-in step 6, high-risk gap-sweep second pass (large/high-risk diffs only, dedicated to miss-prone categories a single pass tends to skip: guard loss on move/extract, dataclass mutable-default evaluation, `hash()` non-determinism, lock-scope shrink, side-effecting predicates, asymmetric test setup/teardown, flipped config defaults). New opt-in step 8, multi-angle parallel re-attack (5 lens-pinned code-reviewer instances, user-request-only, for extremely-hard-to-reverse changes). Fix loop gained skip-reason logging (`SKIP_REASON: {finding} — {reason-category} — {one-line reason}`, no silent skips). Error Recovery's code-reviewer fallback now runs an inline abbreviated review rather than skipping.
- **session-checkpoint** → adds `Bash` to `tools:`. New Stage 1, CT promotion queueing (`scripts/ct_promotion_queue.py`, opt-in via a marker file, pure deterministic token-overlap clustering — no LLM judgment, no writes to MEMORY.md/context-log.md itself, only appends candidates to a review queue). Ships with `scripts/test_ct_promotion_queue.py` (35 regression cases, all passing). Invocation-log skip condition clarified — reuses only the two activity-volume legs of the Phase 1.5 Triple Gate (tokens<5000 AND tools<3), deliberately drops the 24h leg (that leg throttles a *different* auto-trigger; applying it here would suppress genuine invocation-log entries and defeat the log's own purpose). `tool_failure` recovery row now cites the shared infra-retry cap (3 attempts) instead of a bare "retry once."
- **code-autopsy**: even though its internal-fork counterpart was absorbed into a code-review agent rather than kept as a standalone skill upstream (see below), the delta was still diffed and ported by hand. Q1 gained 7 more code-smell terms, explicit SOLID-principle naming for dependency-direction violations, a wrapper/proxy forwarding-correctness check, and a governing-rules violation check (quote-only, no inferred "intent"). Q3 gained off-by-one/falsy-zero/copy-paste/unescaped-regex plus Python's mutable-default-argument and late-binding-closure traps. Q7's memory-leak check now names closure-captured-large-object as a pattern. STEP 0 gained a function-level contract check (caller-side precondition/return-type/exception-contract breakage, not just file-level import graphs), an explicit diff-scope pinning step, and a governing-CLAUDE.md/rules discovery step. New re-established-invariant check after the 12Q list — for every deleted/replaced line, name the invariant it guaranteed and confirm the new code re-establishes it (generalizes the fixed-pattern Silent Failure Rules grep into an open-ended check). New [FAST MODE] (`--fast`) tier between the full pipeline and [QUICK MODE] — one read, runtime-bugs-only, capped at 8 findings, no padding.

### Not ported this release
- One session-checkpoint upstream note (a pointer to a long-running research-session skill's resume state) references a skill outside this repo's 20 and was dropped as a dangling reference rather than ported as-is.

---

## v6.5.7 — 2026-07-31

Refinement release — no skills added or removed; several gained working deterministic scripts in place of LLM self-scoring.

### Changed
- **project-overview**: `generate_overview.py` is no longer a stub — fully implemented (registry parsing, state-snapshot extraction, AUTO:START/END block render+replace), actually runs end to end. Added `_escape_table_cell()` (neutralizes `|`/newlines when interpolating another project's handoff text — treats cross-project data as untrusted input) and malformed-marker recovery in `apply_auto_markers()` (END-before-START or missing markers no longer crash or silently corrupt the file — safely re-appends fresh markers). Backed by unit tests (`test_generate_overview.py`) and an integration test (`test_integration.py`), both with generic fixtures. New `## Output` section separates chat report / disk write (AUTO block only) / final status label.
- **scope**: Quick-mode 4-dimension ambiguity gating and Full-mode L2 Decision-clarity gating switched from LLM self-averaging prose to deterministic `scripts/ambiguity_gate.py quick|full` stdout (ok/avg/weakest). BRIEF.md's pre-save minimum-item check (Scope OUT≥2, Risk Flags≥1, Contraindication≥1) now runs through a `min-items` bullet-counting subcommand, with a regression test locking a bug where a bold-text aside inside a section was miscounted as a new header (premature counting cutoff). Invariants 1-10 gained explicit "Violation → ..." consequence clauses. New `## Output` section (pre-approval draft is chat-only, file writes happen only post-approval, final status label required).
- **skill-ops** → v1.2: Health Mode status classification (Active/Low/Unused/Dead/Discarded/Unknown) and Quality Mode structural(S)/usage(U)/S_Q scoring now run through `scripts/skill_health_bucket.py` instead of manual checklist arithmetic. New Invariant + Rationalization Table row documenting "scores come from the script, not eyeballed."
- **collab-audit**: Step 0.6 Source Hygiene Filter (auto-derived/subagent sessions vs organic ones) and the Step 0 minimum-session gate now run through `scripts/session_hygiene_scan.py` (thread_spawn/subagent/agent_nickname/cwd-pattern/originator classification), falling back to manual counting only when no session-metadata directory exists.
- **session-checkpoint**: new Key Assumption — unconfirmed exit codes from timed-out/killed tool calls must be tagged `[UNVERIFIED]`, never recorded as settled fact. Phase 1.7 Reflexion gained two gates before writing a lesson: a generality filter (non-generalizing incidents downgrade to a `context-log.md` ttl:30d entry instead of a permanent `lessons.md` rule) and a diagnosis-completeness check (missing root-cause "why" gets tagged `[DIAGNOSIS_MISSING]`). Raw-observation capture gained a PII-redaction rule (personal remarks generalized to the pattern, not stored verbatim). Key Files verification now calls `scripts/validate_memory_claims.py check-paths` (exit 0/1/2 contract) instead of ad-hoc Glob. New Phase-3 step, **Discoverability Check** — a fact newly added to the memory index this session must have a grep-verified backlink, or it's flagged `[UNDISCOVERABLE]` and an index line is added (catches "recorded a true fact nobody can ever find again").
- **goal-lock**: new scope-check rule — the check surface is file changes *plus* interface/functionality surface, so an unrequested CLI flag or public-API parameter counts as scope creep even when the touched file is technically in-scope. New "chain length" DO-phase risk item (tool-chain/step count is itself a reliability dominant variable — cites benchmarks where accuracy drops as chains lengthen; look for ways to cut step count before optimizing individual steps). The Stop-hook order gate is now a verified implementation (explicit 4-condition AND check including a `stop_hook_active` re-entrancy guard) rather than a described pattern, with a self-test-suite-on-modification requirement. New top-level Safety Layers section (reversibility-tiered classification of the skill's own risky actions). VERIFY failures now use fixed enum labels (`checker_overfit`/`irrelevant_fetch`/`no_fetch`) instead of free text. REFINE's DELTA CHECK gained a self-judgment caveat (self-report isn't independent verification; route high-stakes artifacts through a separate reviewer). New B5.2 Termination Handshake (check for a safe stop point before force-killing a background task; if unreachable and urgent, force-kill but notify the user — silent kill is a B1 honesty violation).
- **code-autopsy**: new Rationalization Table (8 common reviewer self-talk rationalizations + rebuttals — e.g. "no Critical found, do I need all 12Q?", "the score is high so it's fine, right?"). Added a note recommending the Severity/Composite-Score arithmetic be run through a script rather than computed by hand — the formulas are unchanged, only where they're evaluated.
- **eval-leakage-audit**: 17→18-pattern taxonomy — adds pattern #18, "Goodhart co-evolution in self-improving loops" (a self-improving harness grading itself with a scorer it also designed can drift lenient over time; defenses: an undisclosed fixed anchor task + independent judge, periodic lenient-drift checks, an intentionally-broken fixture shipped with any new capability, and validating harness/rule improvements only on new held-out tasks, never the task that produced them). New "Reviewer Independence Honest 4-Label" check operationalizing independence as `independent`/`same_vendor`/`unverified`/`unavailable` instead of a binary call, with a "votes beat purity" quorum rule for same-vendor shortfalls.
- **integration-intake**: `tools:` frontmatter now declares Read/Glob/Grep/WebFetch/WebSearch only (no Edit/Write — read-only/judgment-only physically enforced). `not_for` entries upgraded to redirect pairs. New "Misjudgment Labels" section — 7 fixed enum labels for each phase's characteristic misjudgment (`wrong_source`, `asserted_without_anchor`, `redundancy_assumed`, `scanner_substituted`, `headroom_skipped`, `category_forced`, `bloat_added`).
- **pre-push**: explicit `depends_on` (code-reviewer/security-reviewer/database-reviewer/refactor-cleaner/build-error-resolver/`scan_secrets.py`) and `concurrency_profile` frontmatter. New "Autonomy Boundary" note clarifying read-only git commands (diff/status/branch/log) run without confirmation while `git push` is the pipeline's single gated write action. Added external reference links (OpenSSF Scorecard, OWASP Cheat Sheet Series) under the Supply-Chain step.
- **session-start**: `depends_on`/`concurrency_profile` frontmatter. Phase 2.2 (model-diff reminder), Phase 2.3 (context-rot), and Phase 2.4 (autoimmunity rate) rewritten from "scan the logs and count" prose into deterministic commands with fixed stdout contracts (`rate=N/A` on zero denominator). New unnumbered "L0 Inheritance" section naming two upstream principles by description only (memory-snapshot discipline, session-scope authorization non-restoration).
- **doc-drift**: new Step 0 deterministic pre-filter (ambiguous-wording density scan + CLAUDE.md-as-machine-prompt linter) feeding the Risky/Ambiguous category as supporting evidence only — the confidence≥80% gate (Invariant 2) still decides inclusion. Invariant 1 violations now get the `asserted_without_anchor` enum label.
- **`depends_on`/`concurrency_profile` frontmatter schema** adopted across `full-audit`, `project-check`, `project-init`, `freeze`, `stepback`, `next-action`, and `clean-room`; several of these also gained tool-category-bracket tags (`[READ]`/`[WRITE]`/`[AGENT]`/`[BASH]`/`[EDIT]`) on their Scope Boundary tables, and `full-audit`'s frontmatter description now spells out its 6-phase pipeline inline instead of a generic one-liner.

### Known gap
`project-check` (and a few siblings) gained unnumbered "inherited principle" notes on their Safety Layers/Error Recovery/Key Assumptions/Truthful Reporting headers. A past release (see the entry below, "removed internal framework references... from Safety Layers and Truthful Reporting section headers") deliberately stripped numbered `(L0 §N)` citations from these same headers across all 10 skills. This release's notes are unnumbered/generic principle statements rather than the removed citations, but the header-annotation pattern itself is back — worth a conscious call before the next release builds further on it, rather than assuming it's uncontroversial.

---

## v6.5.6 — 2026-07-24

Refinement release — no skills added or removed; existing skills sharpened.

### Changed
- **eval-leakage-audit**: 13→17-pattern taxonomy — respawn masking (state-snapshot scoring lets a respawn/reset hide a failure), pseudo-replication (probe cells from the same arm miscounted as independent n), stimulus-calibration gap (the grader is fine but the test stimulus never elicits the target behavior), unaudited cost-saving skips (skipped checks left unaudited indefinitely).
- **goal-lock**: an S7 stop rule — STOP before forcing an implementation through when execution evidence (a failing test, a broken existing contract) already contradicts an explicit user instruction, with no post-hoc autonomous "fix" allowed afterward; a B1.1 5-tier evidence-rigor ladder (executed > integration-tested > unit-tested > typed > reasoned) with mandatory `verified:`/`unverified:` tagging, failure-first reporting order, and banned hedge phrases; a "layer laundering" success-masquerade pattern (narrating a unit-test pass as if the user-facing feature works); an evidence-rigor pre-spec note for DONE EVIDENCE involving concurrency/benchmark/long-running claims.
- **full-audit**: a composite-accumulation-gate — flags death-by-thousand-cuts risk when the same file/module accumulates 3+ UNCERTAIN or 5+ combined UNCERTAIN+NIT findings even though each was individually dismissed; an Assumption Ledger for coverage maps whose CONFIRMED verdicts rest on an unverified assumption (5-state table, downgrades to PARTIAL when a high-materiality assumption is unresolved).
- **session-checkpoint**: optional `regime`/`escalate_if` lesson metadata fields; an optional `outcomes` field tracking first-attempt-pass rate, rework rounds, and resolvedBy for goal-lock/verification loops; a second lessons-archival OR-condition (`obs=1 AND >90 days idle`, since `conf<0.4` almost never fires in practice) plus a mandatory cross-reference check before archiving a lesson still cited as completion evidence elsewhere.
- **code-autopsy** → v7.2: a preferred code-smell vocabulary for Q1 findings (Long Method, Feature Envy, Data Clump, etc.); a concrete-failure-scenario requirement (a finding without one is a style opinion, not a defect); object-level authorization added to Q5; expanded network/DB/streaming/async/cache checks added to Q7; a shallow-module deletion-test + ADR-conflict check added to Q8; a numeric confidence-threshold system (security ≥60, other categories <80 excluded from the verdict, Quick Mode lowers the non-security floor to 70); an outcome-ceiling-to-process-metric switch for when compared implementations tie on outcome.
- **pre-push** → v3.8.0: ships `scan_secrets.py` alongside the existing `scan_secrets.pl` (Python preferred when a Python runtime is present, Perl as fallback), plus `LICENSE.txt` restored for upstream (coinangel/claude-pre-push-skill) attribution. Known gap surfaced by this release: the two scanners' pattern coverage is not identical — the Python port adds an f13 Slack-incoming-webhook check the Perl version lacks, and several shared patterns (f1/f2/f4a/f4b/f6/f8/f9/f10) cover a narrower or wider set of variants depending on which implementation runs. Not yet reconciled — tracked as follow-up.

## v6.5.5 — 2026-07-18

Refinement release — no skills added or removed; existing skills sharpened.

### Changed
- **eval-leakage-audit**: 8→13-pattern taxonomy (dual-fail-flag, asymmetric-baseline self-falsification, evidence-burn, ungraded-grader 4-gate check, ceiling-task detection) + a stratification-claim substantiation checklist + an honest reviewer-independence 4-label verdict (independent / same_vendor / unverified / unavailable).
- **goal-lock**: order gate (blocks completion when no verification ran after the last edit), evidence-channel branching (non-exit-code deliverables get a valid channel instead of auto-FAIL), comprehension check, adversarial-criteria design, post-hoc-abstention masquerade pattern, capability-spillover flag-don't-fix.
- **pre-push** → v3.7: cross-bundle joint pass, three-state false-positive gate, deterministic claim-verification (conceptual, degrades gracefully without a script).
- **integration-intake**: headroom pre-classification, trait-vs-procedure termination, triple-check effectiveness claims, independent-source floor, 4-axis adoption status.
- **session-start**: added `claude-sonnet-5` to the model-ID allowlist — fixed a false "invalid model" warning for the current default model.
- **setup**: removed a duplicate `/setup` trigger.
- **full-audit**: rule-dry-run verification layer + kill-test anchor injection.
- **clean-room**: reconciled with upstream autobahn v0.14.0 — independent re-sweep capped at N=1 (not open-ended fan-out).
- **code-autopsy**: Q10 oracle-redefinition detection; report header v7.0 → v7.1.
- Smaller refinements: `session-checkpoint`, `skill-ops`, `collab-audit`, `scope`.

---

## v6.5 — 2026-07-15

### Added
- **eval-leakage-audit**: audits whether an eval/metric/holdout actually
  secures independent external ground truth vs circular self-confirmation,
  using an 8-pattern taxonomy. Read-only. Use before trusting any "how we'll
  know it worked" — A/B tests, holdouts, scores, validation — especially
  when a result feels too clean or self-confirming.
- **doc-drift**: audits the memory/docs Claude Code loads into context
  (CLAUDE.md/MEMORY.md/skills/agents/commands, plus @imports and installed
  plugins) for three issue kinds — outdated claims, mutually contradictory
  statements, and risky/ambiguous wording. Produces a prioritized fix list
  at `.drift-reports/`. Zero config.

### Changed
- **project-init**: fixed a filename-casing bug (`skill.md` → `SKILL.md`,
  which could fail skill loading on case-sensitive filesystems) and
  externalized the Phase 3 templates into `references/templates.md`
  (progressive disclosure).
- **pre-push** → v3.6: added two secret-scanner patterns — f11
  (prompt-injection strings found in diffs) and f12 (non-PyPI supply-chain
  index URLs) — plus a Step 0 Hook Pipeline Health check.
- **scope**: added the Mid-Task Scope Drift (10x-Discovery Rule) — stop and
  surface when scope balloons to a multiple of the original understanding.
- **collab-audit**: added Step 0.6 Source Hygiene Filter, excluding
  auto-derived subagent/thread sessions from being mistaken for organic
  user sessions.
- **full-audit**: added a Safety Layers section (risky-action/reversibility
  /applied-layers table).
- **integration-intake**: added a Safety Layers section.
- **goal-lock**: added a `migration` task template (up+down both succeed,
  data preserved, destructive change needs approval).
- **project-overview**: added a Rationalization Table.
- **stepback**: added a Dominant Variable section + frontmatter fields.

---

## v6.4 — 2026-07-10

### Added
- **full-audit**: exhaustive audit of an entire area (codebase/docs/skills/
  memory/config) via a two-layer method — a deterministic sweep (counts,
  version stamps, path/reference existence, frontmatter parsing, a
  cross-index contract sweep for index-vs-reality and routing-vs-reality
  reconciliation) followed by fanned-out content review with a 4-bucket
  anti-false-positive classification and a per-finding kill-test. Persists
  a coverage map across runs and states remaining gaps explicitly.
- **integration-intake**: a 5-item screening gate (specificity, value,
  structural fit, global applicability, redundancy) for deciding whether to
  adopt an external skill/agent/rule/plugin/MCP pattern, plus a provenance
  and injection-defense check for any imported executable content and a
  skill-evolution protocol for sharpening an existing asset instead of
  creating a new one.
- **clean-room**: carves safety-adjacent requests into a safe scope,
  executed by a genuinely isolated fresh-context subagent that never sees
  the original request, with an adversarial verify pass (including
  re-checking the carve judgment itself) and a descope ledger. Adapted from
  LilMGenius/paperthin's "autobahn" skill (MIT license); this version adds
  filesystem-layer isolation (the subagent is instructed not to consult
  decision logs or session-transcript search tools), ledger-write timing
  (write after the subagent's execution window closes, not before), and a
  fresh-context appeal path for disputed bright-line calls.

### Changed
- **goal-lock**: added a constraint re-echo check to B5 (Long-running
  Tasks) — at each BUDGET-80% checkpoint or progress-resume point, the
  GOAL input sheet's CONSTRAINTS/SCOPE-Exclude get echoed verbatim,
  separately from the status report, so they don't quietly fall out of
  view during extended work as attention shifts to raw progress.
- **session-checkpoint**: added Phase 2.4 (Attestation) — an
  evidence-chain receipt log (`~/.claude/.harness/receipts/YYYY-MM.jsonl`)
  plus a SHA-256 hash sidecar for the handoff file, written via a bundled
  `scripts/handoff_attestation.py`, so a SessionStart hook in the next
  session can detect handoff tampering.

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
