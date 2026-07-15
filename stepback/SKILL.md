---
skill_type: utility
tools: Read
name: stepback
description: "One-shot perspective reset. Scans current work context, generates 1 abstract reframing question + 3 quick checks (scope drift, side effects, better approach) in under 10 lines. No dialogue, no code, no agents."
depends_on:
  skills: []
  agents: []
  files: []
tags: [meta, analysis]
version: "1.0.0"
source: "team-attention/hoyeon pattern"
triggers:
  - "/stepback"
  - "step back"
  - "zoom out"
  - "blind spot"
  - "am I on track"
  - "big picture"
  - "what am I even doing"
user_invocable: true
not_for:
  - "Next action recommendation -> next-action skill"
  - "Session start -> session-start"
see_also:
  - skill: next-action
    relation: "stepback=direction check, next-action=action recommendation"
---
# /stepback — One-Shot Perspective Reset

> Source: team-attention/hoyeon pattern. Read-only, zero side effects.

## Purpose

Scan the current work context, generate 1 abstract reframing question + 3 quick checks (scope drift, side effects, better approach) in under 10 lines. No dialogue, no code, no agents.

Use when you're deep in implementation and need to check if you're solving the right problem at the right level.

## Dominant Variable

Whether the work direction is solving the right problem at the right level — if this is off, even flawless implementation produces the wrong outcome.

## Key Assumptions

1. **Current work context exists in the conversation** — if broken: ask once,
   "tell me in one line what you're doing."
2. **Output fits an abstraction level expressible in ≤10 lines** — if broken:
   the question is too concrete → self-check "go more abstract."

## Trigger

- `/stepback`
- "step back"
- "zoom out"
- "blind spot"
- "am I on track"
- "big picture"
- "what am I even doing"

## Discard If

- Work is already completed (use retrospective tools instead)
- Code review requested (use code review tools instead)
- Specific change impact analysis needed (use scope definition tools instead)

---

## Architecture

```
Recent conversation context (current work direction)
    ↓
[PARSE]      → Extract current direction + original intent + scope signals
    ↓
[STEP-BACK]  → Generate 1 abstract reframing question
    ↓
[CHECK]      → Run 3 checks
    ↓
[OUTPUT]     → Under 10 lines, return immediately
```

---

## Stage 1: PARSE

Extract from recent conversation:
- **Current direction** — what the user is actively working on
- **Original intent** — why this work was started (implicit is OK)
- **Scope signals** — size/complexity of the change

---

## Stage 2: STEP-BACK

**DeepMind step-back pattern**: abstract from the specific subject of current work → the general principle/system it belongs to.

| Current Work | Step-Back Question |
|-------------|-------------------|
| "Fixing this null pointer bug" | "Is the error handling strategy of this module correct in the first place?" |
| "Adding a new API endpoint" | "Should this feature live in the API layer, or somewhere else?" |
| "Refactoring this function" | "Should this function exist at all, or is the caller the real problem?" |
| "Writing tests for module X" | "Is X's boundary designed in a testable way?" |
| "Optimizing this query" | "Should this query be called at this point at all?" |

The question must make the user reconsider whether they're **solving the right problem at the right level**.

---

## Stage 3: CHECK

Each check = 1 sentence max.

**Scope Drift**: Has the current work drifted from the original goal?
- If drifted → state how
- If on track → "Scope on track."

**Side Effects**: Could this change affect something else?
- State potential blast radius (modules, schemas, tests, integrations)
- If none → "No visible side effects."

**Better Approach**: Is there a more fundamental/simpler solution?
- If yes → 1 sentence
- If current approach is right → "Current approach seems appropriate."

---

## Stage 4: OUTPUT

```
**Step-Back:** [1 abstract reframing question]

**Scope Drift:** [1 sentence]
**Side Effects:** [1 sentence]
**Better Approach:** [1 sentence]

Continue.
```

4 core lines + closing. **Under 10 lines** total.

Output and stop immediately. No follow-up questions, no menus, no "would you like to...".

---

## Hard Rules

1. **No user questions** — output and return immediately. No input requests.
2. **No agent spawning** — runs in main context only.
3. **No code generation** — analysis only. No code writing or suggestions.
4. **No request restatement** — don't summarize what the user asked. Analyze what's happening now.
5. **10-line cap** — more than 10 lines means over-explaining. Cut.
6. **1 question only** — suppress the urge to generate multiple step-back questions.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| Read recent conversation context for work direction | Write code or modify files |
| Generate 1 abstract reframing question | Spawn agents or ask user questions |
| Run 3 checks (scope/side effects/better approach) | Suggest next actions or generate menus |
| Output under 10 lines and return immediately | Continue working on the task |

---

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| (none — read-only one-shot) | — | L1 (Invariant 3: immediate return, no further action) |

## Invariants (never violate)

1. **10-line cap**: Output exceeding 10 lines has already failed. Cut it down. Violation → over-explanation dilutes the perspective reset.
2. **1 question limit**: Multiple questions split focus. Pick the most important one. Violation → user gets a list instead of a lens.
3. **Immediate return**: No follow-up after output. User decides what to do next. Violation → stepback becomes a dialogue instead of a reset.

---

## Error Recovery

| Failure Type | Detection | Recovery |
|---------|---------|--------|
| `input_error` | Current work context unclear | Ask once: "tell me in one line what you're doing now" |
| `missing_data` | No git diff/status context | Infer from user's last message. If inference impossible, use generic reframing |

---

## Example

```
User: "/stepback"
(Context: debugging a flaky integration test that intermittently times out)

**Step-Back:** Is the test flaky because of a timing issue, or because the component under test has a non-deterministic dependency that shouldn't be there?

**Scope Drift:** Started with fixing one test, now touching retry logic in three modules.
**Side Effects:** Changing the retry config could mask real failures in CI.
**Better Approach:** Check if the test is testing the right thing — a unit test might eliminate the flakiness entirely.

Continue.
```

---

## Rationalization Table

| Rationalization | Counter |
|----------------|---------|
| "10 lines isn't enough, I need to explain more" | If 10 lines isn't enough, the question isn't abstract enough. Go higher. |
| "I should ask the user to confirm before continuing" | Stepback is one-shot. If confirmation is needed, the user will follow up. |
| "Two questions would be more useful" | Two questions halve the focus. Picking one better question is the answer. |
| "Showing code would make it more concrete" | Stepback is direction check, not code review. No code generation. |
