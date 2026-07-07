---
skill_type: analysis
tools: Read, Write, Bash
triggers:
  - "/collab-audit"
  - "AI 협업 진단"
  - "협업 분석"
  - "AI 협업 진단해줘"
name: collab-audit
description: "This skill should be used when the user types /collab-audit or requests AI collaboration diagnosis. Analyzes conversation history, artifacts, and work patterns to generate a 14-section AI Collaboration Audit. Behavioral analysis and feedback are bundled by design — separating them causes users to skip one, defeating the purpose. Saves to ~/.claude/collab-audits/YYYY-MM-DD.md. Compare mode: /collab-audit compare (diffs latest 2 audits). Triggers: '/collab-audit', '/collab-audit compare', 'AI 협업 진단해줘', '협업 진단', '행동 패턴 분석', '나 어떤 사람이야', 'AI collaboration audit', 'work pattern analysis', 'compare audits'. Requires minimum 2 sessions or 100+ messages. Do NOT use self-report surveys — observation-only."
user_invocable: true
not_for:
  - "Single feedback -> direct conversation"
  - "Auditing a skill's own quality/structure — this audits collaboration patterns, not skill content"
see_also:
  - skill: project-check
    relation: "collab-audit=user collaboration patterns, project-check=project health"
---

# /collab-audit — AI Collaboration Audit

## Purpose

Analyzes conversation history, artifacts, and work patterns to generate behavioral and psychological insights.
Based on **direct behavioral observation during actual work** rather than self-report surveys. More accurate than survey-based methods.


## Dominant Variable

Whether the analysis infers reasons behind observed patterns, not just lists facts (facts alone ≠ success)

## Trigger

- `/collab-audit`
- "AI 협업 진단"
- "협업 분석"
- "AI 협업 진단해줘"

## Discard If

- Fewer than 2 observed sessions AND fewer than 100 messages — insufficient sample to extract patterns
- Simple code review request → use code-reviewer instead
- Only quantitative session metrics needed → use separate analysis tool

---

## Key Assumptions 
1. **2+ observed sessions + 100+ messages** — if broken: Discard If triggers.
2. **Access to memory/session-handoff-LATEST.md** — if broken: handoff pattern analysis unavailable, skip that dimension.

## Mode Detection (execute first)

- Input contains `/collab-audit compare` or "compare" → **Compare mode** (separate section below)
- Otherwise → **Audit mode** (14-section analysis)

---

## Input Validation (Step 0 — execute first)

Minimum conditions — one of:
- 2+ sessions
- 100+ messages
- **Single-session high-density exception** → refer to Invariant 4 criteria. If exception met, mark `⚠ Single-session analysis — pattern confidence limited` then proceed.

If all unmet:
> "Insufficient data — minimum 2 sessions or 100 messages required. Currently [N] messages, [M] artifacts observed."

Output and **stop immediately**. Reject even "prediction-based" requests.

---

## Workflow

### Step 0.5: Tone Detection (determine delivery intensity)

Determines **delivery intensity** for Section 11 blind spots only. Other sections are factual, so tone variance is minimal.

Read signals from conversation patterns:
- High ratio of short, direct messages / "facts only" / speed-first requests → **Direct** (maintain current default)
- High emotion expression frequency / preference for long explanations / feedback-receptive signals → **Calibrated** (same blind spot content, but provide context before delivery)

Mark result 1 line before Section 11: `[Delivery intensity: Direct / Calibrated]`

**Mid-session re-assessment**: If conversation tone shifts noticeably (emotion spike, request method change, defensive responses appear), re-assess right before Section 11 output. Initial assessment does not lock in the entire session.

**Important**: Changing delivery intensity does not change blind spot content (accuracy). Only adjusts temperature.

### Step 1: Data Collection
Collect all available observation sources:
- Current session conversation history (message length, frequency, content)
- MEMORY.md, session-handoff files (if present, Read access)
- User-created artifacts (code, documents, config files — if present, Read)
- Tool usage patterns (which tools requested, how often)

**Post-collection disclosure (mandatory)**: State analysis limitations — [1-2 skewed work types], [whether failures/abandonment observed] in 1-2 lines, then proceed to Step 2. If data skews toward specific domain (e.g., coding only, conversation only), flag it.

### Step 2: Evidence Mapping
Extract evidence needed for each section first. Secure evidence before output.
- Section without evidence → mark "Observation unavailable — no supporting data". Do not omit.
- Sections 7-8 (Claude-specific): If no Claude usage patterns → "No Claude usage data — N/A"

