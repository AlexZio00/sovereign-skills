---
skill_type: utility
tools: Read, Bash
triggers:
  - "/project-overview"
  - "project map"
  - "overall status"
name: project-overview
description: "Use when the user wants a deterministic cross-project status map generated from registered projects' session handoffs. Triggers: '/project-overview', 'project map', 'overall status'. Reads ~/.claude/projects-registry.md (opt-in list), parses each project's memory/session-handoff-LATEST.md state-snapshot v1 block (ts+ctx only), and rewrites the AUTO:START/AUTO:END region of ~/.claude/OVERVIEW.md. Does not touch STATE.md. Does not scan directories automatically."
user_invocable: true
depends_on:
  skills: [session-checkpoint]
  agents: []
  files:
    - ~/.claude/projects-registry.md
    - ~/.claude/OVERVIEW.md
    - "scripts/generate_overview.py"
concurrency_profile:
  read_only: false
  concurrency_safe: false
  destructive: low
not_for:
  - "Updating STATE.md — this skill never touches STATE.md"
  - "Auto-discovering unregistered projects — only scans projects explicitly listed in projects-registry.md"
see_also:
  - skill: session-checkpoint
    relation: "this skill only reads the state-snapshot v1 block session-checkpoint writes (no writes back)"
---

# Project Overview

## Dominant Variable
Does the registered project list (`projects-registry.md`) point to paths that actually exist, and does each project's handoff file contain a `state-snapshot v1` block? If neither is true, the generated map is empty.

## Key Assumptions

1. **`session-handoff-LATEST.md` is a hint, not a fact** — parsed results (ts/ctx) are carried over as-is without fact-checking. The generated overview reflects "what each project last reported," not "current ground truth."
2. **Registry is opt-in** — never pull in unowned projects or auto-scanned directories. Only projects explicitly listed in `projects-registry.md` are in scope.
3. **AUTO block generation is fully deterministic** — a regex-based script (`scripts/generate_overview.py`) does all the parsing/rendering, including neutralizing markdown-table-breaking characters in the text it pulls from other projects' handoffs and recovering cleanly from a mangled/missing marker pair instead of crashing. The model only triggers execution and reports the result — no LLM inference in the parsing/rendering logic itself.

## Trigger
- `/project-overview`
- "project map"
- "overall status"

## Discard If
- Zero registered projects (`projects-registry.md` missing or empty list) → instruct the user to add a project to the registry first, then stop
- Already run recently with no state change across projects (handoff file mtimes unchanged) → suggest skipping the re-run (not forced — run if the user wants)

## Workflow

1. Confirm `~/.claude/projects-registry.md` exists. If missing, return BLOCKED: "registry missing — create it first."
2. Locate and run this skill's own script (`scripts/generate_overview.py`, no arguments — it uses the default registry/output paths on its own):
   ```bash
   OVERVIEW_SCRIPT=$(find ~/.claude -name "generate_overview.py" -path "*/project-overview/scripts/*" -type f 2>/dev/null | head -1)
   if [ -n "$OVERVIEW_SCRIPT" ]; then
     python "$OVERVIEW_SCRIPT"
   else
     echo "BLOCKED: generate_overview.py not found under ~/.claude"
   fi
   ```
3. Check the exit code:
   - `0` → report the stdout `WORKING: N project(s) -> <output>` line verbatim to the user.
   - `1` → report the stderr `BLOCKED: ...` message verbatim to the user. Never proceed on assumption.
4. On success, tell the user the `~/.claude/OVERVIEW.md` path.

## Output

