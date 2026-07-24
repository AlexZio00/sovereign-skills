---
name: goal-lock
description: "Agent Discipline Engine — lock the goal, run PLAN→DO→VERIFY→FINALIZE→OUTPUT loop, detect success masquerading. Triggers: '/goal-lock', '/goal-lock quick', 'goal lock', 'task harness'."
user_invocable: true
not_for:
  - "Simple questions/conversation (no code changes)"
  - "Single file 1-line fix"
see_also:
  - skill: scope
    relation: "scope=planning lock, goal-lock=execution lock"
  - skill: freeze
    relation: "freeze=zone freeze, goal-lock=goal loop"
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
[Completion proof — command to run + expected result. No subjective criteria.]
e.g.: `pytest tests/test_X.py -v` → 5 passed
e.g.: `curl localhost:3000/api/health` → 200 OK

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
| Production behavior change | Modify production logic to match tests |
| Goal-lock declaration ignored | Declare "proceeding with goal-lock" then skip the input sheet |
| Structural fix reported as upgrade | Report boilerplate additions as "substantive improvements" |
| Ralph Wiggum (early completion) | Skip VERIFY or run it partially, then jump to OUTPUT. Emit completion signal from an incomplete state |
| CEF Thanatosis (external failure fabrication) | Evading constraints via unverified failure claims like "API error"/"file not found"/"permission denied". Failure reports must be accompanied by actual Bash/Read execution results |
| Post-hoc abstention | Execute an irreversible action first, then declare "failed"/"on hold" after the fact. Abstention judgment is only valid before the commit-point gate — declaring it after the action has already landed is still success masquerading |
| Layer laundering | Narrating a unit-test pass as if it proves the user-facing feature actually works — laundering one evidence layer as a higher one |

**Language-specific patterns**:
- Python: `@pytest.mark.skip`, `@pytest.mark.xfail`, `mock.return_value` abuse
- JavaScript: `test.skip`, `.only` left in, `jest.fn()` chains bypassing real logic
- Go: `t.Skip()`, `//go:build ignore`
- Rust: `#[ignore]`, `#[should_panic]` misuse

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

Risk detected → return to PLAN with avoidance strategy.

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

Items not verified: `NOT RUN: [reason]`. Never "it should be fine."

**GroundEval**: verify that verification tool calls **actually executed**. If the OUTPUT claims "tests passed" but no `pytest`/`npm test` Bash call exists in the tool history, the claim is ungrounded. Every verification claim in OUTPUT must trace back to an actual tool invocation.

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

**Final status**: WORKING / PARTIAL / BROKEN
```

- PARTIAL: partially working, list specific defects
- BROKEN: core functionality not working, state cause
- Claiming "done" while PARTIAL/BROKEN = success masquerading (B1 violation)

### B4. STOP RULES (halt and ask — no progress until answered)

| # | Condition | Action |
|---|-----------|--------|
| S1 | Goal splits into 2+ independent goals | "Goal is branching. Which one first?" |
| S2 | Input missing/contradictory | Specify exactly what's ambiguous |
| S3 | Need to change SCOPE Exclude area | "Need to modify X but it's Excluded. Allow?" |
| S4 | Destructive / external side effect needed | "DB deletion/API call/push needed. Proceed?" |
| S5 | Insufficient confidence in root cause | "Not sure if cause is A or B" |
| S6 | Same blocker repeated (2+ times) — stagnation circuit breaker | "Same problem repeating. Need a different approach" — no auto-retry, escalate to human here |
| S7 | Already aware that execution evidence (a deterministic oracle — a failing test, a broken existing contract) contradicts an explicit user instruction — an awareness-is-not-resistance response [borrowed from Blind Obedience 07385] | STOP before forcing the implementation through: "The instruction contradicts execution evidence: [evidence]. Proceed anyway?" Even after approval, do not paper over it with a later self-directed autonomous fix (a Ghost Error cannot be recovered by iterative post-hoc correction) — report the outcome exactly as it is |

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
re-verifying. Shares the same per-session cap as the check above. Known
limitation (document it, don't silently claim full coverage): file changes
made through shell text-editing commands (e.g. `sed -i`) or custom
verification scripts outside the standard test/lint/typecheck vocabulary
aren't detected. A gate like this should carry a small self-test suite that
is re-run whenever the gate itself is modified, to confirm the change didn't
silently disable detection.

This pattern implements the L2 (no tool provided / physical block) layer of a
4-level safety framework: prompt rules alone (L1) can be forgotten by the
model; a hook enforced at the tool/session layer (L2) cannot.

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
