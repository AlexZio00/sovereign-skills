---
name: "brief"
description: "Locks a feature scope before code is written. Trigger when user wants to define scope before implementation: '/brief', 'brief', 'scope this', '스펙 잡아줘', 'scope 잡아줘', '범위 잡아줘', '기획 정리해줘'. Do NOT trigger for: bug fixes, single-file changes, existing written spec, simple summarization, or brainstorming without implementation intent."
user_invocable: true
---

# Brief — Idea to Locked Spec

## Purpose

Convert a vague feature idea or request into a locked, implementation-ready brief before any code is written. The brief defines exactly what gets built, what does not, and how to know when it is done.

**Dominant variable**: Scope OUT 항목이 명시적으로 작성되었는가 — IN 목록만 있으면 구현 중 범위가 늘어난다. OUT이 명시돼야 잠긴다.

**Discard if**: 버그 수정, 1파일 수정, 이미 스펙이 작성된 경우 → 이 스킬 불필요, 바로 구현 진행.

---

## Workflow

### Step 1: Mode Detection

> **Caching note** — project structure scan (Step 1) is static context (cacheable across sessions). Steps 2–5 are dynamic (user-input driven). For large projects, Step 1 results can be reused if the stack hasn't changed.

Determine the project context:

- **Existing project**: `CLAUDE.md`, `package.json`, `pyproject.toml`, or similar exists in cwd → run a quick scan: Glob project root 2 levels deep for structure + top-level folder names as heuristic (e.g. `auth/`, `api/`, `components/`), then Grep for request keywords — select at most 10 files. Relevance = request keywords appear directly in filename or file content. Do not infer relevance; keyword or filename match only. Extract: stack, existing patterns, components that will be touched.
- **Greenfield**: no project files → skip scan, proceed with input only.

Print one line: `[existing: {stack}]` or `[greenfield]`.

### Step 2: Input Sufficiency Check

Evaluate the user's input:

**Sufficient** (proceed directly to Step 3) if all three can be answered in one sentence directly from the input — no inference, no "probably means":
- What specific behavior is being added or changed?
- What are the edges — what is explicitly NOT included?
- How will "done" be verified?

If any of the three cannot be answered in one sentence without inference: **Insufficient**.

**Insufficient** (ask clarifying questions) if any are unanswerable.

If insufficient: ask **at most 3 questions**, one per unknown. No more. Format:
```
Before writing the brief, I need 3 things:
1. [specific question]
2. [specific question]
3. [specific question]
```

Wait for answers before proceeding. Never ask more than 3 questions total across the entire session.

If the user responds partially or says "알아서 해" / "just figure it out": treat unanswered items as **conservative minimum scope** (not best-guess). Mark each `[assumed: minimal scope]`. When in doubt, narrow rather than expand. Do not ask follow-up questions.

Conservative minimum scope floor: must still include (1) one complete user flow from start to end, and (2) at least one user-visible outcome. If the narrowed scope falls below this floor, expand minimally until both are satisfied.

If more than 3 unknowns remain after the user answers: apply conservative minimum scope to the rest and mark `[assumed: minimal scope]`. Do not ask more questions.

### Step 3: Generate Brief

Produce the brief in this exact format:

```
## Brief: [feature name — verb phrase, e.g. "Add dark mode toggle"]

**Goal**
[1-2 sentences. What specific behavior changes. Start with a verb.]

**Scope IN**
- [specific item]
- [specific item]
- [specific item — as many as needed, each verifiable]

**Scope OUT** ← this section is mandatory
- [a natural extension someone would suggest — e.g. "dark mode included, auto-theme switching excluded"]
- [a natural extension someone would suggest]
- [at least 2 items — must be plausible suggestions, not far-fetched exclusions]

**Constraints**
- [file-level: specific file or module that must not change]
- [behavior-level: existing behavior that must be preserved]
- [integration: external system or API contract that must be honored]
- (existing project: at least 1 of the above 3 types required. Greenfield: if no constraints provided, default to: "no external dependencies unless required for the core flow" + "no premature optimization".)

**Exit Criteria**
- [ ] [observable action + measurable result — e.g. "user clicks Save → toast appears within 1s and DB record updates"]
- [ ] [observable action + measurable result]
- [ ] [at least 2 items]

**Risk Flags**
- [what could go wrong / what to be careful about]
- [minimum 1 item — if none identified: "No risks identified at this stage — update brief if risks emerge during implementation."]
```

