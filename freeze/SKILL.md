---
skill_type: utility
tools: Read
name: freeze
description: "Scope lock for current task. Declares editable zone — everything outside is frozen (read-only). Call before starting implementation to prevent scope creep."
tags: [meta, safety]
version: "1.0.0"
source: "freeze pattern"
triggers:
  - "/freeze"
  - "freeze this"
  - "scope lock"
  - "스코프 잠금"
  - "이것만 건드려"
  - "나머지 건드리지 마"
  - "범위 잠가"
user_invocable: true
---

# /freeze — Scope Lock

> Declare editable zone — everything outside is frozen.

## Dominant Variable

In this task, **is the editable scope explicitly declared?** — If unclear, scope creep naturally develops during implementation. First of three principles (freeze / careful / guard): freeze = boundary lock (this skill), careful = 3-strike debugging gate, guard = risky path protection.

## Trigger

- `/freeze`
- "freeze this"
- "scope lock"
- "스코프 잠금"
- "이것만 건드려"
- "나머지 건드리지 마"
- "범위 잠가"

## Discard If

- Exploration / research only (no modifications expected)
- Already a clear single-file edit (1 file, ≤10 lines)
- Brainstorming phase (scope not yet finalized before design approval)

---

## Key Assumptions 
1. **User specifies ≥1 modification target** — If broken: ask once for clarity; if still unclear, freeze broadly.
2. **Implementation work follows in the same session** — If only declaring scope and ending, this skill is unnecessary.

## Architecture

```
User input (file / module / concept scope)
    ↓
[PARSE]   → classify as editable / frozen / read-only
    ↓
[DECLARE] → generate FROZEN SCOPE block
    ↓
[OUTPUT]  → emit immediately, then exit
```

---

## Stage 1: PARSE

Extract from user input:
- **editable**: explicitly named files / modules / paths — modifications allowed
- **frozen**: everything else (default frozen if not mentioned)
- **read-only**: mentioned but modification status unclear → conservatively treat as read-only

If scope is too vague ("everything", "roughly") → ask for clarity **once only**.
Still unclear → freeze more broadly (Invariant 2).

---

## Stage 2: DECLARE

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 FROZEN SCOPE — [One-line task description]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ EDITABLE (modifications allowed)
  [list of files / modules]

❌ FROZEN (no modifications)
  [everything else — or "all except above"]

⚠️  READ-ONLY (reference only)
  [mentioned but no modifications allowed]

Rules:
- FROZEN files: Edit/Write forbidden. Read only.
- If modification necessity discovered → stop immediately, report to user
- Thaw: user must explicitly say "unfreeze [file]" or "expand scope"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Stage 3: OUTPUT

Emit FROZEN SCOPE block, then exit immediately.
No code generation, no agent spawning, no implementation start.

All implementation work in this session follows this declared scope.

---

## Hard Rules

1. **Emit immediately, exit immediately** — no "I'll now start implementing" after declaration.
2. **No agent spawning** — main context only.
3. **No code generation** — scope declaration only.
4. **Ask for clarity at most once** — if still unclear, freeze more broadly.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Parse user input → classify editable/frozen/read-only | Write code or modify files |
| Emit FROZEN SCOPE block | Spawn agents or start implementation |
| Ask for clarity once if scope is ambiguous | Make direct judgment calls on out-of-scope modifications |

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| (none — read-only, block output only) | — | L1 (Invariant 1: no modifications to frozen files, ever) |

- **L1 (Invariants)**: Frozen = intended physical block on Edit/Write. Exit immediately after declaration.

## Error Recovery 

On failure detection: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure Type | Detection Condition | Recovery Path |
|---------|---------|--------|
| `input_error` | Unclear which files / scope to freeze | Ask once for target — never guess scope |
| `logic_inconsistency` | Freeze request conflicts with simultaneous modification request | Clarify: "This file will be frozen — modification requests rejected." Do not allow both. |
| `missing_data` | Specified file does not exist | State "file not found." Do not guess paths and freeze different files. |

---

## Invariants (never violate)

1. **Frozen = absolutely no modifications**: Files declared frozen cannot be edited/written in this session. "Just a tiny tweak" is rationalization. Violation → scope creep and unexpected side effects.

2. **When unclear, freeze broader**: If boundaries are ambiguous, choose the broader frozen range. Narrow scope fails to prevent creep. Violation → freeze declaration becomes meaningless.

3. **Exit immediately after declaration**: No further action after emitting FROZEN SCOPE block. User initiates follow-up implementation requests normally. Violation → declaration and implementation blur, scope awareness fades.

---

## Thaw Protocol

When a frozen file needs modification mid-work:

**Trigger**: "unfreeze [file]", "thaw", "expand scope"

**Steps:**
1. **State reason** — why the frozen file must be touched (no reason → refuse)
2. **Blast radius check** — what else is affected if this file changes
3. **Re-emit FROZEN SCOPE block** — add thawed file to editable, keep rest frozen
4. **Invalidate previous block** — "Previous freeze replaced" 1 line

**Limits:**
- 3+ thaws → `⚠️ Freeze is being repeatedly lifted — consider re-running /scope to redefine boundaries`
- Full thaw ("unfreeze everything") → freeze skill terminates (Discard)

---

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "It's frozen but I just need to change one line" | Violates Invariant 1. Stop and report to user. |
| "Scope is unclear, let me narrow it for now" | Violates Invariant 2. When unclear, freeze broader. |
| "Declaring and implementing immediately is faster" | Violates Invariant 3. Exit after declaration. |
| "It's one file, why declare a freeze?" | Discard If: ≤10 lines in 1 file excluded. Otherwise declare. |
| "No actual modifications needed, so it's fine" | Scope creep often begins when we think nothing needs to change. |

---

## Example

```
User: "/freeze src/components/UserProfile.tsx"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 FROZEN SCOPE — UserProfile component refactor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ EDITABLE
  - src/components/UserProfile.tsx

❌ FROZEN (no modifications)
  - everything outside the above

⚠️  READ-ONLY (reference only)
  - src/hooks/useAuth.ts (auth logic reference)

Rules:
- No Edit/Write outside UserProfile.tsx
- If modification needed elsewhere → stop and report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Design Note

This version uses task-level declaration (not session-global file lists) because Claude Code cannot persist state across sessions — the declaration block itself serves as in-context state.
