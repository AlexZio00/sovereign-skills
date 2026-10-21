---
skill_type: workflow
tools: Read, Edit, Bash, Glob, Grep, Agent
triggers:
  - "git push"
  - "push my changes"
  - "ship it"
  - "푸시해"
name: "pre-push"
description: "Pre-push security and quality pipeline: secrets scan, then tests, lint and review. TRIGGER automatically whenever the user requests a git push: 'push my changes', 'push to origin', 'push this', 'push the code', 'commit and push', 'ship it', 'deploy to remote', 'deploy to prod/staging/production', or any git push command. Blocks hardcoded credentials and prompt-injection/exfiltration markers (14 patterns: AWS/GCP/Azure/LLM keys, private keys, connection strings, platform tokens, merge conflicts, embedded prompt-injection strings, non-standard package sources, Slack webhooks), and runs supply-chain, MCP tool-poisoning and OWASP-style review checks. Do NOT skip unless the user says 'skip review' (Emergency Override)."
license: "MIT"
user-invocable: true
not_for:
  - "Code review only -> code-autopsy"
  - "Lint/type check only -> run the linter directly"
depends_on:
  - "scripts/scan_secrets.py"
  - "scripts/scan_secrets.pl"
  - "scripts/ruff_changed_lines.py"
optional_agents:
  - "code-reviewer"
  - "security-reviewer"
  - "database-reviewer"
  - "refactor-cleaner"
  - "build-error-resolver"
concurrency_profile:
  agents: "parallel (Step 6 review agents, cap 5 per wave; large diffs use deterministic bundling)"
  bash: "serial (git state advances sequentially: Steps 1/4/5/8 each depend on the prior step's exit code)"
see_also:
  []
---

<!--
  Derived from coinangel/claude-pre-push-skill (MIT, see LICENSE.txt).
  The plugin version lives only in .claude-plugin/plugin.json; user-visible changes are in the repository CHANGELOG.
-->
# Pre-Push Pipeline

## Dominant Variable
Does the secrets scanner run without exception — a single skip permanently records credentials in git history.

## Trigger

- Any `git push` request, including the push-intent phrases listed in the description.

## Discard If
- User explicitly says "skip review" → proceed directly to Emergency Override (a request to force-push is never a trigger: this skill never force-pushes)
- 0 staged files **AND** 0 outgoing (already-committed, not-yet-pushed) commits — check both before discarding: `git rev-list --count '@{upstream}'..HEAD 2>/dev/null || git rev-list --count origin/HEAD..HEAD 2>/dev/null`. If outgoing has 1+ commits, this is NOT a discard case — proceed to Step 1 so the outgoing commits get scanned too (a secret committed earlier this session, with staging now empty, used to slip past a staged-files-only check entirely).
- `*.md` / `docs/**` changes only (fast-exit at Step 2, but agent review overhead unnecessary at this condition). **This skips the agent-review overhead only — Step 1/2 scanning (and Step 3.5 when a public-mirror scrub is configured) still runs**; the Step 2 fast-exit fires only after `SECRETS_EXIT=0` is already known, not before scanning.

## Key Assumptions 
1. **A bundled scanner is accessible** (`scan_secrets.py` with Python 3.9+, or `scan_secrets.pl` with Perl) — if broken: secrets scan unavailable → push blocked.
2. **git staged files exist** — if broken: inform user and halt.
3. **Review agents dispatchable** — the agents named in Step 6 (code-reviewer, security-reviewer, database-reviewer, refactor-cleaner, build-error-resolver) are optional and not included in this repo (`/setup` can generate code-reviewer, security-reviewer, database-reviewer and build-error-resolver agents). If an agent is not installed or cannot be dispatched, replace code-reviewer with an inline review using code-autopsy's FAST MODE (shipped in this repo; see Error Recovery below) rather than skipping it outright. Conditional agents (security/database/refactor) are skipped with an explicit `SKIPPED` note in the report.

## Autonomy Boundary

Every step through Step 6 only *inspects git state* — `git diff`, `git status`, `git branch --show-current`, `git log`, linters, and the parallel review agents never mutate the repo or its remote (the fix loop in Step 7 edits working-tree files but never stages, commits or rewrites history), so none of them need a per-command confirmation to run. **Build and test runners (Step 4) are not fully read-only**: they don't touch git state (no commits, no staged-index changes), but they do have local filesystem side effects — `npm run build` writes build artifacts to the project's configured output directory, and the Python test-count-floor check writes/updates a local state file under `.git/` (`pre-push-vars.sh`, `pre-push-test-count-floor.json` -- never staged or committed, so nothing to gitignore). These are non-git, locally-reversible outputs (re-running regenerates them), so they still need no per-command confirmation, but "read-only" is the wrong label for them — treat them as side-effecting-but-non-git. `git push` is the one write action against git/remote state in this entire pipeline, and it's exactly where the gates apply: it only fires after Step 8's Overall verdict is READY TO PUSH, and a push to `main`/`master` additionally needs an explicit "yes" (Step 1 protected-branch block, Safety Layers L3). Treat "runs freely" and "needs approval" as following directly from read-vs-write-to-git-state, not from step number or perceived risk.

## Step 0: Hook Pipeline Health (Fast, WARN-only)

Before scanning the diff, confirm your PreToolUse/Stop hook pipeline itself hasn't silently regressed — a broken hook is invisible until something it should have caught gets through.

If your setup has a hook smoke-test script (a script that exercises your hooks end-to-end and reports pass/fail), run it here:

```bash
# Optional, user-supplied script: this repo ships no hook smoke test.
SMOKE_SCRIPT=$(find "$HOME/.claude" -maxdepth 3 -iname "hook_smoke_test*" -type f 2>/dev/null | head -1)
if [ -n "$SMOKE_SCRIPT" ]; then
  "$SMOKE_SCRIPT" full 2>&1 | tail -20
  SMOKE_EXIT=${PIPESTATUS[0]}  # not $? — that would capture tail's exit code, not the smoke test's
  [ $SMOKE_EXIT -ne 0 ] && echo "⚠️ hook smoke test FAIL — hook pipeline regression suspected, recommend investigating before Step 7 Gate Check (does not block)"
else
  echo "➖ No hook smoke-test script found — skipping Step 0 (optional check)"
fi
```

WARN-only — a smoke failure does not block push (avoids introducing a new hard gate outside design scope), but MUST be surfaced in the Step 8 report.

## Step 1: Assess & Scan

Run everything in **one bash call** — variables share the same shell session, so `$STAGED_DIFF` is reused for the secrets scan without a second `git diff` invocation.

`${CLAUDE_SKILL_DIR}` is this skill's folder; Claude Code fills it in. In other agents, replace it with the path where you installed the skill. Use `python` instead of `python3` where only that exists (common on Windows) — the block below picks one automatically into `PYBIN`.

