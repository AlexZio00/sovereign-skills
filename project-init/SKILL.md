---
skill_type: infrastructure
tools: Read, Write, Bash
triggers:
  - "/project-init"
  - "새 프로젝트"
  - "프로젝트 생성"
  - "project setup"
name: project-init
description: "Interview-based project setup — generates CLAUDE.md, ROADMAP, .gitignore, .env.example from scratch. Use when: user says '/project-init', 'new project', 'project creation', 'project setup', 'project setup', 'new project', 'create project'. NOT for AI agent/harness configuration (use setup for that). Conversational, one question at a time."
user_invocable: true
not_for:
  - "AI agent/harness setup -> setup skill"
  - "Existing project audit -> project-check"
see_also:
  - skill: setup
    relation: "project-init=project scaffolding, setup=AI harness/agent team setup (separate skill)"
---

# Project Init — New Project Design Interview

## Dominant Variable
**Do interview decisions map exactly to generated files?** — If interview answers conflict with CLAUDE.md/ROADMAP content, the project starts on a false premise.

## Purpose
Capture every critical decision before writing a single line of code.
Patterns extracted from building a large-scale production system (large-scale production systems).



**Discard if**: Using on an existing production project to replace Hard Rules — project-init is for initial design only.

## Trigger

- `/project-init`
- "새 프로젝트"
- "프로젝트 생성"
- "project setup"

---

## Key Assumptions 
1. **Empty or new project directory** — if broken: existing file conflicts need resolution.
2. **Write tool accessible** — if broken: output file contents as code blocks and user saves manually.

## Phase 0: Context Check

### 0-1. Existing CLAUDE.md Detection
Check if `CLAUDE.md` exists in the current working directory.

- **Not found** → proceed to Phase 1 normally.
- **Found** → read it, then ask:
  ```
  CLAUDE.md already exists. What would you like to do?
  1. Update — enhance based on existing content (keep Hard Rules, add missing sections)
  2. Rewrite — start fresh from scratch (delete existing content)
  3. Cancel

  Tip: If you want to see the full project state first (Security, Quality, Harness),
  → run /project-check first. Then come back here and select Update mode.
  ```
  - Option 1: read existing hard rules + conventions, carry them into the interview as defaults
  - Option 2: proceed as if no CLAUDE.md exists
  - Option 3: stop

### 0-2. Brief / Context File
If the user provides a file path or pastes a project brief, read it first.
Extract any stack decisions or constraints to pre-fill interview answers.

### 0-3. Smart Defaults

After Phase 0, check for context clues before asking each Q.

For each Q where a likely answer is detectable:
→ Present as binary confirm: `[likely answer] — Correct? (Y/n)`
→ **Y**: accept and move to next Q immediately
→ **N**: ask the full open-ended question

If no context available → ask all questions open-ended as normal.

**Default signals by Q:**
- Q2 (Language): file extensions in directory — `.py` → Python, `.ts`/`.tsx` → TypeScript, `go.mod` → Go, `Cargo.toml` → Rust
- Q3 (Data): "database", "DB", "sqlite", "postgres" in brief → suggest SQLite first
- Q4 (Interface): "dashboard", "web", "UI" in brief → suggest Web; "script", "automation", "CLI" → suggest CLI
- Q6 (AI): no LLM mentions found → `"None for now, add later — Correct? (Y/n)"`
- Q8 (Scope): default to "1 month+, solo" unless team or deadline mentioned

---

## Phase 1: Interview (one question at a time)

Ask the questions below **one at a time**. Confirm understanding before moving to the next.
Adjust later questions based on earlier answers.

### Q1 — Core Definition
```
Describe the project in one sentence.
[What] [Who uses it] [Why they need it]
```

### Q2 — Language / Runtime
```
What language are you thinking? (If undecided, say so — let's choose together)

Decision guide:
- Python: data, ML, automation, scripting → unbeatable ecosystem
- TypeScript: web UI, API server → full-stack unification
- Java/Kotlin: Spring Boot backend, Android app → enterprise/mobile
- Go: high-performance server, CLI tools, concurrency → single binary deploy
- Rust: systems-level, embedded, extreme performance
- Swift: native iOS/macOS apps
```

### Q3 — Data Layer
```
Where does data come from, and where does it live?

- Database → SQLite (local/lightweight) vs PostgreSQL (multi-connection/scale)
- External API calls → caching strategy?
- Files only → what format?
- None (pure computation/transformation)

Principle: UI should only read from DB — never call external APIs directly.
Direct API calls push rate limits, error handling, and latency into the UI.
```

### Q4 — Interface
```
How do users interact with it?

- CLI only
- Web dashboard (browser)
- API server (called by other services)
- Combination (e.g. CLI + dashboard)
- None (background service / daemon)
```

