---
skill_type: workflow
tools: Read, Bash, Glob, Grep
triggers:
  - "push"
  - "git push"
  - "푸시해"
name: "pre-push"
description: "Mandatory pre-push security and quality pipeline. TRIGGER automatically whenever the user requests any git push: 'push my changes', 'push to origin', 'push this', 'push the code', 'commit and push', 'ship it', 'deploy to remote', 'deploy to prod/staging/production', or any git push command. Blocks hardcoded credentials (12 patterns: AWS/GCP/Azure/LLM keys, private keys, connection strings, platform tokens, merge conflicts), supply chain risks (9-IOC), MCP tool poisoning (3 patterns), auth bypasses, and OWASP Top 10 vulnerabilities. Do NOT skip unless user says 'skip review' or 'force push'."
license: "MIT"
metadata:
  version: "3.7.0"
  author: "coinangel"
user_invocable: true
not_for:
  - "Code review only -> code-reviewer agent"
  - "Lint/type check only -> code-reviewer --quick"
see_also:
  []
---

<!--
  v3.7.0 (2026-07-18) — Step 6: cross-bundle joint pass (catches changes fragmented across bundles that
                        look safe in isolation) + deterministic claim verification (optional, checks
                        finding citations against the actual diff) added. Step 7: three-state false-positive
                        gate for high-FP pattern classes (PII/name-like matches) added.
  v3.6.0 (2026-07-15) — scan_secrets.pl synced to v2.1.0: f11 (prompt-injection string detection) + f12
                        (non-PyPI/HTTP-git supply-chain source detection) ported. Step 0: Hook Pipeline
                        Health section added (WARN-only smoke-test check before Step 1).
  v3.5.0 (2026-07-07) — 6-IOC→9-IOC expansion: dependency confusion / missing pinned version / post-install
                        hook network calls. MCP tool poisoning 3 patterns (hidden instructions/Unicode
                        deception/parameter injection) ported.
  v3.3.0 (2026-06-12) — Step 6 Large diff deterministic bundling (coverage guaranteed by structure, not agent integrity)
  v3.2.0 (2026-05-06) — Error Recovery (Step 7) + State Sync (Step 6 parallel result merge)
  v3.1.0 (2026-04-11) — defense structure: Dominant variable, Discard if,
                         Rationalization Table (6), Invariants (4), Scope Boundary
  v3.0.0 (2026-04-10) — scanner: scripts/scan_secrets.pl (12 patterns) |
                         multi-lang tests + direct lint | parallel AI review agents
-->
# Pre-Push Pipeline

## Dominant Variable
Does the secrets scanner run without exception — a single skip permanently records credentials in git history.

## Trigger

- "push"
- "git push"
- "푸시해"

## Discard If
- User explicitly says "skip review" or "force push" → proceed directly to Emergency Override
- 0 staged files (nothing to commit)
- `*.md` / `docs/**` changes only (fast-exit at Step 2, but agent review overhead unnecessary at this condition)

## Key Assumptions 
1. **`scan_secrets.pl` script accessible** — if broken: secrets scan unavailable → push blocked.
2. **git staged files exist** — if broken: inform user and halt.
3. **Agent tools (code-reviewer, etc.) dispatchable** — if broken: skip AI review, run lint/test only.

## Step 0: Hook Pipeline Health (Fast, WARN-only)

Before scanning the diff, confirm your PreToolUse/Stop hook pipeline itself hasn't silently regressed — a broken hook is invisible until something it should have caught gets through.

If your setup has a hook smoke-test script (a script that exercises your hooks end-to-end and reports pass/fail), run it here:

```bash
SMOKE_SCRIPT=$(find ~/.claude -maxdepth 3 -iname "hook_smoke_test*" -type f 2>/dev/null | head -1)
if [ -n "$SMOKE_SCRIPT" ]; then
  "$SMOKE_SCRIPT" full 2>&1 | tail -20
  SMOKE_EXIT=$?
  [ $SMOKE_EXIT -ne 0 ] && echo "⚠️ hook smoke test FAIL — hook pipeline regression suspected, recommend investigating before Step 7 Gate Check (does not block)"
else
  echo "➖ No hook smoke-test script found — skipping Step 0 (optional check)"
fi
```

WARN-only — a smoke failure does not block push (avoids introducing a new hard gate outside design scope), but MUST be surfaced in the Step 8 report.

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
- **9-IOC Supply Chain + MCP Check**: for newly added dependencies and MCP configuration, check 9 indicators of compromise:
  1. **External install links** — does the package README or setup script fetch from non-registry URLs?
  2. **Obfuscated exfiltration** — base64/hex-encoded strings in post-install scripts?
  3. **Capability mismatch** — does a "utility" package request network/filesystem access beyond its stated purpose?
  4. **MCP hidden instructions** — does an MCP tool description/parameter embed text meant to steer agent behavior?
  5. **MCP Unicode deception** — direction-override characters (e.g. U+202E) or homoglyphs in a tool name/description?
  6. **MCP parameter injection** — an executable command or URL embedded in a tool parameter default/enum?
  7. **Dependency confusion** — is an internal/private package name unregistered on public PyPI/npm? An attacker can register the same name (Birsan 2021). Check registry existence when adding a new package to `requirements.txt`/`package.json`.
  8. **Missing pinned version** — warn when a new dependency has no pinned version (`requests` vs `requests==2.32.3`). Unpinned = supply-chain attack surface.
  9. **Post-install hook** — does `setup.py`/`pyproject.toml`'s `[tool.setuptools.cmdclass]` or an npm `postinstall` script make network calls or write files?
  Flag any match as `⚠️ SUPPLY_CHAIN_IOC` or `⚠️ MCP_POISONING` in the report.

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

