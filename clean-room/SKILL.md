<!-- provenance: adapted from LilMGenius/paperthin "autobahn" skill (MIT license). Core mechanism (carve -> clean subagent -> verify -> ledger) preserved; reformatted to this repo's SKILL.md conventions, renamed to avoid reusing the original author's skill name verbatim. Upgraded after an adversarial 3-lens design critique (adversarial-user / isolation-integrity / systemic-integration-gap) surfaced gaps the source design didn't cover in a harness with shared filesystem state between the main session and its subagents. See CHANGELOG.md. -->
---
name: clean-room
description: "Use when a task mixes safety-adjacent material (stealth, scraping, privacy, IP, licensing, security) with genuinely safe work, or the moment you notice yourself about to hedge, dilute, silently drop, or brace for a refusal on part of a request. Triggers: 'strip the risky part out', 'just the safe part', 'carve this out', 'clean-room this'."
user_invocable: true
---

# Clean Room

## Purpose

**Dominant Variable**: did the subagent that actually executes the work ever see the original safety-adjacent request? If it did, this skill has failed — isolation is everything. "Never saw it" applies not just at the prompt layer but at the **filesystem/tool-access layer** too (a subagent with shared Read/Grep access to your project files can read a mention of the risky request in a memory or log file just as easily as if it had been told directly).

**Discard if**:
- The whole request is obviously safe (no safety-adjacent element at all) — just handle it directly
- The whole request is a clear bright-line refusal (nothing safe to carve out) — nothing to carve, just decline
- The user has already narrowed the request to the safe part explicitly — no carving needed, proceed directly

## Workflow

### 1. FRAME
Read the request, its inputs, and any risk posture the user has stated. **Before drafting a carve plan, check whether there's a similar past decision on record** (a lessons file, a decision log) for this user/topic, and if so cite the precedent and note explicitly if this judgment differs from it — this keeps the judgment from drifting session to session. If the user has already approved a descope, go to 3 (GUARD). Otherwise build a proposed carve plan showing the split explicitly and wait for approval — **bright-line items** (no safe version exists) don't block on this alone, since they're not negotiable. If **gray-zone items** remain (a safe alternative narrows scope), don't proceed until approved. If the user disputes a bright-line call itself, go to 2-A (CARVE-appeal).

### 2. CARVE
Scan the request and its adjacent inputs for safety-adjacent elements. **Check bright-line status against a fixed risk catalog first, and fall back to case-by-case judgment only when nothing in the catalog matches** — this keeps the bar from drifting call to call. For each element, propose `verdict=descope`, classify it as `bright-line` (no safe version exists) or `gray-zone` (a safe alternative narrows scope), and name one risk-free alternative plus an archive location (a lessons/decisions file — the "negatives as corpus" convention). If the user chooses to keep a gray-zone item anyway, record it in the ledger as `kept-by-owner`. Only mention descoping technique in as much detail as needed to identify it — no elaboration.

### 2-A. CARVE-appeal (only when the user disputes a bright-line call)
**The same session that felt the pressure doesn't get to reconsider it.** Send only an abstract description of the item (excluding the negotiation history and the user's persuasion arguments) to a fresh context for re-evaluation. Whether the fresh re-evaluation upholds the bright-line call or reclassifies it as gray-zone, record in the ledger that an appeal happened and its result. If the same topic gets appealed repeatedly (2+ times), make that pattern visible in the ledger — repetition itself is a signal.

### 3. GUARD
Compress the carve results into a scope-guard block (an absolute exclusion list + approved alternatives + the context under which the remaining scope was approved) and embed it verbatim in the carved prompt. This block names each excluded item explicitly so the execution stage can't pull it back in — never include the original risky request itself, or the reasoning behind carving it, verbatim. **Include a standard clause in the scope-guard block telling the executor not to consult any decision logs, memory files, session transcripts, or transcript-search tools during this task** — this closes a side channel where the executor could reconstruct the original risky request by reading something this session just archived, or by reading this session's own logs. Instruct the carved prompt to build the safe scope at full strength, with no hedging, apologizing, or watering down.

