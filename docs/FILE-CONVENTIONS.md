# File conventions

These are the files the session skills (`session-start`, `session-checkpoint`, `next-action`, `project-overview`, `collab-audit`) read and write, and the other skills that touch them. Every format below is taken from what `session-checkpoint` writes; it is the writer of nearly all of them. Paths without a leading `~` are relative to the project root.

Rule for every skill: a missing file is never an error. The reader skips that step and says so; only `session-checkpoint` creates files.

| File | Written by | Read by |
|---|---|---|
| `memory/session-handoff-LATEST.md` | session-checkpoint (setup creates a first one) | session-start, next-action, project-overview, collab-audit |
| `tasks/lessons.md` | session-checkpoint (setup creates the file) | session-start, next-action, project-check, skill-ops, collab-audit |
| `~/.claude/STATE.md`, `docs/STATE.md` | session-checkpoint (edits only) | session-start, next-action |
| `memory/MEMORY.md` | session-checkpoint, session-start (promotion only), setup | session-start, session-checkpoint, collab-audit, doc-drift |
| `memory/context-log.md` | session-checkpoint | session-start, `ct_promotion_queue.py` |
| `~/.claude/.harness/invocations/YYYY-MM.jsonl` | session-checkpoint only | collab-audit, skill-ops, `harness_observability.py` |
| `~/.claude/.harness/interventions/YYYY-MM.jsonl` | session-checkpoint | session-start (`harness_observability.py`) |
| `~/.claude/projects-registry.md` | you | project-overview |
| `~/.claude/OVERVIEW.md` | project-overview (AUTO block only) | you |

## Session handoff: `memory/session-handoff-LATEST.md`

One file, no version numbers, at most 200 lines. It lists what the next session must do, never what was done; finished items are deleted (git history keeps them).

If missing: session-start prints `[No handoff — starting fresh]` and continues with its other steps; next-action skips it; project-overview shows "no handoff file" for that project; collab-audit skips handoff analysis; session-checkpoint writes a new one.

Layout, in this order:

````markdown
---
name: Session Handoff — Latest          (front matter is optional)
---
<!-- state-snapshot v1 -->
```yaml
ts: 2026-10-21
ctx: "one-line session summary"          # at most 20 words
next:                                    # at most 5; verb + object, no commands
  - "Fix the loader KeyError (urgency: H)"
diff:                                    # at most 5
  - op: add|del|mod|decide
    item: "file, skill or decision name"
    why: "at most 10 words"              # optional
    basis: run|doc|user|dialogue         # op: decide only
blocked:                                 # at most 3
  - item: "issue"
    risk: H|M|L
```

# Session Handoff (2026-10-21 — title)

## What to do now (priority order)
1. Most urgent item, with the command to run (since: 2026-10-20)
## Scheduled checks (by date)
- 2026-10-25 what to check (since: 2026-10-21)
## Current work status
## Pending decisions
- Topic: options — opinion · urgency: H · basis: run · since: 2026-10-18
## Outstanding issues
- Unresolved problem · risk: M
## System understanding (context needed next session)
## User's current interests
````

