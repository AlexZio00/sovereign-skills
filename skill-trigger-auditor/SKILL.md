---
skill_type: analysis
tools: Read, Grep, Glob, Bash
disallowed-tools: Edit, Write, NotebookEdit
name: skill-trigger-auditor
description: "Audit whether skills, agents and slash commands route correctly and safely, and whether a trigger regression test is needed. Use before changing routing metadata or widening a description."
depends_on:
  skills: []
  agents: []
  files:
    - "scripts/trigger_probe.py"
concurrency_profile:
  read_only: true
  concurrency_safe: true
  destructive: false
tags: [audit, routing, triggers, skills, regression]
triggers:
  - "/skill-trigger-auditor"
  - "trigger audit"
  - "routing audit"
  - "skill routing check"
  - "description collision"
  - "트리거 감사"
  - "라우팅 감사"
user-invocable: true
not_for:
  - "Creating a skill -> use your skill-authoring workflow (collision checks belong there)"
  - "Editing a skill's internal logic without touching its trigger or description -> a normal code review"
see_also:
  - skill: skill-ops
    relation: "skill-trigger-auditor=routing and trigger collision audit; skill-ops=snapshots and usage stats (similar names, different targets)"
  - skill: doc-drift
    relation: "doc-drift=stale or contradictory claims in loaded docs; skill-trigger-auditor=whether the right skill fires on the right input"
---

# Skill Trigger Auditor

Layer: validation / routing audit.

## Dominant variable
**Does the right skill fire on the right input, without collisions?** When that is uncertain, settle it before any other check.

## Discard if
- The skill's description and triggers are not changing: use a general skill-quality audit instead.
- The change is internal logic only, with no trigger change: use a normal code review.
- This session already completed a trigger audit for that skill, and its description and triggers have not changed since.

## Key assumptions
1. **A routing table or skill index is available, if you keep one** (a file that maps intents to skills and names collision winners). If it is missing, collision detection loses precision: say so in the report and audit from the skills' own descriptions.
2. **You can list the installed skills** (user skills in `~/.claude/skills`, project skills in `.claude/skills`, plus plugin skills). If not, only a partial audit is possible: say so.

## Required sequence
1. Apply your safety, permission and truthfulness rules first when the audited skill involves risky actions.
2. Read the current routing table or skill index (if any), the project's agent routing notes (if any), and the list of installed skills.
3. Read the candidate SKILL.md files and only the reference files directly tied to them. If recent failure reports tag a skill as chosen wrongly or applied outside its scope, audit that skill first.
4. Classify each candidate:
   - `should_trigger`: must fire on this input
   - `should_not_trigger`: must stay silent on this input
   - `ask_clarifying_question`: needs clarification before triggering
   - `route_to_governance`: belongs to a higher-level policy or rule layer
   - `blocked_by_risk`: stopped at a risk gate
5. When a description or routing field changes, create at least 1 positive and 1 negative case.

## Audit axes

### 1. Description clarity
Does the `description` state the task type, its boundaries and its collision risk?
- **State the "model would do it alone" case.** Adapted from addyosmani/agent-skills (evals/README.md). If the model tends to handle an input without the skill (the user pastes code or a diff, the request does not say "test" or "review"), does the description say the skill applies there too? The source reports a single-source measurement on a fixed model: that one phrase raised a review skill from 7/27 to 21/27 activations and a TDD skill from 6/24 to 19/24, while adjacent prompts that must not trigger stayed at 0. Treat it as a Claim. When you add such a phrase, also create the matching negative case (same paste, different skill, for example a diff plus a commit-message request).
- Does it name a verb-form task?
- Does it state hard exclusions?
- Does it state priority against skills it can collide with?
- **No procedure words in the description.** The description should hold routing language only. An instruction like "always do X first" in a description is loaded all the time, even when the skill is never invoked, and can distort behavior. The body loads only on invocation, so this risk is limited to the description field.