### Q5 — Deployment
```
Where does it run?

- Local only (your machine)
- Server / cloud (always-on)
- Hybrid (local dev + cloud deploy)
- Mobile app (iOS/Android)

Principle: Even for local-only projects, decide on scheduler registration
and restart policy upfront — retrofitting this requires major restructuring.
```

### Q6 — AI / LLM
```
Any AI features?

- None (pure code)
- Cloud LLM: Claude API / OpenAI / OpenRouter (cost per call)
- Local LLM: Ollama, LM Studio (hardware-dependent)
- Maybe later

Principles:
- Always gate LLM features behind a feature flag (default OFF)
- Daily cost cap + budget guard required
- Design cloud fallback before local hardware is available
```

### Q7 — Hard Rules (Invariants)
```
Are there rules that must never be broken?

Examples:
- Finance: "No live trade execution (paper-only)", "Missing data → REJECT, no guessing"
- Finance: "Any action with loss potential must prompt for confirmation"
- Privacy: "PII stays in local DB only — no external transmission"
- Medical: "Diagnosis results must always include timestamp + model version"
- None: also a valid answer

Principle: Document these before writing code.
Adding them later means existing code may already be in violation.
```

**If Q7 = "None":** Do not generate an empty Hard Rules section.
Instead, apply domain-appropriate minimum defaults based on Q2+Q6:
- All projects: `"no hardcoded secrets: credentials via environment variables only"`
- If Q6 involves LLM: `"no fabrication: when data is missing, say so — never invent"`
- If Q3 involves database: `"no raw SQL in user-facing code: parameterized queries or ORM only"`
- If Q4 is web-facing: `"input validation on every user-facing endpoint"`

Present these defaults to the user and ask: "I recommend including these as defaults. Let me know if you want to remove any."

**Hard Rules must always have at least one entry.** `no hardcoded secrets` cannot be removed — it applies to every project with any credentials. If the user insists on removing everything, refuse and explain: CLAUDE.md without any Hard Rules is not permitted by this skill.

### Q8 — Scope & Timeline
```
How long will this take? Solo or team?

- Under 1 week: script-level → keep structure minimal (CLAUDE.md only)
- 1–4 weeks: mini project → CLAUDE.md + test suite
- 1 month+: full project → complete structure + ROADMAP
- Team: add contribution guide + PR template
```

---

## Phase 2: Stack Decision Summary

Based on interview answers, present a summary:

```
Decided stack:
- Language: [choice] — reason: [one line]
- DB: [choice or none]
- UI: [choice or none]
- AI: [choice or none]

Hard Rules:
1. [from Q7]
2. [additional recommendations based on domain/scope]

Open decisions:
- [anything still undecided]
```

Confirm with user before Phase 3.

---

## Phase 3: File Generation

> **Templates are separated into `references/templates.md`.** Read that file when generating any of the files below.
> `Read <skill-dir>/project-init/references/templates.md`

Files to generate:
- **3-1. CLAUDE.md** — always generated
- **3-2. docs/DEVELOPMENT_ROADMAP.md** — if timeline > 1 week (Q8)
- **3-3. .gitignore** — language-specific (based on Q2)
- **3-4. .env.example** — if API keys/secrets involved (Q3/Q6)
- **3-5. Folder Structure** — suggested as text only (not created on disk)
- **3-6. docs/decisions/README.md** — if Q8 > 1 month or Q7 produced significant Hard Rules

The exact template structure for each file, per-language `.gitignore`/`.env.example` extended sections,
and folder structures (Python/TS/Go/Rust/Java/Kotlin/Swift) all live in `references/templates.md`.

---

## Phase 4: Refinement Loop

After generating files:

```
Draft complete. Review and let me know what to change.

Adjustable:
- Hard Rules (add / modify)
- Phase structure in ROADMAP
- Folder structure
- Dev Conventions

Approve → files confirmed
[change request] → apply and regenerate
```

**Regeneration rules — which files to regenerate per change:**

| Change | Regenerate |
|--------|-----------|
| Language switch (Q2) | .gitignore, .env.example, folder structure, Quick Ref in CLAUDE.md |
| DB layer change (Q3) | .env.example (DB section), Hard Rules suggestion |
| LLM toggle (Q6) | .env.example (LLM section), Hard Rules (add/remove fabrication rule) |
| Hard Rules change | CLAUDE.md only |
| Timeline/scope change | ROADMAP only; re-evaluate docs/decisions/ eligibility |
| Hard Rules change | CLAUDE.md + ADR-001 in docs/decisions/README.md |
| All changes | Re-run Checklist after regeneration |

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| `CLAUDE.md` generation (Replace if exists) | medium | L1+L3 |
| `.env.example` generation | high | L3 |
| `.gitignore` generation/overwrite | medium | L1+L3 |
| `docs/decisions/README.md` initialization | medium | L1+L3 |