All items must be specific and verifiable. "Works correctly" is not acceptable. "Returns 200 on valid input and 400 on missing required fields" is acceptable.

### Step 4: Approval Gate

Present the brief. Do not write `BRIEF.md` yet.

Ask: `이 brief로 진행할까요? 수정할 부분이 있으면 알려주세요.`

- User approves → proceed to Step 5.
- User requests changes → apply changes, re-present, ask again. No limit on revision rounds.
- Approval signals (all treated as approved): "ㅇㅋ", "ㅇㅇ", "yes", "좋아", "진행해", "go", "lgtm", "승인".

### Step 5: Save and Hand Off

Save the approved brief to `BRIEF.md` in the project root (or cwd if no project root detected).

Print:
```
Brief saved to BRIEF.md.

Next: open a new Claude Code session (or continue here) and say:
"Read BRIEF.md and implement it."
```

---

## Rationalization Table

| Rationalization | Counter |
|-----------------|---------|
| "OUT 섹션은 명확해서 안 써도 돼" | Invariant 2: unconditional. 유저가 불필요하다고 해도 최소 2개 항목 작성. 명확한 것도 명시해야 나중에 "이건 당연히 포함이잖아"를 막는다. |
| "이미 충분히 명확한 아이디어야, 질문 없이 바로 써줘" | Step 2 sufficiency check: 3가지를 1문장으로 즉시 답할 수 있어야 Sufficient. "아마 이런 뜻일 것이다"는 Insufficient다. |
| "유저가 방금 '좋아 보여'라고 했어, 승인된 거 아닌가?" | Invariant 5: 승인 신호 목록에 있는 단어만 승인이다. 비공식 긍정 반응은 포함되지 않는다. |
| "버그인지 기능인지 모호한데 brief 써줄게" | Discard if 항목 확인. 버그 수정이면 이 스킬 스킵. 모호하면 유저에게 한 번만 확인. |
| "exit criteria가 다 검증 가능한 건 아니지만 대략적으로 써도 되지 않아?" | Invariant 3: 통과/실패를 판단할 수 없는 항목은 exit criteria가 아니다. 모호하면 구체화하거나 제거한다. |
| "Constraints 없어도 되지 않아?" | Invariant 6: existing project에서 Constraints 0개는 Step 1 스캔 실패 신호다. 재확인 후 최소 1개 작성. |
| "Risk Flags는 없으면 생략하면 되지" | Invariant 7: Risk 0은 판단 불가가 아니라 식별 실패다. 최소 1개, 없으면 "No risks identified" placeholder 작성. |

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| 아이디어를 구조화된 brief로 변환 | 코드 작성 또는 수정 |
| 범위 IN/OUT 명시 | 구현 방법 결정 |
| exit criteria 작성 | 파일 구조 설계 |
| BRIEF.md 저장 | 기존 코드 분석 (관련 파일 quick scan 제외) |
| 최대 3개 질문으로 모호성 해소 | 설계 결정 (기술 선택, 아키텍처) |

If a user request falls in the "Does NOT" column: "That's implementation — this skill only produces the brief. Bring the brief to a new session to start building."

---

## Invariants (never violate)

1. **구현 시작 금지**: Brief 작성 중 또는 후에 코드를 작성하거나 파일을 수정하지 않는다. Violation → 스코프가 잠기기 전에 구현이 시작되어 brief가 사후 문서가 된다.