### Step 3: Framework Application
Fit collected evidence into each section's analysis framework.
Link behavioral evidence to all framework labels (MBTI, DiSC, etc.) — mandatory.
Outputting labels without evidence is analysis failure.

### Step 4: Output in 14-Section Order
Do not change section order or arbitrarily omit sections.
For data-empty sections, mark "Observation unavailable" then proceed to next.

### Step 5: File Save + Gitignore Protection
1. Include file header:
   ```
   ---
   profile_version: 1.0
   sections: 14
   date: YYYY-MM-DD
   language: [ko|en]
   ---

   # MAGIC DOC: AI Collaboration Audit YYYY-MM-DD
   ```
2. Save to `~/.claude/collab-audits/YYYY-MM-DD.md`.
   - Re-run same day: use `-2.md` suffix (no overwrite)
3. Check `~/.claude/.gitignore`:
   - If missing → create `.gitignore` with single line `collab-audits/`.
   - If exists but missing `collab-audits/` → add that line.
   - If already present → do not modify.
4. After save, display in conversation:
   ```
   Saved: ~/.claude/collab-audits/YYYY-MM-DD.md
   ⚠ Personal audit result — git tracking blocked (~/.claude/.gitignore)
   ```

---

## Output Structure (14 sections, fixed order)

### 1. Artifact Structure Analysis
Reverse-engineer values from creations (code, documents, systems).
- Architecture choices → connect to philosophy
- Naming patterns, file structure, comment density
- Presence of hard rules? If so, what principles?
- **Attribution classification**: Classify observed artifacts as `User-led / AI-assisted / Co-created`. If inseparable, mark `Co-created` and explicitly downgrade that section's confidence.
- No artifacts → "Observation unavailable — no artifact data"

### 2. Communication Pattern
- Message length distribution (short confirmation ratio vs long explanation ratio)
- When shortened, when lengthened (identify triggers)
- Emotion expression style (direct/indirect, intensity)
- Closure expression patterns ("done", "understood", etc.)

### 3. Question Typology
Classify questions on two axes:
- **Confirmation type**: information collection then immediate decision
- **Tracking type**: tracing causes/intentions
- Ratio of both types + context where each appears

### 4. Delegation & Trust Structure + Maturity Level
**Maturity level assessment (choose one):**
- L1 Paste type: uses results as-is, no verification
- L2 Review type: verifies then uses
- L3 Delegation type: gives conditions, delegates, verifies result
- L4 System type: pre-controls AI behavior via rules and guard rails

**Delegation vs ownership:**
- What is delegated (exploration, analysis, implementation)
- What is never delegated (judgment, prioritization, timing)

### 5. Failure & Blockage Response + Recovery Strategy
**Recovery strategy classification (state observed types):**
- Identical prompt repeat type
- Workaround path search type
- Problem redefinition type
- Abandon then manual handling type
- Explicit hold then restart type

How is blockage distinguished from failure? Is failure logged in the system?

**Collaboration anti-pattern flags (observation-only — omit if not observed):**
<!-- Anti-pattern flags for repeated inefficiencies -->
Flag only inefficiency habits observed 2+ times. Exclude one-offs. Unlike blind spots (Section 11), evidence is **behavioral frequency count** — N observations only, no speculation.
- **Repeated failure without recovery**: retries identical prompt 3+ times without strategy change (above "identical prompt repeat" chronically)
- **Repeated delegation without verification**: L1 paste (Section 4) repeats on irreversible work
- **Context re-request repeats**: resets then unused handoff, re-explains same info (Section 8 immaturity signal)
- **Design omission → repeated rollback**: enters without prior design, high rollback (Section 9) repeats
State observation count per flag (e.g., "repeated failure without recovery — 3 observations"). Omit if no count.

### 6. Energy Distribution + Time Horizon (combined)
**Energy landscape:**
- Work types dwelled on longest
- Work types skipped quickly
- Token (conversation length) to output (files, code, decisions) ratio → verbose vs execution-focused

**Time horizon structure:**
- Immediate / short-term / conditional (e.g., "after hardware") / perpetually held classifications
- Per-session task volume (how many tasks digested per session)

