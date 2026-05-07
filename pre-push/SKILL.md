---
name: "pre-push"
description: "Mandatory pre-push security and quality pipeline. TRIGGER automatically whenever the user requests any git push: 'push my changes', 'push to origin', 'push this', 'push the code', 'commit and push', 'ship it', 'deploy to remote', 'deploy to prod/staging/production', or any git push command. Blocks hardcoded credentials (12 patterns: AWS/GCP/Azure/LLM keys, private keys, connection strings, platform tokens, merge conflicts), supply chain risks, auth bypasses, and OWASP Top 10 vulnerabilities. Do NOT skip unless user says 'skip review' or 'force push'."
license: "MIT"
metadata:
  version: "3.2.0"
  author: "coinangel"
---

<!--
  v3.2.0 (2026-05-06) — agent failure recovery + conflict resolution rules in Step 7
  v3.1.0 (2026-04-11) — defense structure: Dominant variable, Discard if,
                         Rationalization Table (6), Invariants (4), Scope Boundary
  v3.0.0 (2026-04-10) — scanner: scripts/scan_secrets.pl (12 patterns) |
                         multi-lang tests + direct lint | parallel AI review agents
-->
# Pre-Push Pipeline

**Dominant variable**: 시크릿 스캔이 예외 없이 실행되는가 — 한 번의 스킵으로 자격증명이 git history에 영구히 기록된다.
**Discard if**: 사용자가 "skip review" 또는 "force push"를 명시적으로 요청한 경우 → Emergency Override 섹션으로 직행.

> ⛔ **BLOCKING REQUIREMENT**: Complete this pipeline and resolve all Critical/High issues BEFORE executing `git push`.

> **YOLO auto-approve**: `git diff`, `git status`, `git branch`, `git log` (read-only ops) are auto-approved without a permission prompt. `git push` is a write operation — it only runs after all gates pass.

## Step 1: Assess & Scan

Run everything in **one bash call** — variables share the same shell session, so `$STAGED_DIFF` is reused for the secrets scan without a second `git diff` invocation.

```bash
STAGED_FILES=$(git diff --staged --name-only)
STAGED_DIFF=$(git diff --staged)
DIFF_LINES=$(echo "$STAGED_DIFF" | wc -l | tr -d ' ')
FILE_COUNT=$(echo "$STAGED_FILES" | grep -c . || echo 0)
CURRENT_BRANCH=$(git branch --show-current)
SCAN_START=$(date +%s)
SCAN_SCRIPT=$(find ~/.claude -name "scan_secrets.pl" -path "*/pre-push/scripts/*" -type f 2>/dev/null | head -1)
SECRETS_OUTPUT=$(echo "$STAGED_DIFF" | perl "$SCAN_SCRIPT")
SECRETS_EXIT=$?
SCAN_TIME=$(($(date +%s) - SCAN_START))
echo "Branch: $CURRENT_BRANCH | Files: $FILE_COUNT | Diff: $DIFF_LINES lines | Scan: ${SCAN_TIME}s"
[ $SECRETS_EXIT -ne 0 ] && echo "$SECRETS_OUTPUT"
```

The scanner (`scripts/scan_secrets.pl`) covers **12 patterns** across two categories:
- **Credentials** (f1–f10): AWS keys, private keys, connection-string passwords, hardcoded assignments (quoted/unquoted), platform tokens (Slack, GitHub 6 types, Stripe live), Dockerfile ENV secrets, Google/Gemini API keys, npm auth tokens, LLM provider keys (Anthropic/OpenAI/HuggingFace/Replicate/Groq), Azure Storage/SAS/connection strings.
- **Code integrity** (f_merge): unresolved merge conflict markers.

**Design note**: the scanner intentionally scans only **added (`+`) lines**, not removed (`-`) lines — this avoids blocking commits that are *removing* a secret. Merge conflict markers are an exception and checked on all lines.

**Empty check**: If `$STAGED_FILES` is empty → inform the user and stop.

