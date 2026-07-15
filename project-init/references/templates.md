# Project Init — File Generation Templates

> Referenced from `SKILL.md` Phase 3 (File Generation). Read this file when generating
> CLAUDE.md, ROADMAP, .gitignore, .env.example, ADR index, or suggesting a folder structure.

### 3-1. CLAUDE.md

Generate at project root using this structure:

```markdown
# [Project Name] v1.0

## Hard Rules (never bend)
{Conditional — check before generating:
  `.claude/rules/project-rules` exists →
    Hard Rules → see [.claude/rules/project-rules](.claude/rules/project-rules)
  Does NOT exist →
    - [each rule from Q7 + domain defaults, listed directly]
}

## Quick Ref
- Entry: [auto-filled from Q2: Python→`python {main}.py`, TS→`npx ts-node src/index.ts`, Go→`go run cmd/{app}/main.go`, Rust→`cargo run`, Java→`./gradlew bootRun`]
- Tests: [auto-filled from Q2: Python→`pytest tests/ -q`, TS→`npm test`, Go→`go test ./...`, Rust→`cargo test`, Java→`./gradlew test`]
- [additional references]

## Secrets Policy
- Never read, print, or log `.env` — use environment variables only.
- Never commit `.env` — `.env.example` is the template (no real values).
- New API keys → add placeholder to `.env.example` + load via env var.

## Dev Conventions
- Tests before merge. Never declare done without a passing test.
- New features: opt-in via env var, default OFF.
- Logs: append-only (never overwrite log/jsonl files).
- Commits: one logical change per commit — independently revertable.
- Commit only when explicitly requested.

## Compact Instructions
Preserve on compaction:
1. Hard Rules
2. Current active branch / uncommitted file list
3. Pending tasks and their status
4. Active errors or bugs being investigated
5. Dev Conventions
6. File paths modified in this session
```

### 3-2. docs/DEVELOPMENT_ROADMAP.md

```markdown
# [Project Name] — Development Roadmap

## Phase 1: Foundation (goal: core functionality working)
- [ ] 1-1. Project structure setup
- [ ] 1-2. DB schema / data layer
- [ ] 1-3. [Core feature #1]
- [ ] 1-4. Basic test suite

## Phase 2: Core Features
- [ ] 2-1. [Main feature]
- [ ] 2-2. [Main feature]

## Phase 3: Polish
- [ ] 3-1. Error handling hardening
- [ ] 3-2. Performance optimization
- [ ] 3-3. Documentation

## Backlog (unscheduled)
- [ ] [Future items]
```

### 3-3. .gitignore

Generate at project root based on language:

**Python:**
```gitignore
# Environment
.env
.env.local
venv/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd

# Outputs & artifacts
outputs/
*.log
*.jsonl

# IDE
.vscode/
.idea/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
```

**TypeScript / JavaScript:**
```gitignore
# Environment
.env
.env.local
.env.*.local

# Dependencies
node_modules/

# Build
.next/
dist/
build/
out/

# Logs
*.log
npm-debug.log*

# IDE
.vscode/
.idea/
```

**Go:**
```gitignore
.env
*.exe
*.exe~
*.test
*.out
vendor/
```

**Rust:**
```gitignore
.env
/target/
Cargo.lock   # remove this line if publishing a library
```

**Java / Kotlin:**
```gitignore
.env
.gradle/
build/
out/
*.class
*.jar
.idea/
*.iml
local.properties
```

**Swift:**
```gitignore
.env
.build/
*.xcworkspace/xcuserdata/
DerivedData/
*.ipa
*.dSYM.zip
```

---

### 3-4. .env.example

Generate based on what was decided in Q6 (AI/LLM) and Q3 (data layer):

```bash
# === API Keys ===
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
# OPENROUTER_API_KEY=

# === Database ===
# DATABASE_URL=sqlite:///app.db
# POSTGRES_URL=

# === Feature Flags (default OFF) ===
# LLM_ENABLED=0
# [FEATURE_NAME]_ENABLED=0

# === App Config ===
# LOG_LEVEL=INFO
# PORT=8000
```

Only include sections relevant to the project's decided stack.
Leave all values empty — this file is a template, never a config.

**Extended sections (conditional on Q3/Q6 answers):**
```bash
# === OAuth / Auth (if auth layer selected in Q3) ===
# OAUTH_CLIENT_ID=
# OAUTH_CLIENT_SECRET=
# JWT_SECRET=

# === External Services (if external APIs in Q6) ===
# STRIPE_API_KEY=
# SENDGRID_API_KEY=
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_REGION=

# === Monitoring (if production deployment planned) ===
# SENTRY_DSN=
# DATADOG_API_KEY=
```

**Security Baseline (always include):**
```bash
# === Security Notes ===
# 1. Copy this file to .env and fill real values
# 2. NEVER commit .env — only .env.example
# 3. Rotate keys if accidentally exposed
# 4. Use least-privilege scopes for all API keys
```