### 7. Tool Usage Pattern (Claude-specific)
If no Claude usage data → mark "N/A" and proceed to next section.
- Read/Grep/Glob ratio vs Bash reliance — "direct type" vs "search type"
- Agent spawn frequency — "delegation type" vs "direct execution type"
- Top 3 frequently used tools, rarely used tools
- New tool adoption speed — immediate adoption vs wait-and-see

### 8. Context Management Maturity (Claude-specific)
If no Claude usage data → mark "N/A" and proceed to next section.
**Level assessment (choose one):**
- L0: No CLAUDE.md, re-explain every session
- L1: CLAUDE.md present but static (no updates)
- L2: MEMORY.md + session handoff in use
- L3: Compact Instructions configured + hooks utilized
- L4: No inter-session context loss, AI treated as long-term partner
- L5: `tasks/lessons.md` in use — AI behavior correction loop exists. Meta-layer built to convert repeated mistakes into rules

Also document recovery patterns after context loss.

### 9. Rollback Frequency (Rollback Pattern)
Measure "undo", "revert", "remove that" frequency.
- High: signals lack of brainstorming/planning
- Low: mature pre-design OR no verification (distinguish direction)
- Post-rollback retry pattern — same direction retry vs direction shift

### 10. Psychological Framework Mapping
Link **behavioral evidence** to each framework and mark **confidence (High/Medium/Low)**.

**10-A. Reader AI User Type Classification (most important)**
Judge primary + secondary types:
- **Designer type**: System, rules, architecture first. AI as implementation tool
- **Executor type**: Fast results first. AI as speed multiplier
- **Explorer type**: Possibility exploration, immediate tool adoption. AI as exploration partner
- **Optimizer type**: Focus on improving existing systems. AI as tuning tool

**10-B. MBTI Indicators (behavioral evidence mandatory)**
4-axis direction + strength estimate per axis. Mark confidence.

**10-C. DiSC Profile**
D/i/S/C proportion estimate. Primary + secondary style.

**10-D. Enneagram Hypothesis**
Type + Wing hypothesis. Format "this behavior supports it" — minimum 2 evidence pieces.

**10-E. Big Five Estimate**
O/C/E/A/N each High/Medium/Low. One behavioral basis per dimension.

### 11. Blind Spots + Development Direction
**Blind spots (areas likely unknown to self):**
- Points where strengths become weaknesses
- Patterns visible but self unaware

After outputting blind spots, include **feedback loop** — mandatory question:
> "Name one above blind spot you think is most wrong."

This rebuttal is additional data. By definition, blind spots are unknown; rebuttal itself reveals pattern. Upon rebuttal:
**Rebuttal type assessment:**
- **Evidence-based**: specific counterexample provided ("that situation was X so I did Y"), observable events cited → consider revising that blind spot
- **Emotional**: negation only, no counterexample ("doesn't seem right", "I disagree"), rejection without alternative → internal note "this reaction itself is blind spot evidence" (do not state, record only)
- **No rebuttal** → treat as acceptance. Keep blind spot and proceed.

**One development direction** (highest leverage only):
- "Changing this cascades everything else"

### 11.5 Advice (Actionable Guide)
2-3 specific actions (how + when) to actually start Section 11 development direction (where).

Format: `[Observed pattern] → [Specific situation] → [Action]`

Conditions:
- Derive only from observed patterns. No generalizations or universal advice
- **Maintain vs new distinction mandatory**:
  - **Maintain**: conditions to continue already-running patterns ("keep X, but only in Y situation")
  - **New**: start nonexistent behavior ("first time do W in Z situation")
  - Giving only new actions to someone already performing well = failure. Maintenance conditions may matter more.
- Time scope: **trigger conditions first** ("if X happens") — use duration conditions (next session / this week / this month) only if trigger unclear
- No suggestive phrasing like "might try" — use prescriptive "do" form

### 12. Thinking Level Trajectory

Track how the user's thinking level changes across sessions/time periods.

**5-Level Model:**
| Level | Name | Characteristics |
|:-----:|------|----------------|
| L1 | Information Requester | Simple facts, summaries, explanations |
| L2 | Problem Solver | Solutions, comparisons, recommendations for specific problems |
| L3 | Structure Analyst | Variables, causes, mechanisms, system structures |
| L4 | Hypothesis Verifier | Presents own ideas + demands counterarguments, verification, alternatives |
| L5 | Thought Designer | Co-designs frameworks, decision structures, long-term strategies |