### 2. Role-class fit
Does the skill type or role fit its failure cost, substitution cost and misfire risk?
- infrastructure (governance, meta): high misfire cost, so explicit-only
- validation: explicit, or triggered by a governance step (a legacy value; new read-only audit skills use `analysis`)
- analysis (read-only diagnosis or audit): low misfire cost; auto-when-matched only when the skill has no write tools
- generation (creates files or content): has side effects, so explicit-only is recommended
- lifecycle (opens or closes sessions, writes memory): mostly writes, so explicit-only is recommended
- quality: treat like analysis (auto-when-matched if it only reports; explicit-only if it also edits)
- workflow / utility: auto-when-matched is acceptable

### 3. Implicit invocation policy
Can Claude pick the skill on its own, without the user naming it?
- `auto_when_matched`: automatic on a description keyword match
- `explicit_only`: the user must name the skill or use a slash command
- `never_auto`: reference-only, persona or lens material

### 4. Risk gate
Does the skill ask for writes, credentials, network access, trading, deletion or deployment? If so, check your risky-action rules and do not recommend `auto_when_matched`.

### 5. Task-skill alignment
A retrieved skill that does not fit the task can push performance below the no-skill baseline: an unrelated skill firing is worse than no skill. Recommend `never_auto` for such a skill.

### 6. Overlap detection
Can two descriptions fire on the same input?
- **Candidate-exposure count.** Count the skill directories, and for every audited trigger phrase count how many descriptions match it. If more than 5 candidates match one phrase, list them. Output fields: `skill_count`, `max_candidates_per_phrase`, `over_limit_phrases[]`. Many candidates split attention and raise wrong picks.
- Collision priority: a higher governance layer beats a lower one. Within one layer the more specific description wins.
- Record each collision winner in your routing table, if you keep one.
- **Name proximity (hard negatives).** Descriptions may not overlap while the skill names are close (same prefix, small edit distance, rearranged domain words), and routing can misfire on name similarity alone. The description-overlap check cannot catch this class. List the skills whose names are close to the audited one, then confirm the actual routing result on hard-negative inputs that must NOT trigger the near-name skill. Also record whether routing read the whole description (single read) or matched early on the start of the name. If a misfire or early match is confirmed, report `NAME_PROXIMITY_RISK: {A} <-> {B}: hard-negative not passed`.

### 7. Behavioral interference (editing one skill changes another)
A self-attention model does not isolate prompt modules from each other. Headings are statistical hints, not namespaces.

**7-1. Semantic overlap scan (always run).** Extract the audited skill's key verb+noun terms (invariants, scope Does / Does NOT, core instructions). Grep the same terms in the other active SKILL.md files. On overlap report `CBL_RISK: '{keyword}' in skill A also appears in skill B: editing may interfere`. With no overlap report `CBL_CLEAR`.

**7-2. Context density warning (always run).** Only descriptions are always loaded (roughly 20 to 250 tokens per skill). A skill body loads on invocation.
- Best source: ask the user to run `/context` and read the real per-category tokens (memory files, skills, custom agents). That is the only ground truth; the estimate below is a fallback.
- Fallback estimate, with two axes kept apart (never sum them as line count x 4):
  - Always fully loaded: rule and memory files, file size in bytes / 4.
  - Description only: the text of each skill and agent `description:` field, bytes / 4.
- Above 40K estimated tokens, report `HIGH_DENSITY: {A}K rules + {B}K descriptions = ~{N}K, confirm with /context`. At 25K or below, print nothing.
- Body length is not the pressure point; the levers are description brevity and the size of always-loaded rule and memory files.

**7-3. Runtime spot-check (`--deep`, opt-in).** Pick the skill closest in meaning to the audited one (from 7-1), describe its expected behavior on a standard prompt, and reason whether it changes before versus after the audited skill is edited. If a change is expected report `CBL_DETECTED: skill B may change when skill A is edited: {concrete path}`. This costs one extra model reasoning pass; routine audits run only 7-1 and 7-2.