**This "one shell session" requirement is not limited to Step 1 alone**: `$STAGED_FILES`/`$STAGED_DIFF`/`$CURRENT_BRANCH`/`$DIFF_LINES`/`$FILE_COUNT`/`$PUSH_FILES`/`$PUSH_DIFF_LINES` (set in Step 1) and `$CHANGED_PY`/`$CHANGED_JS`/`$CHANGED_GO` (set in Step 4) are reused all the way through **Step 1-Step 5a** (Step 6 only dispatches agents and runs no bash, so it is out of scope here). If your Bash tool does not keep shell state across separate tool calls (some agent harnesses reset the shell each call, keeping only the working directory), running Steps 1-5a as separate calls silently empties these variables in later steps — Step 4's Build & Test "Fail Fast" and Step 5a's Lint "BLOCK" gate can then no-op quietly (an empty `$CHANGED_PY` means nothing gets checked, which reads as "passed"). **Run Steps 1-5a as one continuous bash call whenever your environment allows it** — do not split each bash code fence into a separate tool call. When a split is unavoidable, Step 1 persists the core variables to `$(git rev-parse --git-dir)/pre-push-vars.sh` (inside `.git/`, never staged or committed) and Steps 3/3.5/4/5a each restore from it if their own copy is empty, keyed to the current `HEAD` plus the staged-diff hash so a stale file from an earlier push is never silently reused. Even with that fallback, Steps 4/5a print an explicit `⚠️ CHANGED_* empty` note instead of quietly doing nothing, so a genuinely empty list isn't mistaken for a passed check.

