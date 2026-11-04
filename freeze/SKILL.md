---
skill_type: utility
tools: Read, Grep, Glob  # descriptive metadata; read-only discipline is stated in Hard Rules
name: freeze
description: "Scope lock for current task. Declares editable zone — everything outside is frozen (read-only). Call before starting implementation to prevent scope creep."
depends_on:
  skills: []
  agents: []
  files: []
concurrency_profile:
  read_only: true
  concurrency_safe: true
  destructive: none
tags: [meta, safety]
source: "garrytan/gstack freeze pattern"
triggers:
  - "/freeze"
  - "freeze this"
  - "scope lock"
  - "스코프 잠금"
  - "이것만 건드려"
  - "나머지 건드리지 마"
  - "범위 잠가"
user-invocable: true
not_for:
  - "Scope planning -> scope skill"
  - "Execution loop -> goal-lock"
  - "One-shot direction check on an in-progress decision -> stepback"
see_also:
  - skill: scope
    relation: "freeze=zone lock, scope=planning scope"
  - skill: goal-lock
    relation: "freeze=manual lock, goal-lock=loop enforcement"
---

# /freeze — Scope Lock

> Declare editable zone — everything outside is frozen.

## Dominant Variable

In this task, **is the editable scope explicitly declared?** — If unclear, scope creep naturally develops during implementation. freeze = boundary lock for one task; it does not stop risky commands or limit what you may read.

## Trigger

- `/freeze`
- "freeze this"
- "scope lock"
- "lock the scope" / "only touch X" / "don't touch anything else" (and equivalents in the user's language; see the frontmatter trigger list)

## Discard If

- Exploration / research only (no modifications expected)
- Already a clear single-file edit (1 file, ≤10 lines, no new function or class, not a file your project marks as sensitive)
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

Extract from user input. If the user passes the path of a saved `BRIEF.md` / `spec.md` from the scope skill, Read it and take **editable** from Scope IN (or the Tasks) and **frozen** from Scope OUT / Non-goals. If the file does not exist, say so and ask once for the targets.
- **editable**: explicitly named files / modules / paths — modifications allowed (for a bug fix, include the regression test file too; if the user names only a function, use Grep/Glob to find the file that defines it and list that file)
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
- This declaration lives only in the conversation. After /compact or a new session, declare it again.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The heading line `🔒 FROZEN SCOPE — ...` is a fixed marker. Other skills (goal-lock, clean-room) look for it to find the active zone, so do not reword it.

---

## Stage 3: OUTPUT

Emit FROZEN SCOPE block, then exit immediately.
No code generation, no agent spawning, no implementation start.

All implementation work in this session follows this declared scope.

---

## Output

The only artifact this skill produces is the FROZEN SCOPE block itself, emitted straight into the conversation — nothing is written to disk. The block is the state (see Design Note below): there is no external file to persist or reload, so "declared" means "visible in this reply," not "saved somewhere." The declaration exists only in this conversation's context: after /compact, or in a new session, the block may be gone, so declare it again (re-run /freeze or paste the block).

---

## Hard Rules

1. **Emit immediately, exit immediately** — no "I'll now start implementing" after declaration.
2. **No agent spawning** — main context only.
3. **No code generation** — scope declaration only.
4. **Ask for clarity at most once** — if still unclear, freeze more broadly.
5. **Read-only skill** — it uses only Read, Grep and Glob (the `tools:` line is descriptive metadata; this rule is the discipline). It never edits or writes files.

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

- **L1 (Invariants)**: Frozen = intended instruction-level block on Edit/Write (a declarative constraint, not sandbox/hook-enforced). Exit immediately after declaration.

## Error Recovery 

On failure detection: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure Type | Detection Condition | Recovery Path |
|---------|---------|--------|
| `input_error` | Unclear which files / scope to freeze | Ask once for target — never guess scope |
| `logic_inconsistency` | Freeze request conflicts with simultaneous modification request (e.g. a file is named as editable and as frozen) | Ask once which is meant. If the user confirms that both are editable, put both in EDITABLE and declare it; if still unclear, freeze the contested file (Invariant 2). Never edit a contested file before the answer. |
| `missing_data` | Specified file does not exist | State "file not found." Do not guess paths and freeze different files. |

---

## Invariants (never violate)

1. **Frozen = absolutely no modifications**: Files declared frozen cannot be edited/written in this session. "Just a tiny tweak" is rationalization. Violation → scope creep and unexpected side effects.

2. **When unclear, freeze broader**: If boundaries are ambiguous, choose the broader frozen range. Narrow scope fails to prevent creep. Violation → freeze declaration becomes meaningless.

3. **Exit immediately after declaration**: No further action after emitting FROZEN SCOPE block. User initiates follow-up implementation requests normally. Violation → declaration and implementation blur, scope awareness fades.

---

## Thaw Protocol

When a frozen file needs modification mid-work:

**Trigger**: "unfreeze [file]", "thaw", "expand scope" — said by the user, or proposed by the model/another skill (for example goal-lock when its SCOPE needs to grow). Only the user decides: a proposal changes nothing until the user agrees in their own words.

**Steps:**
1. **State reason** — the model states why the frozen file must be touched, and the user decides. If the model cannot give a concrete reason, refuse the thaw
2. **Blast radius check** — what else is affected if this file changes
3. **Re-emit FROZEN SCOPE block** — add thawed file to editable, keep rest frozen
4. **Invalidate previous block** — "Previous freeze replaced" 1 line

**Limits:**
- 3+ thaws → `⚠️ Freeze is being repeatedly lifted — consider re-running /scope to redefine boundaries`
- Full thaw ("unfreeze everything") → the freeze declaration ends (lifted); say so in one line

---

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "It's frozen but I just need to change one line" | Violates Invariant 1. Stop and report to user. |
| "Scope is unclear, let me narrow it for now" | Violates Invariant 2. When unclear, freeze broader. |
| "Declaring and implementing immediately is faster" | Violates Invariant 3. Exit after declaration. |
| "It's one file, why declare a freeze?" | Discard If: ≤10 lines in 1 file with no new function or class (and not a sensitive file) is excluded. Otherwise declare. |
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
- Thaw: "unfreeze [file]" or "expand scope"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Design Note

This skill adapts the freeze pattern from garrytan/gstack. The original uses session-global file lists; this version uses task-level declaration instead, because the declaration block itself serves as in-context state. That state is lost on /compact or in a new session and must be declared again.

See `scenarios/case-1.md`, `scenarios/case-2.md` for regression test scenarios.