- Dates are absolute (`YYYY-MM-DD`, optionally followed by `HH:MM`); relative words such as "tomorrow" are converted when an item is carried forward.
- `since: YYYY-MM-DD` is the date an item was first listed; carrying an item forward never changes it. It is an age, not a due date.
- `basis:` says how a conclusion was reached: `run` (a tool run), `doc` (read in docs or code), `user` (the user's own words), `dialogue` (conversation only; the default when unsure).
- Optional fields on high-urgency or high-risk items: `stop:`, `owner:`, `fallback:`.
- Items that wait for a future date belong under "Scheduled checks"; "What to do now" holds only what can start immediately, because session-start takes Priority 1 from its first entry. The `next:` list follows the same rule and restates the top of "What to do now" in compressed form.
- `memory/.session-handoff.sha256` is an optional hash sidecar written by session-checkpoint Phase 4.5 (see below).

`handoff_due_check.py` (identical copies in session-start, session-checkpoint and next-action) reads the `next:` list and every item under the headings "What to do now", "To do", "Next steps", "Next actions", "Next", "Pending decisions" and "Scheduled checks". For each item it prints one status:

- `PAST`, `TODAY`, `FUTURE`: the item's due date compared with now. With several dates on one line, the latest (by parsed date and time) is the due date and `+N` counts the earlier ones.
- `STALE`: the `since:` date is 14 or more days old. A `FUTURE` item is never `STALE`.
- An item that appears in the `next:` list and in a prose section is reported once.

## Lessons: `tasks/lessons.md`

Behavior corrections the next session should carry forward. If missing: session-start and next-action skip it; session-checkpoint creates it when it records the first lesson (title line `# tasks/lessons.md — AI behavior correction rules`).

```markdown
### [2026-10-21] One-line lesson title
> conf: 0.5 · seen: 2026-10-21 · obs: 1 · model: opus-4.8

Concrete correction: when X happens, do Y.
```

- Header: `### [YYYY-MM-DD] title`, with `[DIAGNOSIS_MISSING]` after the title when the root cause is not known yet.
- Meta line (`>` quote, middle-dot separated, any order): `conf` (0.3 to 0.9), `seen` (last date the lesson applied), `obs` (times observed). Optional: `model:` (the model that made the mistake), `regime:`, `escalate_if:`, `kill_if:`, `rule_gap: A|B` (A = a rule existed and was not followed, B = no rule existed), `cause: harness`, `gate: <name>` (added by you when a rule or gate already enforces the lesson). A lesson may also carry a line `> hook_candidate: true`.
- Updates: a re-occurrence sets `seen` to today and adds 1 to `obs` (not twice on the same day). `conf` rises by 0.1 when `obs` reaches 3, 6 or 9 (maximum 0.9). A user correction after a violation lowers `conf` by 0.1 (minimum 0.3) and sets `seen` to today.
- Archive rule (the only one; session-checkpoint's monthly cleanup applies it): archive a lesson when `conf < 0.4` and `seen` is more than 90 days old, or `obs = 1` and `seen` is more than 90 days old. Move it to `tasks/_archive/lessons-pre-YYYY-MM.md`, unless a roadmap, handoff or STATE file still cites it.
- Optional sections: `## Synthesis — conf≥0.7 clusters` (overwritten monthly by session-checkpoint), `## Pending patterns`, and `## Graduated Gates`, a table you maintain with one row per verified gate (columns: trigger, check). session-start shows those rows; no skill here writes them.

## Global state: `~/.claude/STATE.md` and `docs/STATE.md`

Cross-project open items. `~/.claude/STATE.md` spans all projects; `docs/STATE.md` is the same format for one project. Readers show a global item only when it relates to the current project, tagged "(global)".

Sections session-checkpoint maintains: a PENDING table (one row per item that waits for a trigger), an active blockers list, and a change log table (date, one-line summary). session-checkpoint only deletes a row when its trigger is met or the blocker is resolved (rows marked done are removed), and appends change-log rows; it never rewrites the file. project-overview never reads or writes it. If missing: skipped by every skill; session-checkpoint does not create it.

## Memory: `memory/MEMORY.md` and `memory/context-log.md`

`MEMORY.md` holds permanent facts. The compiled-truth part ("CT") is rewritten in place, never appended to; recorded file paths and function names are checked with Glob or Grep before they are written, and the index points at `session-handoff-LATEST.md`. Optional tags on `##` headings: `<!-- #always -->` (session-start loads the section) and `<!-- #on-demand -->` (session-start lists only the heading). A file without tags is loaded whole. Paths in backticks are checked by `validate_memory_claims.py`. If missing: session-start skips it; session-checkpoint creates an empty one.

`context-log.md` is the episode log, one entry per line:

```
[2026-10-21] [TYPE] [ttl:90d] [risk:H] [ref:0] what happened or was decided
```

- `TYPE` is free text; used values include `LESSON`, `CRYSTALLIZE_CANDIDATE`, `CRYSTALLIZE_REJECTED` and `QUARANTINE` (content that came from outside, kept out of promotion).
- `ttl` is `30d`, `90d` or `permanent`. `[risk:H|M]` is optional. Brackets may or may not be separated by spaces, and a line may start with `- `. Readers match a line that starts with `[YYYY-MM-DD]`.
- `ref:N` counts how often the topic came up again. When a session revisits a topic, session-checkpoint raises N in place (the only edit it makes to old lines). Entries with `ref` 3 or more are promotion candidates for MEMORY.md; entries older than 90 days with `ref:0` are skipped by session-start.
- If missing: session-start skips it; session-checkpoint creates it.

## Invocation ledger: `~/.claude/.harness/invocations/YYYY-MM.jsonl`

One JSON object per line, append-only, one file per month. session-checkpoint is the only writer (Phase 1.6.5 is the primary point, Phase 3.7 the fallback). Readers must count records from every `source` and accept both forms of `discarded`.

```json
{"ts":"2026-10-21T14:32:11","date":"2026-10-21","skills":["scope"],"agents":["Explore"],"discarded":[{"skill":"freeze","reason":"discard_if"}],"source":"session-checkpoint-phase1.6.5","session_id":"2026-10-21T14:32:11"}
```

| Field | Meaning |
|---|---|
| `ts`, `date` | ISO 8601 time and `YYYY-MM-DD` date of the record |
| `skills`, `agents` | names called in the session (Skill tool `skill:`, Agent tool `subagent_type:`) |
| `discarded` | skills that triggered and were skipped by their Discard If rule. Each entry is a string (skill name) or an object `{"skill": ..., "reason": ...}`; the writer uses the object form |
| `source` | `session-checkpoint-phase1.6.5`, `session-checkpoint-phase1.6.5-growth` (activity after a checkpoint in the same session) or `session-checkpoint-phase3.7-fallback`. Other values may appear; readers do not filter on source |
| `session_id` | the record's own timestamp string; the fallback step skips a session whose `session_id` is already present |
| `prior_session_id` | growth records only: the `session_id` of the record they continue, or `"unknown"` |
| `outcomes` | optional list of `{target, firstAttemptPass, reworkRounds, resolvedBy}` |

A growth record lists only calls made after the record it continues, so adding records never counts a call twice. If the ledger does not exist, readers report "no log" or zero counts.

Related logs written by session-checkpoint: `~/.claude/.harness/interventions/YYYY-MM.jsonl` (fields `ts`, `date`, `session_id`, `type` = correction | rejection | override | escalation, `skill`, `agent`, `model`, `rule_reference`, `context`; older logs may name `rule_reference` as `l0_clause`) and, only with the optional Phase 4.5, `~/.claude/.harness/receipts/YYYY-MM.jsonl` (a hash receipt per checkpoint). Raw log lines are never pasted into model context; skills use counts only.

## Project registry and overview (project-overview)

`~/.claude/projects-registry.md` is written by you. One line per project, `- name: /absolute/path` (a POSIX, `~`, `C:\` or `C:/` path). Lines starting with `#` or `>` and blank lines are ignored; any other bullet whose value is not an absolute path is ignored with a warning.

```
# Registered projects
- api: /home/me/work/api
- site: C:/work/site
```

project-overview reads `<project>/memory/session-handoff-LATEST.md` for each entry, takes only `ts` and `ctx` from the `state-snapshot v1` block, and rewrites the region between `<!-- AUTO:START -->` and `<!-- AUTO:END -->` in `~/.claude/OVERVIEW.md` (a table: Project, Path, Last Update, Context). Text outside the markers is never changed. If the registry is missing the skill stops with BLOCKED; a project without a handoff is listed as "no handoff file", and one without a snapshot block as "handoff has no state-snapshot block".

Optional: `~/.claude/memory/model-diff-ledger.md` is a file you keep yourself; session-start reads only its `last-analysis: YYYY-MM-DD` line to time a model-comparison reminder.

## Optional attestation (session-checkpoint Phase 4.5)

`handoff_attestation.py write-receipt checkpoint <session_id>` appends a hash receipt and refreshes `memory/.session-handoff.sha256`. Nothing in this repo reads them back; `verify`, `guard` and `verify-receipt` exist for a hook or manual run that you set up. The step runs only when `~/.claude/.harness/receipts/` already exists.