**Scan scope — staged diff AND every outgoing commit**: `git diff --staged` alone is not what `git push` actually sends. A push transmits every commit from the upstream (or the merge-base with the remote's default branch) up to `HEAD`. The net diff of that range is not enough either: a secret added in commit A and removed in commit B is absent from the net diff but still reaches the remote inside commit A. Step 1 therefore feeds the scanner three inputs in one pass: the staged diff, the per-commit patches (`git log -p --no-merges` over the range, so every added line of every commit is scanned), and the net diff of the range (which also covers merge-commit conflict resolutions that `--no-merges` omits).

**Scanner selection**: prefer `scan_secrets.py` when Python 3.9+ is available (`PYBIN`, resolved once below: `python3`, else `python`), otherwise fall back to `scan_secrets.pl` (needs Perl). Both are maintained and both honor the same-line allow marker (see Step 2).

```bash
# Resolve the Python interpreter once (python3, else python); a Windows Store stub that cannot run is skipped.
PYBIN=""
for c in python3 python; do
  command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1 && { PYBIN="$c"; break; }
done
# GNU timeout is missing on stock macOS (gtimeout comes with coreutils); without either, commands run with no time limit.
TMO=$(command -v timeout || command -v gtimeout)
STAGED_FILES=$(git diff --staged --name-only)
STAGED_DIFF=$(git diff --staged)
DIFF_LINES=$(echo "$STAGED_DIFF" | wc -l | tr -d ' ')
FILE_COUNT=$(echo "$STAGED_FILES" | grep -c .)  # grep -c already prints 0 on no match -- a `|| echo 0` fallback prints a second "0" line on top of it
CURRENT_BRANCH=$(git branch --show-current)

# Outgoing-commit range (already committed, not yet pushed). Falls back to the
# remote's default branch when no upstream is configured (new/never-pushed
# branch); if that's also unresolvable (no network, origin/HEAD never set
# locally), outgoing-commit scanning degrades to staged-only — surfaced below
# and in the Step 8 report, never silently dropped.
UPSTREAM_REF=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)
[ -z "$UPSTREAM_REF" ] && UPSTREAM_REF=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's#^refs/remotes/##')
MERGE_BASE=""
[ -n "$UPSTREAM_REF" ] && MERGE_BASE=$(git merge-base "$UPSTREAM_REF" HEAD 2>/dev/null)
if [ -n "$MERGE_BASE" ]; then
  OUTGOING_DIFF=$(git diff "$MERGE_BASE"..HEAD)
  # Per-commit patches: a secret added in one commit and removed in a later one is absent from the net diff above.
  OUTGOING_LOG=$(git log -p --no-merges --no-color --no-ext-diff "$MERGE_BASE"..HEAD)
  OUTGOING_COMMIT_COUNT=$(git rev-list --count "$MERGE_BASE"..HEAD)
  OUTGOING_MODE="${UPSTREAM_REF}..HEAD (${OUTGOING_COMMIT_COUNT} commit(s))"
else
  OUTGOING_DIFF=""
  OUTGOING_LOG=""
  OUTGOING_COMMIT_COUNT=0
  OUTGOING_MODE="unresolvable (no upstream, no origin/HEAD) — staged-only, degraded mode"
fi
COMBINED_DIFF="$STAGED_DIFF
$OUTGOING_LOG
$OUTGOING_DIFF"
# What the push actually carries = staged + outgoing (deleted files excluded -- nothing to test or
# lint). Steps 3/4/5/6 use PUSH_FILES/PUSH_DIFF_LINES, not STAGED_FILES: in the usual "commit first,
# push later" flow STAGED_FILES is empty, so the .py test and lint lists came out empty and both
# steps were silently skipped.
PUSH_FILES=$({ git diff --staged --name-only --diff-filter=d; [ -n "$MERGE_BASE" ] && git diff --name-only --diff-filter=d "$MERGE_BASE"..HEAD; } | sort -u | grep .)
PUSH_DIFF_LINES=$(printf '%s\n%s\n' "$STAGED_DIFF" "$OUTGOING_DIFF" | grep -c '^[+-]')

SCAN_START=$(date +%s)
SCAN_SCRIPT_PY="${CLAUDE_SKILL_DIR}/scripts/scan_secrets.py"
SCAN_SCRIPT_PL="${CLAUDE_SKILL_DIR}/scripts/scan_secrets.pl"
if [ -n "$PYBIN" ] && [ -f "$SCAN_SCRIPT_PY" ]; then
  SECRETS_OUTPUT=$(printf '%s\n' "$COMBINED_DIFF" | "$PYBIN" "$SCAN_SCRIPT_PY")
  SECRETS_EXIT=$?
elif command -v perl >/dev/null 2>&1 && [ -f "$SCAN_SCRIPT_PL" ]; then
  SECRETS_OUTPUT=$(printf '%s\n' "$COMBINED_DIFF" | perl "$SCAN_SCRIPT_PL")
  SECRETS_EXIT=$?
else
  echo "🚨 No usable scanner (need Python 3.9+ and ${CLAUDE_SKILL_DIR}/scripts/scan_secrets.py, or Perl and scan_secrets.pl). If that path looks wrong, replace CLAUDE_SKILL_DIR with the folder where this skill is installed. Secrets scan unavailable, push blocked."
  SECRETS_EXIT=1
fi
SCAN_TIME=$(($(date +%s) - SCAN_START))
echo "Branch: $CURRENT_BRANCH | Staged files: $FILE_COUNT | Push files: $(printf '%s\n' "$PUSH_FILES" | grep -c .) | Push diff: $PUSH_DIFF_LINES lines | Outgoing: $OUTGOING_MODE | Scan: ${SCAN_TIME}s"
[ $SECRETS_EXIT -ne 0 ] && echo "$SECRETS_OUTPUT"

# Newly added database files -- blocked for public and private repos alike. The text secrets
# scanner only reads text diff lines, so it cannot see inside a binary DB file. An intended test
# fixture is excluded when it lives under tests/ or fixtures/.
NEW_DATA_FILES=$({ git diff --staged --name-only --diff-filter=A; [ -n "$MERGE_BASE" ] && git diff --name-only --diff-filter=A "$MERGE_BASE"..HEAD; } \
  | sort -u | grep -iE '\.(db|sqlite|sqlite3|db-wal|db-shm)$' | grep -vE '(^|/)(tests?|fixtures?)/')
if [ -n "$NEW_DATA_FILES" ]; then
  echo "🚨 NEW_DATA_FILE: about to commit a new database file -- push blocked:"
  echo "$NEW_DATA_FILES"
  SECRETS_EXIT=1
fi

# Second secrets engine: gitleaks, WARN-only. This block never changes SECRETS_EXIT -- the
# scan_secrets result above is the only blocking evidence, and nothing here skips any other step.
# A commit-time hook that runs `gitleaks protect --staged` sees only what was staged at commit time;
# this pass re-reads the outgoing range the push really carries with a second engine, which catches
# commits made with --no-verify or in an environment without hooks. It runs only when the outgoing
# commit count is above 0: gitleaks can hang on an empty --log-opts range.
GITLEAKS_BIN=$(command -v gitleaks 2>/dev/null || ls "$HOME/bin/gitleaks" "$HOME/bin/gitleaks.exe" 2>/dev/null | head -1)
if [ -z "$GITLEAKS_BIN" ]; then
  echo "➖ gitleaks second scan skipped -- gitleaks not installed (WARN-only step, the scan_secrets result stands)"
else
  GL_WARN=0
  if [ -n "$MERGE_BASE" ] && [ "${OUTGOING_COMMIT_COUNT:-0}" -gt 0 ]; then
    ${TMO:+$TMO 90} "$GITLEAKS_BIN" git --log-opts "${MERGE_BASE}..HEAD" --redact --no-banner --no-color . 2>&1 | tail -15
    GL_EXIT=${PIPESTATUS[0]}
    [ $GL_EXIT -eq 1 ] && { echo "⚠️ GITLEAKS_2ND: possible secret in outgoing commits -- a separate engine's warning (does not block; list it in the Step 8 report, and add # gitleaks:allow on the line if it is a false positive)"; GL_WARN=1; }
    [ $GL_EXIT -eq 124 ] && { echo "⚠️ GITLEAKS_2ND: timeout (90s) -- result unknown (does not block)"; GL_WARN=1; }
    [ $GL_EXIT -ne 0 ] && [ $GL_EXIT -ne 1 ] && [ $GL_EXIT -ne 124 ] && { echo "⚠️ GITLEAKS_2ND: scanner error exit=$GL_EXIT -- result unknown (does not block)"; GL_WARN=1; }
  fi
  if [ -n "$STAGED_FILES" ]; then
    ${TMO:+$TMO 60} "$GITLEAKS_BIN" git --staged --redact --no-banner --no-color . 2>&1 | tail -15
    GL_EXIT=${PIPESTATUS[0]}
    [ $GL_EXIT -eq 1 ] && { echo "⚠️ GITLEAKS_2ND: possible secret in staged changes (does not block)"; GL_WARN=1; }
    [ $GL_EXIT -ne 0 ] && [ $GL_EXIT -ne 1 ] && { echo "⚠️ GITLEAKS_2ND: staged scan error or timeout exit=$GL_EXIT -- result unknown (does not block)"; GL_WARN=1; }
  fi
  [ $GL_WARN -eq 0 ] && echo "gitleaks second scan: clean (outgoing ${OUTGOING_COMMIT_COUNT:-0} commit(s)$( [ -n "$STAGED_FILES" ] && echo ' + staged'))"
fi

# Persist core vars so a later Step (3/3.5/4/5a) running in a fresh bash call
# (see the note above this block) can restore them. Stored under .git/
# (git-dir, not the worktree), so it is never staged or committed.
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
{
  printf 'STAGED_FILES=%q\n' "$STAGED_FILES"
  printf 'STAGED_DIFF=%q\n' "$STAGED_DIFF"
  printf 'OUTGOING_DIFF=%q\n' "$OUTGOING_DIFF"
  printf 'COMBINED_DIFF=%q\n' "$COMBINED_DIFF"
  printf 'PYBIN=%q\n' "$PYBIN"
  printf 'CURRENT_BRANCH=%q\n' "$CURRENT_BRANCH"
  printf 'DIFF_LINES=%q\n' "$DIFF_LINES"
  printf 'FILE_COUNT=%q\n' "$FILE_COUNT"
  printf 'MERGE_BASE=%q\n' "$MERGE_BASE"
  printf 'OUTGOING_MODE=%q\n' "$OUTGOING_MODE"
  printf 'OUTGOING_COMMIT_COUNT=%q\n' "$OUTGOING_COMMIT_COUNT"
  printf 'PUSH_FILES=%q\n' "$PUSH_FILES"
  printf 'PUSH_DIFF_LINES=%q\n' "$PUSH_DIFF_LINES"
  printf 'SECRETS_EXIT=%q\n' "$SECRETS_EXIT"
  printf 'STATE_KEY=%s\n' "$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)"  # ties the file to this exact push
} > "$STATE_FILE"
```

The preferred scanner (`scripts/scan_secrets.py`) covers **14 patterns** across three categories:
- **Credentials** (f1–f10): AWS keys, private keys, connection-string passwords, hardcoded assignments (quoted/unquoted), platform tokens (Slack, GitHub 6 types, Stripe live), Dockerfile ENV secrets, Google/Gemini API keys, npm auth tokens, LLM provider keys (Anthropic/OpenAI/HuggingFace/Replicate/Groq), Azure Storage/SAS/connection strings.
- **Injection & exfiltration channels** (f11–f13): embedded prompt-injection strings (supply-chain prompt attack), non-standard package install sources, Slack incoming webhook URLs.
- **Code integrity** (f_merge): unresolved merge conflict markers.

**Parity note**: `scripts/scan_secrets.py` began as a straight port of the Perl scanner but has since received independent anti-evasion hardening (Unicode/homoglyph normalization, reversed-line re-scan) not back-ported to `scan_secrets.pl`. Pattern coverage has also diverged: `scan_secrets.pl` has f11 and f12 but **lacks f13** (Slack webhook detection), so it covers 13 patterns, not 14 — the two implementations are **not** guaranteed to have identical coverage. Both support the same-line allow marker. Treat `scan_secrets.py` as the more complete/current scanner where they diverge; when only Perl is available, say so in the Step 8 report (reduced coverage).

**Design note**: the scanner intentionally scans only **added (`+`) lines**, not removed (`-`) lines — this avoids blocking commits that are *removing* a secret. Merge conflict markers are an exception and checked on all lines. This applies identically to every input inside `$COMBINED_DIFF` (staged diff, per-commit patches, net diff).

**Empty check**: only stop when `$STAGED_FILES` **and** `$OUTGOING_COMMIT_COUNT` are **both** empty/zero (matches the Discard If condition above). If staged is empty but outgoing has 1+ commits, the scan above already ran against `$COMBINED_DIFF` (staged + outgoing) — carry that `$SECRETS_EXIT` forward into Step 2 rather than stopping early. This closes the "already committed, staging is empty" gap: a secret committed earlier in the session but never (re-)staged used to be treated as "nothing to check" and skipped entirely.

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
| NEW_DATA_FILE (new `.db`/`.sqlite`/`.sqlite3`/`.db-wal`/`.db-shm`) | `git rm --cached <file>` and add it to `.gitignore`. If it is an intended test fixture, move it under `tests/` or `fixtures/`. |
| False positive (scanner's own pattern-definition line, a synthetic test fixture) | Append `# scan-secrets: allow` (or the pre-existing `# gitleaks:allow` convention; `//`, `/*`, `--` and `;` comment leaders also work) to that **same line only**. Both scanners honor it. Every skip is counted and printed as `[ALLOW] N ...` so it can't hide a real finding silently — never add this marker to a line that holds an actual value. |

**How to clear a block** (this skill never stages, commits or rewrites history; the user does):
1. A secret still only in the working tree or staged: remove it, then tell the user to `git add <file>` and commit the fix. The scan reads staged and committed content, so an unstaged edit is invisible to the re-scan.
2. A secret already inside an outgoing commit (including one a later commit removed): deleting it now does not remove it from that commit, and the push would still send it. Tell the user to rewrite that commit themselves (for example an interactive rebase or amend) and to **rotate the secret**, since it must be treated as exposed. Locate the commit with `git log -p --no-merges "$MERGE_BASE"..HEAD`, or `git log -S'<fragment>' "$MERGE_BASE"..HEAD` once a fragment is known. The skill never rewrites history.
3. Then re-run Step 1 from the top.

**Re-scan required after any fix**: once `SECRETS_EXIT=1` has fired, do not push on a hand-checked "that was a false positive" judgment alone — re-run Step 1's scan after fixing/marking the finding and paste the resulting `SECRETS_EXIT=0` output into the Step 8 report before pushing.

**SECRETS_EXIT=0 AND only `*.md` / `docs/**` changed** → fast exit: run Step 3.5 first if a public-mirror scrub is configured, then push directly and skip all agents.

**Otherwise** → continue to Step 3.

## Step 3: Supply Chain & Infrastructure Check (WARN — never blocks)

Scan `$PUSH_FILES` (staged + outgoing) and list findings in the final report:

- **Package manifests** (`package.json`, `yarn.lock`, `pnpm-lock.yaml`, `requirements.txt`, `Gemfile`, `go.mod`, `Cargo.toml`): list all **added** dependencies. Flag misspelled or unfamiliar names as potential typosquats.
- **Infrastructure files** (`Dockerfile`, `docker-compose*.yml`, `*.tf`, `*.yaml`/`*.yml` in `k8s/` or `infra/`, `nginx.conf`): flag any ENV, ARG, or environment sections for human review.
- **Python CVE scan** (`pip-audit`, optional tool): run once per changed `requirements*.txt` (`-r <file>`) or `pyproject.toml` when `pip-audit` is installed; skipped with a note otherwise. WARN only — never blocks.
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
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ Step 3 skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
else
  CHANGED_REQS=$(printf '%s\n' "$PUSH_FILES" | grep -E "(requirements.*\.txt|pyproject\.toml)$")
  if [ -n "$CHANGED_REQS" ] && command -v pip-audit >/dev/null 2>&1; then
    # Audit each changed manifest itself: a bare `pip-audit` audits the current environment, not the project.
    # requirements*.txt -> `-r <file>`; pyproject.toml -> its directory. setup.py changes are not audited (note it in the report).
    while IFS= read -r f; do
      [ -z "$f" ] && continue
      case "$f" in
        *pyproject.toml) AUDIT_RAW=$(pip-audit "$(dirname "$f")" 2>&1); AUDIT_EXIT=$? ;;
        *)               AUDIT_RAW=$(pip-audit -r "$f" 2>&1); AUDIT_EXIT=$? ;;
      esac
      # exit code captured before truncating -- piping into $(... | tail) would capture tail's exit code
      AUDIT_OUT=$(printf '%s\n' "$AUDIT_RAW" | tail -20)
      [ $AUDIT_EXIT -ne 0 ] && echo "pip-audit ($f): $AUDIT_OUT"
    done <<EOF
