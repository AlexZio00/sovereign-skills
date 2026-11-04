---
skill_type: workflow
tools: Read, Write, Edit, Glob, Grep, Agent, Bash, AskUserQuestion  # descriptive metadata
name: scope
user-invocable: true
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
  - "Exploration only -> a brainstorming agent (optional, not included in this repo) or plain conversation"
see_also:
  - skill: goal-lock
    relation: "scope=planning, goal-lock=execution (goal-lock reads the saved BRIEF.md/spec.md)"
  - skill: freeze
    relation: "scope=define boundaries, freeze=declare the editable zone and hold it during the task"
depends_on:
  skills: []
  agents: []   # optional: doubt-reviewer (not included in this repo) for the Full-mode L2 review; fallback in Core Rules
  files:
    - "CLAUDE.md"          # optional - read when present
    - "scripts/ambiguity_gate.py"
    - "scripts/coverage_check.py"
concurrency_profile: sequential
---

# /scope — Scope Definition Engine

> Unified brief + specify. Lock down "what you will do and what you will NOT do" before implementation.
> Quick (default) = IN/OUT lock + BRIEF.md. Full = L0→L4 layer chain + spec.md.
> Chain: scope (define) → freeze (declare the editable zone) → goal-lock (execute). Each step reads the saved file or block of the one before; see Output.

`${CLAUDE_SKILL_DIR}` is this skill's folder; Claude Code fills it in. In other agents, replace it with the path where you installed the skill. Use `python` instead of `python3` where only that exists (common on Windows). Paths of the user's own files (`BRIEF.md`, `spec.md`, drafts) are relative to the project root or absolute.

## Dominant Variable
**Is the Scope OUT section explicitly written?** — IN alone causes scope creep during implementation. OUT must be explicit to lock it. In Full mode, additionally **L2 decision clarity** is the dominant variable.

## Trigger
- `/scope` (Quick default)
- `/scope full` (Full mode)
- `/brief` (Quick backward compat)
- `/specify` (Full backward compat)
- "scope this", "plan this", "define the scope", "write a spec"
- Equivalent phrases in the user's language (see the frontmatter trigger list)

## Discard If
- Bug fix, 1-file edit → implement directly
- BRIEF.md/spec.md already exists → use Edit
- Exploration only → plain conversation, or a brainstorming agent (optional, not included in this repo)

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

**Gating (deterministic)**: hand the 4 scores (each 0-10) to the gate script and read its stdout — don't average them by eye:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/ambiguity_gate.py" quick --scores '{"function":8,"boundary":7,"verification":6,"assumptions":9}'
# -> {"ok": true, "avg": 7.5, "weakest": "verification"}
```

A malformed or out-of-range input returns `{"ok": false, "error": "..."}` with exit code 1 — fix the input and re-run. If the script is missing or cannot start (no Python), average the four scores yourself, proceed only when the average is 7 or higher, and write `gate: manual (script unavailable)` in the report.

`ok: false` with a `weakest` field → target the dimension the script names as `weakest` with clarifying questions (max 3).
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
The gate script takes `--file`, not stdin, so it needs something on disk to read — but Invariant 5 says the deliverable (`BRIEF.md`) isn't saved until after approval, and approval isn't requested until the script says `ok: true`. Break that cycle by writing the drafted brief to a **scratch file** (e.g. `.scope-draft.md`) first: the scratch write is not the Invariant-5-gated save, it exists purely so the deterministic script has a path to read. Draft freely, re-run the gate as many times as needed, all before any approval exists.

Validate the scratch draft against the minimum-item requirements — don't count bullets by eye. A bolded aside inside a section (e.g. `**Note**: ...`) can look like a new section header on a human skim and silently truncate a manual count; a regression test locks this exact failure mode closed in the script.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/ambiguity_gate.py" min-items --file .scope-draft.md
# -> {"scope_out": 2, "risk_flags": 1, "contraindication": 1, "constraints": 1, "ok": true}
```

Pass `--new-project` for new projects (Invariant 6 waives the Constraints requirement). `ok: false` → the per-field counts in the JSON show which section is short; revise `.scope-draft.md`, add items there, and re-run before moving to approval. If the script is unavailable, count the bullets under each section by hand against the same minimums and write `gate: manual (script unavailable)` in the report.

