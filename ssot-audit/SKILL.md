---
skill_type: analysis
tools: Read, Grep, Glob, Edit
name: ssot-audit
description: "Find where one fact, value or decision is duplicated or contradicted across files, name the single source of truth (read-only), then consolidate the copies after user approval."
depends_on:
  skills: []
  agents: []
  files: []
concurrency_profile:
  read_only: false
  concurrency_safe: false
  destructive: low
tags: [audit, consolidation, source-of-truth, dedupe]
triggers:
  - "/ssot-audit"
  - "source of truth"
  - "find where this fact is duplicated"
  - "consolidate the duplicates"
  - "which file is canonical"
  - "정본이 뭐야"
  - "이 사실 어디어디 흩어져있는지 찾아줘"
  - "중복된 거 통합해줘"
user-invocable: true
not_for:
  - "Checking only the instruction docs Claude Code loads (CLAUDE.md, MEMORY.md, skills, agents, commands, plugins) for stale or contradictory claims -> doc-drift"
  - "Exhaustive audit of a whole area, not one fact -> full-audit"
see_also:
  - skill: doc-drift
    relation: "doc-drift=loaded context files only (CLAUDE.md, memory, skills, agents); ssot-audit=any artifact in a repo or notes folder, one fact at a time"
  - skill: full-audit
    relation: "full-audit=everything in an area; ssot-audit=one tracked fact"
---

# SSOT Audit: find the source of truth, then consolidate

## Purpose
One fact often lives in several artifacts (docs, code, config, tickets, notes) and the copies drift or contradict each other. This skill finds where the fact lives and how many copies exist, names one source of truth (Phase A, read-only), and after user approval brings the other copies in line with it (Phase B).

`doc-drift` only checks the instruction docs Claude Code loads into context (CLAUDE.md, MEMORY.md, skills, agents, commands, plugins) for stale claims. This skill works on any artifact in a repo or notes folder.

**Dominant variable**: is the chosen source of truth really the most authoritative location and the one updated most often? A wrong pick makes consolidation distort the fact instead of fixing it.

**Discard if**: the fact already lives in exactly one place (no duplication), or the job is only a stale-claim check of the loaded instruction docs (use `doc-drift`).

**Run only on explicit request**: this skill edits files in Phase B, so it does not start on its own; run it only when the user asks for it.

**Verify before acting**: every artifact found in Phase A is a snapshot from the time of the audit. Before Phase B edits anything, re-check the current state with Glob/Grep. "I saw it during the audit, so it must still be right" is not allowed.

## Trigger
- "where is this fact scattered", "what is the source of truth", "consolidate the duplicated content"
- "find where this fact is duplicated", "consolidate the source of truth"
- `/ssot-audit`

## Workflow

### Phase A: audit (read-only by policy, not by enforcement)
Edit is listed in `tools:` (the tool list is descriptive metadata, nothing enforces it), so keeping this phase read-only is a rule you follow.

1. Fix the scope (repo, folder or notes directory) and the tracked item: one specific value, spec or decision, not a whole document.
2. Enumerate every occurrence of the item with the Grep and Glob tools (no shell flags needed). Narrow Grep with its `glob` or `type` filter to text files, and exclude `__pycache__` and build output (for example glob `!**/__pycache__/**`), otherwise compiled-file matches have to be filtered by hand.
3. Classify each occurrence: exact copy, paraphrase, partial excerpt, stale, or contradictory.
   - **stale**: the copy differs from the source of truth and you can show it is an earlier version of the fact (version history, a changelog, or the source of truth explicitly superseding it). Action: reference or dedupe, after Phase B approval.
   - **contradictory**: the copy differs and you cannot show it is the older one. Action: reconcile.
4. Pick a source-of-truth candidate: the most authoritative location, closest to the point where the fact actually changes (code or config for a value, a spec document for a decision, a state file for a status). Designate it with a one-line reason; never pick arbitrarily.
   - Two or more candidates of the same kind (for example constants in two different modules): do not choose, classify as reconcile.
   - One source of truth but a non-canonical copy holds a different value: that copy is also reconcile. An older date alone does not make it stale.
5. For each non-canonical occurrence choose an action:
   - dedupe: remove the copy (removing content inside a file is done with Edit in Phase B; deleting a whole file is only proposed to the user, who runs the command, for example `git rm <file>`; this skill has no tool to delete files)
   - reference: replace the copy with a link or pointer to the source of truth
   - reconcile: contradiction, a human has to decide
6. Output the audit report: occurrence table (location, kind, action), source-of-truth proposal with reason, and a separate list of contradictions.