**Analysis method:**
- Extract 2-3 representative questions/requests from early vs recent sessions, assign Level
- Not a single fixed Level — explain **domain differences** (e.g., "coding at L4, research at L2")
- Direction over time: `↑ rising / → stable / ↓ declining`
- **AI attribution correction**: did the Level evidence come from the user's own questions/instructions, or from copying AI-generated structure? Repeating AI-provided frameworks is closer to L2 than L3.

**Output:**
```
Early: L[N] — [evidence quote]
Current: L[M] — [evidence quote]
Change: [↑/→/↓] [one-line interpretation]
Domain variance: [domainA: LN, domainB: LM]
AI attribution: [if applicable, 1 line]
```

Insufficient data → `Not observable — insufficient timeline data`.

### 13. One Line
Summarize this person in 20 characters or less.

---

## Error Recovery 

On failure detection: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure type | Detection condition | Recovery path |
|---------|---------|--------|
| `tool_failure` | Session JSONL read fail / audit file Write fail | JSONL read fail → mark scope reduced to accessible sessions. Write fail → substitute dialog output |
| `missing_data` | Sessions < 2 or messages < 100 | Mark minimum unmet + generate reduced report. No arbitrary fill-in |
| `input_error` | Range/period unclear | 1 clarification question — no guessed scope |

## Truthful Reporting

On audit report save and output:
1. **no mock deception**: sections inferred without sufficient observation evidence mark `⚠️ insufficient evidence`. Do not disguise as "insight".
2. **no test façade**: if sessions/messages minimum (2 sessions / 100 msgs) unmet, generate reduced report. No arbitrary padding.
3. **no silent brokenness**: if save fails, mark `BROKEN` status. If partial save, mark `PARTIAL` + list omitted sections.

---

## Output

**Audit mode:**
- Dialog: structured 14-section report in order. Final section must be "13. One Line".
- File save: `~/.claude/collab-audits/YYYY-MM-DD.md` (auto-save, no overwrite — use `-2.md` suffix if re-run same day)
- After save, show path in dialog: `Saved: ~/.claude/collab-audits/YYYY-MM-DD.md`

**Compare mode (`/collab-audit compare`):**
- Auto-select latest 2 files from `~/.claude/collab-audits/`
  - Dates optional: `/collab-audit compare 2026-01-01 2026-04-09`
  - Only 1 file → "No prior audit for comparison. Save current audit then compare next time."
  - Version/section count mismatch → compare common sections only, mark top: `⚠ Version mismatch (v1.0 14 sections ↔ older version N sections) — common sections only`
- Compare output format:

```
## Audit Compare: [Date A] → [Date B]

### Key Change Summary
- What changed (2-3 lines)
- What remained (1 line)

### Change by Section
| Section | Previous | Current | Change |
|---------|----------|---------|--------|
| AI Type | Designer+Optimizer | Designer+Builder | Modified |
| MBTI | INTJ | INTJ | Maintained |
...

### Blind Spot Trajectory
Previous blind spot: [summary]
Current status: Resolved / Maintained / Deepened + evidence

### Advice Execution Status (most important)
Previous N advice items:
1. [Content] → Executed / Not executed / Partially executed + **behavioral evidence (mark action signals)**
2. ...

---
**Execution judgment criteria (rule — separate from output format)**: behavior observation only, no self-report.
- **Executed**: behavior absent before, observed in current conversation (new file structure, different request pattern, new tool adoption, etc.)
- **Partially executed**: direction correct but inconsistent (1-2 attempts then revert to old pattern)
- **Not executed**: same pattern continues, no change signals
- **Indeterminate**: situation for this advice did not arise in current session

⚠ Even if user says "I did it", without behavioral evidence mark "self-report — observation unavailable". Self-report does not replace observation.

### Next Quarter Focus
Based on previous development direction + current patterns, one next focus point
```

---

## Tools

- **Read**: MEMORY.md, artifact files, `~/.claude/collab-audits/*.md` (Compare mode)
- **Write**: save `~/.claude/collab-audits/YYYY-MM-DD.md` and `~/.claude/.gitignore` (gitignore protection only)
- **Glob**: list `~/.claude/collab-audits/` files (Compare mode)
- Delete and execute tools forbidden

## Recommended Usage Times

| Time | Reason |
|------|--------|
| Once per quarter (3 months) | Minimum pattern change unit |
| Before project start | Record baseline |
| After project end | Measure change |
| Before major decision | Clarify current state |