**Protected branch block**: If `$CURRENT_BRANCH` is `main` or `master` → stop and ask for an explicit "yes" before proceeding.

## Step 2: Routing & Remediation

**SECRETS_EXIT=1 → BLOCKED.** Print each finding with its specific remediation:

| Finding | Remediation |
|---------|-------------|
| Merge conflict markers | Resolve conflicts: `git status` to find files, fix markers, re-stage. |
| AWS Access Key | Replace with `process.env.AWS_ACCESS_KEY_ID`. **If real key: rotate immediately** at AWS IAM console. |
| Private key | Move to `~/.ssh/` or a secrets manager. Add path to `.gitignore`. |
| Connection string password | Use `process.env.DATABASE_URL`. Never embed credentials in URLs. |
| Platform token (GitHub/Slack/Stripe) | Revoke in provider dashboard. Re-create with minimal scopes. |
| LLM API key | Replace with `process.env.ANTHROPIC_API_KEY` (or provider equivalent). Rotate if exposed. |
| Azure credential | Replace with Managed Identity or environment variable. |
| Dockerfile ENV secret | Use `--secret` mount or ARG with external injection. Never hardcode in ENV. |
| Generic hardcoded credential | Move to `.env.local` → `process.env.YOUR_KEY`. Verify `.gitignore` covers `.env*`. |

**SECRETS_EXIT=0 AND only `*.md` / `docs/**` changed** → fast exit, push directly, skip all agents.

**Otherwise** → continue to Step 3.

## Step 3: Supply Chain & Infrastructure Check (WARN — never blocks)

Scan `$STAGED_FILES` and list findings in the final report:

- **Package manifests** (`package.json`, `yarn.lock`, `pnpm-lock.yaml`, `requirements.txt`, `Gemfile`, `go.mod`, `Cargo.toml`): list all **added** dependencies. Flag misspelled or unfamiliar names as potential typosquats.
- **Infrastructure files** (`Dockerfile`, `docker-compose*.yml`, `*.tf`, `*.yaml`/`*.yml` in `k8s/` or `infra/`, `nginx.conf`): flag any ENV, ARG, or environment sections for human review.
- **Python CVE scan** (`pip-audit`): run when `requirements.txt` or `pyproject.toml` changed and `pip-audit` is installed. WARN only — never blocks.

```bash
CHANGED_REQS=$(echo "$STAGED_FILES" | grep -E "(requirements.*\.txt|pyproject\.toml|setup\.py)$")
if [ -n "$CHANGED_REQS" ] && command -v pip-audit >/dev/null 2>&1; then
  AUDIT_OUT=$(pip-audit --format=columns 2>&1 | tail -20)
  AUDIT_EXIT=$?
  [ $AUDIT_EXIT -ne 0 ] && echo "pip-audit: $AUDIT_OUT"
fi
```

> **Install**: `pip install pip-audit` (Python native, no Go binary needed — preferred over osv-scanner for Python projects)

## Step 4: Build & Test (Fail Fast)

Detect changed languages first, then run only the relevant test/build commands. Skip entirely for config, docs, or style-only commits.

```bash
CHANGED_PY=$(echo "$STAGED_FILES" | grep -E "\.py$")
CHANGED_JS=$(echo "$STAGED_FILES" | grep -E "\.(ts|tsx|js|jsx)$")
CHANGED_GO=$(echo "$STAGED_FILES" | grep -E "\.go$")
```

**Python** — run when `.py` files changed and a test runner is configured:
```bash
if [ -n "$CHANGED_PY" ] && ([ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]); then
  TEST_START=$(date +%s)
  timeout 120 pytest -q 2>&1 | tail -20
  PYTEST_EXIT=$?
  TEST_TIME=$(($(date +%s) - TEST_START))
fi
```

**Go** — run when `.go` files changed and `go.mod` exists:
```bash
if [ -n "$CHANGED_GO" ] && [ -f "go.mod" ]; then
  TEST_START=$(date +%s)
  timeout 120 go test ./... 2>&1 | tail -20
  GO_TEST_EXIT=$?
  TEST_TIME=$(($(date +%s) - TEST_START))
fi
```