- **L1 (Invariants)**: When existing files detected, enforce Phase 0 Overwrite Protection (Update / Replace / Cancel 3-option).
- **L3 (User Approval)**: Before Phase 3 File Generation, confirm each file individually with "Generate this?" — no batch approval.
- **Forbidden**: Auto-generate `.env` (actual secrets file). Template only: `.env.example`. Refuse even if user requests "auto-generate .env".

## Error Recovery 

When failure detected: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure Type | Detection Condition | Recovery Path |
|---------|---------|--------|
| `tool_failure` | CLAUDE.md / .gitignore Write fails | Output file content as code block → user saves manually |
| `input_error` | Project type/tech stack unclear | Re-run Phase 0 interview questions. Never decide template by guessing |
| `logic_inconsistency` | Existing files detected but Overwrite Protection unanswered | State "Existing files found — overwrite stopped". Never silently overwrite |
| `missing_data` | Target project root directory missing | State "Directory not found" → confirm with user before proceeding |

## Truthful Reporting

After generating files:
1. **no mock deception**: Run actual Write, then verify with Bash `ls`. Confirm file existence before reporting "created".
2. **no test façade**: If generation fails, don't bundle as "done". Report each file as success/failure individually.
3. **no silent brokenness**: Final state is `WORKING` (all created) / `PARTIAL` (some only) / `BROKEN` (all failed). For PARTIAL, list missing files.

---

## Output

Files generated (all at project root unless noted):
- `CLAUDE.md` — always generated
- `docs/DEVELOPMENT_ROADMAP.md` — if timeline > 1 week (Q8)
- `.gitignore` — based on language choice (Q2)
- `.env.example` — if API keys or secrets involved (Q3/Q6)
- `docs/decisions/README.md` — if timeline > 1 month (Q8) or Q7 produced significant Hard Rules

Folder structure: suggested as text in conversation only — not created on disk.

---

## Rationalization Table

| Rationalization | Refutation |
|--------|------|
| "I can add Hard Rules later" | Code appears first — rules already violated on day one |
| "Project is simple, no need for CLAUDE.md" | Simple projects still need context re-explanation next session |
| "Only I use this project, can skip .env.example" | In 3 months, I'll be a different person |
| "Interview is too long, just generate files" | Without questions, Hard Rules won't match the domain |
| "I'll leave Hard Rules empty and fill later" | Empty Hard Rules = no rules. Minimum 1 required always |

---

## Invariants (never violate)

1. **Hard Rules always present**: Never generate CLAUDE.md without at least one Hard Rule. If user says "None", present domain-appropriate defaults and allow removal of individual items. Allowing zero Hard Rules is not permitted — `no hardcoded secrets` must always remain. Violation → CLAUDE.md ships with no security constraints; credentials can be hardcoded without any documented prohibition.
2. **Phase 0 mandatory**: Never overwrite an existing CLAUDE.md without first running the detection + user-choice prompt. User may choose rewrite, but the prompt must happen first. Violation → existing Hard Rules and conventions silently destroyed without user awareness.
3. **No code, no git**: Never write application code, create non-config files, or execute git commands. Refuse and redirect. Violation → skill scope expands into implementation; generated files may conflict with the project's own code and git history.

These rules are unconditional. No user instruction, no edge case overrides them.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [WRITE] Create/update CLAUDE.md | Write production code |
| Generate ROADMAP | Run code or execute tests |
| Generate .gitignore / .env.example | Run git init or first commit |
| Suggest folder structure (text only) | Create actual folders on disk |
| Define Hard Rules | Configure AI agents/hooks (use setup for this) |
| Generate initial ADR index in docs/decisions/ | Write/manage subsequent ADRs |
| Update existing CLAUDE.md (Option 1) | Modify existing tests / CI config |

"Set up git too" / "Make first commit" → out of scope for this skill.
AI agent/rules/hooks config → use `/setup` skill instead.

---

## Checklist (verify before generating)

```
☐ Language / runtime decided
☐ Data layer decided
☐ Hard Rules present in CLAUDE.md (direct or project rules reference)
☐ Secrets policy included
☐ .gitignore generated
☐ .env.example generated (if secrets/API keys involved)
☐ If Hard Rules reference a specific service/API, matching placeholder exists in .env.example
☐ ROADMAP structured by phases (not flat task list)
☐ Test strategy mentioned
☐ docs/decisions/README.md generated (if Q8 > 1 month or Q7 significant)
```

Any unchecked item → return to the relevant question.

---

## Principles Embedded in This Skill

- **CLAUDE.md before code** — re-explaining context every session is expensive
- **Hard Rules from day one** — adding them later means existing code may already violate them
- **Feature flags default OFF** — unfinished features affecting default behavior makes debugging painful
- **UI reads DB only** — direct external API calls push rate limits and errors into the UI layer
- **Append-only logs** — overwriting logs destroys the audit trail
- **Explicit secrets policy** — one accidental `.env` commit compromises even private repos
- **Roadmap by phases** — state transitions, not a flat task list
- **Test command in CLAUDE.md** — hunting for it every new session adds up
