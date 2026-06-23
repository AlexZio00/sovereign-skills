---
skill_type: workflow
tools: Read, Write, Edit, Glob, Grep, Agent, Bash, AskUserQuestion
name: scope
user_invocable: true
description: |
  Scope definition before implementation — two modes.
  Quick mode (default): IN/OUT/exit criteria brief → BRIEF.md.
  Full mode (/scope full): L0→L4 layered spec chain → spec.md.
  Trigger: '/scope', '/brief', '/specify', 'scope this', '스펙 잡아줘', '범위 잡아줘',
  'spec 만들어', '스펙 만들어', '기획 정리해줘', 'plan this'.
  Do NOT trigger for: bug fixes, single-file changes, existing spec, brainstorming.
---

# /scope — Scope Definition Engine v1.0

> brief + specify 통합. 구현 전에 "무엇을 하고 무엇을 안 하는지" 잠근다.
> Quick(기본) = IN/OUT 잠금 + BRIEF.md. Full = L0→L4 레이어 체인 + spec.md.

## Dominant Variable
**Scope OUT 항목이 명시적으로 작성되었는가** — IN만 있으면 구현 중 범위가 늘어난다. OUT이 명시돼야 잠긴다. Full 모드에서는 추가로 **L2 결정 명확도**가 지배 변수.

## Trigger
- `/scope` (Quick 기본)
- `/scope full` (Full 모드)
- `/brief` (Quick 하위호환)
- `/specify` (Full 하위호환)
- "scope this", "스펙 잡아줘", "범위 잡아줘", "기획 정리해줘"
- "spec 만들어", "스펙 만들어", "plan this"

## Discard If
- 버그 수정, 1파일 수정 → 직접 구현
- 이미 BRIEF.md/spec.md 존재 → Edit이 맞음
- 탐색만 원함 → brainstorming으로 위임

## Key Assumptions 
1. **프로젝트 CLAUDE.md 존재** (기존 프로젝트 시) — 깨지면: Constraints 자동 스캔 불가, 유저 입력만으로 작성.
2. **유저가 아이디어/요구사항을 1문장 이상 제시** — 깨지면: "무엇을 만들지 한 줄로 알려주세요" 1회 질문.


## Mode 선택

| Mode | 트리거 | 산출물 | 적합 상황 |
|------|--------|--------|---------|
| **Quick** (기본) | `/scope`, `/brief` | BRIEF.md | 기능 추가, 명확한 변경 |
| **Full** | `/scope full`, `/specify` | specs/{name}/spec.md | 아키텍처 변경, 멀티모듈, 복잡 설계 |

불확실하면 Quick으로 시작 → 유저가 더 상세 원하면 "full로 전환할까요?"

---

## Quick Mode — IN/OUT Brief

### Step 1: 프로젝트 감지
- 기존 프로젝트: CLAUDE.md, package.json 등 존재 → 2레벨 Glob + 키워드 Grep (10파일 cap)
- 신규: 스킵

### Step 2: 입력 충분성 체크
3가지를 1문장으로 답할 수 있는가:
- 무슨 행동이 추가/변경되나?
- 무엇이 명시적으로 제외되나?
- "완료"를 어떻게 검증하나?

불충분 → **최대 3개 질문**. 초과 → conservative minimum scope + `[assumed]` 태그.

### Step 3: Brief 생성

```markdown
## Brief: [feature name — verb phrase]

**Goal**: [1-2문장. 동사로 시작.]

**Scope IN**
- [구체 항목]

**Scope OUT** ← 필수, 최소 2개
- [자연스러운 확장인데 제외하는 것]

**Constraints**
- [파일/행동/통합 제약 — 기존 프로젝트면 최소 1개]

**Exit Criteria**
- [ ] [누가/무엇이] [행동] → [측정 가능한 결과]

**Risk Flags**
- [최소 1개]
```

### Step 4: 승인 → BRIEF.md 저장

---

## Full Mode — L0→L4 Spec Chain

### Layer Flow

| Layer | 무엇 | 게이트 |
|-------|------|--------|
| L0 | Mirror → Goal, Non-goals, Confirmed Goal | 유저 확인 |
| L1 | Codebase research → Research 섹션 | 자동 |
| L2 | Interview → Decisions + Constraints | L2-reviewer + 유저 승인 |
| L3 | Requirements (GWT sub-requirements) | 유저 승인 |
| L4 | Tasks (Fulfills 링크) + Plan Summary | 유저 승인 |