$CHANGED_REQS
EOF
  fi
fi
```

> **Install**: `pip install pip-audit` (Python native, no Go binary needed — preferred over osv-scanner for Python projects)

> **Further reading**: the 9-IOC checklist above is a lightweight, offline heuristic run inline by this skill — it is not a substitute for dedicated supply-chain tooling. For broader, actively maintained coverage (SBOM generation, provenance attestation, dependency health scoring), see the [OpenSSF Scorecard](https://github.com/ossf/scorecard) project and the [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/).

## Step 3.5: Public-Mirror Scrub (WARN — never blocks, conditional)

A push-time backstop for any write-time reminders you run elsewhere (e.g. a
pre-commit leak scanner) — different layers, so if one is bypassed the other
still catches it (defense in depth). Useful if this repo is a curated public
mirror of a private source (internal identifiers, ticket numbers, or
internal-only tool paths can leak into a public-facing copy through
copy-paste).

**Trigger condition**: only runs when `git remote get-url origin` matches a
repo you've configured as a known public mirror. Private/internal repos
should skip this step entirely.

```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }
[ -z "$COMBINED_DIFF" ] && COMBINED_DIFF="$STAGED_DIFF
$OUTGOING_DIFF"  # normally restored from the state file; this fallback lacks the per-commit patches

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ Step 3.5 skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
else
ORIGIN_URL=$(git remote get-url origin 2>/dev/null || echo "")
# Replace the pattern below with your own public-mirror repo name(s), and the YOUR_INTERNAL_TERM_* placeholders with your own vocabulary.
if echo "$ORIGIN_URL" | grep -qiE "YOUR_PUBLIC_MIRROR_REPO_NAME_HERE"; then
  # (a) org-identifier / internal-jargon term list, applied to the ADDED lines of everything
  # the push carries ($COMBINED_DIFF = staged + outgoing commits) -- reuse your leak-scan
  # script's pattern list if you have one, e.g. internal ticket IDs, private absolute paths,
  # internal-only repo names.
  printf '%s\n' "$COMBINED_DIFF" | grep -E '^\+' | grep -vE '^\+\+\+' | grep -nE "YOUR_INTERNAL_TERM_1|YOUR_INTERNAL_TERM_2" \
    && echo "⚠️ PUBLIC_MIRROR_SCRUB: possible internal identifier/section-number string found — verify before pushing to public mirror (${ORIGIN_URL})"
  # (b) binary sweep — staged non-text assets
  BINARY_FILES=$(git diff --staged --name-only --diff-filter=A | while read -r f; do
    file --mime-encoding "$f" 2>/dev/null | grep -q "binary" && echo "$f"
  done)
  [ -n "$BINARY_FILES" ] && echo "⚠️ PUBLIC_MIRROR_SCRUB: new binary file(s) — confirm these are intentional public assets: $BINARY_FILES"
  # (c) a surface the diff won't catch — internal identifiers baked into the branch name itself
  echo "$CURRENT_BRANCH" | grep -qiE "YOUR_INTERNAL_TERM_1|YOUR_INTERNAL_TERM_2" \
    && echo "⚠️ PUBLIC_MIRROR_SCRUB: possible internal identifier in branch name — this surface isn't visible in the diff"
