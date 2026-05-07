---
name: session-start
description: "Opens a session by loading handoff context, reviewing lessons, and producing a ready signal. Triggers: '/session-start', 'start session', 'load context', 'what was I working on', 'resume', '세션 시작', '이어서 해줘', '어디까지 했지'. Discard if: first session on a project (no handoff file yet) or user wants to start fresh without prior context."
user_invocable: true
context: !cat memory/session-handoff-LATEST.md
---

# Session Start

## Dominant Variable
Does the handoff contain **what to do next**, or **a list of what was done**? If it's a completion log, it was written wrong. If you can't identify Priority 1 immediately, go deeper in Phase 1.

## Discard If
- `memory/session-handoff-LATEST.md` missing (first session) → skip, start fresh
- User says "start fresh" / "ignore context" → skip
- Quick one-off question unrelated to ongoing work → skip

> **Auto-trigger signal**: If ≥5,000 tokens accumulated AND ≥3 tool calls AND ≥24h since last session — high-value context is at risk. Run this skill before starting new work (Triple Gate pattern).

---

## Phase 1: Load Handoff

Read `memory/session-handoff-LATEST.md` (auto-loaded above).

Extract:
- **Priority 1** — the most urgent next action for this session
- **Open decisions** — questions awaiting user input
- **Remaining issues** — unresolved bugs or blockers
- **Context notes** — failed approaches to avoid repeating, key causation discovered last session

If the file is empty or missing: output `[no handoff found — starting fresh]` and exit.

---

## Phase 2: Review Lessons

Read `tasks/lessons.md`.

Scan for rules relevant to today's priorities:
- Code changes planned → look for correction rules about patterns in that area
- About to commit or push → check commit-related rules
- Debugging → check any debugging anti-patterns recorded

**v2 metadata utilization (`> conf · seen · obs`, added 2026-04-28~)**:
- `conf ≥ 0.7` (verified/core) → flag the **rule body in 1 line** as priority signal
- `conf 0.5` (moderate) → show **title only, 1 line**
- `conf < 0.5` (tentative/experimental) → **TOC header only** or skip (noise)
- `seen` within 30 days AND `obs ≥ 3` → active pattern, surface first
- Lessons without v2 metadata (legacy) → handle normally (backward compat)

Flag each applicable rule, one line each. Skip silently if file missing.

---

## Phase 3: Global State Check

Read `~/.claude/STATE.md` (cross-project blockers and decisions).

Check:
- Any open decisions resolvable in this session?
- Any active blockers you can touch now?

Skip if STATE.md missing.

---

## Phase 4: Memory Quick-Check

### 4.1 Selective Load

Read `memory/MEMORY.md` with tag-based filtering:

- `<!-- #always -->` tagged sections → load in full (core information)
- `<!-- #on-demand -->` tagged sections → extract headers as TOC only (Grep when needed)
- Untagged MEMORY.md → load in full (backward compatible)

Steps:
1. `Grep "^##.*<!-- #always -->"` → Read those sections in full
2. `Grep "^##.*<!-- #on-demand -->"` → Collect header names only
3. Output TOC for on-demand sections in the ready signal:
   ```
   MEMORY.md (on-demand — Grep to access):
   - Section A
   - Section B
   ```

### 4.2 Spot-Check

1. **Stale references** — handoff names a file path or function → Glob/Grep one or two key items to confirm they still exist. If not, flag immediately.
2. **Overdue promotions** — any item in `memory/context-log.md` with `[ref:N]` where N ≥ 3 → promote to MEMORY.md now, before starting work.

This is a spot-check on 1-2 items. If it takes more than 60 seconds, you're scanning too many items.

Skip if MEMORY.md missing.

---

## Phase 5: Ready Signal

Output a structured briefing:

```
## Session Ready

**Priority 1:** [top item from handoff — specific, actionable]
**Priority 2:** [second item if present]

**Open decisions:** [list, or "none"]
**Active blockers:** [list, or "none"]

**Lessons flagged:** [applicable rules from Phase 2, or "none"]
**Memory alerts:** [stale refs or promotions triggered, or "none"]
**Global:** [STATE.md items relevant to this session, or "none"]
```

Then: `Ready. What would you like to start with?`

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Load and summarize handoff + lessons | Write code or modify files |
| [READ] Spot-check 1-2 stale memory references | Run full test suite or project scan |
| [READ] Flag applicable correction rules for today | Rewrite the handoff file |
| [EDIT] Promote overdue context-log entries to MEMORY.md | Make architecture or design decisions |

---

## Invariants (never violate)

1. **Read-only by default**: session-start loads context — it does not modify files. The one permitted exception: promoting a `[ref:N≥3]` entry to MEMORY.md (this is a stale-detection write, not a session write). No other writes.

2. **Missing file = silent skip, not error**: if `memory/session-handoff-LATEST.md`, `tasks/lessons.md`, or `memory/MEMORY.md` is missing, skip that phase without error. Never block session start on a missing file.

3. **Ready signal must include Priority 1**: the output must name at least one concrete next action. "Session started" with no priority is a violation — it means the handoff has no actionable items, which is worth flagging to the user explicitly.

---

## Output

- **Conversation**: structured ready signal (priorities + open decisions + lessons flagged)
- **Files written**: none — or `memory/MEMORY.md` if an overdue promotion was triggered

---

## Rationalization Table

| Rationalization | Counter |
|-----------------|---------|
| "The handoff looks empty, I'll just say 'ready'" | Invariant 3: must name Priority 1. If handoff is truly empty, say so — that itself is actionable information. |
| "I should update the handoff now that I've read it" | Invariant 1: session-start is read-only. Handoff updates happen at session end via `/session-checkpoint`. |
| "Phase 4 memory check feels slow, I'll skip it" | It is a spot-check on 1-2 items. If it's slow, you are scanning too many. Narrow the scope and run it. |
| "No handoff exists yet, but I'll generate one based on the codebase" | Discard condition: no handoff = start fresh. Do not synthesize a handoff — that would invent context that wasn't saved. |

---

## Pair

This skill is the opening half of the session lifecycle.
`/session-start` → work → `/session-checkpoint`

Install both or install neither — designed as a pair.

---

## In production
Managing context across many sessions on a 12-agent system.
Past 200 files, the handoff file became the difference between
"pick up immediately" vs "20 min reconstructing state."