### Core Rules
1. 레이어 순서 엄수 — 건너뛰기·역행 금지
2. Append, don't overwrite — 기존 spec.md Read 선행
3. L2-reviewer 독립 검증 필수 (스킵 시 `Reviewer: SKIPPED` 명시)
4. Tasks는 Requirements 링크 필수 (`Fulfills: R{n}.{m}`)

### L2 Self-Validation
각 Decision에 clarity score (0-5):
- 5: 구현자가 1문장으로 무엇을 할지 말할 수 있음
- 3: 추가 질문 1-2개 필요
- 1: 완전히 모호

평균 < 3.5 → "결정이 모호합니다" 경고 + 재작성 권유.

### 산출물
`specs/{kebab-name}/spec.md` — 필수 섹션:
Meta / Goal / Non-goals / Confirmed Goal / Research / Decisions / Constraints / Known Gaps / Requirements / Tasks / Plan Summary

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] 아이디어→구조화된 brief/spec | 코드 작성 또는 수정 |
| [READ] IN/OUT 명시 + exit criteria | 구현 방법 결정 (how는 구현자) |
| [WRITE] BRIEF.md 또는 spec.md 저장 | 기존 코드 분석 (quick scan 제외) |
| [AGENT] L2-reviewer 독립 검증 (Full) | 설계 결정 자체 (brainstorming 역할) |

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| BRIEF.md / spec.md 파일 저장 | high (git) | L1+L3 (Invariant 5: 유저 승인 게이트) |
| 기존 spec 덮어쓰기 | medium | L1 (Invariant 9: append/edit만) |

## Invariants (never violate)

1. **구현 시작 금지**: scope 작성 중/후에 코드 수정 금지.
2. **Scope OUT 필수**: 최소 2개. 유저가 불필요하다 해도 작성.
3. **Exit Criteria = observable + measurable**: "정상 작동" 같은 항목 자동 거부.
4. **질문 3개 제한** (Quick): 초과 시 conservative minimum scope.
5. **승인 게이트 필수**: 파일 저장은 유저 명시 승인 후.
6. **Constraints 필수** (기존 프로젝트): 0개면 스캔 재확인.
7. **Risk Flags 최소 1개**.
8. **레이어 순서 엄수** (Full): L0→L1→L2→L3→L4.
9. **기존 spec 덮어쓰기 금지** (Full): Append 또는 Edit.
10. **Tasks→Requirements 링크 필수** (Full).

## Error Recovery 

| 실패 유형 | 복구 |
|---------|------|
| `tool_failure` | 대화창에 내용 출력 → 유저 수동 저장 |
| `input_error` | 질문 1개로 명확화. 추측 금지 |
| `missing_data` | "컨텍스트 없음" 명시 + 유저 정보만으로 작성 |
| `logic_inconsistency` | 충돌 항목 유저에게 선택 요청 |

## Rationalization Table

| 합리화 | 반박 |
|--------|------|
| "OUT 안 써도 돼" | Invariant 2. 명확한 것도 명시해야 scope creep 방지 |
| "충분히 명확해, 질문 없이 바로" | 3가지를 1문장으로 즉시 답해야 Sufficient |
| "L0-L1 뻔한데 넘어가자" (Full) | L2 decisions 기반 없어 허공에 뜸 |
| "spec 한번에 다 쓰자" (Full) | 중간 게이트가 방향 수정 기회 |
| "Requirements 없이 Tasks 바로" (Full) | Fulfills 링크 없으면 추적 불가 |

## Truthful Reporting 
1. **no mock deception**: 승인 없이 저장 금지.
2. **no test façade**: OUT 누락 = `⚠️ Scope OUT 미작성`.
3. **no silent brokenness**: Exit Criteria 측정 불가 = PARTIAL.

## Principles
- **OUT이 IN보다 중요하다** — 사람들은 할 것은 말하지만 안 할 것은 안 말한다.
- **질문은 적을수록 좋다** — 4개+ 되면 유저는 "그냥 만들어줘"로 돌아간다.
- **brief는 구현 지시서가 아니다** — what과 done만. how는 구현자.
- **Full은 Quick의 확장** — Quick에서 복잡도 감지하면 Full 전환 제안.