**Swift projects:** same structure — include only sections relevant to your app's API dependencies:

```bash
# === API Keys ===
# API_KEY=

# === Feature Flags (default OFF) ===
# FEATURE_NAME_ENABLED=0

# === App Config ===
# BASE_URL=https://api.example.com
```

---

### 3-6. docs/decisions/README.md _(optional)_

Generate if Q8 timeline > 1 month OR if Q7 produced significant Hard Rules:

```markdown
# Architecture Decision Records

Decisions that shaped this project. Add an entry whenever you:
add a new dependency, replace an existing pattern, change the data model, or restructure agents.

## Template
\`\`\`markdown
# [Decision Title]
## Context: Why is this decision needed
## Decision: What did we choose
## Consequences: Tradeoffs, known constraints
\`\`\`

## Decisions

### ADR-001: Initial Stack Decisions
**Context**: Stack and rules decided during `/project-init` interview.
**Decision**: Language: [Q2 answer], Data: [Q3 answer], Interface: [Q4 answer], AI: [Q6 answer]
**Hard Rules origin**: [from Q7 — why each rule exists]
```

---

### 3-5. Folder Structure (reference only — not generated)

Auto-select based on language. Combine for multi-language projects.

**Python (data / automation / backend):**
```
[project]/
├── CLAUDE.md
├── .env.example
├── requirements.txt          # pip install -r requirements.txt
├── [main_entry].py
├── [core_module]/            # core logic
├── tests/                    # pytest
│   └── conftest.py
├── docs/
│   ├── INDEX.md
│   └── DEVELOPMENT_ROADMAP.md
├── scripts/                  # utility scripts
├── config/                   # YAML/JSON config
└── outputs/                  # artifacts (.gitignore)
```

**TypeScript — Next.js / Full-stack web:**
```
[project]/
├── CLAUDE.md
├── .env.example
├── package.json
├── tsconfig.json
├── next.config.ts            # if using Next.js
├── src/
│   ├── app/                  # App Router (Next.js 14+)
│   ├── components/
│   ├── lib/                  # utils, DB client
│   └── types/
├── tests/                    # Vitest / Jest
├── docs/
│   └── DEVELOPMENT_ROADMAP.md
└── scripts/
```

**TypeScript — API server (Express / Fastify / Hono):**
```
[project]/
├── CLAUDE.md
├── .env.example
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # entrypoint
│   ├── routes/
│   ├── services/             # business logic
│   ├── middleware/
│   └── types/
├── tests/
└── docs/
    └── DEVELOPMENT_ROADMAP.md
```

**Java / Kotlin — Spring Boot (backend API):**
```
[project]/
├── CLAUDE.md
├── .env.example
├── build.gradle.kts           # or pom.xml (Maven)
├── settings.gradle.kts
├── src/
│   ├── main/
│   │   ├── kotlin/            # or java/
│   │   │   └── com/[pkg]/
│   │   │       ├── Application.kt
│   │   │       ├── controller/
│   │   │       ├── service/
│   │   │       ├── repository/
│   │   │       └── domain/
│   │   └── resources/
│   │       └── application.yml
│   └── test/
│       └── kotlin/
│           └── com/[pkg]/
├── docs/
│   └── DEVELOPMENT_ROADMAP.md
└── scripts/
```

**Kotlin — Android:**
```
[project]/
├── CLAUDE.md
├── build.gradle.kts
├── settings.gradle.kts
├── app/
│   ├── build.gradle.kts
│   └── src/
│       ├── main/
│       │   ├── kotlin/com/[pkg]/
│       │   │   ├── MainActivity.kt
│       │   │   ├── ui/
│       │   │   ├── viewmodel/
│       │   │   └── data/
│       │   └── res/
│       └── test/
├── docs/
│   └── DEVELOPMENT_ROADMAP.md
└── scripts/
```

**Go (CLI / high-performance server):**
```
[project]/
├── CLAUDE.md
├── .env.example
├── go.mod
├── go.sum
├── cmd/
│   └── [app]/
│       └── main.go           # entrypoint
├── internal/                 # unexported packages
│   └── [feature]/
├── pkg/                      # exported packages
├── tests/
└── docs/
    └── DEVELOPMENT_ROADMAP.md
```

**Rust (systems / CLI):**
```
[project]/
├── CLAUDE.md
├── .env.example
├── Cargo.toml
├── src/
│   ├── main.rs               # or lib.rs for libraries
│   └── [module]/
│       └── mod.rs
├── tests/                    # integration tests
├── benches/                  # benchmarks (optional)
└── docs/
    └── DEVELOPMENT_ROADMAP.md
```

**Swift (iOS / macOS):**
```
[project]/
├── CLAUDE.md
├── [Project].xcodeproj/      # or Package.swift (SPM)
├── Sources/
│   └── [Target]/
├── Tests/
│   └── [Target]Tests/
└── docs/
    └── DEVELOPMENT_ROADMAP.md
```