**JS/TS** — build then test when source files changed:
```bash
if [ -f "package.json" ] && [ -n "$CHANGED_JS" ]; then
  BUILD_START=$(date +%s)
  timeout 120 npm run build 2>&1 | tail -30
  BUILD_EXIT=$?
  BUILD_TIME=$(($(date +%s) - BUILD_START))
  if node -e "const p=require('./package.json');process.exit(p.scripts&&p.scripts.test?0:1)" 2>/dev/null; then
    timeout 60 npm test -- --passWithNoTests 2>&1 | tail -20
    JS_TEST_EXIT=$?
  fi
fi
```

Any failure → stop immediately. Run `build-error-resolver` agent, then restart from Step 1.

## Step 5: Lint Gate (Direct → AI)

Two sub-steps in order. Direct lint runs first (fast, no token cost). AI layer runs after.

### 5a: Direct Lint (Blocking)

Run only for changed files of the matching language.

**Python** — `ruff` preferred, `flake8` fallback:
```bash
if [ -n "$CHANGED_PY" ]; then
  if command -v ruff >/dev/null 2>&1; then
    timeout 30 ruff check $CHANGED_PY 2>&1 | tail -20; LINT_EXIT=$?
  elif command -v flake8 >/dev/null 2>&1; then
    timeout 30 flake8 $CHANGED_PY 2>&1 | tail -20; LINT_EXIT=$?
  fi
fi
```

**Go** — `go vet` (always available):
```bash
if [ -n "$CHANGED_GO" ]; then
  timeout 30 go vet ./... 2>&1 | tail -20; GO_VET_EXIT=$?
fi
```

**JS/TS** — `eslint` if config file present:
```bash
if [ -n "$CHANGED_JS" ] && ls .eslintrc* eslint.config* 2>/dev/null | head -1 | grep -q .; then
  timeout 30 npx eslint $CHANGED_JS 2>&1 | tail -20; ESLINT_EXIT=$?
fi
```

Lint fails → **BLOCK**. Fix errors before continuing to 5b.

### 5b: quick-validator Gate (AI, Serial)

**Skip if `$DIFF_LINES` < 50** — tiny diffs have negligible type/lint risk.

Run **quick-validator** (haiku) for type errors and logical lint issues that static tools miss. FAIL → fix before continuing.

```
Review the following staged diff for type errors and lint issues only.
Do NOT read entire files unless absolutely necessary.

<diff>
[paste full output of: git diff --staged]
</diff>
```

## Step 6: Launch Review Agents in Parallel

> **Spawn all applicable agents in a SINGLE response turn** using concurrent subagent calls — never sequentially. Parallel execution cuts total wall time by the duration of the slowest agent.

**Large diff** (`$DIFF_LINES` > 500): also pass `git diff --staged --stat` as a preamble so agents can prioritise which files to read in full.

### Always run

| Agent | Model | Role |
|-------|-------|------|
| **code-reviewer** | sonnet | Quality, dead code, duplication, logic |

### Conditional — trigger `security-reviewer` (opus) if ANY match

| Category | Trigger |
|----------|---------|
| API routes | `src/app/api/**`, `**/routes/**`, `**/controllers/**` |
| Auth & access control | `**/auth*`, `**/middleware*`, `**/guard*`, `**/permission*`, `**/rbac*`, `**/acl*` |
| Secrets & config | `**/.env*`, `**/config*`, `**/settings*`, `**/secrets*` |
| Infrastructure | `Dockerfile`, `docker-compose*.yml`, `*.tf`, `nginx.conf`, `*.conf` |
| Dangerous patterns | diff contains `child_process`, `exec(`, `spawn(`, `eval(`, `new Function(`, `dangerouslySetInnerHTML` |
| Sensitive filenames | filename contains `secret`, `token`, `password`, `key`, `credential`, `cert`, `private` |
| Supply chain | `package.json` with new packages added |