### 8. Built-in command collision
Does a skill trigger collide with a built-in Claude Code command?
- Check against the built-in list in your Claude Code version (for example `/help`, `/clear`, `/compact`, `/model`, `/config`, `/permissions`, `/doctor`, `/hooks`, `/agents`, `/review`, `/init`, `/loop`, `/schedule`). The list changes between versions, so verify it against the current docs.
- A description or frontmatter trigger equal to a built-in command: `BUILTIN_COLLISION: '{trigger}' collides with a Claude Code built-in`.
- A prefix overlap (for example `/re` matches both `/review` and `/research`): `PREFIX_AMBIGUITY`.

### 9. Cascade depth
Depth of the chain skill -> agent -> skill. Check whether a SKILL.md uses the `Agent` tool, open each called agent file, and check whether that agent uses the `Skill` tool again.
- depth <= 2: `SHALLOW`
- depth = 3: `DEEP_CASCADE: hard to debug and trace`
- depth >= 4 or a cycle: `CIRCULAR_CASCADE`

### 10. Model migration risk
Does the skill text contain patterns that break when the model changes?
- Hard-coded numeric thresholds ("score 7.5 or higher", "3 or more") depend on a model's output distribution: `MODEL_SENSITIVE: L{line} threshold needs recalibration after a model change`.
- Strict format parsing ("always JSON", "first line is only the score") differs in compliance between models.
- Hard-coded specific model versions (`model: opus-4.6`) are the risk. Generic tier aliases such as `model: sonnet`, `haiku`, `opus` are the normal convention and are not a risk signal (no false alarm).
- If there is no risk, print nothing.

### 11. Resource disclosure
Is the active SKILL.md short, with bulky doctrine, examples and rubrics split into `references/`?
- Over 300 lines: recommend splitting into `references/`.
- Safety boundaries (risky-action gates) stay in SKILL.md.

## Output contract

```
VERDICT: PASS | FIX | HOLD

ROUTING_MATRIX:
  {skill-name}: trigger / no-trigger / defer-to:{other-skill}

COLLISIONS:
  {skill-a} vs {skill-b}: winner={winner}, reason={reason}

REGRESSION_CASES:
  positive: [{input} -> should trigger {skill}]
  negative: [{input} -> should NOT trigger {skill}]
  adversarial: [{ambiguous input} -> expected: {route}]
  note: synthesize new positive cases; do not reuse the skill's own interview examples or trigger list (held-out principle).

HOLDOUT_TEST:
  holdout_prompts: [at least 10: 5 that must fire the skill + 5 that must not]
  scoring:
    precision: true positive / (true positive + false positive)
    recall: true positive / (true positive + false negative)
  pass_threshold: precision >= 0.9 AND recall >= 0.9
  splits: tag every prompt with a `split` —
    tuning (seen while editing the description) / heldout (written and committed BEFORE the edit, not looked at while editing) /
    review (a reviewer's counterexamples) / real (actual misroutes seen in sessions).
    An untagged prompt counts as tuning. In empirical mode the result's `split_metrics` gives precision and recall per split,
    and PASS needs EVERY present split to pass. A split with fewer than 3 measured cases is `too_small`, and one with a
    zero denominator is `UNMEASURED`; either makes the overall verdict INCOMPLETE (not a pass).
    Compare the result's `eval_set_sha256` before and after the description edit to show the heldout prompts did not change.
  route_confusion: [cases where two similar skills both fire on the same prompt]
  empirical_floor: consistent | DIVERGED({case + numbers}) | DECLINED_BY_USER | SKIPPED(cli-missing | script-missing | errored: {reason}) | N/A
    (shown only when Invariant 5 applies, otherwise N/A)
  note: the holdout prompts must be judged by a scorer independent of the author of the audited skill (no self-verification).

INDEX_PATCH_PLAN:
  - routing table: add/update entry for {skill}   (if you keep one)
  - skill index: update role class, description   (if you keep one)

RISK_NOTES:
  - {item}: {risk or unclear boundary}
```