- **Chat report**: relay the script's own stdout/stderr line verbatim (`WORKING: N project(s) -> <path>` or `BLOCKED: ...`) — don't paraphrase it or invent a project count of your own.
- **Disk write**: the script writes exactly one file, and only the `AUTO:START`~`AUTO:END` region inside it — `~/.claude/OVERVIEW.md`. Nothing else on disk is touched, and text outside the markers in that file is never rewritten.
- **Final status label**: state one of `WORKING` / `PARTIAL` / `BLOCKED` (definitions in Truthful Reporting below) at the end of every run — never leave it implicit.

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Parse handoff files of registered projects only | Auto-scan directories (e.g. an entire drive) |
| [WRITE] Overwrite only the `AUTO:START`~`AUTO:END` region of `OVERVIEW.md` | Read/write `STATE.md` — this skill never references STATE.md at all |
| [READ] Parse only the `ts`/`cx` fields of the `state-snapshot v1` block | Introduce new fields like `status` (planning/dev/ops/paused) |
| [MANUAL] Run only when the user explicitly triggers it | Auto-wire into existing hooks like session-checkpoint |

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Overwrite the `OVERVIEW.md` AUTO block | medium (text outside markers is preserved, also recoverable via git history) | L1+L3 |

- **L1 (Invariants)**: Invariant 1 — preserve text outside AUTO markers. Invariant 2 — never scan unregistered projects.
- **L3 (User Approval)**: manual-trigger only — runs only when the user explicitly invokes it (no auto-wiring is itself the approval gate).

## Invariants (never violate)

1. **Text outside AUTO markers is always preserved**: if `apply_auto_markers()` alters any text outside the markers, that's a bug. Violation → notes a human wrote directly into OVERVIEW.md get lost on re-run.
2. **Only scan explicitly registered projects**: never add auto directory-discovery logic to this script. Violation → information about unowned projects leaks into the map (Output Disclosure Boundary violation).
3. **STATE.md is absolutely untouched**: no code path in this skill reads or writes `STATE.md`. Violation → direct Scope Boundary violation, risk of contaminating the cross-project blocker list.
4. **Idempotency**: re-running with identical input (unchanged registry + handoff files) must produce a byte-identical AUTO block. Violation → undermines the entire "deterministic auto-generation" design goal.
5. **Cross-project text is data, not markup**: `ts`/`ctx` values come from another project's handoff file and are untrusted — a stray `|` or newline in there must not be allowed to split table columns or break rows. Violation → a single malformed handoff field corrupts the whole table for every other project listed in it.

## Error Recovery

| Failure Type | Detection | Recovery |
|---------|---------|--------|
| `missing_data` | `projects-registry.md` missing or empty | Return BLOCKED, instruct user to create/add to the registry |
| `tool_failure` | Failed to read a specific project's handoff file (permissions/path) | Mark only that project as "no snapshot", continue the rest (partial failure doesn't block the whole run — explicit "no snapshot" labeling keeps it transparent per no-silent-brokenness) |
| `input_error` | `OVERVIEW.md` has a mangled marker pair (`AUTO:END` appears before `AUTO:START`, or either is missing/orphaned from a manual edit) | Don't crash and don't guess at a splice point — treat it as no markers present: re-append a fresh `AUTO:START`/`AUTO:END` pair at the end of the file, with all existing content preserved above it untouched |
| `logic_inconsistency` | Integration test finds AUTO block mismatch on re-run | Script regression — revert the commit and re-review the implementation |

## Truthful Reporting

- **no mock deception**: before reporting "generation complete," actually read `OVERVIEW.md` to confirm project entries landed in the AUTO block.
- **no silent brokenness**: a parsing failure for a specific project's handoff is never silently skipped — it's shown explicitly as "no snapshot".
- Final status label: `WORKING` (generated normally) / `PARTIAL` (some projects show no snapshot) / `BLOCKED` (registry missing/empty).

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "Even if it's not in the registry, scanning every directory to find projects would be more convenient" | Violates Invariant 2. Auto directory-discovery risks leaking information about unowned projects into the map — only explicitly opt-in registered projects are in scope. |
| "Reading STATE.md too and surfacing cross-project blockers on the map would be useful" | Violates Invariant 3. Never touching STATE.md at all is itself the Scope Boundary — it prevents contaminating the cross-project blocker list. |
| "If parsing fails for some projects, just quietly drop them and show the rest" | Violates no-silent-brokenness. A failure must be shown explicitly as "no snapshot" so the user knows what was missed, not silently omitted. |