Trigger `database-reviewer` (sonnet): `prisma/**`, `**/migrations/**`, `**/db*`, `*.sql`

Trigger `refactor-cleaner` (sonnet): 10+ files changed, or user explicitly requested refactoring

**Agent prompt template**:

```
Review the following staged diff. Focus on changed lines.
Only read full files if you need more context.

<diff>
[paste full output of: git diff --staged]
</diff>
```

## Step 7: Gate Check

| Severity | Action |
|----------|--------|
| **Critical / High** | Fix before push. No exceptions. |
| **Medium** | Fix if < 5 min. Otherwise add `// TODO(security):` comment and report. |
| **Low / Info** | Report to user. Push allowed. |

**Test file exceptions**: Findings in `**/__tests__/**`, `**/*.test.*`, `**/*.spec.*`, or `**/fixtures/**` are likely test fixtures, not real secrets. Downgrade to Medium severity and note in report.

**Fix loop** (Critical/High found):
1. Apply fixes with the Edit tool
2. Re-run only the agent(s) that reported the issue
3. Max 1 retry per agent
4. Still failing → halt and report exact issue + file location to user

**Agent failure handling**: If a review agent times out or errors:
- Retry once. Still failing → report `⚠️ SKIPPED (agent unavailable — {agent})` in Step 8 and continue.
- Never silently skip a failed agent as "PASS."

**Conflict resolution**: When agents give opposing verdicts on the same file:
- security-reviewer Critical + any Non-critical → **Critical wins** (weakest-link principle).
- Fully opposing verdicts (one PASS, one Critical FAIL) → report both to user, do not push.

## Step 8: Report & Push

Include elapsed time next to each step result.

```
## Pre-Push Review Summary
Branch: <current> → origin
Files: N | Diff: N lines | Total time: Xs

- Secrets scan:      ✅ CLEAN (Xs) / 🚨 CRITICAL (N findings — push BLOCKED)
- Supply chain:      ✅ No new deps / ⚠️ N new packages (listed below)
- Build:             ✅ PASS (Xs) / ❌ FAIL (Xs) / ➖ SKIPPED (no source changes)
- Tests:             ✅ PASS (Xs) / ⚠️ SKIPPED / ❌ FAIL (N failed)
- Lint (direct):     ✅ PASS (Xs) / ❌ FAIL (N errors) / ➖ SKIPPED (no linter found)
- quick-validator:   ✅ PASS (Xs) / ❌ FAIL (N issues) / ➖ SKIPPED (<50 lines)
- code-reviewer:     ✅ PASS / ⚠️ N issues (X fixed, Y remaining)
- security-reviewer: ✅ PASS / ❌ N issues / ➖ NOT TRIGGERED
- database-reviewer: ✅ PASS / ⚠️ N issues / ➖ NOT TRIGGERED
- refactor-cleaner:  ✅ PASS / ⚠️ N suggestions / ➖ NOT TRIGGERED

[Supply chain — new packages listed here if applicable]
[Secrets remediation steps listed here if blocked]

Overall: ✅ READY TO PUSH / ❌ BLOCKED — <reason>
```

Execute `git push` only when Overall = **READY TO PUSH**.

## Emergency Override

If user explicitly says "skip review" or "force push":
1. Print: `⚠️ Pre-push pipeline bypassed by user request. Secrets scan and agent reviews were NOT run.`
2. Execute `git push` immediately.

---

## Safety Layers

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| `git push` (일반 브랜치) | low | L1+L2+L3 |
| `git push` (main/master) | low | L1+L2+L3+L4 |
| `git push --force` | low | L1+L2 (deny 권고) |
| 시크릿 노출 (secrets scan FAIL) | **none** | L1+L2+L3+L4 (BLOCK) |