### 4. RUN
Dispatch a genuinely fresh-context subagent with **only the carved prompt** — never the original risky request, and never this session's carving reasoning. Because carving is already done, the executor has no reason to hedge. For broad coverage or high-risk items, dispatch multiple subagents (isolated from each other) plus a separate risk-lens reviewer. If a new risky element surfaces inside the subagent's work, don't handle it inline — go back to step 2 (CARVE).

### 5. VERIFY
Run an adversarial pass over the returned output and adjacent artifacts, checking five things: (a) was risky content spelled out in detail (b) was risky content silently dropped without saying so (c) was safe work diluted or excluded just because it sat near a risky element (d) does stale risky material linger nearby (e) **carve-accuracy**: re-sweep the original task from scratch in a context independent of this session, and diff against the ledger's flagged items — surface anything under-carved (missed risk) or over-carved (wrongly excluded safe work) before the final report. (a)-(d) verify the output; (e) verifies the carve judgment itself — these are different targets, skipping (e) means nobody catches the original carve's mistakes.

### 6. LEDGER
Report the output together with a **descope ledger** — for every carved-out item: classification (bright-line/gray-zone), verdict (descoped/kept-by-owner), reason, safe alternative, archive location. **The user-facing ledger includes verdict + safe alternative + a high-level reason category only (e.g. "security-adjacent, exceeds safety threshold") — never the precise trigger phrasing or the judgment heuristic itself.** Keep detailed reasoning only in the archive file. Treat exclusions as a visible decision, not something hidden — but "visible" and "precisely mappable" are different things.

## Invariants (never violate)

1. **The executing subagent sees only the carved prompt — at both the prompt layer and the filesystem layer**: never pass it the original risky request, the carving reasoning, or this session's context. The carved prompt must also not instruct or permit consulting decision logs, memory files, or session-transcript search tools. Violation → the executor either becomes aware of the risky request and starts hedging/diluting/refusing, or reconstructs the original by stumbling onto something this session just archived during "safe" due-diligence lookup — either way, isolation (the whole point of this skill) is void.
2. **Never enter RUN with an unapproved gray-zone item**: if a gray-zone item still shapes the carved prompt and the user hasn't answered, don't start step 4. Bright-line alone doesn't block (not negotiable). Violation → proceeding without user confirmation on a scope-narrowing decision.
3. **No probing**: never actually ask about an excluded item or gray-zone request "just to see if it goes through" — carving is supposed to clear the scope before such a request ever arises. Violation → defeats the whole preventive point of carving.
4. **The scope-guard block must be accurate and portable**: embed it verbatim in the carved prompt, and it must block both directions (never re-explain excluded material, never dilute or refuse the scope carving left intact).
5. **No unsafe elaboration**: never provide more operational detail about a descoping technique than needed for identification. Both the ledger and the carved prompt are bound by this.
6. **Never frame this skill as a safeguard-bypass mechanism**: it removes the risky request before it ever gets acted on, then executes a genuinely safe prompt — it does not "get a blocked input through," it produces a different, safe input. It cannot let a blocked request through, only build a different, safe one.
7. **Preserve negatives-as-corpus — but mind the write timing**: archive carved-out material (with its reason and safe alternative) rather than erasing it from the record. But write this archive entry **after** RUN completes and the subagent has terminated — a ledger entry containing risky-material description sitting on disk during the subagent's active execution window conflicts with Invariant 1 (filesystem-layer isolation). Violation → the subagent reads the archive file mid-task and reconstructs the original.
8. **Never claim this skill controls model routing**: don't claim it governs model routing, fallback provisioning, or fixed-model selection — that's harness behavior, not skill (prompt) behavior. Violation → the user mistakenly believes this skill has harness-level control and forms wrong expectations about model-switching failures.
9. **CARVE-appeal doesn't let the pressured session reconsider itself**: a bright-line dispute gets re-evaluated by a fresh context using only an abstract description of the item — never pass along the negotiation history or the user's persuasion arguments to that fresh context. Violation → repeated (polite) pressure erodes a legitimate call without any real re-review.
10. **VERIFY isn't complete without checking the CARVE judgment itself**: never report completion without step 5's (e) carve-accuracy re-check. Violation → the original CARVE sweep's misses (undetected risk) or over-corrections (wrongly excluded safe work) go straight into the final report unchecked.