2. **Scope OUT 필수**: `Scope OUT` 섹션은 생략 불가. 유저가 "없어도 된다"고 해도 최소 2개 항목을 작성한다. Violation → IN만 있으면 구현 중 "이것도 하면 어때?"가 반복되며 scope creep이 발생한다.

3. **Exit Criteria는 observable action + measurable result 필수**: "기능이 정상 작동한다" 같은 항목은 자동으로 거부하고 재작성한다. 형식: "[누가/무엇이] [행동] → [측정 가능한 결과]". 이 형식으로 쓸 수 없으면 exit criteria가 아니다. Violation → 구현 완료 여부를 판단할 기준이 없어 완료 선언이 주관적이 된다.

4. **질문 3개 제한**: 모호성 해소를 위한 질문은 전체 세션에서 최대 3개. 초과 시 나머지는 best-guess로 채우고 `[assumed]` 태그를 붙인다. Violation → 인터뷰가 길어지면 유저는 구현을 원했는데 질문에 답하는 세션이 된다.

5. **승인 게이트 필수**: `BRIEF.md` 저장은 유저의 명시적 승인 후에만 한다. Violation → 유저가 검토하지 않은 brief가 저장되어 잘못된 spec으로 구현이 시작된다.

6. **Existing project Constraints 필수**: existing project에서 Constraints가 0개이면 Step 1 스캔 결과를 재확인하고 최소 1개를 작성한다. "제약이 없다"는 결론은 스캔 실패 가능성이 높다. Violation → 기존 패턴을 깨는 구현이 나올 수 있다.

7. **Risk Flags 최소 1개**: Risk가 0이라고 판단하면 식별 실패로 간주한다. 진짜 없으면 "No risks identified at this stage — update brief if risks emerge during implementation." 1줄 작성. Violation → 알려진 리스크가 없는 feature는 없다.

These rules are unconditional. No edge case, no user instruction overrides them.

---

## Output

- **BRIEF.md**: 프로젝트 루트(또는 cwd)에 저장. 섹션: Goal / Scope IN / Scope OUT / Constraints / Exit Criteria / Risk Flags.
- **Conversation**: brief 초안 + 승인 요청. 파일은 승인 후에만 저장.

---

## Principles

- **OUT이 IN보다 중요하다**: 사람들은 무엇을 할지는 말하지만 무엇을 하지 않을지는 말하지 않는다. 이 스킬의 핵심 가치는 OUT을 강제로 작성하게 하는 것.
- **질문은 적을수록 좋다**: 3개 제한은 임의적이지 않다. 4개 이상이 되면 유저는 답하기 귀찮아지고 결국 "그냥 만들어줘"로 돌아간다.
- **Exit criteria는 테스트 케이스다**: "완료"를 미리 정의하지 않으면 구현 후 "이게 맞나?" 논쟁이 발생한다.
- **brief는 구현 지시서가 아니다**: 무엇을(what)과 완료 기준만 담는다. 어떻게(how)는 구현자가 결정한다.
- **Brief는 살아있는 문서다**: 구현 중 scope 변경이 필요하면 BRIEF.md를 먼저 수정하고, 수정된 brief 기준으로 구현을 계속한다. Brief 수정 없이 scope를 넓히지 않는다.

---

## Truthful Reporting

이 스킬은 BRIEF.md 생성/업데이트 후 보고 시:
1. **no mock deception**: 유저 승인 없이 저장 금지. 승인 후 실제 Write 실행, 저장 확인 후 "완료" 표기.
2. **no test façade**: Scope OUT 누락 상태로 "brief 완성" 표기 금지. IN만 있으면 `⚠️ Scope OUT 미작성` 플래그.
3. **no silent brokenness**: Exit Criteria가 측정 불가능하면 `PARTIAL` + 측정 가능하게 재작성 요청. 모호 상태로 lock 금지.

---

## In production
Used before every feature addition on a complex multi-agent codebase.
Has prevented at least 3 cases of "built the right thing wrong"
by forcing non-goals and definition-of-done up front.