### Phase B: consolidation (writes, needs user approval)
1. Show the Phase A report and ask which actions to apply. Even a blanket "do it all" is followed only after you show, item by item, what will be removed.
2. Before applying, check each item for details that exist only in the non-canonical copy, and move them into the source of truth first (Invariant 4). Then apply only the approved dedupe/reference items with Edit. Leave reconcile items untouched until a human decides. For an approved whole-file deletion, print the command and let the user run it.
3. Re-verify with Grep: the fact should now exist once in the source of truth plus references.

## When to retire this skill
Review it for narrowing, merging or removal if any of these is observed:
- It has not been invoked for 90 days and no other skill or agent calls it. (If it exists for safety or recovery, judge by likelihood, failure impact, difficulty of detection and lack of substitutes, not by call count.)
- The same defect (wrong trigger, wrong result, ignored instruction) comes back three or more times after fixes.
- Another asset gives the same result at lower cost.
- A rule, tool or platform feature this skill relied on has changed and the premise is gone.

## When a result is invalid
If the files, command output or source text a result relied on look different when re-checked (the target changed or was misread), treat that result as invalid and run it again. A result is valid only for the point in time its inputs were read.

## Invariants (never violate)
1. **Phase A never writes.** Do not fix anything you find mid-audit. Violation → destructive edits without confirmation, deletions that are hard to undo.
2. **Contradictions (reconcile) are never resolved by guesswork.** Which side is right needs a human. Violation → silently declaring one side correct can make a wrong fact the only source of truth.
3. **No findings is a valid result.** Do not invent duplicates. Violation → forced findings cause needless edits.
4. **Keep details that exist only in a non-canonical copy.** Move them into the source of truth before deleting the copy. Violation → dedupe turns into information loss.
5. **Copies across a trust or permission boundary are flagged, not touched.** Private versus public, internal versus customer-facing: leave them as they are and report. Violation → internal-only information leaks into a public copy.
6. **Whole-file deletion is proposed, never done.** Violation → a file that held unique content is lost without the user running the command knowingly.

### Safety layers
| Risky action | Reversibility | Layers |
|---|:---:|---|
| Phase B edit (dedupe/reference) | medium | prompt rules + user approval (recoverable through git, approval still required) |

Phase B approval is valid for the current session only. Re-running in a new session needs fresh approval.

## Scope boundary
| Does | Does NOT |
|---|---|
| [READ] enumerate every occurrence with Grep/Glob | edit files without user approval |
| [READ] designate a source-of-truth candidate and propose actions | resolve contradictions (reconcile) on its own |
| [EDIT] apply only approved dedupe/reference actions | delete a copy before preserving its unique details, or delete a whole file (propose it instead) |
| [READ] report Phase A and Phase B separately | the stale-claim check of the loaded instruction docs (that is doc-drift) |

## Rationalization table
| Rationalization | Rebuttal |
|---|---|
| "It's obvious which one is right, I'll just merge them" | Violates Invariant 2. "Obvious" is the auditor's opinion, not a verified fact. Reconcile goes to a human. |
| "While auditing I might as well fix what I found" | Violates Invariant 1. The A/B split exists to stop edits that cannot be undone before approval. |
| "Saying there are no duplicates feels weak, let me find something" | Violates Invariant 3. Forced findings cause needless edits. |
| "doc-drift already covers this project" | doc-drift only checks the loaded instruction docs for stale claims. One fact's duplicates across a whole repo or notes folder, and consolidating them, are this skill. |

## Output
- Phase A: occurrence table (location, kind, action), source-of-truth proposal, contradiction list, in the conversation.
- Phase B: list of changes actually applied, per file, plus the re-verification result.

## Error recovery
| Failure type | Recovery |
|---|---|
| input_error | No fact to track, or one too broad (for example "consolidate the duplicated content"): do not start; ask the user to name the fact (a value, spec or decision) in one line. |
| missing_data (Phase A) | Grep/Glob cannot find the scope: report "scope unclear" and ask the user to confirm it. |
| tool_failure (Phase A) | Retry a failed Grep/Glob once, then report which searches failed and mark the occurrence list as incomplete. Do not start Phase B on an incomplete list. |
| tool_failure (Phase B) | Retry a failed Edit once, then stop. Report which items were applied and which were not; do not continue with the remaining items. |
| logic_inconsistency | Two or more equally authoritative source-of-truth candidates: classify as reconcile, never pick one. |

## Truthful reporting
1. Report only occurrences you actually confirmed with Grep. Do not list guessed locations.
2. If Phase B is applied only in part, state which items were applied and which were not.