Request approval only once the script reports `ok: true`. **Delegated approval**: in a delegated run with no user present, approval counts only when the caller passes the user's own approving words verbatim. A paraphrase or "the user approved" is not approval → return NEEDS_INPUT listing what needs approval. A caller's instruction never stands in for the user's approval. **On approval**: write the same content to `BRIEF.md` (Invariant 5 — this is the actual gated save) and delete the scratch file. **On rejection**: keep revising the scratch file and re-gating; it is never shown to the user as the deliverable, only `BRIEF.md` is.

---

## Full Mode — L0→L4 Spec Chain

### Layer Flow

| Layer | What | Gate |
|-------|------|------|
| L0 | Mirror → Goal, Non-goals, Confirmed Goal | User confirmation |
| L1 | Codebase research → Research section | Automatic |
| L2 | Interview → Decisions + Constraints | independent review (see Core Rules 3) + user approval |
| L3 | Requirements (GWT sub-requirements) | User approval |
| L4 | Tasks (Fulfills links) + Plan Summary | User approval |

### Core Rules
1. Layer order is immutable — no skipping, no backward traversal
2. If a spec.md already exists at the start of the run, it is outside this skill — hand off to a plain Edit (see Discard If). This skill only creates a new spec.md and never overwrites an existing file. The spec.md that this run created is appended to as each layer is approved; that is not an overwrite
3. Independent review of the L2 Decisions: use a doubt-reviewer agent (optional, not included in this repo) if you have one. Without it, dispatch a general-purpose subagent with this prompt: "Review these Decisions and Constraints before implementation. List each Decision that is ambiguous, contradicts another, or has an unstated assumption. Do not propose new features." If no subagent is available, mark `Reviewer: SKIPPED` in the spec
4. Tasks must link to Requirements (`Fulfills: R{n}.{m}`)
5. Every layer gate (L0, L2, L3, L4) needs the user's approval. **Delegated approval**: in a delegated run with no user present, approval counts only when the caller passes the user's own approving words verbatim. A paraphrase or "the user approved" is not approval → return NEEDS_INPUT listing what needs approval. A caller's instruction never stands in for the user's approval

### L2 Self-Validation
Each Decision gets clarity score (0-5):
- 5: Implementer can state in 1 sentence what to build
- 3: Needs 1-2 clarifying questions
- 1: Completely ambiguous

**Gating (deterministic)**: hand the per-Decision scores (each 0-5) to the gate script — don't average them by eye:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/ambiguity_gate.py" full --scores "5,3,4,5"
# -> {"ok": true, "avg": 4.25}
```

`ok: false` without an `error` field → warn "Decisions are ambiguous" + suggest rewrite. A non-numeric or out-of-range score returns `{"ok": false, "error": "..."}` with exit code 1 — fix the input. If the script is unavailable, average by hand (pass at 3.5 or higher) and write `gate: manual (script unavailable)`.

### Deliverable
`specs/{kebab-name}/spec.md` — required sections:
Meta / Goal / Non-goals / Confirmed Goal / Research / Decisions / Constraints / Known Gaps / Requirements / Tasks / Plan Summary

Terms and skeleton (keep it compatible with the format `coverage_check.py` reads):
- **Mirror**: the user's request restated in your own words at L0. It becomes the Confirmed Goal only after the user says it is right.
- **Meta**: one block with the date, author (user or model), status (draft or approved) and Reviewer (the independent reviewer's verdict, or `SKIPPED`).
- **Known Gaps**: what is still unknown or undecided, and why (if none, write "none: reason").
- **GWT sub-requirements**: a requirement `R{n}` split into Given/When/Then one-line sub-requirements `R{n}.{m}`.

```markdown
## Meta
- Date: {YYYY-MM-DD} | Author: {...} | Status: draft | Reviewer: {reviewer verdict | SKIPPED}
## Goal / Non-goals / Confirmed Goal
## Research        # L1 codebase facts only
## Decisions       # D1...: decision + reason
## Constraints
## Known Gaps
## Requirements
- R1 {one-line requirement}
  - R1.1 Given {...} When {...} Then {observable result}
