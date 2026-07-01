---
skill_type: workflow
tools: Read, Write, Edit, Glob, Grep, Agent, Bash, AskUserQuestion
name: scope
user_invocable: true
description: |
  Scope definition before implementation — two modes.
  Quick mode (default): IN/OUT/exit criteria brief → BRIEF.md.
  Full mode (/scope full): L0→L4 layered spec chain → spec.md.
  Trigger: '/scope', '/brief', '/specify', 'scope this', '스펙 잡아줘', '범위 잡아줘',
  'spec 만들어', '스펙 만들어', '기획 정리해줘', 'plan this'.
  Do NOT trigger for: bug fixes, single-file changes, existing spec, brainstorming.
---

# /scope — Scope Definition Engine v1.0

> Unified brief + specify. Lock down "what you will do and what you will NOT do" before implementation.
> Quick (default) = IN/OUT lock + BRIEF.md. Full = L0→L4 layer chain + spec.md.

## Dominant Variable
**Is the Scope OUT section explicitly written?** — IN alone causes scope creep during implementation. OUT must be explicit to lock it. In Full mode, additionally **L2 decision clarity** is the dominant variable.

## Trigger
- `/scope` (Quick default)
- `/scope full` (Full mode)
- `/brief` (Quick backward compat)
- `/specify` (Full backward compat)
- "scope this", "스펙 잡아줘", "범위 잡아줘", "기획 정리해줘"
- "spec 만들어", "스펙 만들어", "plan this"

## Discard If
- Bug fix, 1-file edit → implement directly
- BRIEF.md/spec.md already exists → use Edit
- Exploration only → delegate to brainstorming

## Key Assumptions 
1. **Project CLAUDE.md exists** (existing projects) — if broken: can't auto-scan constraints, write from user input only.
2. **User provides idea/requirement in ≥1 sentence** — if broken: ask "Tell me in one sentence what to build" once.


## Mode Selection

| Mode | Trigger | Output | Best For |
|------|---------|--------|----------|
| **Quick** (default) | `/scope`, `/brief` | BRIEF.md | Feature add, clear change |
| **Full** | `/scope full`, `/specify` | specs/{name}/spec.md | Architecture change, multi-module, complex design |

Unsure? Start Quick → if user wants more detail: "Shall we switch to full mode?"

---

## Quick Mode — IN/OUT Brief

### Step 1: Detect project
- Existing project: CLAUDE.md, package.json etc. exist → 2-level Glob + keyword Grep (10-file cap)
- New project: skip

### Step 2: Check input sufficiency
Can you answer these 3 things in 1 sentence each?
- What action is being added/changed?
- What is explicitly excluded?
- How do you verify "done"?

Insufficient → **ask max 3 clarifying questions**. Beyond that → conservative minimum scope + `[assumed]` tag.

### Step 3: Generate Brief

```markdown
## Brief: [feature name — verb phrase]

**Goal**: [1-2 sentences. Start with verb.]

**Scope IN**
- [concrete items]

**Scope OUT** ← Required, min 2 items
- [natural extension but excluded]

**Constraints**
- [file/action/integration constraints — min 1 if existing project]

**Exit Criteria**
- [ ] [who/what] [action] → [measurable result]

**Risk Flags**
- [min 1]

**Contraindication**
- [condition where this approach doesn't fit — min 1]
- Example: "If data > 100K rows, this design has performance issues", "If team > 2 people, API contract first"
```

### Step 4: Approval → Save BRIEF.md

---

## Full Mode — L0→L4 Spec Chain

### Layer Flow

| Layer | What | Gate |
|-------|------|------|
| L0 | Mirror → Goal, Non-goals, Confirmed Goal | User confirmation |
| L1 | Codebase research → Research section | Automatic |
| L2 | Interview → Decisions + Constraints | L2-reviewer + user approval |
| L3 | Requirements (GWT sub-requirements) | User approval |
| L4 | Tasks (Fulfills links) + Plan Summary | User approval |

### Core Rules
1. Layer order is immutable — no skipping, no backward traversal
2. Append, don't overwrite — Read existing spec.md first
3. L2-reviewer independent validation required (if skipped: mark `Reviewer: SKIPPED`)
4. Tasks must link to Requirements (`Fulfills: R{n}.{m}`)

### L2 Self-Validation
Each Decision gets clarity score (0-5):
- 5: Implementer can state in 1 sentence what to build
- 3: Needs 1-2 clarifying questions
- 1: Completely ambiguous

Average < 3.5 → warn "Decisions are ambiguous" + suggest rewrite.

### Deliverable
`specs/{kebab-name}/spec.md` — required sections:
Meta / Goal / Non-goals / Confirmed Goal / Research / Decisions / Constraints / Known Gaps / Requirements / Tasks / Plan Summary

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Idea → structured brief/spec | Write or modify code |
| [READ] IN/OUT explicit + exit criteria | Decide implementation method (how is implementer's job) |
| [WRITE] Save BRIEF.md or spec.md | Analyze existing code (quick scan only) |
| [AGENT] L2-reviewer independent validation (Full) | Make design decisions (brainstorming's role) |

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Save BRIEF.md / spec.md | high (git) | L1+L3 (Invariant 5: user approval gate) |
| Overwrite existing spec | medium | L1 (Invariant 9: append/edit only) |

## Invariants (never violate)

1. **No implementation during scope**: no code changes during/after scope writing.
2. **Scope OUT mandatory**: min 2 items. Write even if user says unnecessary.
3. **Exit Criteria = observable + measurable**: auto-reject vague items like "works correctly".
4. **Question limit 3** (Quick): exceed → conservative minimum scope.
5. **Approval gate required**: save file only after explicit user approval.
6. **Constraints mandatory** (existing project): 0 items → rescan.
7. **Risk Flags min 1**.
8. **Layer order immutable** (Full): L0→L1→L2→L3→L4.
9. **No spec overwrite** (Full): append or edit only.
10. **Tasks→Requirements link required** (Full).

## Error Recovery 

| Failure Type | Recovery |
|---------|------|
| `tool_failure` | Print to chat → user manual save |
| `input_error` | Ask 1 clarifying question. No guessing |
| `missing_data` | Note "no context" + write from user input only |
| `logic_inconsistency` | Present conflicting items to user for selection |

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "Skip OUT" | Invariant 2. Explicit even when clear prevents scope creep |
| "Clear enough, no questions" | Need immediate 1-sentence answer to 3 questions for Sufficient |
| "L0-L1 obvious, skip" (Full) | L2 decisions have no foundation without them |
| "Write spec in one go" (Full) | Mid-gates allow course correction |
| "Tasks before Requirements" (Full) | No Fulfills link = untraceable |

## Truthful Reporting 
1. **no mock deception**: never save without approval.
2. **no test façade**: missing OUT = `⚠️ Scope OUT not written`.
3. **no silent brokenness**: unmeasurable Exit Criteria = PARTIAL.

## Principles
- **OUT matters more than IN** — people say what to do but skip what NOT to do.
- **Fewer questions better** — 4+ and users say "just build it".
- **Brief is not an implementation spec** — what and done only. How is implementer's.
- **Full extends Quick** — detect complexity in Quick → offer Full switch.
