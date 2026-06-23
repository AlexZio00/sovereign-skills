---
skill_type: workflow
tools: Read, Bash, Glob, Grep
triggers:
  - "push"
  - "git push"
  - "푸시해"
name: "pre-push"
description: "Mandatory pre-push security and quality pipeline. TRIGGER automatically whenever the user requests any git push: 'push my changes', 'push to origin', 'push this', 'push the code', 'commit and push', 'ship it', 'deploy to remote', 'deploy to prod/staging/production', or any git push command. Blocks hardcoded credentials (12 patterns: AWS/GCP/Azure/LLM keys, private keys, connection strings, platform tokens, merge conflicts), supply chain risks, auth bypasses, and OWASP Top 10 vulnerabilities. Do NOT skip unless user says 'skip review' or 'force push'."
license: "MIT"
metadata:
  version: "3.2.0"
  author: "coinangel"
user_invocable: true
---

<!--
  v3.3.0 (2026-06-12) — Step 6 대형 diff 결정론 번들링 (출처: alibaba/open-code-review 차용 —
                         커버리지를 에이전트 성실성이 아닌 구조로 보장. 번들 합집합 = staged 전체 검증)
  v3.2.0 (2026-05-06) — /XVII 상속 추가: Error Recovery (Step 7) + State Sync (Step 6 병렬 결과 병합)
  v3.1.0 (2026-04-11) — defense structure: Dominant variable, Discard if,
                         Rationalization Table (6), Invariants (4), Scope Boundary
  v3.0.0 (2026-04-10) — scanner: scripts/scan_secrets.pl (12 patterns) |
                         multi-lang tests + direct lint | parallel AI review agents
-->
# Pre-Push Pipeline

## Dominant Variable
시크릿 스캔이 예외 없이 실행되는가 — 한 번의 스킵으로 자격증명이 git history에 영구히 기록된다.

## Trigger

- "push"
- "git push"
- "푸시해"

## Discard If
- 사용자가 "skip review" 또는 "force push" 명시 → Emergency Override로 직행
- staged 파일이 0개 (커밋할 것이 없음)
- `*.md` / `docs/**` 변경만 (Step 2에서 fast-exit되지만, 이 조건이면 에이전트 리뷰 오버헤드 불필요)

## Key Assumptions 
1. **scan_secrets.pl 스크립트 접근 가능** — 깨지면: 시크릿 스캔 불가 → push 차단.
2. **git staged files 존재** — 깨지면: "staged 파일 없음" 안내 후 중단.
3. **에이전트 도구(code-reviewer 등) 디스패치 가능** — 깨지면: AI 리뷰 스킵, lint/test만 실행.


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

### 5b: code-reviewer --quick Gate (AI, Serial)

**Skip if `$DIFF_LINES` < 50** — tiny diffs have negligible type/lint risk.

Run **code-reviewer --quick** (haiku) for type errors and logical lint issues that static tools miss. FAIL → fix before continuing.

```
Review the following staged diff for type errors and lint issues only.
Do NOT read entire files unless absolutely necessary.

<diff>
[paste full output of: git diff --staged]
</diff>
```

## Step 6: Launch Review Agents in Parallel

> **Spawn all applicable agents in a SINGLE response turn** using concurrent subagent calls — never sequentially. Parallel execution cuts total wall time by the duration of the slowest agent.

**Large diff — 결정론 번들링** (`$DIFF_LINES` > 500 OR 파일 > 10개) (출처: alibaba/open-code-review 차용, 2026-06-12):

대형 changeset에서 에이전트가 "알아서 골라 읽는" 방식은 커버리지 누락을 낳는다 — 커버리지는 프롬프트 성실성이 아니라 **구조로 보장**한다:

1. **번들 분할 (결정론)**: `$STAGED_FILES`를 최상위 디렉토리/모듈 기준으로 그룹핑. 자연 쌍(소스+테스트, 구현+설정)은 같은 번들에. 번들 크기 가이드: diff ≤ ~300줄 또는 ≤ 5파일. 초과 시 번들 재분할.
2. **번들당 리뷰어 1개**: code-reviewer를 번들 수만큼 디스패치 — 각 에이전트는 **자기 번들의 diff만** 받는다 (격리 컨텍스트, 전체 diff 전달 금지). 병렬 cap 5 — 번들 6개+면 5개씩 배치.
3. **커버리지 검증 (결정론)**: 디스패치 전 `번들들의 파일 합집합 == $STAGED_FILES 전체` 카운트 대조. 불일치 → 누락 파일을 마지막 번들에 추가. 이 검증 없이 디스패치 금지.
4. **조건부 에이전트**(security/database/refactor)는 기존 트리거 규칙대로 — 단 트리거에 매칭된 번들의 diff만 전달.