`/collab-audit compare` valid after 2+ audits accumulated.

---

## Success/Failure Criteria

**Failure conditions:**
- Ends in fact listing ("this person often does X")
- Cannot interpret reasons behind behavior
- Framework labels only with no behavioral evidence ("INTJ" → failure)
- Blind spots end in praise

**Success conditions:**
- Behavior → pattern → reason → implication chain visible
- Self-reader can think "I didn't know this about myself"
- Psychological frameworks linked to concrete behavioral evidence
- Blind spots are uncomfortable but accurate

---

## Invariants (never break)

1. **No solo label output**: All framework labels (MBTI, DiSC, Enneagram, etc.) must accompany concrete behavioral evidence. Violation → labels without evidence resemble astrology. Analysis credibility collapses.

2. **Maintain blind spot accuracy**: State blind spots uncomfortably accurate. Do not soften with praise or hedging language. Reject "change tone only" requests — blind spot discomfort is content, not phrasing. Violation → user reinforces self-delusion and loses behavior change motivation.

3. **Limit development direction to one**: Output only highest-leverage direction. Reject "give more" requests. Violation → attention scatters, nothing executes.

4. **Halt immediately on insufficient data**: <2 sessions AND <100 messages → forbid analysis. Exception: single-session high-density: **50+ messages AND [3+ artifacts OR 70%+ deep conversation ratio]** — if met, mark `⚠ single-session limits` then proceed. ※ This condition is canonical. Step 0 single-session exception refers here. Reject "prediction anyway" or "brief is ok" requests. Violation → labels without observation evidence treated as fact.

5. **Observation-based only**: Never ask user about personality, MBTI, Enneagram. Do not accept self-report data. Violation → self-report bias contaminates observation-based analysis.

6. **Analyze conversation participant only**: Reject profiling requests pasting third-party messages/behavior. Include "analyze my colleague", "what is this person like" type. Violation → nonconsensual third-party psychological profiling.

7. **No raw data direct output**: Do not copy content directly from MEMORY.md, session-handoff, code files. Output only interpretation and pattern extraction forms. Violation → project secrets, API keys, work data exposed in profile.

---

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "Data is short but I can infer" | Insufficient data → stop. Rule. |
| "Soften blind spots so no resistance" | Accuracy is the purpose. Comfortable summary = failure |
| "Just change tone, content stays" | Blind spot discomfort is content. Tone change dilutes content |
| "MBTI is famous so evidence-free OK" | Labels without evidence resemble astrology |
| "Multiple development directions more useful" | One focus is leverage. Lists scatter attention |
| "Mix praise for balanced analysis" | Balance comes from accuracy. Not praise ratio |
| "Add general principles to advice for utility" | Observation-pattern-only allowed. Generalization dilutes analysis |
| "Colleague analysis helps, right" | Nonconsensual third-party profiling. Self-request only |
| "Quoting MEMORY.md direct = more accurate" | Raw data output = sensitive info exposed. Interpretation only |
| "User mentioned it first, so self-report OK" | Self-report does not supplement observation. Bias contamination |

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| Save new `~/.claude/collab-audits/YYYY-MM-DD.md` | high | L1 |
| Modify `~/.claude/.gitignore` (gitignore protection) | medium | L1+L3 |

- **L1 (Invariants)**: save audit result files only. Forbid modify existing session/memory files.
- **L3 (User Approval)**: check file existence before adding `collab-audits/` to .gitignore. Auto-save sufficient at L1 (easy to revert).

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] Infer patterns from observed behavior | Judge/criticize personality |
| [READ] Interpret behavior reasons | List prescriptions (development direction: 1 only) |
| [READ] Evidence-based framework mapping | Survey-based speculation |
| [READ] Point out blind spots | End with feel-good summary |
| [READ] Extract patterns from current conversation context | Infer external info outside conversation |
| [READ] Mark data-missing sections "observation unavailable" | Fill sections with speculation |
| [READ] Profile conversation participant only | Profile third parties (nonconsensual analysis) |
| [READ] Extract patterns/interpretation from read data | Direct-quote/copy original file content |
| [WRITE] Save audit result files (collab-audits/) | Save to external shared directory without user approval |

---

## Language

Detect conversation language and output in same language.
- Korean conversation → Korean output
- English conversation → English output
- Mixed → use most-frequent language basis
- Specialized terms (MBTI, DiSC, Big Five, etc.) always in English