HOLD: PASS is not allowed when the positive and negative cases were not run.

### Mandatory floor and empirical mode
The default HOLDOUT_TEST is one model judgment. Two measured modes exist; both use `trigger_probe.py` in this skill's `scripts/` folder, which spawns tool-restricted `claude -p` subprocesses and observes real Skill tool calls. Adapted from the measurement engine of Anthropic's skill-creator plugin.

`${CLAUDE_SKILL_DIR}` is this skill's folder; Claude Code fills it in. In other agents, replace it with the path where you installed the skill. Use `python` instead of `python3` where only that exists (common on Windows). If the script is missing or fails to start, report `empirical_floor: SKIPPED(script-missing)` and continue on model judgment; do not skip silently.

Probe facts to state in the report when you run it:
- **Skill names**: `--skill-name` is matched exactly against the `skill` value of the Skill tool call. A plugin skill is called `plugin:skill`, so pass that full name (for example `--skill-name my-plugin:my-skill`).
- **Project skills**: by default the probe runs in an empty temp folder, where a project's `.claude/skills` does not load. To probe a project skill pass `--cwd <project folder>`. The probe disallows Bash/Write/Edit/NotebookEdit, so it does not modify that folder.
- **Isolation is partial**: the subprocess still loads your user settings, hooks and MCP servers, which can change routing and add noise. `--strict-mcp-config` skips MCP servers and `--setting-sources project` (or another list) limits settings files; both are opt-in because they can also change which skills are visible. Keep a positive-control query in the eval set when you use them.
- **Errored runs**: a run whose subprocess fails (non-zero exit, timeout, error result) is reported as `errored` with a short reason in `errors`, excluded from `trigger_rate`, `precision` and `recall`, and never counted as "not triggered". A query with no valid run has `pass: null`. If `errored_runs` is above 0 the script exits 3 after printing the JSON: report the reasons, do not treat the result as a clean measurement, and rerun after fixing the cause.

- **Mandatory floor** (Invariant 5 applies): propose a small measurement with 1 positive and 1 negative case. Command: `python3 "${CLAUDE_SKILL_DIR}/scripts/trigger_probe.py" --skill-name <skill> --eval-set <2-case json> --floor --runs-per-query 2 --dry-run`. Check `within_limit: true` in the output (4 calls, cap 5), then rerun without `--dry-run`. If you omit `--runs-per-query` it defaults to 5 (10 calls, over the cap); the dry run still exits 0 in that case, so judge by the `within_limit` field, not the exit code. A real run over the cap stops with an error.
  - Both cases pass: `empirical_floor: consistent`.
  - Either case fails: HOLD, whatever the model judgment said, with `empirical_floor: DIVERGED: {case + trigger_rate}`.
  - Either case errored (no valid run): not a pass and not a fail. Report `empirical_floor: SKIPPED(errored: {reason})`, continue on model judgment, and say the floor was not measured.
  - User declines: you may continue on model judgment alone, but you must write `empirical_floor: DECLINED_BY_USER: precision/recall not measured`. A silent PASS is not allowed.
  - `claude` CLI missing (exit 2): `empirical_floor: SKIPPED: claude CLI not found`; the audit continues.
  - With runs-per-query = 2, a trigger_rate of exactly 0.5 passes a positive case (`>= 0.5`) and fails a negative case (`< 0.5`). If you observe that boundary, say so in one line of the report.
