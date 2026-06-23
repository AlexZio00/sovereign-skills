---
skill_type: utility
tools: Read
name: freeze
description: "Scope lock for current task. Declares editable zone — everything outside is frozen (read-only). Call before starting implementation to prevent scope creep."
tags: [meta, safety]
version: "1.0.0"
source: "garrytan/gstack freeze pattern — adapted (2026-05-08)"
triggers:
  - "/freeze"
  - "freeze this"
  - "scope lock"
  - "스코프 잠금"
  - "이것만 건드려"
  - "나머지 건드리지 마"
  - "범위 잠가"
user_invocable: true
---

# /freeze — Scope Lock

> 출처: garrytan/gstack freeze 패턴 차용 (2026-05-08).  상속.

## Dominant Variable

이 태스크에서 **수정 허용 범위가 명시되었는가** — 모호하면 구현 중 자연스럽게 scope creep이 발생한다. freeze/careful/guard 3원칙 중 첫 번째 (careful = 3-strike → systematic-debugging, guard = 위험 경로 보호).

## Trigger

- `/freeze`
- "freeze this"
- "scope lock"
- "스코프 잠금"
- "이것만 건드려"
- "나머지 건드리지 마"
- "범위 잠가"

## Discard If

- 탐색/리서치만 하는 경우 (수정 없음)
- 이미 명확한 단일 파일 수정 (1파일, 10줄 이하)
- brainstorming 단계 (설계 전에는 scope 미확정)

---

## Key Assumptions 
1. **유저가 수정 대상을 1개 이상 명시** — 깨지면: 1회 질문 후 여전히 모호하면 넓게 freeze.
2. **같은 세션에서 구현 작업이 후속** — freeze만 하고 끝나는 세션이면 이 스킬 불필요.

## Architecture

```
유저 입력 (파일/모듈/개념 범위)
    ↓
[PARSE]   → editable / frozen / read-only 분류
    ↓
[DECLARE] → FROZEN SCOPE 블록 생성
    ↓
[OUTPUT]  → 즉시 출력 후 종료
```

---

## Stage 1: PARSE

유저 입력에서 추출:
- **editable**: 명시된 파일/모듈/경로 — 수정 허용
- **frozen**: 나머지 전체 (명시 없으면 기본값 frozen)
- **read-only**: 언급됐지만 수정 여부 불명확 → 보수적으로 read-only 처리

범위가 너무 모호 ("모든 것", "적당히") → **1회만** AskUserQuestion으로 명확화.
그래도 모호 → 더 넓은 쪽으로 freeze (Invariant 2).

---

## Stage 2: DECLARE

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 FROZEN SCOPE — [태스크 한 줄 설명]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ EDITABLE (수정 허용)
  [파일/모듈 목록]

❌ FROZEN (수정 금지)
  [나머지 — 또는 "위 목록 외 전체"]

⚠️  READ-ONLY (참조만)
  [참조는 하되 수정 금지인 것]

규칙:
- FROZEN 파일은 Edit/Write 금지. Read만 허용.
- 수정 필요성 발견 시 → 즉시 중단, 유저에게 보고
- Freeze 해제: 유저가 "unfreeze [파일]" 또는 "freeze 해제" 명시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Stage 3: OUTPUT

FROZEN SCOPE 블록 출력 후 즉시 종료.
코드 생성, 에이전트 스폰, 구현 시작 금지.

이 선언 이후 같은 세션의 모든 구현 작업은 이 scope를 따른다.

---

## Hard Rules

1. **즉시 출력, 즉시 종료** — 선언 후 "그럼 시작할게요" 없음.
2. **에이전트 스폰 금지** — 메인 컨텍스트에서만 실행.
3. **코드 생성 금지** — 범위 선언만.
4. **모호하면 1회만 질문** — 여전히 모호하면 더 넓은 쪽으로 freeze.

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] 유저 입력 파싱 → editable/frozen/read-only 분류 | 코드 작성 또는 파일 수정 |
| FROZEN SCOPE 블록 출력 | 에이전트 스폰 또는 구현 시작 |
| 범위 모호 시 1회 명확화 질문 | 범위 밖 수정 여부 직접 판단 |

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| (없음 — 읽기 전용, 블록 출력만) | — | L1 (Invariant 1: frozen 파일 수정 절대 금지) |

- **L1 (Invariants)**: Frozen = Edit/Write 물리적 차단 의도. 선언 후 즉시 종료.

## Error Recovery 

실패 감지 시: **Stop → Classify → Apply Recovery → Report & Resume**.

| 실패 유형 | 감지 조건 | 복구 경로 |
|---------|---------|--------|
| `input_error` | 어떤 파일/범위를 freeze할지 불명확 | 1개 질문으로 대상 확인 — 추측으로 scope 결정 금지 |
| `logic_inconsistency` | freeze 요청과 동시에 수정 요청이 충돌 | "이 파일은 freeze됩니다 — 수정 요청은 거부됩니다" 명시. 둘 다 허용 금지 |
| `missing_data` | 지정된 파일 없음 | "파일 없음" 명시. 경로 추측하여 다른 파일 freeze 금지 |

---

## Invariants (never violate)

1. **Frozen = 수정 절대 금지**: frozen 선언된 파일은 해당 세션에서 Edit/Write 불가. "살짝만 건드리는 거라서"는 합리화. Violation → scope creep, 예상치 못한 부작용 발생.

2. **모호하면 더 넓게**: 어디까지 frozen인지 불명확하면 더 넓은 범위를 frozen으로. 좁게 잡으면 scope creep 방어 불가. Violation → freeze 선언이 유명무실.

3. **선언 후 즉시 종료**: FROZEN SCOPE 블록 출력 후 다음 행동 없음. 유저가 이어서 구현 요청하는 것이 정상 flow. Violation → 선언과 구현이 섞여 scope 의식이 희미해짐.

---

## Rationalization Table

| 합리화 | 반박 |
|--------|------|
| "frozen인데 딱 1줄만 바꾸면 되는데" | Invariant 1 위반. 중단하고 유저에게 보고. |
| "범위가 모호한데 일단 좁게 잡자" | Invariant 2 위반. 모호하면 넓게. |
| "freeze 선언하고 바로 구현하면 더 빠르지" | Invariant 3 위반. 선언 후 종료. |
| "1파일인데 freeze 선언이 왜 필요해" | Discard If: 1파일 10줄 이하는 제외. 그 외는 선언. |
| "실제로 수정할 게 없어서 괜찮아" | 수정할 게 없다고 생각할 때가 scope creep 시작점. |

---

## Example

```
유저: "/freeze dashboard_dash/pages/financial_report_tab.py"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 FROZEN SCOPE — financial_report_tab.py 렌더링 수정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ EDITABLE
  - dashboard_dash/pages/financial_report_tab.py

❌ FROZEN (수정 금지)
  - 위 파일 외 전체

⚠️  READ-ONLY (참조만)
  - skills/financial_report.py (render() 구현 참조용)

규칙:
- financial_report_tab.py 외 파일은 Edit/Write 금지
- 수정 필요 발견 시 즉시 중단 → 유저 보고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## gstack 원형과의 차이

gstack freeze는 세션 전역 파일 목록 기반. 이 버전은 태스크 단위 선언 기반 (세션 상태 저장 없음).
이유: Claude Code는 세션 간 상태 지속 불가 → 선언 블록 자체가 컨텍스트 내 state 역할.