fi
fi
```

WARN-only (advisory, never blocks) — mirrors the same explicit non-blocking
decision as the write-time leak scanner it backstops. Adjust the grep
patterns to whatever your own internal-only vocabulary actually is.

## Step 4: Build & Test (Fail Fast)

Detect changed languages first, then run the project's own test/build command for each language that has changed files (the whole configured suite, not a per-file selection). Skip entirely for config, docs, or style-only commits.

**Gate on the exit codes**: every command below records its exit code (`PYTEST_EXIT`, `GO_TEST_EXIT`, `BUILD_EXIT`, `JS_TEST_EXIT`, `LINT_EXIT`, `GO_VET_EXIT`, `ESLINT_EXIT`) and echoes it. The tail of the output alone is not the verdict. A printed `❌ BLOCK` line means stop: do not run the later steps and do not push. The only non-zero code that is not a block is pytest exit 5 (no tests collected), which is reported as SKIPPED.

```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ Step 4 skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
else
  CHANGED_PY=$(echo "$PUSH_FILES" | grep -E "\.py$")
  CHANGED_JS=$(echo "$PUSH_FILES" | grep -E "\.(ts|tsx|js|jsx)$")
  CHANGED_GO=$(echo "$PUSH_FILES" | grep -E "\.go$")
  {
    printf 'CHANGED_PY=%q\n' "$CHANGED_PY"
    printf 'CHANGED_JS=%q\n' "$CHANGED_JS"
    printf 'CHANGED_GO=%q\n' "$CHANGED_GO"
  } >> "$STATE_FILE"  # append so a later split-off Step 5a call can restore these too
fi
```

**Python** — run when `.py` files changed and a test runner is configured:
```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES$CHANGED_PY" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ Python test step skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
elif [ -z "$CHANGED_PY" ]; then
  echo "⚠️ CHANGED_PY empty -- nothing to test"
elif [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ] || [ -f "pytest.ini" ] || [ -f "setup.cfg" ] || [ -f "tox.ini" ] || [ -f "Pipfile" ] || [ -f "poetry.lock" ] || git ls-files | grep -qE '(^|/)(test_[^/]+|[^/]+_test)\.py$'; then
  # Trigger widened beyond pyproject.toml/setup.py/requirements.txt -- repos using only
  # pytest.ini/setup.cfg/tox.ini/Pipfile/poetry.lock, or with tracked test_*.py/*_test.py
  # files and no manifest at all, previously skipped pytest silently.
  TEST_START=$(date +%s)
  TMO=$(command -v timeout || command -v gtimeout)
  PYTEST_OUTPUT=$(${TMO:+$TMO 120} pytest -q 2>&1)
  PYTEST_EXIT=$?
  echo "$PYTEST_OUTPUT" | tail -20
  echo "PYTEST_EXIT=$PYTEST_EXIT"
  case "$PYTEST_EXIT" in
    0) ;;
    5) echo "⚠️ pytest collected no tests (exit 5) -- report Tests as SKIPPED, not PASS" ;;
    *) echo "❌ BLOCK: pytest failed (exit $PYTEST_EXIT; 124 = timed out, 127 = pytest not installed) -- stop here, do not run Step 5/6 or push" ;;
  esac
  TEST_TIME=$(($(date +%s) - TEST_START))

  # Test-count floor (WARN-only, pattern credited to CopilotKit/openbot's scripts/test-ci.ts) —
  # exit=0 (all passed) doesn't mean nothing broke: if a whole file silently drops out of
  # collection (e.g. an import-time exception), the suite just got smaller and still "passes".
  # Track the previous run's passed-count in a local, gitignored state file and compare —
  # warn only on a sharp drop; a first run (no state file yet) just records and passes.
  PASSED_COUNT=$(echo "$PYTEST_OUTPUT" | grep -oE "[0-9]+ passed" | tail -1 | grep -oE "^[0-9]+")
  FLOOR_FILE="$(git rev-parse --git-dir)/pre-push-test-count-floor.json"  # was PWD-relative .harness/test-count-floor.json -- could get committed in other repos; .git/ is never tracked
  if [ -n "$PASSED_COUNT" ]; then
    if [ -f "$FLOOR_FILE" ]; then
      LAST_COUNT=$(grep -oE '"count": *[0-9]+' "$FLOOR_FILE" | grep -oE '[0-9]+' | tail -1)
      if [ -n "$LAST_COUNT" ] && [ "$LAST_COUNT" -gt 0 ]; then
        DROP_PCT=$(( (LAST_COUNT - PASSED_COUNT) * 100 / LAST_COUNT ))
        [ "$DROP_PCT" -ge 10 ] && echo "⚠️ TEST_COUNT_FLOOR: ${PASSED_COUNT} passed (down ${DROP_PCT}% from ${LAST_COUNT} last run) — a file may have silently dropped out of collection. Ignore if intentional deletion, otherwise check for a collection error."
      fi
    fi
    mkdir -p "$(dirname "$FLOOR_FILE")"
    printf '{"count": %s, "updated": "%s"}\n' "$PASSED_COUNT" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$FLOOR_FILE"
  fi
else
  echo "➖ Python test runner config not found -- skipping pytest"
fi
```

**Go** — run when `.go` files changed and `go.mod` exists:
```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES$CHANGED_GO" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ Go test step skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
elif [ -z "$CHANGED_GO" ]; then
  echo "⚠️ CHANGED_GO empty -- nothing to test"
elif [ -f "go.mod" ]; then
  TEST_START=$(date +%s)
  TMO=$(command -v timeout || command -v gtimeout)
  ${TMO:+$TMO 120} go test ./... 2>&1 | tail -20
  GO_TEST_EXIT=${PIPESTATUS[0]}  # not $? — that would capture tail's exit code, not go test's
  echo "GO_TEST_EXIT=$GO_TEST_EXIT"
  [ "$GO_TEST_EXIT" -ne 0 ] && echo "❌ BLOCK: go test failed (exit $GO_TEST_EXIT; 124 = timed out) -- stop here, do not run Step 5/6 or push"
  TEST_TIME=$(($(date +%s) - TEST_START))
else
  echo "➖ go.mod not found -- skipping go test"
fi
```

**JS/TS** — build then test when source files changed:
```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES$CHANGED_JS" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ JS/TS build&test step skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
elif [ -z "$CHANGED_JS" ]; then
  echo "⚠️ CHANGED_JS empty -- nothing to build/test"
elif [ -f "package.json" ]; then
  TMO=$(command -v timeout || command -v gtimeout)
  BUILD_START=$(date +%s)
  # Build only if package.json defines a build script (otherwise `npm run build` fails on every repo without one).
  if node -e "const p=require('./package.json');process.exit(p.scripts&&p.scripts.build?0:1)" 2>/dev/null; then
    ${TMO:+$TMO 120} npm run build 2>&1 | tail -30
    BUILD_EXIT=${PIPESTATUS[0]}  # not $? — that would capture tail's exit code, not the build's
    echo "BUILD_EXIT=$BUILD_EXIT"
    [ "$BUILD_EXIT" -ne 0 ] && echo "❌ BLOCK: build failed (exit $BUILD_EXIT; 124 = timed out) -- stop here, do not run Step 5/6 or push"
  else
    echo "➖ no build script in package.json -- skipping build"
  fi
  BUILD_TIME=$(($(date +%s) - BUILD_START))
  if node -e "const p=require('./package.json');process.exit(p.scripts&&p.scripts.test?0:1)" 2>/dev/null; then
    ${TMO:+$TMO 60} npm test -- --passWithNoTests 2>&1 | tail -20
    JS_TEST_EXIT=${PIPESTATUS[0]}  # not $? — that would capture tail's exit code, not the test run's
    echo "JS_TEST_EXIT=$JS_TEST_EXIT"
    [ "$JS_TEST_EXIT" -ne 0 ] && echo "❌ BLOCK: npm test failed (exit $JS_TEST_EXIT; 124 = timed out) -- stop here, do not run Step 5/6 or push"
  fi