- **Empirical mode** (opt-in, for requests like "precise trigger check" or "empirical trigger test"): the same script at full scale, with a cap of 100 total calls checked before any process is spawned. There is no auto-improvement loop, because it would conflict with Invariant 3.
  - Run `--dry-run` first to show the expected number of calls and the estimated worst-case time (`estimated_max_seconds`, calls x per-call timeout / workers, rounded up to whole waves; most calls end sooner), then dispatch only after explicit user confirmation. The run is read-only but spends real API cost. Each query in the eval set must be unique; duplicates stop the script with exit 2.
  - A trigger counts only when the Skill call's `skill` value equals the target name exactly (substring matching was dropped: `pdf-tools` and `anthropic-skills:pdf` had counted as hits for `pdf`).
  - The result JSON has per query `invoked_skills` (every skill called in that query and the number of runs that called it, to see leaks to non-target or competing skills), `served_models` and `model_unrecorded_runs`, and at the top level `requested_model` and `served_models`. For comparison runs pass a full model ID to `--model`, not an alias such as `haiku`, and quote `served_models` in the report. If it is empty (`model_unrecorded_runs` > 0) write "served model not recorded" and do not guess the model.
  - **Eval set location**: `.trigger-evals/<skill-name>.json` in the working directory (override with the `TRIGGER_EVAL_DIR` environment variable). Format: `[{"query": "...", "should_trigger": true|false, "split": "tuning|heldout|review|real"}, ...]` (`split` is optional, default `tuning`; an unknown value stops the script with exit 2). Without `--eval-set` the script uses this path; a bare name resolves to `<name>.json` in the same folder. A malformed file stops the script with exit 2. This skill cannot write files, so print REGRESSION_CASES as a JSON block in this format and let the main session save it after user approval. A saved set is reused on the next audit, but add at least one newly synthesized positive case to keep the held-out principle.
  - If the `claude` CLI is missing, the script hard-stops instead of falling back to model judgment.
  - Differences from the skill-creator original: it plants a temporary `.claude/commands/{uuid}.md` file to test an unregistered candidate; this skill audits only already-registered skills, so that workaround is not used.

### JSON companion (inline, no file write)
After the output contract print a fenced JSON block. If you need it persisted, use a skill-authoring or audit workflow that can write files; this skill does not write.

```
{
  "skill": "{audited-skill}", "overall_pass": VERDICT == "PASS",
  "score": lower of precision and recall x 100, rounded; null if HOLDOUT_TEST was not run,
  "score_direction": "higher_is_better",
  "verdict": "PASS" | "FIX" | "HOLD",
  "checks": [
    {"id": "collision-{a}-{b}", "category": "collision", "status": "PASS" | "FAIL", "evidence": "..."},
    {"id": "holdout-{query-idx}", "category": "holdout", "status": "PASS" | "FAIL" | "ERRORED", "evidence": "trigger_rate=..."}
  ]
}
```

- If `trigger_probe.py` ran, map its stdout `results[]` into `checks[]` as is; do not rejudge (`pass: true` is PASS, `false` is FAIL, `null` is ERRORED). Put `invoked_skills` (calls that leaked to non-target skills) and `served_models` in `evidence`. Any ERRORED check makes `run_status` `DONE_WITH_CONCERNS` and the VERDICT at most HOLD.
- If neither measured mode ran (model judgment only), `score` is null.
- The score here is quality (higher is better). If you join this JSON with a risk score where higher is worse, use `score_direction` to tell them apart.
- Add `run_status` (DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED) and `unprocessed` (skipped scenarios) at the top level, separate from VERDICT. If any scenario was skipped, `run_status` is `DONE_WITH_CONCERNS` whatever the VERDICT.

## Routing metadata fields
When you register a skill in your skill index (if you keep one), record:

| Field | Meaning | Allowed values |
|---|---|---|
| `role_class` | why the skill is active | `governance_core`, `high_risk_gate`, `domain_specialist`, `workflow_utility`, `reference_rare` |
| `implicit_invocation` | can Claude pick it without being asked | `auto_when_matched`, `explicit_only`, `never_auto` |
| `risk_level` | cost when misrouted | `low`, `medium`, `high` |
| `resource_type` | main artifact type | `active_skill`, `validation_skill`, `reference_lens`, `prompt_pack` |
| `validation_method` | check needed before activation or a routing change | `skill-trigger-auditor`, `manual-review` |

