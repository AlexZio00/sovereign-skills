---
name: next-action
description: "Use when the user wants a next-action recommendation based on current state — reads handoff/git/lessons/STATE and proposes top-3 by impact. Trigger: '/next', 'what should I do next', 'next action'. Proposes only, never executes."
user_invocable: true
not_for:
  - "Right after session start (session-start already outputs state)"
  - "User already gave a specific task"
see_also:
  - skill: session-start
    relation: "next-action=recommendation from current state, session-start=restore prior session"
  - skill: stepback
    relation: "next-action=what's next, stepback=am I doing the right thing right now"
---
# /next — Next Action Recommender

## Dominant Variable
**Is the proposed action actually high-impact based on current project state?** — it must come from measured files, not guesses.

## Purpose

Reads current project state and proposes the top 3 next actions by impact.
Different from stepback (direction check) — stepback asks "am I doing the right thing right now", this asks "what should I do next".
Different from session-start (handoff load) — session-start restores the prior session, this recommends actions from current state.

**Discard if**: right after session start (session-start already loaded the handoff + output state). User already gave a specific task.

## Key Assumptions

1. **Project has a CLAUDE.md** — if broken: propose from git status alone (reduced scope).
2. **Is a git repository** — if broken: propose from filesystem scan alone.

## Trigger

- `/next`
- "what should I do next"
- "next action"

## Workflow

### Step 1: Collect State (parallel, 30s cap)

Read the following 5 sources. Skip missing files.

1. `memory/session-handoff-LATEST.md` — "What to do now" section
2. `git status --short` — uncommitted changed files
3. `git log --oneline -5` — recent work flow
4. `tasks/lessons.md` — `conf≥0.7` lessons stale 30+ days (need re-application)
5. `docs/STATE.md` or `~/.claude/STATE.md` — PENDING blockers

### Step 2: Derive Candidates

Extract action candidates from collected data:

- Handoff "what to do now" → candidate as-is
- Uncommitted files → "commit + push" or "needs verification"
- PENDING blocker trigger satisfied → "resolve blocker"
- Stale lesson → "re-apply/verify lesson"
- git log pattern → "continue ongoing work" or "pivot direction"

### Step 3: Sort by Impact

Narrow candidates to 3. Sort criteria:

1. **Urgency** — resolve blocker > verify uncommitted > handoff item
2. **Dependency** — prerequisites for other work take priority
3. **Timeliness** — time-sensitive items (data collection after market close, pre-deploy verification, etc.)

### Step 4: Output

```
## Next Actions

1. **[action]** — [1-line rationale. State which source it came from]
2. **[action]** — [rationale]
3. **[action]** — [rationale]

Pick a number to proceed immediately.
```

Output and stop immediately. If the user picks a number, start that work.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Read handoff/git/lessons/STATE | Execute the proposed action directly |
| [READ] Propose top-3 actions by impact | Modify code or create files |
| [READ] State the evidence source for each proposal | Start work without user confirmation |

## Invariants (never violate)

1. **Proposal only, never execute**: recommend an action but never start it directly. Only proceed once the user picks. Violation → work executed without user intent.
2. **Evidence-based proposals**: derive candidates only from git status/Glob/Read results. Never guess "this is probably needed". Violation → phantom proposals for nonexistent files/issues.
3. **3-item cap**: even with 10 candidates, narrow to 3. Prevents choice overload. Violation → user can't choose and defaults to "just handle it yourself".
4. **10-line cap**: output exceeding 10 lines is over-explaining. Violation → no longer distinguishable from stepback.

## Error Recovery

| Failure Type | Recovery |
|---------|--------|
| `tool_failure` | Skip the source that failed to read, propose from the rest |
| `missing_data` | If both handoff and STATE are absent, propose from git status alone (minimal mode) |

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "5 recommendations would be more useful" | Beyond 3 is choice overload. 3 is the optimal number for action conversion |
| "Just executing right away is faster" | Violates Invariant 1. Proposal and execution are different skills' jobs |
| "Handoff alone is enough, why check git too?" | Handoff is a past snapshot. Current git status is the real state |

## Truthful Reporting

1. **no mock deception**: never conclude "nothing to do" without actually reading files.
2. **no silent brokenness**: if a source fails to read, state `⚠️ failed to read [source name]` explicitly.

## Principles

- **Current state is truth** — the filesystem is authoritative, not memory
- **Proposal is light, execution is heavy** — this skill stays on the light side