else
  echo "➖ package.json not found -- skipping build/test"
fi
```

Any `❌ BLOCK` → stop immediately. Read the failing output and fix it (or dispatch a `build-error-resolver` agent if you have one: optional, not included in this repo; `/setup` can generate one), then restart from Step 1.

## Step 5: Lint Gate (Direct → AI)

Two sub-steps in order. Direct lint runs first (fast, no token cost). AI layer runs after.

### 5a: Direct Lint (Blocking)

Run only for changed files of the matching language.

**Python** — `ruff` preferred, `flake8` fallback:
```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES$CHANGED_PY" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ Python lint step skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
elif [ -z "$CHANGED_PY" ]; then
  echo "⚠️ CHANGED_PY empty -- nothing to lint"
else
  # printf | tr '\n' '\0' | xargs -0 keeps paths with spaces intact and works on GNU and BSD xargs.
  # PIPESTATUS[2] is xargs here (printf | tr | xargs | tail) -- xargs maps the linter's own
  # nonzero exit to 123; any nonzero from xargs still means the linter found issues, so it is
  # treated as BLOCK below.
  TMO=$(command -v timeout || command -v gtimeout)
  # ruff blocks only on findings located on lines this push changed (scripts/ruff_changed_lines.py).
  # Whole-file ruff on a large push reports mostly old findings that the push did not touch. The helper
  # is fail-closed: a ruff, JSON or diff error is exit 2 = BLOCK, a finding on a changed line or a
  # syntax error is exit 1 = BLOCK. If the helper cannot be found, or MERGE_BASE is empty (no upstream
  # or origin/HEAD, so committed changed lines are unknown), fall back to whole-file ruff, the stricter way.
  RUFF_LINES="${CLAUDE_SKILL_DIR}/scripts/ruff_changed_lines.py"
  PY="${PYBIN:-python3}"
  if command -v ruff >/dev/null 2>&1 && [ -f "$RUFF_LINES" ] && [ -n "$MERGE_BASE" ]; then
    # pipeline = printf | python | tail, so PIPESTATUS[1] is the python helper (not [0], not tail)
    printf '%s\n' "$CHANGED_PY" | ${TMO:+$TMO 60} "$PY" "$RUFF_LINES" --base "$MERGE_BASE" 2>&1 | tail -20; LINT_EXIT=${PIPESTATUS[1]}
  elif command -v ruff >/dev/null 2>&1; then
    printf '%s\n' "$CHANGED_PY" | tr '\n' '\0' | xargs -0 ${TMO:+$TMO 30} ruff check 2>&1 | tail -20; LINT_EXIT=${PIPESTATUS[2]}
  elif command -v flake8 >/dev/null 2>&1; then
    printf '%s\n' "$CHANGED_PY" | tr '\n' '\0' | xargs -0 ${TMO:+$TMO 30} flake8 2>&1 | tail -20; LINT_EXIT=${PIPESTATUS[2]}
  else
    echo "➖ no ruff or flake8 found -- Python lint skipped"
  fi
  if [ -n "${LINT_EXIT+x}" ]; then
    echo "LINT_EXIT=$LINT_EXIT"
    [ "$LINT_EXIT" -ne 0 ] && echo "❌ BLOCK: Python lint failed (exit $LINT_EXIT) -- fix, then restart from Step 1"
  fi
fi
```

**Go** — `go vet` (always available):
```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES$CHANGED_GO" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ Go vet step skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
elif [ -z "$CHANGED_GO" ]; then
  echo "⚠️ CHANGED_GO empty -- nothing to lint"
else
  TMO=$(command -v timeout || command -v gtimeout)
  ${TMO:+$TMO 30} go vet ./... 2>&1 | tail -20; GO_VET_EXIT=${PIPESTATUS[0]}  # not $? — tail's exit code
  echo "GO_VET_EXIT=$GO_VET_EXIT"
  [ "$GO_VET_EXIT" -ne 0 ] && echo "❌ BLOCK: go vet failed (exit $GO_VET_EXIT) -- fix, then restart from Step 1"
fi
```

**JS/TS** — `eslint` if config file present:
```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES$CHANGED_JS" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }

if [ "${SECRETS_EXIT:-1}" -ne 0 ]; then
  echo "⏭️ ESLint step skipped -- SECRETS_EXIT=${SECRETS_EXIT:-unset} (secrets scan failed/unknown, push already BLOCKED)"
elif [ -z "$CHANGED_JS" ]; then
  echo "⚠️ CHANGED_JS empty -- nothing to lint"
elif ls .eslintrc* eslint.config* 2>/dev/null | head -1 | grep -q .; then
  # tr+xargs -0 keeps paths with spaces intact. PIPESTATUS[2] is xargs here
  # (printf | tr | xargs | tail pipeline) -- xargs maps eslint's nonzero exit to 123; treat as BLOCK.
  TMO=$(command -v timeout || command -v gtimeout)
  printf '%s\n' "$CHANGED_JS" | tr '\n' '\0' | xargs -0 ${TMO:+$TMO 30} npx eslint 2>&1 | tail -20; ESLINT_EXIT=${PIPESTATUS[2]}  # not $? — tail's exit code
  echo "ESLINT_EXIT=$ESLINT_EXIT"
  [ "$ESLINT_EXIT" -ne 0 ] && echo "❌ BLOCK: eslint failed (exit $ESLINT_EXIT) -- fix, then restart from Step 1"
else
  echo "➖ No eslint config found -- skipping eslint"
fi
```

Any `❌ BLOCK` from 5a → stop; fix errors (then re-run from Step 1) before continuing to 5b.

### 5b: Quick Review Gate (AI, Serial)

**Skip if `$PUSH_DIFF_LINES` < 50** (staged + outgoing changed lines) — tiny diffs have negligible type/lint risk.

Run a quick type/lint review for errors that static tools miss: use code-autopsy's FAST MODE (shipped in this repo) inline, or dispatch the optional `code-reviewer` agent (not included in this repo; `/setup` can generate one) or a general-purpose subagent with the prompt below. FAIL → fix before continuing.

```
Review the following staged diff for type errors and lint issues only.
Do NOT read entire files unless absolutely necessary.