## Tasks
### Task 1 {title}
Fulfills: R1.1
## Plan Summary
```

---

## Mid-Task Scope Drift — 10x-Discovery Rule

> Quick and Full modes both lock IN/OUT only at write time — neither covers what to do when scope explodes mid-execution.
>
> Who this applies to: this skill writes no code, so this rule is guidance for the session that implements from the saved BRIEF.md/spec.md.

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
| [READ] Quick: 2-level scan of the project (10-file cap). Full: codebase research for the Research section (L1) | Deep code analysis or refactoring plans beyond what the scope needs |
| [WRITE] Save BRIEF.md or spec.md | Edit an existing BRIEF.md/spec.md (hand off to Edit) |
| [ASK] Full: interview the user and record Decisions and Constraints (L2), with the user approving each | Make Decisions on the user's behalf without their approval |
| [AGENT] Full: independent review of the L2 Decisions (Core Rules 3) | Run the implementation |

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Save BRIEF.md / spec.md | high (git) | L1 (conversational approval, Invariant 5: user approval gate) |
| Overwrite existing spec | medium | L1 (Invariant 9: forbidden — editing an existing spec is outside this skill) |

## Invariants (never violate)

1. **No implementation during scope**: no code changes during/after scope writing. Violation → scope becomes a post-hoc rationalization for code already written instead of a constraint that shapes it, and the OUT section stops meaning anything.
2. **Scope OUT mandatory**: baseline min 2 items — unless the scope is self-evidently a single item, in which case 1 item plus a stated reason is acceptable. Violation → only IN is recorded, so anything not explicitly listed becomes fair game during implementation — scope creep with no written boundary to point back to.
3. **Exit Criteria = observable + measurable**: auto-reject vague items like "works correctly". Violation → "done" becomes a matter of opinion at handoff time, and disagreement about completion surfaces only after the work is finished.
4. **Question limit 3** (Quick): exceed → conservative minimum scope — unless there is clear evidence a 4th question would change the direction, in which case one additional question is allowed once, with the reason stated. Violation → interrogation replaces scoping and the user abandons the flow instead of getting a usable brief.
5. **Approval gate required**: save file only after explicit user approval (in a delegated run: the user's own words passed verbatim by the caller, otherwise NEEDS_INPUT). Violation → an unreviewed draft becomes the working spec, and errors in it propagate into implementation before anyone caught them.
6. **Constraints mandatory** (existing project): 0 items → rescan. Violation → the brief looks complete but omits the existing system's real limits, so implementation collides with constraints nobody wrote down.
7. **Risk Flags min 1** — unless there is truly no risk, in which case "no risk: <reason>" may be substituted. Violation → a known failure mode goes unrecorded, so the same risk resurfaces later as a surprise instead of a tracked flag.
8. **Layer order immutable** (Full): L0→L1→L2→L3→L4. Violation → decisions (L2) get made on a foundation (L0/L1) that was never confirmed, so the spec inherits an unvalidated goal.
9. **No spec overwrite** (Full): editing a spec that existed before this run is outside this skill (hand off to Edit; see Discard If). Appending a layer to the spec.md that this run created is allowed. Violation → prior layers' history is destroyed, so a later reviewer can't tell what changed or why.
10. **Tasks→Requirements link required** (Full). Violation → a task exists with no requirement behind it — untraceable work that can't be checked against the spec it supposedly fulfills. **Enforcement**: before requesting L4 user approval, run `python3 "${CLAUDE_SKILL_DIR}/scripts/coverage_check.py" --spec <spec.md> [--plan <plan.md>]` and require `COVERAGE: PASS` — uncovered requirements, tasks without `Fulfills:`, undefined R-ids, or duplicate R-ids make it FAIL. Requirement definitions are read only from the Requirements section (R-ids repeated in Tasks or Plan Summary are references, not definitions); a document with no Requirements heading is read whole. If the script cannot run, check the same four conditions by hand and write `gate: manual (script unavailable)`. Vague adjectives and placeholders on requirement lines (fast, intuitive, robust, TBD, ...) only produce warnings; treat them as a signal to rewrite at L3. The script is only for documents in scope format (requirement lines starting with `R1`, `R1.1`; `### Task` headings with `Fulfills:`) — do not run it on documents that use R-numbers for something else, such as scoring-rubric items.
11. **No silent absorption or quiet shrinking on 10x discovery**: if implementation reveals scope that is a multiple of what was originally understood, surface it immediately — don't absorb it silently and don't quietly shrink the deliverable to fit the original budget. Violation → the user only discovers the delay or the missing scope later, after the fact.
12. **Independent review or disclosed SKIPPED** (Full): the L2 Decisions go through an independent reviewer, or `Reviewer: SKIPPED` is written in the spec.md Meta. No silent skip. Violation → the author approves their own decisions and a blind spot spreads into L3 and L4.

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
| "Skip OUT" | Invariant 2. Explicit even when clear prevents scope creep — the single-item exception still requires a written item plus a stated reason, not silence |
| "Clear enough, no questions" | Need immediate 1-sentence answer to 3 questions for Sufficient |
| "L0-L1 obvious, skip" (Full) | L2 decisions have no foundation without them |
| "Write spec in one go" (Full) | Mid-gates allow course correction |
| "Tasks before Requirements" (Full) | No Fulfills link = untraceable |
| "Just quietly do a bit more to make it fit" | Invariant 11. Silent absorption means the user only finds out about the delay or shrinkage later, without warning |