## Safety layers
| Risky action | Reversibility | Layers |
|---|:---:|---|
| Suggesting edits to a routing table or skill index | high | prompt rules + user approval (suggest only, the user executes) |

- Invariant 3: never change skill content; return the audit as a VERDICT.
- INDEX_PATCH_PLAN is a proposal only; apply it after user approval.
- Read-only discipline is a rule you follow, not something the frontmatter enforces: `tools:` and `disallowed-tools:` are descriptive metadata. Do not edit or write files, including through Bash (`echo x > file`). Use only read-style Bash commands, and the probe script.

## Error recovery
| Type | Detection | Recovery |
|---|---|---|
| `missing_data` | routing table or skill index absent | skip that source, report "reference file missing" |
| `logic_inconsistency` | the same pair judged both colliding and not colliding | report both pieces of evidence and return HOLD |
| `tool_failure` | Grep/Glob failed | skip that skill; do not stop the whole audit |

## When to retire this skill
Review it for narrowing, merging or removal if any of these is observed:
- It has not been invoked for 90 days and no other skill or agent calls it. (For a safety or recovery skill, judge by likelihood, failure impact, difficulty of detection and lack of substitutes, not by call count.)
- The same defect comes back three or more times after fixes.
- Another asset gives the same result at lower cost.
- A rule, tool or platform feature it relied on has changed and the premise is gone.

## When a result is invalid
If the files, command output or source text a result relied on look different when re-checked, treat the result as invalid and run it again. A result is valid only for the point in time its inputs were read.

## Invariants (never violate)
1. **No PASS without a negative case.** With positive cases only, return HOLD. Without negative and adversarial cases coverage is incomplete.
2. **Never promote reference-only material to an active skill.** Files in `references/` are not runtime authority and cannot be run directly or given autonomous authority.
3. **Never rewrite the doctrine.** During a trigger audit do not edit the audited skill; return a separate VERDICT.
4. **No implicit firing for risk-gate skills.** Never recommend `auto_when_matched` for a skill that writes, handles credentials, trades or deletes.
5. **No broad trigger expansion without a holdout test.** If you widen a description or add 3 or more triggers, a HOLDOUT_TEST must pass: precision and recall below 0.9 gives HOLD. The mandatory floor above applies whenever this condition holds, and it must be offered to the user.
6. **Empirical mode obeys Invariant 3 too.** Even when a measured run sees a real trigger failure, do not edit the description on the spot. Measure, return the VERDICT, and leave the fix to your skill-authoring workflow. This also covers the mandatory floor: after DIVERGED, still no automatic description edit.
7. **No dispatch without a cost notice.** Show the `--dry-run` call count and time and get explicit confirmation before spawning any real `claude -p` subprocess. This applies to every size, including the floor, with no exception.

## Scope boundary
| Does | Does NOT |
|---|---|
| [READ] SKILL.md files, routing table, skill index, agent routing notes | modify skill content |
| [READ] detect trigger collisions and judge a winner | execute routing policy changes directly |
| [WRITE] print VERDICT, ROUTING_MATRIX, REGRESSION_CASES | judge a skill's internal structural quality |
| [WRITE] propose INDEX_PATCH_PLAN | edit a routing table or skill index without a proposal |

## Rationalization table
| Rationalization | Rebuttal |
|---|---|
| "Passing the positive cases is enough" | Violates Invariant 1. An audit meant to catch collisions with no negative case checked nothing. |
| "This skill is obvious, no audit needed" | Collisions happen on obvious skills too. The broader the description, the higher the collision risk. |
| "The auditor could fix the skill too, more efficient" | Violates Invariant 3. The auditor audits; fixes go to the authoring workflow. |

## Principles
- Ambiguous audit result: return HOLD. Never change routing on your own.
- The auditor is independent of the author. If the same agent builds and audits a skill, that is not an audit.
- For skills with risky actions (write, credential, trading, deletion), Invariant 4 and a user-approval layer are mandatory.