<diff>
[paste the push diff: git diff --staged plus git diff $MERGE_BASE..HEAD]
</diff>
```

## Step 6: Launch Review Agents in Parallel

> **Agents are optional and not included in this repo**: code-reviewer, security-reviewer, database-reviewer and refactor-cleaner are your own agents (`/setup` can generate code-reviewer, security-reviewer and database-reviewer). When one is not installed, use this fallback: dispatch a general-purpose subagent with the "Agent prompt template" below, adding the agent's focus line (code-reviewer: correctness, dead code, duplication; security-reviewer: injection, authorization, secrets, unsafe exec or deserialization; database-reviewer: schema, migration safety, indexes, injection). For the code-reviewer role you can also use code-autopsy (FAST MODE for a quick pass, full mode otherwise). If you do none of this, mark the review `⚠️ SKIPPED (agent not installed)` in the Step 8 report.

> **Spawn all applicable agents in a SINGLE response turn** using concurrent subagent calls — never sequentially. Parallel execution cuts total wall time by the duration of the slowest agent.

**Large diff — deterministic bundling** (`$PUSH_DIFF_LINES` > 500 OR `$PUSH_FILES` has more than 10 files):

In large changesets, agents choosing which files to read on their own leads to coverage gaps — coverage is guaranteed by **structure, not agent integrity**:

1. **Deterministic bundle split**: group `$PUSH_FILES` by top-level directory/module. Natural pairs (source+test, implementation+config) go in the same bundle. Bundle size guide: diff ≤ ~300 lines or ≤ 5 files; if larger, re-split.
2. **One reviewer per bundle**: dispatch code-reviewer once per bundle — each agent receives **only its bundle's diff** (isolated context, never send full diff). Parallel cap 5 — if 6+ bundles, batch in groups of 5.
3. **Coverage validation (deterministic)**: before dispatch, verify `union of bundle files == all of $PUSH_FILES` by count. Mismatch → add missing files to final bundle. Never dispatch without this check.
4. **Cross-bundle joint pass**: after all per-bundle reviews complete, forward the union of each bundle's finding-list summary to a single reviewer (code-reviewer) for one final pass across bundle boundaries. This catches fragmentation — a change deliberately or accidentally split across bundles can look safe in each isolated review but be unsafe once combined. Do not declare a large-diff review complete without this joint pass.
5. **Deterministic claim verification** (optional, environment-specific): save the joint-pass output (finding list with file/line-range citations — e.g. `【F:path†Lstart-Lend】`-style anchors) to a file, then run a claim-verification script against it if your setup has one — for example `python "$HOME/.claude/scripts/verify_review_claims.py" --review <finding-list-file> --repo-root .`. It should check, per finding: (a) the cited file exists in the staged diff, (b) the cited line range overlaps the diff hunk, and (c) an optional grep cross-check passes — labeling each finding `CONFIRMED` or `UNVERIFIED-CLAIM`. Keep `UNVERIFIED-CLAIM` findings open for re-review before Step 7 Gate Check — do not auto-downgrade them. This script is optional and environment-specific: if `~/.claude/scripts/verify_review_claims.py` (or your own equivalent) is not present, skip this sub-step and proceed with the cross-bundle joint pass alone; note the skip in the Step 8 report.
6. **Opt-in high-risk gap-sweep second pass**: a single review pass tends to miss categories like a guard lost during a move/extract, a dataclass default evaluated once, `hash()` non-determinism, a shrunk lock scope, a side-effecting predicate, asymmetric test setup/teardown, or a flipped config default are exactly the kind of thing a first pass tends to miss structurally. **Only when `$PUSH_DIFF_LINES` > 500 OR `$PUSH_FILES` has more than 10 files (same trigger as the large-diff bundling above)** — dispatch one fresh code-reviewer instance dedicated solely to this miss-category checklist (not re-checking findings already surfaced), capped at 8 new findings (empty result if none — no padding). It costs a second pass, so it's opt-in and scoped to large/high-risk diffs only — don't apply it to small diffs.
7. **Conditional agents** (security/database/refactor): follow existing trigger rules, but only pass diff for bundles matching those triggers.
8. **Multi-angle parallel re-attack** (opt-in, not the default): a 12-question review (code-autopsy's Q1-Q12) already sweeps correctness/resource-management/security/design/convention in one pass, so this doesn't belong in the default pipeline. For changes that are extremely hard to reverse (a merged DB migration, payment/funds logic) — **only when the user explicitly asks for it** — dispatch 5 parallel code-reviewer instances, each pinned to one of those five lenses, to re-attack the same diff.

Small diff (≤500 lines AND ≤10 files): use existing approach, send full diff to each agent. Bundling overhead not needed.

### Always run

| Agent | Suggested model | Role |
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

Trigger `database-reviewer` (sonnet): `prisma/**`, `**/migrations/**`, `**/db*`, `*.sql`, **or** a non-test `.py` file whose **added lines** contain SQL schema or write statements. Path patterns alone miss most code that touches a database (a module such as `data/store.py` matches none of them). Decide this with the deterministic block below. Read-only `sqlite3` or `.execute(` calls do not trigger on their own, because that is far too noisy. When it triggers, pass database-reviewer only the diffs of the files that contain the SQL.

```bash
STATE_FILE="$(git rev-parse --git-dir)/pre-push-vars.sh"
[ -z "$PUSH_FILES" ] && [ -f "$STATE_FILE" ] && { grep -qxF "STATE_KEY=$(git rev-parse HEAD 2>/dev/null):$(git diff --staged | git hash-object --stdin)" "$STATE_FILE" && . "$STATE_FILE" || { echo "⚠️ pre-push-vars.sh does not match this push (HEAD or staged diff changed since Step 1) -- rerun from Step 1"; SECRETS_EXIT=1; }; }
DB_PY=$(printf '%s\n' "$PUSH_FILES" | grep -E '\.py$' | grep -vE '(^|/)tests?/')
DB_SQL_FILES=""
if [ -n "$DB_PY" ]; then
  while IFS= read -r f; do
    { git diff --staged -U0 --no-color -- "$f"; [ -n "$MERGE_BASE" ] && git diff -U0 --no-color "$MERGE_BASE"..HEAD -- "$f"; } \
      | grep -E '^\+' | grep -vE '^\+\+\+' \
      | grep -qiE 'executescript|CREATE +(TABLE|INDEX|VIEW|UNIQUE)|ALTER +TABLE|DROP +(TABLE|INDEX|VIEW)|INSERT +(OR +[A-Za-z]+ +)?INTO|UPDATE +[A-Za-z_]+ +SET|DELETE +FROM|PRAGMA' \
      && DB_SQL_FILES="$DB_SQL_FILES$f
"
  done <<EOF
$DB_PY
EOF
fi
if [ -n "$DB_SQL_FILES" ]; then echo "database-reviewer TRIGGER (SQL in added lines):"; printf '%s' "$DB_SQL_FILES"; else echo "database-reviewer: SQL-in-diff trigger not matched"; fi
```

Test paths (`tests/`) are excluded: a `CREATE TABLE` in a temporary test fixture is not a schema change. A non-match here does not cancel the path-pattern triggers above (they are OR).

Trigger `refactor-cleaner` (sonnet): 10+ files changed, or user explicitly requested refactoring

**Agent prompt template** (intent-passing — distinguish intentional decisions from mistakes to reduce false positives):

```
Review the following staged diff. Focus on changed lines.
Only read full files if you need more context.

<intent>
[What the user aimed to achieve in this change — verbatim from session conversation. Goal + consciously made decisions/trade-offs + intentionally excluded scope. Not a diff explanation. Do not leave blank — blank intent causes reviewers to misclassify intentional choices as mistakes.]
</intent>

<diff>
[paste the push diff: git diff --staged plus git diff $MERGE_BASE..HEAD]
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

**Three-state false-positive gate**: for pattern classes prone to false positives (e.g. PII/name-like matches), don't force a binary hard-block/skip decision — present each hit to the user individually. If the user confirms it's a false positive or non-sensitive, record a one-line reason and let it through (stays auditable in the report). If it's real, require removal. Blanket bypass without a stated reason is not allowed. Low-false-positive hard-block classes (the credential patterns f1-f10) remain immediate-block as before — this gate does not soften those.

**Fix loop** (Critical/High found):
1. Apply fixes with the Edit tool. These are working-tree edits only: tell the user to `git add` and commit them (this skill does not), because the scan and the reviewers read staged and committed content. A flaw that already sits in an outgoing commit needs that commit rewritten by the user (see "How to clear a block" in Step 2).
2. Re-run only the agent(s) that reported the issue, after the user has staged or committed the fix
3. Max 1 retry per agent
4. Still failing → halt and report exact issue + file location to user
5. **Skip-reason logging**: when a finding is knowingly left unfixed (superseded by a later feature change / genuinely out of scope / judged a false positive), record `SKIP_REASON: {finding} — {feature_change|out_of_scope|false_positive} — {one-line reason}` in the Step 8 report. No silent skips without a stated reason.

**Error Recovery**: if Step 6 agents or Bash tools fail:
- Classify: `tool_failure`
- Apply: retry same agent once → still fail:
  - **code-reviewer (Always run)**: instead of an outright skip, fall back to an inline abbreviated review — the pre-push executor itself reads the staged diff once, applying code-autopsy's FAST MODE bar (runtime bugs only, max 8 findings, no padding), and merges those findings into the Step 8 report. Note `⚠️ INLINE_FALLBACK: code-reviewer subagent unavailable — replaced with inline abbreviated review`.
  - **Conditional agents (security/database/refactor)**: as before, report `⚠️ TOOL_FAILURE: {agent} — manual review needed` and continue remaining steps. No silent failures.
- Step 8 report that line: explicitly note `⚠️ SKIPPED (tool_failure — {agent})` or `⚠️ INLINE_FALLBACK (code-reviewer)`.

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
- gitleaks 2nd (WARN): ✅ clean / ⚠️ GITLEAKS_2ND (N) / ➖ not installed — never a blocking reason
- Supply chain:      ✅ No new deps / ⚠️ N new packages (listed below)
- Build:             ✅ PASS (Xs) / ❌ FAIL (Xs) / ➖ SKIPPED (no source changes)
- Tests:             ✅ PASS (Xs) / ⚠️ SKIPPED / ❌ FAIL (N failed)
- Lint (direct):     ✅ PASS (Xs) / ❌ FAIL (N errors; ruff counts changed lines only) / ➖ SKIPPED (no linter found)
- Quick review:      ✅ PASS (Xs) / ❌ FAIL (N issues) / ➖ SKIPPED (<50 lines)
- code-reviewer:     ✅ PASS / ⚠️ N issues (X fixed, Y remaining)
- security-reviewer: ✅ PASS / ❌ N issues / ➖ NOT TRIGGERED
- database-reviewer: ✅ PASS / ⚠️ N issues / ➖ NOT TRIGGERED (say whether a path pattern or SQL-in-diff triggered it)
- refactor-cleaner:  ✅ PASS / ⚠️ N suggestions / ➖ NOT TRIGGERED

[Supply chain — new packages listed here if applicable]
[Secrets remediation steps listed here if blocked]

Overall: ✅ READY TO PUSH / ❌ BLOCKED — <reason>
```

Execute `git push` only when Overall = **READY TO PUSH**.

Once the pipeline ends (push succeeded or BLOCKED, either way), delete the persisted-variable file so a later push never reads this run's values (each step's key check is the first line of defense, this deletion is the second):
```bash
rm -f "$(git rev-parse --git-dir)/pre-push-vars.sh"
```

### Memory Sync Reminder (only when READY TO PUSH)

If push target files include memory path changes:

```
💡 Memory Sync: Code has changed.
   If you haven't run session-checkpoint yet, memory may be stale.
   Consider running /session-checkpoint before ending this session.
```

## Emergency Override

If the user explicitly says "skip review":
1. If the current branch is `main` or `master`, ask for an explicit "yes" first (Invariant 2 still applies).
2. Print: `⚠️ Pre-push pipeline bypassed by user request. Secrets scan and agent reviews were NOT run.`
3. Execute a plain `git push` (never `--force`). A request to force-push is not an Emergency Override trigger: tell the user this skill never force-pushes and that they must run it themselves.

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| `git push` (regular branch) | low | L1+L2+L3 |
| `git push` (main/master) | low | L1+L2+L3+L4 |
| `git push --force` | low | L1+L2 (deny recommended; this skill never runs it) |
| Secrets exposure (secrets scan FAIL) | **none** | L1+L2+L3+L4 (BLOCK) |

- **L1 (Invariants)**: secrets scan must pass, Critical/High issues must be fixed.
- **L2 (Tool Restriction)**: recommend deny `git push --force`, `--no-verify` in `settings.json` hooks.
- **L3 (User Approval)**: main/master branches require explicit "yes" confirmation. Emergency Override only with an explicit "skip review" (and, on main/master, an explicit "yes").
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
| `missing_data` | Scanner script / pytest missing | No scanner (`scan_secrets.py` / `scan_secrets.pl`): stop the push and tell the user (Key Assumption 1 — a push without a secrets scan is blocked). pytest missing: skip that check + note `⚠️`, and confirm with the user before pushing without it |
| `logic_inconsistency` | pytest passed but lint failed | Push only after all checks pass. Do not treat partial pass as sufficient |

---

## Invariants (never violate)

1. **Secrets scan always runs**: if SECRETS_EXIT=1, push BLOCKED. Even "just push" requests cannot bypass without Emergency Override. Violation → credentials permanently in git history, entire remote repo contaminated.

2. **Protected branch check**: main/master pushes require explicit "yes". Violation → unreviewed code flows directly to production branch.

3. **Critical/High blocks push**: if agent review finds Critical/High, no push without fix. Medium: fix within 5 min or add TODO tag. Violation → known vulnerabilities deployed to remote.

4. **Added lines only scanned**: `-` (removed) lines are not scanned. Violation → secret removal commits get BLOCKED, cleanup becomes impossible.

5. **Re-scan after a block, don't eyeball it**: once `SECRETS_EXIT=1` has fired, only push after re-running Step 1's scan and getting `SECRETS_EXIT=0` -- a manual "that's a false positive" judgment without a fresh scan run is not sufficient. Violation → a genuine finding gets waved through on a hurried visual check.

These rules are unconditional. Emergency Override applies only when the user explicitly says "skip review".

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [BASH] scan secrets in the staged diff and every outgoing commit (added lines only) | Create or modify commits |
| [BASH] run the project's own test command when files of that language changed (whole configured suite) | Run test suites for languages with no changed files |
| [AGENT] parallel agent reviews (code/security/db/refactor; optional agents) | Modify code directly (except working-tree fixes in the fix loop; the user stages and commits them) |
| [BASH] check protected branches (main/master) | Modify git history or rebase |
| [BASH] execute push (all gates passed) | `--force` or `--no-verify` push, or rewrite a commit to remove a secret |
