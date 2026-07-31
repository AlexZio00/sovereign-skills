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
not_for:
  - "Bug fix, single-file change -> implement directly"
  - "Existing BRIEF.md/spec.md -> Edit directly"
  - "Exploration only -> brainstorming agent"
see_also:
  - skill: goal-lock
    relation: "scope=planning, goal-lock=execution"
  - skill: freeze
    relation: "scope=define boundaries, freeze=enforce boundaries"
depends_on:
  skills: []
  agents: []
  files:
    - "CLAUDE.md"
    - "scripts/ambiguity_gate.py"
concurrency_profile: sequential
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

### Step 2: Ambiguity score gating
Score clarity across 4 dimensions (0-10 each), by judgment.

| Dimension | Check |
|-----------|-------|
| **Function** | What behavior is being added/changed — are inputs/outputs concrete? |
| **Boundary** | What is explicitly excluded — is IN/OUT clear? |
| **Verification** | How is "done" verified — is there a measurable criterion? |
| **Assumptions** | Any hidden assumptions — dependencies on existing system/data/environment? |

**Gating (deterministic)**: hand the 4 scores to the gate script and read its stdout — don't average them by eye.

```bash
python scope/scripts/ambiguity_gate.py quick --scores '{"function":8,"boundary":7,"verification":6,"assumptions":9}'
# -> {"ok": true, "avg": 7.5, "weakest": "verification"}
```

`ok: false` → target the dimension the script names as `weakest` with clarifying questions (max 3).
Exceeds question limit → conservative minimum scope + `[assumed]` tag.

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

### Step 4: Min-item validation → Approval → Save BRIEF.md
Before requesting approval, validate the drafted brief against the minimum-item requirements — don't count bullets by eye. A bolded aside inside a section (e.g. `**Note**: ...`) can look like a new section header on a human skim and silently truncate a manual count; a regression test locks this exact failure mode closed in the script.

```bash
python scope/scripts/ambiguity_gate.py min-items --file <path-to-drafted-brief>
# -> {"scope_out": 2, "risk_flags": 1, "contraindication": 1, "constraints": 1, "ok": true}
```

Pass `--new-project` for new projects (Invariant 6 waives the Constraints requirement). `ok: false` → the per-field counts in the JSON show which section is short; add items there and re-run before moving to approval.

Request approval only once the script reports `ok: true`. Save BRIEF.md only after explicit user approval (Invariant 5).

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

**Gating (deterministic)**: hand the per-Decision scores to the gate script — don't average them by eye.

```bash
python scope/scripts/ambiguity_gate.py full --scores "5,3,4,5"
# -> {"ok": true, "avg": 4.25}
```

`ok: false` → warn "Decisions are ambiguous" + suggest rewrite.

### Deliverable
`specs/{kebab-name}/spec.md` — required sections:
Meta / Goal / Non-goals / Confirmed Goal / Research / Decisions / Constraints / Known Gaps / Requirements / Tasks / Plan Summary

---

## Mid-Task Scope Drift — 10x-Discovery Rule

> Quick and Full modes both lock IN/OUT only at write time — neither covers what to do when scope explodes mid-execution.

Even for scope locked in BRIEF.md/spec.md, if evidence found during implementation (hidden coupling, a required migration, a stopgap carrying far more load than expected) shows the work is a multiple of what was originally understood, **stop immediately and surface it**:
- What was discovered
- The honest new scale
- 2-3 costed options (full fix / narrow workaround / defer)
- A recommendation

**Two things are forbidden**: (a) silently absorbing the explosion (the user ends up waiting 5x longer than promised) (b) quietly shrinking the deliverable to fit the original budget (the user only discovers later they got less than expected). Both are worse than a plain "here's what I found."

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

1. **No implementation during scope**: no code changes during/after scope writing. Violation → scope becomes a post-hoc rationalization for code already written instead of a constraint that shapes it, and the OUT section stops meaning anything.
2. **Scope OUT mandatory**: min 2 items. Write even if user says unnecessary. Violation → only IN is recorded, so anything not explicitly listed becomes fair game during implementation — scope creep with no written boundary to point back to.
3. **Exit Criteria = observable + measurable**: auto-reject vague items like "works correctly". Violation → "done" becomes a matter of opinion at handoff time, and disagreement about completion surfaces only after the work is finished.
4. **Question limit 3** (Quick): exceed → conservative minimum scope. Violation → interrogation replaces scoping and the user abandons the flow instead of getting a usable brief.
5. **Approval gate required**: save file only after explicit user approval. Violation → an unreviewed draft becomes the working spec, and errors in it propagate into implementation before anyone caught them.
6. **Constraints mandatory** (existing project): 0 items → rescan. Violation → the brief looks complete but omits the existing system's real limits, so implementation collides with constraints nobody wrote down.
7. **Risk Flags min 1**. Violation → a known failure mode goes unrecorded, so the same risk resurfaces later as a surprise instead of a tracked flag.
8. **Layer order immutable** (Full): L0→L1→L2→L3→L4. Violation → decisions (L2) get made on a foundation (L0/L1) that was never confirmed, so the spec inherits an unvalidated goal.
9. **No spec overwrite** (Full): append or edit only. Violation → prior layers' history is destroyed, so a later reviewer can't tell what changed or why.
10. **Tasks→Requirements link required** (Full). Violation → a task exists with no requirement behind it — untraceable work that can't be checked against the spec it supposedly fulfills.
11. **No silent absorption or quiet shrinking on 10x discovery**: if implementation reveals scope that is a multiple of what was originally understood, surface it immediately — don't absorb it silently and don't quietly shrink the deliverable to fit the original budget. Violation → the user only discovers the delay or the missing scope later, after the fact.

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
| "Just quietly do a bit more to make it fit" | Invariant 11. Silent absorption means the user only finds out about the delay or shrinkage later, without warning |

## Truthful Reporting 
1. **no mock deception**: never save without approval.
2. **no test façade**: missing OUT = `⚠️ Scope OUT not written`.
3. **no silent brokenness**: unmeasurable Exit Criteria = PARTIAL.

## Output

**Before approval**: the brief (Quick) or the current layer's draft (Full) is emitted into the conversation only — no file is written yet. This is the review surface; catch problems here, not after the file exists.

**After approval**:
- Quick → `BRIEF.md` written to disk (Step 4, gated by the min-items script above).
- Full → `specs/{kebab-name}/spec.md` written/appended per layer (L0→L4), each layer gated by its own user-approval checkpoint.

**Final status label** (required on completion): `WORKING` (brief/spec saved, all gates passed) / `PARTIAL` (saved with a documented gap — e.g. `[assumed]` tags from a question-limit exit, or a section marked `⚠️`) / `BROKEN` (approval never reached, or the save itself failed). Conditions per label are the same as Truthful Reporting above.

## Principles
- **OUT matters more than IN** — people say what to do but skip what NOT to do.
- **Fewer questions better** — 4+ and users say "just build it".
- **Brief is not an implementation spec** — what and done only. How is implementer's.
- **Full extends Quick** — detect complexity in Quick → offer Full switch.