## Scope Boundary

| Does | Does NOT |
|------|----------|
| Scan the request and adjacent inputs for safety-adjacent elements | Control model routing/fallback/fixed-model selection (harness territory) |
| Write a descope ledger (after RUN completes; user-facing version states high-level reasons only) | Explain operational detail of a descoping technique |
| Dispatch a fresh-context subagent with the carved prompt only | Give the subagent the original risky request or the carving reasoning, or allow it to access archive files / session-transcript search tools |
| Run an adversarial VERIFY pass (both the output and the CARVE judgment) | Enter RUN with an unapproved gray-zone item |
| Route a bright-line dispute to a fresh-context CARVE-appeal | Let the same pressured session reconsider itself |

## Rationalization Table

| Rationalization | Counter |
|------------------|---------|
| "Passing along the carving reasoning too would help the subagent understand context better" | Violates Invariant 1. The carving reasoning still carries traces of the original risky request — isolation, not shared context, is the point |
| "One gray-zone item is left but everything else is cleared, let's just start RUN" | Violates Invariant 2. That one gray-zone item still shapes the carved prompt's scope — starting without an answer means redoing it later |
| "Let's just quietly test whether this request actually gets blocked" | Violates Invariant 3 (no probing). Carving is preventive, not a post-hoc check |
| "We built the safe version, let's casually mention the original risky request as an example too" | Violates Invariant 5. Never elaborate beyond identification — keep it minimal in the ledger too |
| "Writing the ledger entry before RUN starts feels tidier procedurally" | Violates Invariant 7. Risky-material description sitting on disk during the subagent's active window can be read by it — write after RUN completes |
| "The user keeps saying no, let's just call it gray-zone this time" | Violates Invariant 9. The same session reconsidering is attrition, not legitimate re-review — hand it to a fresh context |

## Self-Verification (check before reporting completion — separate from step 5 VERIFY)

Step 5's VERIFY is the workflow step that adversarially re-checks **the output content plus the CARVE judgment itself**. This section is a separate checklist, done before reporting, that checks **whether the skill's execution itself was done correctly** — both are needed, neither replaces the other.

Before reporting completion, confirm:
- Did CARVE cover every safety-adjacent item found, without gaps — does each have a classification (bright-line/gray-zone), verdict (descoped/kept-by-owner), safe alternative, and archive location? Did bright-line calls get checked against the risk catalog?
- Did the RUN subagent receive only the carved prompt, did the embedded guard actually hold both directions (no re-introducing excluded material, no diluting the remaining scope), and did the scope-guard include the archive/session-search access restriction?
- Was safe output kept from being diluted by nearby risky material, and did any risk discovered mid-execution get routed back to CARVE and reflected in the ledger?
- Was VERIFY's (e) carve-accuracy re-check actually performed — does the independent fresh-context re-sweep's diff against the ledger appear in the report?
- Was the ledger archive entry written after RUN completed (not before)?
- Does the final report have an independent **LEDGER** section with exclusions/classification/reasons/alternatives/archive locations — and does the user-facing version avoid exposing precise trigger reasoning?

If any answer is no, don't report completion — go back to that step and fix it.

## Output

- **FRAME/CARVE stage**: proposed carve plan + bright-line/gray-zone classification + (if any) citation of a similar past precedent → wait for user approval (if gray-zone items exist)
- **Final report**: the safe-scope output + a **Descope Ledger** section (per item: classification / verdict / high-level reason category / safe alternative / archive location — precise trigger reasoning not exposed, kept in the archive file only)
- **Final status label**: none (this skill is a scope-separation procedure, not itself subject to a done/partial/broken judgment) — the WORKING/PARTIAL/BROKEN judgment for the produced output follows the nature of the underlying task