- **L1 (Invariants)**: 시크릿 스캔 통과 필수, Critical/High 이슈 수정 필수.
- **L2 (Tool Restriction)**: `settings.json` hooks에서 `git push --force`, `--no-verify` deny 권고.
- **L3 (User Approval)**: main/master 브랜치는 명시적 "yes" 확인. Emergency Override는 "skip review"/"force push" 명시.
- **L4 (Independent Verification)**: Step 6 review agents (code-reviewer/security-reviewer/etc)가 구현자와 독립 검증.

**세션 승인 유효기간**: Emergency Override는 **해당 1회 push에만** 유효. "앞으로 계속 skip" 금지 — 매 push마다 재승인.

## Truthful Reporting

파이프라인 실행 후:
1. **no mock deception**: Step별 실제 실행 결과만 보고. 미실행 Step은 `➖ SKIPPED`, 이유 명시.
2. **no test façade**: test 실행 결과 맹신 금지. `pytest --passWithNoTests`로 PASS 나오면 실제 테스트 있는지 확인.
3. **no silent brokenness**: 최종 상태 `✅ READY TO PUSH` / `❌ BLOCKED` 이분법. 중간 `⚠️ PARTIAL` 시 이유 구체 명시.

---

## Rationalization Table

| 합리화 | 반박 |
|--------|------|
| "diff가 작으니까 스캔 필요 없어" | 1줄짜리 diff도 API 키 1개 포함 가능 |
| "이미 로컬에서 테스트 통과했어" | 로컬 통과 ≠ 스테이지 diff 안전. 다른 파일이 스테이징에 섞일 수 있음 |
| "docs만 바꿨으니까 괜찮아" | SECRETS_EXIT=0 + docs-only이면 Step 2에서 자동 fast-exit됨. 직접 스킵하지 말 것 |
| "시크릿이 있어도 private repo라 괜찮아" | private repo는 보호가 아님. 팀원 전원 접근 가능하고 git history는 영구적 |
| "보안 리뷰어 트리거 조건이 안 맞아서 수동으로 스킵할게" | 트리거 조건 미충족이면 자동으로 NOT TRIGGERED. 수동 스킵은 별개 문제 |
| "급한 버그 fix라 스킵해도 돼" | 급할수록 실수 가능성 높음. 시크릿 스캔은 <10초 |

---

## Invariants (never violate)

1. **시크릿 스캔은 항상 실행**: SECRETS_EXIT=1이면 push BLOCK. "그냥 push해" 요청도 Emergency Override 확인 없이는 우회 불가. Violation → 자격증명이 git history에 영구히 남고 원격 저장소 전체가 오염된다.

2. **보호 브랜치 확인**: main/master push는 명시적 "yes" 없이 진행 불가. Violation → 미검증 코드가 프로덕션 브랜치에 직접 유입된다.

3. **Critical/High는 push 차단**: 에이전트 리뷰에서 Critical/High 발견 시 수정 없이 push 불가. Medium은 5분 내 수정 또는 TODO 태그. Violation → 알려진 취약점이 원격에 배포된다.

4. **추가 라인만 스캔**: 시크릿을 제거하는 `-` 라인은 스캔 대상이 아님. Violation → 시크릿 제거 커밋이 BLOCK되어 정리가 불가능해진다.

These rules are unconditional. Emergency Override는 사용자가 명시적으로 "skip review" 또는 "force push"를 말한 경우에만 적용된다.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [BASH] 스테이지 diff에서 시크릿 스캔 (추가 라인만) | 커밋 생성 또는 수정 |
| [BASH] 언어별 테스트 실행 (변경 파일만) | 전체 테스트 스위트 강제 실행 |
| [AGENT] 병렬 에이전트 리뷰 (code/security/db/refactor) | 코드 직접 수정 (fix loop 제외) |
| [BASH] 보호 브랜치 확인 (main/master) | git history 수정 또는 rebase |
| [BASH] push 실행 (모든 게이트 통과 시) | `--force` 또는 `--no-verify` push |

---

## In production
Running on a 99K LOC Python project, 1,326 tests, 200+ files.
Every push goes through this gate — catches credential leaks,
dependency drift, and logic errors before they reach main.
4+ months in production.
