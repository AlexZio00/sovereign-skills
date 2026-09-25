---
name: goal-lock
description: "Agent Discipline Engine — lock the goal, run PLAN→DO→VERIFY→FINALIZE→OUTPUT loop, detect success masquerading. Triggers: '/goal-lock', '/goal-lock quick', 'goal lock', 'task harness'."
user-invocable: true
not_for:
  - "Simple questions/conversation (no code changes)"
  - "Single file 1-line fix"
see_also:
  - skill: scope
    relation: "scope=planning lock, goal-lock=execution lock"
  - skill: freeze
    relation: "freeze=zone freeze, goal-lock=goal loop"
  - skill: verification
    relation: "goal-lock's VERIFY/REFINE loop is implementer self-check, not independent verification — an independent verification pass after FINALIZE is mandatory for any non-trivial code change, not merely recommended"
  - skill: doubt-reviewer
    relation: "ATTACK Tier-1 reuses doubt-reviewer's trigger conditions and defers to it via S8 rather than dispatching it directly — goal-lock has no sub-agent dispatch of its own (see B5), so the calling session must dispatch doubt-reviewer and resume goal-lock with its verdict"
---

# /goal-lock — Agent Discipline Engine v1.0

> Lock the goal. Run the loop. Ship clean.
>
> Prevents agents from drifting off target, masquerading success, or creeping scope.
> Quality through enforced loops, not prompt obedience.

## Dominant Variable
**Is DONE EVIDENCE verified by actual execution?** — What the agent says is done vs what is actually done. Closing this gap to zero is the purpose of this skill.

## Trigger
- `/goal-lock`
- `/goal-lock quick` (Quick mode)
- "goal lock"
- "task harness"

## Discard If
- Simple question/conversation (no code changes)
- goal-lock already active in this session
- Single-file 1-line fix — goal-lock overhead > the work itself

---

## Architecture: 2 Layers

```
[A] GOAL Input Sheet — fill per task (goal definition)
[B] Fixed Loop — same for every task (execution discipline)
```

Missing/contradictory input → STOP. Conflicts → PRIORITY. STOP RULES → halt.

---

## Mode Selection

| Mode | Condition | Input Sheet | Loop |
|------|-----------|-------------|------|
| **Quick** | 1 file, clear change, ≤10 lines | 3 fields (GOAL/DONE/SCOPE) | DO→VERIFY only |
| **Full** | Everything else | All 7 fields | B1~B5 full |

User specifies `/goal-lock quick`, or change fits Quick criteria. When unsure, use Full.

---

## [A] GOAL Input Sheet

### Full Mode (7 fields)

```markdown
## GOAL Input Sheet

### 1. GOAL
[Single measurable goal. No expansion.]

### 2. DONE EVIDENCE
[Completion proof. The evidence contract branches by artifact type —
don't force one shape onto both:]
- **Code artifact** → command to run + expected result. No subjective
  criteria.
  e.g.: `pytest tests/test_X.py -v` → 5 passed
  e.g.: `curl localhost:3000/api/health` → 200 OK
- **Non-code artifact** (writing, analysis, reports, designs, prompts, spec
  docs) → no exit code exists to demand. State the review contract instead:
  what a reviewer checks off, or what a named approver signs off on (e.g.
  "reviewer confirms the 3 required sections are present and each claim
  cites a source" or "user approves the draft"). This feeds directly into
  the REFINE loop below (VERIFY/REFINE split) rather than VERIFY's execution
  path.

**Adversarial criteria design**: when setting DONE EVIDENCE, ask first "how
could an agent game this criterion." An unblocked loophole tends to get
found eventually — threshold relaxation, mock wrapping, hardcoding all
exploit a DONE EVIDENCE that was underspecified to begin with. Check for
loopholes at design time, especially on long-running or repeated tasks.

**Evidence-Rigor Pre-spec** [borrowed from ultraprompt]: when DONE EVIDENCE
includes concurrency, benchmark, p99-style statistics, or long-running-process
claims, pre-check the verification agent's evidence-rigor rules (N≥5 repeats,
before/after symmetry, evidence-scope matching, flaky-means-new-bug,
positive-signal-required) and write DONE EVIDENCE to already satisfy them —
this prevents a later insufficient-evidence rejection at the verify step by
fixing the design at spec time instead.

### 3. CONTEXT
[Current state · existing structure · prior decisions · dependencies · known constraints]

### 4. STARTING POINT
[Files/logs/tests to look at first. Start here, no broad exploration.]

### 5. SCOPE
- **Include**: [Editable area + required work]
- **Exclude**: [Out of bounds · unrelated refactors · new features · production behavior changes]
  - **Capability-spillover (flag, don't fix)**: other bugs, design/structural
    improvement ideas, or similar edge cases noticed mid-task all stay in
    Exclude. Report them separately (one inline line, or a follow-up task)
    and return to the current GOAL. Stronger models trend toward "fixing it
    all while I'm in here" — scope is a lock, not a ceiling.

### 6. CONSTRAINTS
- New dependencies: allow/forbid
- Network/API calls: allow/forbid
- Commit/PR/push: allow/forbid
- Migration/DB changes: allow/forbid
- Destructive actions: allow/forbid

### 7. BUDGET
[Time/token/call/cost limits. Follow if given, don't invent if not.]

### 8. EVAL TYPE (optional — only for tasks measuring a skill/hook/gate's own reliability)
[yes — this GOAL measures whether the verification logic itself actually works]
[no or omit — regular implementation. Normal DO→VERIFY iteration is allowed]
```