소형 diff (≤500줄 AND ≤10파일): 기존대로 전체 diff를 각 에이전트에 전달. 번들링 오버헤드 불필요.

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

**Agent prompt template** (intent-passing — `no-mistakes` 차용: 의도적 결정 vs 실수 구분으로 오탐↓):

```
Review the following staged diff. Focus on changed lines.
Only read full files if you need more context.

<intent>
[이번 변경에서 유저가 달성하려던 것 — 세션 대화 기준 verbatim. 목표 + 의식적으로 내린 결정/트레이드오프 + 일부러 제외한 것. diff 설명이 아님. 비우지 말 것 — 비면 리뷰어가 의도적 선택을 "실수"로 오탐한다.]
</intent>

<diff>
[paste full output of: git diff --staged]
</diff>

위 <intent>는 유저가 의도한 목표다. diff가 intent에서 벗어나면 플래그하되, intent에 명시된 의식적 결정·트레이드오프는 "실수"로 플래그하지 말 것.
```

> **Intent 출처**: 별도 입력 아님 — pre-push 실행 에이전트(=너)가 **이 세션 대화에서 이미 알고 있는** 목표를 채운다. 모르면 채우지 말고 "intent 불명"으로 두되, 그 경우 리뷰 오탐 가능성을 Step 8 리포트에 명시.

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

**Error Recovery ( 상속)**: Step 6 에이전트 또는 Bash 도구 실패 시:
- Classify: `tool_failure`
- Apply: 동일 에이전트 1회 재시도 → 여전히 실패 → `⚠️ TOOL_FAILURE: {agent} — 수동 검토 필요`로 보고 후 나머지 단계 계속. Silent failure 금지.
- Step 8 리포트 해당 줄: `⚠️ SKIPPED (tool_failure — {agent})` 명시.

**Parallel Conflict Resolution ( 상속)**: Step 6 에이전트들이 동일 파일에 상반된 판정 시:
- security-reviewer Critical + code-reviewer Non-critical → **Critical 우선** (약한 고리 원칙).
- 복수 에이전트 동일 파일 Critical → 합산하지 않음 (중복 계산 금지).
- 판정 방향 완전 상충(한쪽 PASS, 한쪽 Critical FAIL) → **유저 에스컬레이션**. 임의 합의 금지.

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
- code-reviewer --quick:   ✅ PASS (Xs) / ❌ FAIL (N issues) / ➖ SKIPPED (<50 lines)
- code-reviewer:     ✅ PASS / ⚠️ N issues (X fixed, Y remaining)
- security-reviewer: ✅ PASS / ❌ N issues / ➖ NOT TRIGGERED
- database-reviewer: ✅ PASS / ⚠️ N issues / ➖ NOT TRIGGERED
- refactor-cleaner:  ✅ PASS / ⚠️ N suggestions / ➖ NOT TRIGGERED

[Supply chain — new packages listed here if applicable]
[Secrets remediation steps listed here if blocked]

Overall: ✅ READY TO PUSH / ❌ BLOCKED — <reason>
```

Execute `git push` only when Overall = **READY TO PUSH**.

### Memory Sync Reminder (READY TO PUSH 시만)

push 대상 파일에 `` 경로 변경이 포함된 경우:

```
💡 Memory Sync: 코드가 변경됐습니다.
   session-checkpoint를 아직 안 돌렸다면 메모리가 stale일 수 있습니다.
   이 세션 종료 전에 /session-checkpoint 실행을 권장합니다.
```

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

**세션 승인 유효기간 **: Emergency Override는 **해당 1회 push에만** 유효. "앞으로 계속 skip" 금지 — 매 push마다 재승인.

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

## Error Recovery 

실패 감지 시: **Stop → Classify → Apply Recovery → Report & Resume**.

| 실패 유형 | 감지 조건 | 복구 경로 |
|---------|---------|--------|
| `tool_failure` | Bash 시크릿 스캔 / pytest 실행 실패 | "체크 실행 불가" 명시 → push 중단. 실행 못 한 체크를 통과로 취급 금지 |
| `input_error` | push 대상 브랜치/원격 불명확 | `git status` 재확인 후 명확화. 추측으로 push 진행 금지 |
| `missing_data` | 시크릿 패턴 파일 / pytest 없음 | 해당 체크 skip + ⚠️ 명시. 빠진 체크 있으면 유저 확인 후 push |
| `logic_inconsistency` | pytest 통과했지만 lint 실패 | 모든 체크 통과 후에만 push. 일부 통과를 "충분"으로 취급 금지 |

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
