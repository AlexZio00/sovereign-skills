---
name: goal-lock
description: "Agent Discipline Engine — lock the goal, run PLAN→DO→VERIFY→FINALIZE→OUTPUT loop, detect success masquerading. Triggers: '/goal-lock', '/goal-lock quick', 'goal lock', 'task harness'."
user_invocable: true
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

### 3. CONTEXT
[Current state · existing structure · prior decisions · dependencies · known constraints]

### 4. STARTING POINT
[Files/logs/tests to look at first. Start here, no broad exploration.]

### 5. SCOPE
- **Include**: [Editable area + required work]
- **Exclude**: [Out of bounds · unrelated refactors · new features · production behavior changes]

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

**Language-specific patterns**:
- Python: `@pytest.mark.skip`, `@pytest.mark.xfail`, `mock.return_value` abuse
- JavaScript: `test.skip`, `.only` left in, `jest.fn()` chains bypassing real logic
- Go: `t.Skip()`, `//go:build ignore`
- Rust: `#[ignore]`, `#[should_panic]` misuse

### B2. PRIORITY (on conflict)

```
0 Honesty → 1 Stability → 2 Preserve existing behavior → 3 Verifiability → 4 Performance → 5 Code cleanup
```

### B3. Execution Loop

```
PLAN → DO → VERIFY → FINALIZE → OUTPUT
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

#### VERIFY
**Actually execute** the verification specified in DONE EVIDENCE.

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

#### FINALIZE
- After goal achieved, **no additional refactoring.**
- Clean up: temp code, debug prints, failed experiments, junk files.
- Before reporting: **re-check scope + verification** — didn't touch Exclude, met DONE EVIDENCE.

#### OUTPUT
```markdown
## Result

**Changed files**: [list]
**Key changes**: [what and why]
**Completion evidence**: [commands run + results]
**Verification**: [passed/failed/not run — each with reason]
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
| S6 | Same blocker repeated (2+ times) | "Same problem repeating. Need different approach" |

### B5. Long-running Tasks

- Short status reports at major milestones — separate completed vs incomplete.
- Save current state in `.goal-lock-progress.md` (session crash protection).
- Resume from last verification point. Never restart from scratch.
- At BUDGET 80% or extended stall → report status, ask whether to continue.

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