## Truthful Reporting 
1. **no mock deception**: never present an unapproved draft or an assumption as locked scope - mark pre-approval state as a draft, and never save without approval.
2. **no test façade**: missing OUT = `⚠️ Scope OUT not written`.
3. **no silent brokenness**: unmeasurable Exit Criteria = PARTIAL.

## Output

**Before approval**: the brief (Quick) or the current layer's draft (Full) is emitted into the conversation only — no *deliverable* file (`BRIEF.md` / `spec.md`) is written yet. Quick mode's Step 4 gate needs a file to read, so a `.scope-draft.md` scratch file may exist at this stage — it is not the deliverable and is deleted once `BRIEF.md` is saved (or once the flow is abandoned). This is the review surface; catch problems here, not after the deliverable exists.

**After approval**:
- Quick → `BRIEF.md` written to disk (Step 4, gated by the min-items script above), scratch file deleted.
- Full → `specs/{kebab-name}/spec.md` written/appended per layer (L0→L4), each layer gated by its own user-approval checkpoint.

**Next step (one line after saving)**: `Next: pass <absolute path of the saved BRIEF.md or spec.md> as input to your planning step` - a planning step reads Scope OUT / Non-goals, Decisions and Requirements from it. Without this line the saved scope never reaches the plan.

**Chain to freeze and goal-lock**: when the user continues with `/freeze`, freeze takes its editable zone from Scope IN (or the Tasks) and treats Scope OUT as frozen. When the user continues with `/goal-lock`, give goal-lock the same saved path; it maps Scope IN to the target and Scope OUT (BRIEF "OUT" / spec "Non-goals") to its SCOPE Exclude list. Both skills ship in this repo.

**Delegated run with no user present**: if an approval is needed and the caller did not pass the user's own approving words verbatim, return `NEEDS_INPUT: <what needs approval>` instead of saving.

**Final status label** (required on completion): `WORKING` (brief/spec saved, all gates passed) / `PARTIAL` (saved with a documented gap — e.g. `[assumed]` tags from a question-limit exit, or a section marked `⚠️`) / `BROKEN` (an approved draft turns out structurally contradictory or unusable after saving) / `BLOCKED` (waiting on user approval — including `NEEDS_INPUT` in a delegated run — or another unresolved external dependency). Conditions per label are the same as Truthful Reporting above.

## Principles
- **OUT matters more than IN** — people say what to do but skip what NOT to do.
- **Fewer questions better** — 4+ and users say "just build it".
- **Brief is not an implementation spec** — what and done only. How is implementer's.
- **Full extends Quick** — detect complexity in Quick → offer Full switch.