### Quick Mode (3 fields)

```markdown
## GOAL (Quick)

### 1. GOAL
[One-line goal]

### 2. DONE EVIDENCE
[One verification command]

### 3. SCOPE
- **Include**: [Files to modify]
- **Exclude**: [Don't touch]
```

### Scope Check Surface

SCOPE Include naming a file is not blanket permission for everything inside
it. The scope check surface is **file changes + interface/functionality
surface** — an unrequested CLI flag, a new public API parameter, or a test
scenario broader than what was asked for is scope creep even when the file
it lives in sits squarely inside SCOPE Include. Applies to both Quick and
Full mode: "the file is in scope" answers a different question than "was
this specific change asked for."

### Auto-fill Rules

Fields extractable from conversation context are **auto-filled and shown for user confirmation**:
- GOAL: from user's last request
- CONTEXT: current git status + recent commits + related files
- STARTING POINT: files mentioned in GOAL, or git diff files

After auto-fill: `"Input sheet filled. Proceed if correct, or tell me what to change."` — never proceed without confirmation.

### Input Validation

Any of 7 fields (Quick: 3) **missing or contradictory → don't guess, STOP.**

- GOAL contains 2+ independent goals → STOP ("Please narrow to one goal")
- DONE EVIDENCE is subjective ("if it works well") → STOP ("Replace with executable verification command")
- SCOPE Include and Exclude overlap → STOP ("X appears in both Include and Exclude")
- BUDGET missing → OK (just don't invent one)

---

## [B] Fixed Loop

### B1. Always-ON Guards (never violate)

**Honesty** (highest priority):
- Never hide failure, uncertainty, or unverified results
- Mark uncertain judgments as uncertain

**Success Masquerading Blocklist**:
| Pattern | Description |
|---------|-------------|
| Test deletion/disable | Delete failing tests or neutralize with skip/xfail |
| Mock wrapping | Assert only mock return values and report "passed" |
| Threshold relaxation | Lower the bar to pass |
| Benchmark condition change | Change measurement conditions to improve numbers |
| Failure log suppression | Send error output to /dev/null or catch-all |
| Hardcoding | Hardcoded results matching test inputs |
| Requirement reinterpretation | "Actually this was supposed to work like..." |
| Acceptance criteria weakening | Subtly lower DONE EVIDENCE standards |
| Production behavior change | Modify production logic in a way that contradicts the actual requirement/spec to make a test pass — normal RED→GREEN (writing the minimal production code a correct failing test demands) is not this pattern; the violation is the *direction* of the change, not the fact that production code changed after a test |
| Goal-lock declaration ignored | Declare "proceeding with goal-lock" then skip the input sheet |
| Structural fix reported as upgrade | Report boilerplate additions as "substantive improvements" |
| Ralph Wiggum (early completion) | Skip VERIFY or run it partially, then jump to OUTPUT. Emit completion signal from an incomplete state |
| CEF Thanatosis (external failure fabrication) | Evading constraints via unverified failure claims like "API error"/"file not found"/"permission denied". Failure reports must be accompanied by actual Bash/Read execution results |
| Post-hoc abstention | Execute an irreversible action first, then declare "failed"/"on hold" after the fact. Abstention judgment is only valid before the commit-point gate — declaring it after the action has already landed is still success masquerading |
| Layer laundering | Narrating a unit-test pass as if it proves the user-facing feature actually works — laundering one evidence layer as a higher one |
| Silent self-correction | On an EVAL TYPE=yes task, quietly re-running DONE EVIDENCE multiple times off the record to hide failures, then reporting only the last (passing) run |

**Language-specific patterns**:
- Python: `@pytest.mark.skip`, `@pytest.mark.xfail`, `mock.return_value` abuse
- JavaScript: `test.skip`, `.only` left in, `jest.fn()` chains bypassing real logic
- Go: `t.Skip()`, `//go:build ignore`
- Rust: `#[ignore]`, `#[should_panic]` misuse

**Judgment-reversal discipline** (arXiv 2608.11624, 2608.21377): when user pushback lands mid-loop, sort it into one of three buckets before reacting — (a) **a new fact** (a new log, a new requirement, a new constraint) → incorporate it, (b) **a pointed-out reasoning error** (they name which premise or step is wrong) → re-examine that specific point, (c) **pressure or preference with no new information** ("are you sure?", "look again", "that doesn't seem right") → restate your original reasoning once, and if nothing they said actually invalidates a specific premise, **keep the original judgment**. When a judgment does change, log it in OUTPUT as `prior conclusion → new conclusion (reason: ...)`. Reversing a conclusion under pressure alone, with no new information, is success masquerading of the same weight as the patterns above.

### B1.1 Evidence-Rigor Ladder + Reporting Order [borrowed from ultraprompt]

**5-tier evidence ladder** — no claim can outrank this ladder:
`executed (actually observed running) > integration-tested > unit-tested > typed (type-checked only) > reasoned (reasoning only)`

Every claim must state its tier: `verified: {concrete evidence}` or
`unverified: {reason}`. An unlabeled "it's done"-type claim is not allowed.

**Failure-first reporting order**: describing successes first and only
mentioning failures afterward is itself an anti-pattern ("burying the
failure") — report failed/unverified items first, successes after.

**Banned hedge phrases**: "should work", "probably fine", "this looks right"
and similar are explicitly banned. If unverified, write `unverified: {reason}`
instead.

### B2. PRIORITY (on conflict)

```
0 Honesty → 1 Stability → 2 Preserve existing behavior → 3 Verifiability → 4 Performance → 5 Code cleanup
```

### B3. Execution Loop

```
PLAN → DO → VERIFY(code) → FINALIZE → OUTPUT
              ↘ REFINE(non-code) ↗
```

#### PLAN GATE
- **No immediate fixes.** Identify root cause + short plan first.
- Big changes, schema changes, dependency additions, production behavior changes → **stop and get approval.**
- Plan is 3 lines max. Steps, not documents.
- **If several root-cause candidates exist and there isn't enough information to rank them**: don't just list the candidates and move on — first run the single cheapest check that discriminates between them, within this skill's own tools (Read, Bash, etc.). If you are still uncertain afterwards, STOP at S5.

#### DO
- **Minimum change** to achieve GOAL. Don't touch SCOPE Exclude.
- Before starting, **check RISKS** (applicable items only):

| Risk | Check |
|------|-------|
| Breaking change | Will existing callers break? |
| Race condition | Concurrent access to shared resource? |
| Stale state | Cache/state might not update? |
| Data loss | Irreversible deletion/overwrite? |
| Security | Input validation, permissions, secret exposure? |
| Perf regression | O(n²) introduction? |
| Backward compat | Existing API/interface changing? |
| Chain length | Can the total number of steps/tool calls be cut before optimizing any single step? |

**Chain length as a dominant variable**: reliability tracks step count, not
just each step's individual correctness. Benchmarks show tool-chain accuracy
falling from roughly 39% to 13% as chains lengthen, and sequential-turn-depth
scores dropping from 82.3 to 51.2 over comparable depth increases — longer
chains fail more often even when every individual step looks reasonable.
Before tuning how a step is done, ask whether it needs to exist at all;
fewer, more consequential steps beat more, smaller ones.

Risk detected → return to PLAN with avoidance strategy.

**ATTACK (mandatory sub-step in Full mode)**: if any RISKS item above is
checked "yes," attack the plan yourself before executing it — enumerating
risks and actually trying to break the plan are not the same exercise.

*Self-assessed depth*: informally gauge your own reasoning capability tier
and scale ATTACK's depth to it — a lighter-capability tier warrants the full
RISKS list plus multiple lenses below, a stronger tier can compress this to
a one-line self-check. When unsure which tier applies, default to the more
thorough end rather than assuming a strong tier.

**Tier-0 (always — reuses only the lens concept from an independent
adversarial-review skill, not its full machinery)**: apply as many of these
lenses as the self-assessed depth calls for — decompose / invert / draw an
analogy / push to the extreme / follow the incentive / check for
grandfathered assumptions — to attack your own plan. Don't import a full
independent reviewer's claim/evidence separation or ground-truth testing
here — doing so just turns this into a shrunken copy of that skill for no
net benefit. Sort findings into four buckets — actionable / tradeoff /
contract-misread / noise — and tag them `[self-attack, non-independent]`:
this is goal-lock interrogating itself, not an independent check, and the
label says so. An actionable finding sends you back to PLAN for an
avoidance strategy. Tradeoff/contract-misread findings get logged in
CONTEXT only. Discard noise.

**Tier-1 (conditional — defer to doubt-reviewer, or an equivalent
adversarial pre-implementation review skill, instead of judging further
yourself)**: if GOAL/SCOPE/CONTEXT match any of the following, stop
self-judging and halt with **S8**: a change to branching or module
boundaries · a property the type system can't verify · an irreversible
blast radius · a change to a core parameter · a change to data-collection
logic · confidence that outruns the certainty actually behind it. (These
six are a subset of a broader trigger set such a review skill might use on
its own — two related conditions are deliberately handled elsewhere
instead: the same approach failing repeatedly is S6's job, and "right
before declaring a large task complete" is a known gap goal-lock doesn't
cover by itself — the calling session should judge whether that review is
warranted at FINALIZE time for large tasks.) goal-lock is a single-process
skill with no sub-agent dispatch of its own (see B5) — it cannot invoke
doubt-reviewer directly. The calling session dispatches it and resumes
goal-lock with the resulting verdict.

**First-Attempt Ledger**: before making any changes, run the DONE EVIDENCE
command once and record the raw result under a `## First run (raw)` field in
`.goal-lock-progress.md`. Root-causing, fixing, and re-running proceed as
normal after that. OUTPUT reports the first-run result side by side with the
final result — hiding the first failure and reporting only the final pass is
success masquerading.

#### VERIFY (Code) / REFINE (Non-code)

Branches by artifact type:

**Code artifacts** → VERIFY: **actually execute** the verification specified in DONE EVIDENCE.

**DONE EVIDENCE ↔ GOAL alignment check** (Building to the Test):
Before running verification, confirm: does DONE EVIDENCE actually prove GOAL?
Agents tend to "build what gets checked, not what was asked." Passing DONE
EVIDENCE while GOAL remains unmet is still a FAIL.
- GOAL: "add search feature" / DONE EVIDENCE: "pytest passes" → confirm the
  test actually validates search functionality
- If DONE EVIDENCE measures something unrelated to GOAL → STOP + rewrite
  DONE EVIDENCE

**Verification recipes** (auto-detect stack):
| Stack | Command |
|-------|---------|
| Python (pytest) | `pytest -q` + `ruff check` (if available) |
| JavaScript (jest) | `npm test` + `npx eslint .` (if available) |
| TypeScript | `npx tsc --noEmit` + `npm test` |
| Go | `go test ./...` + `go vet ./...` |
| Rust | `cargo test` + `cargo clippy` |
| General | `git diff --stat` (verify change scope) |

Items not verified: `NOT RUN: {label}` using the failure-label enum below,
plus a one-line detail. Never "it should be fine."

**GroundEval**: verify that verification tool calls **actually executed**. If the OUTPUT claims "tests passed" but no `pytest`/`npm test` Bash call exists in the tool history, the claim is ungrounded. Every verification claim in OUTPUT must trace back to an actual tool invocation.

**Failure-label enum**: when a verification claim can't be grounded,
classify it with one of these fixed labels instead of a free-text reason —
labels are greppable and comparable across runs, prose isn't:
- `no_fetch` — no verification tool call exists in the tool history at all
- `irrelevant_fetch` — a tool call happened, but it checked something other than DONE EVIDENCE
- `checker_overfit` — the check ran, passed, and traces back to a real tool call, but is narrow enough that a broken implementation would pass it too

**Evidence channel branching**: not every DONE EVIDENCE produces an exit
code. If DONE EVIDENCE is a visual artifact, confirm via rendered output
(screenshot / extracted page text); if it's a read-only analysis, confirm
via artifact comparison. Absence of an exit code is not an automatic FAIL —
but regardless of channel, "no evidence produced" is still NOT RUN.

**Non-code artifacts** (writing, analysis, reports, designs, prompts, spec
docs) → REFINE: artifacts without an executable verification command are
validated through a self-review loop.

1. **CRITIQUE** — re-read the artifact and identify the "3 weakest points."
   Be specific about where and why each is weak.
   Weakness types: insufficient evidence / logical leap / vague wording /
   missing perspective / structural imbalance / potential for reader
   misunderstanding
2. **REWRITE** — rewrite only the identified weaknesses, once. Leave strong
   parts untouched.
3. **DELTA CHECK** — compare original vs rewrite:
   - improved → adopt rewrite → FINALIZE
   - negligible difference or worse → keep original → FINALIZE
   - can't tell → note "REFINE performed, improvement uncertain" → FINALIZE
   - **Self-judgment caveat**: CRITIQUE → REWRITE → DELTA CHECK is the same
     agent grading its own work — a self-report, not an independent check.
     Treat "improved" as a working judgment, not proof. For high-stakes
     artifacts (specs, published content, anything a real decision gets
     made from), route the result through a separate reviewer pass after
     FINALIZE instead of trusting DELTA CHECK alone.
4. **1-round limit** — REFINE runs at most once. A second round has
   diminishing returns. No infinite self-correction loops.

**REFINE eligibility criteria:**
- DONE EVIDENCE has an executable command → VERIFY
- DONE EVIDENCE is a content criterion ("includes X", "explains Y",
  "analyzes Z") → REFINE
- Both present → VERIFY first, then REFINE after passing (code + docs
  delivered together)

#### FINALIZE
- After goal achieved, **no additional refactoring.**
- Clean up: temp code, debug prints, failed experiments, junk files.
- Before reporting: **re-check scope + verification** — didn't touch Exclude, met DONE EVIDENCE.
- **Comprehension check**: can the key change be explained in one sentence?
  If not, flag `⚠️ High complexity — review recommended` in OUTPUT. Code you
  can't explain is debt.

#### OUTPUT
```markdown
## Result

**Changed files**: [list]
**Key changes**: [what and why]
**Completion evidence**: [commands run + results] or [REFINE: original→rewrite DELTA summary]
**Verification tool calls**: [actual tools invoked during VERIFY — GroundEval principle] or [REFINE: 3 CRITIQUE weaknesses + REWRITE fixes]
**Verification**: [passed/failed/not run — each with reason] or [REFINE: adopted/kept original/uncertain]
**Risks/trade-offs**: [if any]
**Remaining known issues**: [if any]
**Follow-up work**: [if any]

**Final status**: WORKING / PARTIAL / BROKEN / BLOCKED
```

- PARTIAL: partially working, list specific defects
- BROKEN: core functionality not working, state cause
- BLOCKED: cannot proceed due to an external unresolved dependency or
  pending user approval — not a code defect. List exactly what's being
  waited on (which dependency, which decision, from whom)
- Claiming "done" while PARTIAL/BROKEN/BLOCKED = success masquerading (B1 violation)

### B4. STOP RULES (halt and ask — no progress until answered)

| # | Condition | Action |
|---|-----------|--------|
| S1 | Goal splits into 2+ independent goals | "Goal is branching. Which one first?" |
| S2 | Input missing/contradictory | Specify exactly what's ambiguous |
| S3 | Need to change SCOPE Exclude area | "Need to modify X but it's Excluded. Allow?" |
| S4 | Destructive / external side effect needed | "DB deletion/API call/push needed. Proceed?" |
| S5 | Insufficient confidence in root cause **after** the PLAN GATE discriminating check | "Not sure if cause is A or B" |
| S6 | Same blocker repeated (2+ times) — stagnation circuit breaker | Ask one question before escalating: "Is this repetition a problem with how DO is attempting it, or was the GOAL input sheet (GOAL / DONE EVIDENCE / SCOPE) set up wrongly from the start?" If it looks like an **execution error** (approach problem), report "Same problem repeating. Need to change the DO approach" and escalate to a human. If it looks like a **design error** (the input sheet itself), report "This repetition looks like a problem with the GOAL input sheet design, not the execution approach — the input sheet needs rewriting" and propose rewriting the input sheet to a human instead of retrying DO. In both cases there is no auto-retry |
| S7 | Already aware that execution evidence (a deterministic oracle — a failing test, a broken existing contract) contradicts an explicit user instruction — an awareness-is-not-resistance response [borrowed from Blind Obedience 07385] | STOP before forcing the implementation through: "The instruction contradicts execution evidence: [evidence]. Proceed anyway?" Even after approval, do not paper over it with a later self-directed autonomous fix (a Ghost Error cannot be recovered by iterative post-hoc correction) — report the outcome exactly as it is |
| S8 | ATTACK Tier-1 matches one of its six escalation conditions | "This change is a candidate for adversarial pre-implementation review: [matching condition]. Dispatch doubt-reviewer (or equivalent), then resume with its verdict (proceed / revise first / escalate)." If the user explicitly says "just proceed," continue on the Tier-0 result alone — that's an intentional override, not a bypass |

> **S7 scope**: "execution evidence" applies only to a code context where a
> deterministic oracle exists (tests, type checker, an existing API/contract).
> The REFINE path (non-code deliverables — prose, analysis, design docs) is
> out of scope, since there is no objective answer to contradict. S7 is the
> epistemic opposite of S5 (uncertain root cause) — S7 blocks a model that is
> confident yet wrong from complying anyway.

### B5. Long-running Tasks

- Short status reports at major milestones — separate completed vs incomplete.
- Save current state in `.goal-lock-progress.md` (session crash protection).
- Resume from last verification point. Never restart from scratch.
- At BUDGET 80% or extended stall → report status, ask whether to continue.
- **Early self-doubt boundary**: long-reasoning models have been shown to misjudge remaining budget by up to 24%, triggering premature self-doubt ("I'm probably about to run out") that causes early abandonment or inefficient hedging — measured at -15pp accuracy and +54% token use on eventual success. When a hard counter like `budget.remaining()` is available, trust that measurement over your own felt pressure — don't shrink and quit early when the actual budget is still fine.
- **Constraint re-echo**: at each BUDGET-80% checkpoint or progress-resume point, echo the GOAL input sheet's CONSTRAINTS/SCOPE-Exclude verbatim, separately from the status report. This is a static check against constraints quietly falling out of view during long tasks as attention shifts to raw progress — a full separate memory agent or a learned injection-timing policy would be overkill for this scale of harness.

### B5.1 Physical Completion Gate (Stop Hook)

Separately from self-reported progress via `.goal-lock-progress.md`,
a Stop hook can be registered to intervene **physically at session-end
time** — checking whether a progress file's "current step" is still
non-empty when the agent attempts to end its response, and blocking once
per session if so (cap=1, to avoid infinite re-blocking).

- **Trigger**: session Stop event (when the agent attempts to end its response)
- **cap=1**: gate intervention limited to once per session — prevents infinite re-blocking
- **What it checks**: whether a `.goal-lock-progress.md`-style progress file
  exists with a non-empty "current step," meaning DONE EVIDENCE verification
  may not have run before the agent tried to end the session
- **L1 (prompt) vs L2 (physical)**: B1/B3 VERIFY is an L1 discipline (the model
  is expected to follow it). A Stop hook is L2 (tool/hook-level) enforcement —
  it blocks session termination itself even if the model forgets the discipline.
- **On failure**: fail-open — if the progress file can't be read or the block-count
  file can't be written, let termination proceed without blocking (avoid false blocks).

**Order gate (loophole closure)**: even when the check above passes (progress
file's current step is empty), a second pass can reconstruct the
deterministic order of tool calls from the session transcript — if no
verification-class command (test runner / linter / typechecker / diff)
appears *after* the last file-modifying edit, block once as
UNVERIFIED-CHANGE. This closes the loophole where verification passes, the
agent makes one more edit, and then declares completion without
re-verifying.

**Document-edit exception**: the gate's own progress-tracking file
self-updating its "current step" doesn't count as a real change requiring
re-verification — otherwise the gate would perpetually re-trigger on its own
bookkeeping writes. Other document edits (a report, a spec, a design doc) do
still count as a change, but once that document has been re-read afterward
(mirroring the REFINE loop's CRITIQUE re-read), the gate can pass without
requiring a verification-class Bash command — code files get no such
exception and still need one. **Recognize wrapped verification commands**:
a verification-class command run through a package-manager wrapper (`poetry
run pytest`, `uv run pytest`, `pipenv run pytest`, `npx jest`) or a named
script segment (`npm run test:unit`) still counts as verification — don't
require the bare binary name.

**Status: reference implementation not shipped.** This section specifies the
intended behavior a Stop hook of this kind should have — this repo does not
ship the hook script, the `settings.json` wiring that registers it, or a
test file for it. A team adopting B5.1 has to write and test that hook
itself; until then, treat every claim below as a design spec, not evidence
that the gate is running. The hook should block termination only when
**all four** of the following hold (AND, not OR):
1. A Stop event has actually fired for this session.
2. The re-entrancy flag (e.g. `stop_hook_active`) is not already true —
   **infinite-loop guard**: without this, the hook's own block can trigger
   another Stop event and re-block itself forever.
3. The per-session block cap (cap=1) has not already been spent.
4. Transcript reconstruction shows no verification-class command after the
   last file-modifying edit.

If any one of the four is false, termination proceeds unblocked. Known
limitation (document it, don't silently claim full coverage): file changes
made through shell text-editing commands (e.g. `sed -i`) or custom
verification scripts outside the standard test/lint/typecheck vocabulary
aren't detected. A gate like this must carry a small self-test suite
(synthetic transcripts exercising each of the 4 conditions, pass and fail
cases both) that is re-run whenever the gate's logic is modified, to confirm
the change didn't silently disable detection.

This pattern implements the L2 (no tool provided / physical block) layer of a
4-level safety framework: prompt rules alone (L1) can be forgotten by the
model; a hook enforced at the tool/session layer (L2) cannot.

### B5.2 Ralph Mode — Context-Isolation Alternative

The default B5 loop assumes context continuity — the same session carries
forward, still referencing the accumulated conversation. In an unattended,
long-running autonomous loop (an overnight unmanned batch, a pipeline that
auto-retries N times with no approval gate between rounds), that continuity
itself becomes the risk — a wrong assumption, an accumulated
rationalization, or drift from one round carries straight into the next
with nothing there to interrupt it. Ralph Mode [the "run fresh agent instances
in a loop" pattern popularized as the Ralph Wiggum technique; not to be
confused with the B1 "Ralph Wiggum" masquerading pattern above, which is
about premature completion signaling, not context isolation] is a
structural alternative for exactly that situation.

- **Each round inherits nothing from prior rounds** — no carried-over
  parent/child session context. Every round starts in a genuinely fresh
  context.
- **State crosses rounds through exactly two channels**: (1) the shared
  workspace itself (the actual filesystem artifacts — a code/doc diff is
  its own evidence), and (2) a single bounded, structured handoff — not a
  free-text summary but fixed fields: `status (active|blocked|complete) /
  summary (1-3 sentences) / evidence (commands run + results) / next_steps
  (what the next round should do) / blocker (if any)`. The handoff
  supplements the workspace, it doesn't replace it — it's an instruction
  about what's left, not a narrative of what happened.
- **When to use this instead of default B5**: only for unattended execution
  stretches where no human is present between rounds to correct direction
  (an autonomous overnight batch, an auto-retry pipeline running N times
  without approval). In an ordinary session where a human is watching every
  turn, default B5 stays more efficient (no context-rebuild cost) — don't
  switch just because Ralph Mode is available.
- **Relationship to B4 S6** (same blocker repeated 2+ times → escalate): S6
  still applies under Ralph Mode. If the handoff's `blocker` field stays
  the same across rounds — as long as a short history of recent handoffs is
  kept — the repetition is detectable even with no memory carried forward,
  and S6 still routes to human escalation instead of letting memoryless
  restarts continue indefinitely.

---

## Safety Layers

goal-lock's own actions differ in how reversible they are. Match the
defense to the reversibility tier, and never let a single layer carry
anything above "trivially reversible" alone:

| Reversibility | Example goal-lock action | Required defense |
|---|---|---|
| Easy — local, no external effect | Local file edit, `.goal-lock-progress.md` checkpoint write | Loop discipline (B1–B3) is sufficient |
| Costly — local but expensive to redo | Local deletion, force-terminating a stalled sub-step | Loop discipline + explicit stop-and-ask (S3/S4) |
| Hard — touches external/shared history | `git push`, remote branch changes, migrations | Loop discipline + STOP RULE + explicit user confirmation before executing |
| Unrecoverable — external side effect, no undo | DB DROP/TRUNCATE, a live API call with real-world effect, secret exposure | Loop discipline + STOP RULE + user confirmation + an independent post-hoc review pass |

Layers stack upward only — moving to a higher tier adds a layer, it never
drops a lower one. An action dressed up as "just this once, low risk" is
still evaluated at its actual reversibility tier, not the tier that's
convenient for the agent in the moment.

---

## Task Templates (optional — quick start)

### bug-fix
```
GOAL: Fix [symptom]
DONE EVIDENCE: Reproduction test → PASS + all existing tests PASS
SCOPE Exclude: No API signature changes, no new features
```

### feature
```
GOAL: Implement [feature]
DONE EVIDENCE: N new tests PASS + all existing tests PASS + render/behavior confirmed
SCOPE Exclude: No changes to existing feature behavior
```

### refactor
```
GOAL: Refactor [target] — no behavior change
DONE EVIDENCE: All existing tests PASS (same test count) + before/after diff scope confirmed
SCOPE Exclude: No new features, no API signature changes
```

### migration
```
GOAL: Migrate [target]
DONE EVIDENCE: Migration succeeds both up and down + all existing tests PASS
CONSTRAINTS: Existing data must be preserved, destructive changes require approval
```

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| Auto-fill input sheet + get user confirmation | Start work without user confirmation |
| Enforce PLAN→DO→VERIFY→FINALIZE→OUTPUT loop | Skip loop steps |
| Halt immediately on STOP RULES | Continue with "probably fine" |
| Detect and block success masquerading patterns | Design code logic (that's the developer/agent's role) |
| Save `.goal-lock-progress.md` checkpoints | Manage memory/handoff systems |

## Invariants (never violate)

1. **DONE EVIDENCE must be actually executed**: Run all items before OUTPUT. "It should pass" is not verification. Violation → unverified code reported as "done."

2. **SCOPE Exclude is absolute**: Need to touch Exclude → S3 STOP. Only proceed after user approval. Violation → unintended changes reach production.

3. **Success masquerading detected → OUTPUT BROKEN**: If B1 pattern found in code, mark that verification as FAIL and downgrade OUTPUT to PARTIAL/BROKEN. Violation → false success report.

4. **Incomplete input sheet → no work**: Any of 7 (Quick: 3) fields missing/contradictory → STOP. Don't guess. Violation → unclear goal → rework.

## Error Recovery

| Failure Type | Recovery |
|-------------|---------|
| VERIFY failure | Return to PLAN for root cause analysis → re-DO. Same approach fails twice → S6 STOP |
| Tool failure (Bash/Edit) | 1 retry → report "tool failure" + suggest alternative |
| BUDGET exceeded | Report status + clearly separate done/not-done → user decides |

## Rationalization Table

| Rationalization | Counter |
|-----------------|---------|
| "Simple change, don't need the input sheet" | Quick mode exists. Can't fill 3 fields → goal is unclear |
| "Most of VERIFY passed so it's WORKING" | One FAIL = PARTIAL. "Most" ≠ "all" |
| "Test was too strict so I skipped it" | Success masquerading B1 violation. If test is strict, fix the code |
| "Doing the refactor together is more efficient" | SCOPE Exclude violation. Achieve goal first, then separate goal-lock for refactor |
| "This should be fine" | DONE EVIDENCE not executed = Invariant 1 violation |
| "I'll add tests later" | If DONE EVIDENCE includes tests, now. If not, they were never needed |
| "Goal-lock format is overhead, just look at the result" | Format IS discipline. Without the input sheet, scope drift and masquerading detection opportunities vanish. Quick mode is 10 seconds |