**Large diff — deterministic bundling** (`$DIFF_LINES` > 500 OR files > 10):

In large changesets, agents choosing which files to read on their own leads to coverage gaps — coverage is guaranteed by **structure, not agent integrity**:

1. **Deterministic bundle split**: group `$STAGED_FILES` by top-level directory/module. Natural pairs (source+test, implementation+config) go in the same bundle. Bundle size guide: diff ≤ ~300 lines or ≤ 5 files; if larger, re-split.
2. **One reviewer per bundle**: dispatch code-reviewer once per bundle — each agent receives **only its bundle's diff** (isolated context, never send full diff). Parallel cap 5 — if 6+ bundles, batch in groups of 5.
3. **Coverage validation (deterministic)**: before dispatch, verify `union of bundle files == all of $STAGED_FILES` by count. Mismatch → add missing files to final bundle. Never dispatch without this check.
4. **Cross-bundle joint pass**: after all per-bundle reviews complete, forward the union of each bundle's finding-list summary to a single reviewer (code-reviewer) for one final pass across bundle boundaries. This catches fragmentation — a change deliberately or accidentally split across bundles can look safe in each isolated review but be unsafe once combined. Do not declare a large-diff review complete without this joint pass.
5. **Deterministic claim verification** (optional, if your setup has a claim-verification script): save the joint-pass output (finding list with file/line-range citations) to a file, then run the script against it. It should check, per finding: (a) the cited file exists in the staged diff, (b) the cited line range overlaps the diff hunk, and (c) an optional grep cross-check passes — labeling each finding `CONFIRMED` or `UNVERIFIED-CLAIM`. Keep `UNVERIFIED-CLAIM` findings open for re-review before Step 7 Gate Check — do not auto-downgrade them. No such script → skip this sub-step, prose-only claims stand as reported.
6. **Conditional agents** (security/database/refactor): follow existing trigger rules, but only pass diff for bundles matching those triggers.

Small diff (≤500 lines AND ≤10 files): use existing approach, send full diff to each agent. Bundling overhead not needed.

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

**Agent prompt template** (intent-passing — distinguish intentional decisions from mistakes to reduce false positives):

```
Review the following staged diff. Focus on changed lines.
Only read full files if you need more context.

<intent>
[What the user aimed to achieve in this change — verbatim from session conversation. Goal + consciously made decisions/trade-offs + intentionally excluded scope. Not a diff explanation. Do not leave blank — blank intent causes reviewers to misclassify intentional choices as mistakes.]
</intent>

<diff>
[paste full output of: git diff --staged]
</diff>

The <intent> above is the user's goal. If diff deviates from intent, flag it — but do not flag conscious decisions or trade-offs explicitly stated in intent as mistakes.
```

> **Intent source**: not a separate input — the pre-push executor agent (you) fills this from **what you already know in this session conversation**. If unsure, leave as "intent unclear", but note in Step 8 report that false positives are possible.

## Step 7: Gate Check

| Severity | Action |
|----------|--------|
| **Critical / High** | Fix before push. No exceptions. |
| **Medium** | Fix if < 5 min. Otherwise add `// TODO(security):` comment and report. |
| **Low / Info** | Report to user. Push allowed. |

**Test file exceptions**: Findings in `**/__tests__/**`, `**/*.test.*`, `**/*.spec.*`, or `**/fixtures/**` are likely test fixtures, not real secrets. Downgrade to Medium severity and note in report.

**Three-state false-positive gate**: for pattern classes prone to false positives (e.g. PII/name-like matches), don't force a binary hard-block/skip decision — present each hit to the user individually. If the user confirms it's a false positive or non-sensitive, record a one-line reason and let it through (stays auditable in the report). If it's real, require removal. Blanket bypass without a stated reason is not allowed. Low-false-positive hard-block classes (the 12 credential patterns) remain immediate-block as before — this gate does not soften those.

**Fix loop** (Critical/High found):
1. Apply fixes with the Edit tool
2. Re-run only the agent(s) that reported the issue
3. Max 1 retry per agent
4. Still failing → halt and report exact issue + file location to user

**Error Recovery**: if Step 6 agents or Bash tools fail:
- Classify: `tool_failure`
- Apply: retry same agent once → still fail → report `⚠️ TOOL_FAILURE: {agent} — manual review needed` and continue remaining steps. No silent failures.
- Step 8 report that line: explicitly note `⚠️ SKIPPED (tool_failure — {agent})`.

**Parallel Conflict Resolution**: if Step 6 agents report conflicting verdicts on the same file:
- security-reviewer Critical + code-reviewer Non-critical → **Critical takes priority** (weakest link principle).
- Multiple agents, same file, both Critical → sum-once (no double-counting).
- Complete conflict (one PASS, other Critical FAIL) → **escalate to user**. No arbitrary consensus.

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

### Memory Sync Reminder (only when READY TO PUSH)

If push target files include memory path changes:

```
💡 Memory Sync: Code has changed.
   If you haven't run session-checkpoint yet, memory may be stale.
   Consider running /session-checkpoint before ending this session.
```

## Emergency Override

If user explicitly says "skip review" or "force push":
1. Print: `⚠️ Pre-push pipeline bypassed by user request. Secrets scan and agent reviews were NOT run.`
2. Execute `git push` immediately.

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| `git push` (regular branch) | low | L1+L2+L3 |
| `git push` (main/master) | low | L1+L2+L3+L4 |
| `git push --force` | low | L1+L2 (deny recommended) |
| Secrets exposure (secrets scan FAIL) | **none** | L1+L2+L3+L4 (BLOCK) |

- **L1 (Invariants)**: secrets scan must pass, Critical/High issues must be fixed.
- **L2 (Tool Restriction)**: recommend deny `git push --force`, `--no-verify` in `settings.json` hooks.
- **L3 (User Approval)**: main/master branches require explicit "yes" confirmation. Emergency Override only with "skip review"/"force push" explicit.
- **L4 (Independent Verification)**: Step 6 review agents (code-reviewer/security-reviewer/etc) provide independent verification separate from implementation.

**Session approval validity**: Emergency Override is **valid for that single push only**. No "continue skipping" — re-approval required for each push.

## Truthful Reporting

After pipeline execution:
1. **no mock deception**: Report actual results per step. Unexecuted steps marked `➖ SKIPPED`, reason noted.
2. **no test façade**: Don't trust test results blindly. If `pytest --passWithNoTests` passes, verify actual tests exist.
3. **no silent brokenness**: Final state is either `✅ READY TO PUSH` or `❌ BLOCKED`. If `⚠️ PARTIAL`, state reason explicitly.

---

## Rationalization Table

| Rationalization | Rebuttal |
|--------|------|
| "diff is small, no need to scan" | A 1-line diff can contain a single API key |
| "already passed tests locally" | Local pass ≠ staged diff safe. Other files may be mixed into staging |
| "only changed docs, so it's fine" | If SECRETS_EXIT=0 + docs-only, Step 2 auto fast-exits. Do not manually skip |
| "secrets are okay because private repo" | Private repo offers no protection. All team members have access, git history is permanent |
| "security reviewer trigger doesn't match, so I'll skip it manually" | If trigger not met, auto-skips as NOT TRIGGERED. Manual skip is a separate concern |
| "urgent bug fix, okay to skip" | Urgency increases mistake likelihood. Secrets scan < 10 seconds |

---

## Error Recovery 

On failure: **Stop → Classify → Apply Recovery → Report & Resume**.

| Failure Type | Detection Condition | Recovery Path |
|---------|---------|--------|
| `tool_failure` | Bash secrets scan / pytest execution fails | Note "check unable to run" → halt push. Never treat unexecuted check as passed |
| `input_error` | Push target branch/remote unclear | Re-confirm `git status`, clarify intent. Never push on assumption |
| `missing_data` | Secrets pattern file / pytest missing | Skip check + note `⚠️`. If checks are missing, confirm with user before push |
| `logic_inconsistency` | pytest passed but lint failed | Push only after all checks pass. Do not treat partial pass as sufficient |

---

## Invariants (never violate)

1. **Secrets scan always runs**: if SECRETS_EXIT=1, push BLOCKED. Even "just push" requests cannot bypass without Emergency Override. Violation → credentials permanently in git history, entire remote repo contaminated.

2. **Protected branch check**: main/master pushes require explicit "yes". Violation → unreviewed code flows directly to production branch.

3. **Critical/High blocks push**: if agent review finds Critical/High, no push without fix. Medium: fix within 5 min or add TODO tag. Violation → known vulnerabilities deployed to remote.

4. **Added lines only scanned**: `-` (removed) lines are not scanned. Violation → secret removal commits get BLOCKED, cleanup becomes impossible.

These rules are unconditional. Emergency Override applies only when user explicitly says "skip review" or "force push".

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [BASH] scan secrets in staged diff (added lines only) | Create or modify commits |
| [BASH] run language-specific tests (changed files only) | Force entire test suite |
| [AGENT] parallel agent reviews (code/security/db/refactor) | Modify code directly (except fix loop) |
| [BASH] check protected branches (main/master) | Modify git history or rebase |
| [BASH] execute push (all gates passed) | `--force` or `--no-verify` push |
