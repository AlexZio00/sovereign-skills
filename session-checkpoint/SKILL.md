---
skill_type: lifecycle
tools: Read, Write, Edit
triggers:
  - "/session-checkpoint"
  - "checkpoint"
  - "compact"
  - "체크포인트"
  - "핸드오프 저장"
  - "컴팩트 전에"
name: session-checkpoint
description: "Use when saving session state before context compaction, switching tasks, or ending a session. Triggers: 'session-checkpoint', 'checkpoint', 'compact', '체크포인트', '핸드오프 저장', '컴팩트 전에', 'save progress', '세션 저장', '세션 체크포인트'. Runs 5-phase pipeline: context extraction → handoff write → memory save → preservation check → compact guidance."
user_invocable: true
# (제거 2026-06-10) context: !cat — CC 미지원 커스텀 태그, YAML 파서 파괴. 핸드오프 주입은 SessionStart 훅 담당
---

# Session Checkpoint

## Dominant Variable
이 세션에서 **다음 세션이 반드시 알아야 할 것이 명확히 식별되었는가**. 식별이 불완전하면 Phase 1을 더 깊게 — compact는 그 다음이다.


## Key Assumptions 

1. **핸드오프 파일 경로 쓰기 가능** — `memory/session-handoff-LATEST.md`. 깨지면: 경로 재확인 후 fail-fast ( Error Recovery: `tool_failure`).
2. **MEMORY.md / context-log.md 존재** — Phase 3 저장 대상. 깨지면: 파일 생성 후 진행. 생성 실패 시 유저 보고.
3. **세션 대화가 Phase 1 추출에 충분** — 최소 5회 이상 교환. 깨지면: Discard If 적용 (세션이 너무 짧음) 또는 최소 핸드오프만 생성.
4. **Reflexion 추출 (Phase 1.7) 가능** — 실패·불만 신호 스캔용 대화 존재. 깨지면: "신규 lessons: 없음" 처리.

## Trigger

- `/session-checkpoint`
- "checkpoint"
- "compact"
- "체크포인트"
- "핸드오프 저장"
- "컴팩트 전에"

## Discard If
- 세션 내 코드 변경 없고 미결 의사결정도 없음 → compact 불필요
- 이미 이번 세션에 checkpoint를 완료했음 → 중복 실행 불필요
- compact가 아닌 단순 핸드오프 업데이트만 원함 → `memory/session-handoff-LATEST.md` 직접 수정

---

## 핵심 원칙
- 핸드오프는 **단일 파일** (`memory/session-handoff-LATEST.md`) — 버전 번호 없음
- 완료된 항목은 **제거**, 새로 생긴 항목만 **추가**
- 다음 세션이 이 파일 하나만 읽으면 바로 시작할 수 있어야 함
- compact 전에 반드시 보존 검증

## Phase 1: Deep Context Extraction

compact로 소실될 수 있는 것들을 먼저 추출:

- **미완결 의사결정** — 논의했지만 결론 안 난 주제
- **사용자 우선순위 신호** — 강조한 것, 반복한 것, 화낸 것 → feedback 메모리
- **현재 멘탈 모델** — 코드 흐름, 버그 인과관계, 실패한 접근과 이유
- **시도했다가 실패한 것** — 다음 세션에서 반복 방지

### Phase 1.5: Entity Extraction (Dream Cycle 패턴)

> **Triple Gate 자동 트리거 기준** (autoDream 패턴, ch13):
> 누적 토큰 ≥ 5,000 AND 도구 호출 ≥ 3 AND 마지막 checkpoint 후 ≥ 24h
> → 세 조건 동시 충족 시 자동 실행 권장. 수동 호출 시에도 동일 기준 적용.

세션 대화를 스캔해 4종류 엔티티를 추출한다:

**① 영구 사실 후보** → MEMORY.md 승격 검토
- 새로 발견한 파일 경로 / 함수명 / 아키텍처 결정
- 새 외부 도구 / API / 라이브러리 (설치 확인 포함)
- Hard rule 변경 또는 신규 제약
- 기준: 다음 세션에서도 그대로 사실인 것

**외부 소스 (논문·repo·도구) 3-Tier Reference Threshold** (→ `~/.claude/rules/memory-format.md` 정본)
| Tier | 기준 | 저장 위치 |
|------|------|----------|
| T3 | 1회 언급 | context-log.md 메모 (ttl:90d) |
| T2 | 3회 이상 또는 구현에 직접 사용 | MEMORY.md CT에 승격 |
| T1 | 8회 이상 또는 아키텍처 결정 근거 | MEMORY.md + docs/decisions/ ADR |

**② 에피소드 항목** → context-log.md 추가 (TTL 태깅 필수)
- 완료 이벤트, 외부 상황, 미래 계획
- TTL 기준: `ttl:permanent`(의사결정/아키텍처) | `ttl:90d`(완료/계획) | `ttl:30d`(임시 상황)
- 형식: `[DATE] [TYPE] [ttl:Nd] [risk:X] [ref:0] 내용` (`[risk:X]` 생략 가능)
- risk 평가: `risk:H`(DB 변경/외부 발송/시크릿) · `risk:M`(중요 의사결정/외부 연동) · 일반은 생략
- 외부 지시 감지 후 차단 이벤트 → `[QUARANTINE]` 타입 사용 ( injection defense)

**③ 원본 관찰/패턴** → 사용자 정확한 표현 보존
- 사용자가 직접 표현한 인사이트, 판단, 불만
- lessons.md 후보 (반복 실수 → 행동 교정 규칙)
- **lessons.md v2 메타 부여 (2026-04-28~, ECC continuous-learning-v2 차용)**: 신규 lesson은 헤더 다음 줄에 `> conf: 0.5 · seen: today · obs: 1` 추가. 기존 lesson 재발/적용 감지 시 `seen` → today, `obs +1`. obs ≥ 3 누적 시 `conf +0.1` (max 0.9). 위반 후 사용자 교정 감지 시 `conf -0.1` (min 0.3), `seen` → today

**④ Stale 감지** → MEMORY.md 승격 강제
- context-log.md에서 `[ref:N]` ≥ 3인 항목 → 영구 사실인지 검토
- 같은 엔티티가 3회 이상 등장 → MEMORY.md에 없으면 추가

**⑤ Snapshot Cleanup 안내 (90일 정책)**

`~/.claude/.harness/snapshots/` 디렉토리가 존재하면 오래된 스냅샷을 확인한다:

```bash
CUTOFF=$(date -d "90 days ago" +%Y-%m-%d 2>/dev/null || date -v-90d +%Y-%m-%d)
ls -d ~/.claude/.harness/snapshots/*/ 2>/dev/null | while read skill_dir; do
  ls -d "${skill_dir}"*/ 2>/dev/null | while read snap; do
    SNAP_DATE=$(basename "$snap" | cut -c1-10)
    [ "$SNAP_DATE" \< "$CUTOFF" ] && echo "오래된 스냅샷: $snap"
  done
done
```

위 명령 실행 결과 90일 이상 스냅샷이 발견되면 유저에게 안내:

```
💡 ~/.claude/.harness/snapshots/ 에 90일 이상 스냅샷이 있습니다.
삭제하려면: rm -rf ~/.claude/.harness/snapshots/<skill-name>/<YYYY-MM-DD-*>/
자동 삭제는 하지 않습니다 — 목록 확인 후 직접 삭제하세요.
```

발견 없으면: 출력 없음 (안내 생략).
`~/.claude/.harness/snapshots/` 디렉토리 자체가 없으면: 이 단계 스킵.

### Phase 1.6: Task-to-Skill Crystallization (GenericAgent 패턴)

> **목적**: 반복 워크플로우를 skill로 자동 승격 제안. "수동 반복 3회"가 "스킬 1회 호출"로 전환되는 지점.
> **출처**: GenericAgent — 태스크 실행 crystallization 패턴.

세션 내 도구 호출·유저 메시지를 스캔해 **반복 워크플로우 시그니처**를 추출한다.

**시그니처 정의:**
동일 워크플로우의 3개 요소가 유사해야 함:
1. **Intent** — 유저 요청 유형 (리뷰 / 분석 / 검증 / 생성 / 배포 등)
2. **Tool Sequence** — 실행된 도구 호출 순서 패턴 (예: Read → Grep → Edit → Bash test)
3. **Output Shape** — 최종 산출물 형태 (리포트 / 코드 변경 / 파일 생성 등)

**크리스탈라이즈 3단계 (세션+누적 합산 빈도 기준):**

| 단계 | 빈도 | 동작 | 출력 |
|------|------|------|------|
| **등록** | ≥ 3회 | context-log.md에 `[CRYSTALLIZE_CANDIDATE]` 항목 추가 (ttl:90d, ref:0). **출력 없음** — 유저 방해 금지 |  silent |
| **제안** | ≥ 5회 | 아래 제안 블록 출력 | `[💡 Crystallization 제안]` |
| **권고** | ≥ 10회 | 제안 블록 + 강조 권고 | `[🔴 Crystallization 권고]` |

빈도 계산: `세션 내 동일 시그니처 횟수 + context-log.md [ref:N]` 합산.

**제안 출력 형식 (≥ 5회):**
```
[💡 Crystallization 제안]
- 시그니처: {Intent} + {Tool Sequence} + {Output Shape}
- 빈도: 세션 {N}회 / 누적 {M}회 (합계 {T}회)
- 제안: `/forge` 실행하여 이 워크플로우를 스킬로 승격할 것 검토
- 예상 스킬명: {snake_case_name}
- 예상 트리거: {Korean + English trigger phrase 3개}
```

**권고 출력 형식 (≥ 10회):**
```
[🔴 Crystallization 권고 — {T}회 반복 감지]
- 시그니처: {Intent} + {Tool Sequence} + {Output Shape}
- 빈도: 세션 {N}회 / 누적 {M}회 → 스킬화 강력 권고
- `/forge` 실행 여부를 이 세션 안에 결정할 것 권고
```

**불발 조건 (Crystallization 안 함):**
- 1회성 탐색 (Glob → Read 단발)
- 이미 존재하는 스킬과 시그니처 중복 — `~/.claude/skills/*/SKILL.md` 스캔해서 확인
- 시그니처가 너무 일반적이라 Collision Map 충돌 발생 예상 (forge Phase 0-2 컷)

**승격 워크플로우:**
제안만 한다. 실제 forge 실행은 사용자 승인 후.
사용자가 "ㅇㅇ" / "승인" / "만들어" 하면 → forge로 넘김.
사용자가 "아니야" / "패스" 하면 → 제안 폐기, lessons.md에 `[YYYY-MM-DD] crystallization 후보 거절: {signature} — 사유 필요` 기록.

### Phase 1.6.5: Invocation Log — 실시간 기록 (E11 인프라)

> **목적**: 세션 crash나 `/session-checkpoint` 미도달 상황에서도 invocation 손실 방지. Phase 3.7 사후 스캔의 fallback이 아닌 **primary recording point**.
> **출처**: STATE.md 단기 보강 — Phase 1.6 직후 실시간 로깅 (이전: Phase 7 사후 스캔만).
>
> Phase 1.6에서 이미 세션 도구 호출을 스캔했으므로, 동일 스캔 결과를 즉시 JSONL에 기록한다. Phase 3까지 도달하지 못하고 세션이 끊겨도 invocation은 보존됨.
>
> **Shadow 격리 원칙** (출처: fablize v2.1 shadow measurement): `.harness/` 하위 JSONL 로그(invocations, interventions, events)는 **모델 컨텍스트에 원본 주입 금지**. 세션 중 이 로그를 읽어 행동을 바꾸면 관측자 효과(Hawthorne effect)가 발생해 측정이 오염된다. 허용: 카운트 집계, 패턴 분석(별도 도구). 금지: 원본 로그 내용을 프롬프트/컨텍스트에 삽입.

**기록 대상** (Phase 1.6과 동일 스캔 결과 재사용):
- **Skill 도구 호출**: tool_use 이벤트의 `skill:` 파라미터 값 추출
- **Agent 도구 호출**: tool_use 이벤트의 `subagent_type:` 파라미터 값 추출
- **Discard If 이벤트**: 세션 중 스킬 트리거 후 Discard If 조건으로 실행 건너뜀 (대화에서 "Discard If" / "조건 불충족" / "스킵" 패턴 감지)

**기록 형식** (1줄 JSON, append-only — Phase 3.7과 동일 스키마):
```json
{"ts":"ISO8601","date":"YYYY-MM-DD","skills":["skill1","skill2"],"agents":["subagent_type1"],"discarded":[{"skill":"X","reason":"discard_if"}],"source":"session-checkpoint-phase1.6.5","session_id":"YYYY-MM-DDTHH:MM:SS"}
```

**`session_id` 필드**: ISO8601 타임스탬프를 그대로 사용 (예: `"2026-05-17T14:32:11"`). Phase 3.7 idempotency 체크의 키. 동일 session_id 항목이 이미 jsonl에 있으면 Phase 3.7은 스킵.

**스킵 조건** (기록 안 함):
- skills + agents + discarded 모두 비어있음 → 세션 호출 없음, 기록 생략
- Phase 1.5의 Triple Gate 미충족 (토큰<5000 AND 도구<3) → 의미 있는 활동 없음

**디렉토리 보장**: 기록 전 `~/.claude/.harness/invocations/` 디렉토리 존재 확인. 없으면 `mkdir -p`로 생성.

**파일 경로**: `~/.claude/.harness/invocations/YYYY-MM.jsonl` (월별 분리, append-only).

**출력 형식** (유저에게 1줄):
```
[Invocation Log] skills: {N}, agents: {M}, discarded: {K} → recorded (session_id: YYYY-MM-DDTHH:MM:SS)
```
전부 0건이면 `[Invocation Log] 세션 호출 없음 — 기록 생략` 1줄.

**실패 시**: 기록 실패해도 checkpoint 전체 중단 금지. 경고 1줄 출력 후 Phase 1.7로 진행 (`⚠️ Invocation log write failed: {reason} — Phase 3.7 fallback will retry`).

### Phase 1.7: Reflexion — 세션 품질 자가평가 

> **출처**: Shinn et al. "Reflexion: Language Agents with Verbal Reinforcement Learning" (2023) 패턴 적용.
> Reflexion = 세션 종료 직전 verbal self-assessment → episodic memory에 저장 → 다음 세션 행동 개선.

세션 대화를 스캔해 **3개 반성 항목**을 추출하고 lessons.md에 즉시 반영한다.

**추출 질문 (내부 처리 — 유저에게 묻지 않음):**
1. **이 세션에서 틀리거나 비효율적이었던 것** — 잘못된 가정, 재작업, 헤맨 것
2. **유저 불만족 신호** — 교정 요청, "아니야", 반복 설명, 짜증 표현
3. **다음에 더 잘할 수 있는 방법** — 구체적 행동 변화 (추상적 "더 신중히" 금지)
4. **이 세션에서 잘 작동한 판단 1건** — 유저 승인을 받은 접근, 효율적이었던 선택, 좋은 결과를 낸 판단. 실패만 기록하면 과도 방어로 경화된다 (출처: Memory Curse, arXiv 2605.08xxx). 성공 lesson도 최소 1건 기록해 실패 편향을 균형 잡는다. 없으면 생략 — 억지로 만들지 않는다.

**항목이 있을 때** → lessons.md에 추가 (v2 포맷):
```
### [YYYY-MM-DD] {one-line lesson title}
> conf: 0.5 · seen: YYYY-MM-DD · obs: 1 · model: opus-4.8

[구체적 행동 교정 내용 — 다음에 X가 발생하면 Y를 한다]
```

**`model:` 필드 (모델 차이 분석 인프라, 설계 `docs/plans/2026-06-11-opus-fable-porting-harness-design.md` §4①)**:
- 실수를 **유발한 모델이 식별될 때만** 추가 — 메인 세션 모델 또는 디스패치된 서브에이전트 모델(예: `opus-4.8` / `sonnet-4.6` / `haiku-4.5`).
- **불명이면 생략**(추측 금지). 기존 lesson 소급 부여 금지.
- 이 태그가 session-start Phase 2.2 리마인드의 집계 대상 — 쓰기(여기)와 읽기(분석)는 쌍.

**중복 감지**: lessons.md 스캔 후 기존 유사 lesson이 있으면:
- 내용 실질적으로 동일 → `obs +1`, `seen` → today, conf 조건부 업데이트 (obs ≥ 3 시 `+0.1`)
- 내용 보완 가능 → 기존 lesson 본문에 append 후 obs/seen 업데이트

**항목 없을 때** (완벽한 세션, 비효율 없음) → Phase 1.7 skip. "반성 없음" 표기도 불필요.

**출력 형식** (유저에게 표시):
```
[Reflexion] 이 세션 lessons: {N}건 → tasks/lessons.md 업데이트
  - {lesson 1 요약 1줄}
  - {lesson 2 요약 1줄}  (있으면)
```
N=0이면 `[Reflexion] 이 세션 신규 lessons: 없음` 1줄만.

### Phase 1.8: Intervention Log — 개입 기록 (E13 인프라)

> **목적**: 유저가 Claude 행동을 교정/거절/재작업 요청한 사건을 JSONL에 기록. quality measurement 인프라.
> E13 = Human Intervention Rate — 개입 빈도가 낮을수록 자율성 신뢰도 높음.
> **Shadow 격리**: Phase 1.6.5와 동일 — 원본 로그를 모델 컨텍스트에 주입 금지(관측자 효과 방지). 카운트 집계만 허용.

**개입 신호 탐지 (세션 대화 스캔, 내부 처리):**

| 유형 | 탐지 패턴 | `type` 필드 |
|------|----------|------------|
| 교정 | "아니야", "그게 아니라", "다시 해", 재작업 요청 | `correction` |
| 거절 | "하지 마", "필요 없어", 승인 거부, "ㄴㄴ" | `rejection` |
| 오버라이드 | 유저가 직접 수행 ("내가 할게", 수동 실행 언급) | `override` |
| 에스컬레이션 | 동일 이슈 3회+ 반복, 유저 불만/짜증 표현 | `escalation` |

**탐지됐을 때** → `~/.claude/.harness/interventions/YYYY-MM.jsonl`에 append:
```json
{"ts":"ISO8601","date":"YYYY-MM-DD","session_id":"YYYY-MM-DDTHH:MM:SS","type":"correction|rejection|override|escalation","skill":"스킬명 또는 null","agent":"에이전트명 또는 null","model":"opus-4.8 등 또는 null","l0_clause":" 등 또는 null","context":"1줄 요약"}
```

**`skill` / `agent` 필드**: 개입이 특정 스킬/에이전트 실행 중 발생한 경우만 기록. 일반 대화 중 개입이면 `null`.
**`model` 필드** (모델 차이 분석 인프라, 설계 §4①): 개입 시점에 응답한 모델(메인 세션 또는 서브에이전트). 불명이면 `null`. session-start Phase 2.2 집계 대상 — append-only 스키마라 신규 필드는 하위호환.

**스킵 조건**: 개입 신호 0건 → 기록 생략, 출력도 없음.

**출력 형식** (개입 있을 때만):
```
[Intervention Log] {N}건 기록 → ~/.claude/.harness/interventions/YYYY-MM.jsonl
  - {type}: {context 1줄}
```

**디렉토리 보장**: 기록 전 `~/.claude/.harness/interventions/` 존재 확인. 없으면 `mkdir -p`로 생성.

**실패 시**: 기록 실패해도 checkpoint 전체 중단 금지. `⚠️ Intervention log write failed: {reason}` 1줄 출력 후 Phase 2 진행.

## Phase 2: 핸드오프 작성 (단일 파일 갱신)

파일: `memory/session-handoff-LATEST.md`

### 규칙
1. **이전 핸드오프를 읽고** (위에 자동 주입됨) 완료된 항목 제거
2. 진행 중인 항목은 상태 업데이트
3. 새로 생긴 항목 추가
4. **완료된 건 아카이브하지 않음** — 그냥 삭제. git history에 남음.

### 필수 섹션

```markdown
## 지금 해야 할 것 (우선순위 순)
1. [가장 급한 것] — 실행 명령어 포함
2. [그 다음]

## 현재 작업 상태  ← Full Compact 2순위 필수 항목
- 진행 중인 작업: [있으면 — 파일명, 함수명, 어디까지 했는지]
- 없으면 이 섹션 생략 가능

## 미결 의사결정
- [주제]: [옵션들] — 의견: [있으면] · urgency: H/M/L

## 잔존 이슈
- [해결 안 된 버그/문제] · risk: H/M/L

## 시스템 이해 (다음 세션에 필요한 맥락)
- [이 세션에서 발견한 중요 인과관계]
- [시도했다가 실패한 접근 — 반복하지 말 것]
- [핵심 파일 경로 및 함수명 — compact 후 복원용]

## 사용자 현재 관심사
- 최우선: [무엇]
- 불만족: [무엇]
```

### 금지 사항
- "이 세션에서 한 것" 나열 금지 — 핸드오프는 미래 지향
- 버전 번호 금지 (v1, v2, v3...)
- 완료된 항목 유지 금지
- 200줄 초과 금지

---

## Phase 2.3: Memento CoT 압축 (State Snapshot 주입)

> **출처**: Step 9 Memento CoT 압축 (2026-05-12). 핸드오프 KV 캐시 2-3x 감소 목표.
> Memento 패턴 — 외부 노트에만 의존하는 기억상실 캐릭터처럼, 다음 세션이 compact block 하나만 읽으면 즉시 복원 가능하게 한다.

Phase 2에서 작성한 핸드오프 prose에서 핵심 상태를 추출해 구조화 YAML로 압축한다.
이 compact 블록을 핸드오프 파일 frontmatter 직후, 제목 행 전에 삽입한다.

### Compact 블록 스키마

```yaml
<!-- state-snapshot v1 -->
ts: YYYY-MM-DD
ctx: "이 세션 한 줄 요약"               # max 20 단어, 핵심 맥락만
next:
  - "작업1 (urgency: H)"               # 최대 5개. 핵심 동사+목적어만. 실행 명령어 제거
diff:
  - op: add|del|mod|decide
    item: "대상 (파일명/스킬명/결정명)"
    why: "사유"                          # max 10 단어. 없으면 생략
blocked:
  - item: "이슈"
    risk: H|M|L
```

### 필드 생성 규칙

| 필드 | 소스 | 변환 방식 |
|------|------|---------|
| `ctx` | "사용자 현재 관심사 → 최우선" | 1줄로 압축. 도구 호출 시퀀스 제거 |
| `next` | "지금 해야 할 것" | 동사+목적어만. inline 코드블록 제거. max 5개 |
| `diff` | "시스템 이해" 변경 목록 | op+item+why로 분해. max 5개 |
| `blocked` | "잔존 이슈" | item+risk만. 설명 제거. max 3개 |

초과 시: impact 높은 것 우선 — 잘라낸 항목은 prose에 유지.

### 삽입 위치

```
---
name: Session Handoff — Latest
...
---
<!-- state-snapshot v1 -->
```yaml
ts: ...
...
```

# Session Handoff (날짜 — 제목)

## 지금 해야 할 것
...
(기존 prose 섹션 유지 — deep context 참조용)
```

compact 블록만 읽으면 다음 세션이 즉시 컨텍스트 복원 가능.
prose 섹션은 그 아래에 유지 — 상세 실행 명령어, 설명 등 deep context 필요 시 참조.

### 압축률 측정 (항상 출력)

Phase 2 직후 prose 바이트 수 측정 → compact 블록 생성 후 비교:
```
[Memento] prose: Xbytes → compact block: Ybytes (Zx reduction)
```

2x 미달 시: `next/diff` 항목에 불필요한 설명이 남아있음 — 추가 압축 권고.

---

## Phase 3: 메모리 저장

Phase 1.5 추출 결과를 파일에 반영:

> **[MUST VERIFY — ]**: MEMORY.md에 파일 경로·함수명·설정 플래그를 기록하기 전, 반드시 Glob/Grep으로 현재 존재 여부를 확인한다. 메모리에 있다고 맞는 게 아니다 — 작성 시점 기준 사실만 기록한다. 검증 없는 경로 기록 금지.

1. **MEMORY.md** — 영구 사실 후보를 해당 섹션에 추가 (기존 내용 재작성, append 금지)
   - **경로·함수명 기록 전**: `Glob` 또는 `Grep`으로 존재 확인 필수 (60초 cap, 1~2개 스팟 체크)
   - 추가 전 중복 확인 (이미 있으면 스킵 또는 내용 업데이트만)
   - stale 항목(현재 상태와 불일치) → 즉시 수정
2. **context-log.md** — 에피소드 항목 append (날짜+TTL+ref:0 형식 필수)
3. **tasks/lessons.md** — 이 세션에서 발생한 행동 교정 규칙 추가 (해당 시)
   - **v2 포맷 (2026-04-28~)**: 신규 lesson 헤더 `### [YYYY-MM-DD] 제목` 다음 줄에 메타 라인 `> conf: 0.5 · seen: YYYY-MM-DD · obs: 1` 추가
   - **재발 감지 시**: 같은 lesson 헤더 검색 → `seen` → today, `obs +1`. obs가 3·6·9 도달 시 `conf +0.1` (max 0.9)
   - **위반 후 교정 감지**: `conf -0.1` (min 0.3), `seen` → today
   - **분기 정리** (매월 1일 또는 stale 감지 시): `conf < 0.4 AND (today − seen) > 90일` → `tasks/_archive/lessons-pre-YYYY-MM.md` 이동
4. MEMORY.md 인덱스에서 이전 핸드오프 참조 제거, LATEST로 통일
5. **`~/.claude/STATE.md`** (글로벌 크로스 프로젝트) — 세션에서 상태 변화가 있으면 반드시 업데이트:
   - PENDING 항목 트리거 충족 / 완료됨 → 해당 행 삭제
   - 활성 블로커 해소됨 → 해당 행 삭제
   - 신규 Major 마일스톤 → `변경 이력` 테이블에 추가 (날짜 + 1줄 요약)
   - 변화 없으면 스킵 — 불필요한 touch 금지
   - STATE.md 경로: `C:\Users\지오\.claude\STATE.md`
6. **Monthly Synthesis (조건부)** — `conf≥0.7` lessons 클러스터링
   - **트리거 조건 (둘 중 하나):** (a) 오늘이 매월 1일, 또는 (b) 이번 세션에서 신규 lesson 추가 후 `conf≥0.7` 총 개수 ≥ 10
   - **비트리거 시**: 이 단계 완전 스킵 (출력 없음)
   - **실행 절차:**
     1. lessons.md 전체 스캔 → `conf≥0.7` 항목 목록 추출
     2. 공통 L0 조항 또는 행동 패턴으로 클러스터링 (최소 2개 이상 묶임)
     3. 클러스터당 통합 룰 1줄 작성 (구체적 행동 기준 포함)
     4. lessons.md `## Synthesis — conf≥0.7 클러스터` 섹션 **덮어쓰기** (append 금지)
        - 섹션 없으면 파일 말미 `## 미결 패턴` 앞에 삽입
     5. 섹션 상단 `> 최종 갱신: YYYY-MM-DD` 날짜 갱신
   - **클러스터 네이밍:** `### Cluster X — 테마명: "한 줄 슬로건"`
   - **Sources 기재:** 묶인 lessons 제목 + conf + obs 함께 표기
   - **L0 연결:** 가장 가까운 L0 조항 1개 명시
7. **Invocation Log — Fallback 기록** (`~/.claude/.harness/invocations/YYYY-MM.jsonl`)
   - **Idempotency 체크 (필수, 가장 먼저)**: Phase 1.6.5가 이미 이 세션 invocation을 기록했는지 확인:
     - 이번 세션의 `session_id` (Phase 1.6.5에서 발급한 ISO8601 타임스탬프) 보유 시 → `YYYY-MM.jsonl` grep으로 동일 session_id 검색
     - 동일 session_id 존재 → **스킵** (`[Invocation Log] Phase 1.6.5에서 이미 기록됨 (session_id: ...) — 중복 방지 스킵` 1줄 출력)
     - 동일 session_id 없음 (Phase 1.6.5 실패 또는 미실행) → 아래 fallback 기록 진행
   - **Fallback 동작 (Phase 1.6.5 실패 시만 실행)**: 이 세션에서 호출된 스킬·에이전트를 append-only JSONL에 기록 (E11 Discard If 거부율 측정 인프라)
   - **탐지 대상**: Skill 도구 호출(`skill:` 파라미터) + Agent 도구 호출(`subagent_type:` 파라미터)
   - **Discard If 이벤트**: 세션 중 스킬 트리거 후 Discard If 조건으로 실행 건너뜀 → `"discarded"` 배열에 기록
   - **기록 형식** (1줄 JSON, append — Phase 1.6.5와 동일 스키마):
     ```json
     {"ts":"ISO8601","date":"YYYY-MM-DD","skills":["skill1","skill2"],"agents":["subagent_type1"],"discarded":[{"skill":"X","reason":"discard_if"}],"source":"session-checkpoint-phase3.7-fallback","session_id":"YYYY-MM-DDTHH:MM:SS"}
     ```
   - `source` 필드로 Phase 1.6.5 정상 기록 vs Phase 3.7 fallback 구분 가능 (분석 시 활용)
   - **스킵 조건**: skills + agents + discarded 모두 비어있으면 기록 생략 (세션 호출 없음)
   - 디렉토리 미존재 시 먼저 생성: `mkdir -p ~/.claude/.harness/invocations/`

8. **Key Files 기존 경로 검증** (conflict detection — )
   - MEMORY.md `## Key Files & Architecture` 섹션에서 파일 경로 3~5개 추출 (entry.py, app.py, 핵심 스크립트 등)
   - 각 경로를 Glob으로 존재 확인 (60초 cap)
   - **stale 발견 시**: MEMORY.md 해당 라인 즉시 수정/삭제 + `⚠️ STALE PATH: {경로} → 제거됨` 출력
   - **이상 없으면**: `[Key Files 검증] {N}개 확인 — 이상 없음` 1줄만
   - 스킵 조건: MEMORY.md Key Files 섹션 없거나 경로 항목이 0개이면 생략

9. **Forgetting Sweep — control-plane purge** (논문 arXiv 2606.15903 "Control-Plane Placement Shapes Forgetting" 적용, 2026-06-16)
   > 메모리 실패의 본질은 recall이 아니라 **forgetting**(폐기됐어야 할 stale이 계속 표면화 — 회전된 자격증명 추천·해결된 블로커 잔존). append만 하면 stale이 누적된다 → checkpoint마다 능동 supersede/purge.
   - **STATE.md**: ✅완료·🟢해결·트리거 충족 항목 → **삭제**(active 목록엔 미결만, 완료는 변경이력에만). "대기/예정/미커밋" status는 Glob/grep으로 실상태 확인 → 이미 active/committed면 정정·퍼지.
   - **MEMORY.md CT**: 현재 사실과 불일치 항목 덮어쓰기( 카운트·버전·플래그는 실측 후 갱신.
   - **superseded 문서**: 통합본·신버전이 생긴 옛 파일 → graveyard/_archive 이동(본문에 superseded 표기).
   - ⚠️ 파일 삭제·이동 전 외부참조 grep — Read-by-path 의존 있으면 보류.
   - 출력: `[Forgetting Sweep] 퍼지 {N} / 정정 {M} / superseded {K}` (0이면 `stale 없음`).

## Phase 4: 보존 검증

compact 전 체크리스트:
```
□ 미완결 의사결정이 핸드오프에 있는가?
□ 이 세션의 피드백이 메모리에 저장되었는가?
□ 핸드오프만 읽고 다음 세션 시작 가능한가?
□ 진행 중인 코드 변경이 설명되었는가?
□ 사용자 마지막 요청이 완료/기록되었는가?
□ STATE.md 업데이트 검토했는가? (변화 없으면 스킵 OK)
```
하나라도 NO → 보완 후 진행.

## Phase 5: Compact 안내

`/compact`는 Claude Code CLI 내장 명령어로, 스킬에서 직접 호출 불가.
검증 통과 후 사용자에게 안내:

"checkpoint 완료. `/compact` 실행하면 컨텍스트가 압축됩니다. 핸드오프: memory/session-handoff-LATEST.md"

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [WRITE] 미완료 항목 핸드오프 파일에 기록 | 완료된 항목 보존 (삭제가 맞음) |
| [EDIT] MEMORY.md 신규/stale 항목 업데이트 | 코드 변경 또는 기능 구현 |
| [EDIT] STATE.md PENDING/블로커/변경이력 업데이트 (변화 있을 때만) | STATE.md 내용 전체 재작성 |
| [READ] Phase 1~5 보존 검증 체크리스트 실행 | `/compact` 명령 직접 호출 (CLI 전용) |
| [READ] 세션 핸드오프 단일 파일 유지 | 버전 번호 핸드오프 파일 생성 (v1, v2 등 금지) |
| [AGENT] Crystallization 후보 제안 (Phase 1.6) | forge 직접 실행 (유저 승인 후에만) |
| [EDIT] tasks/lessons.md — Reflexion 추출 lesson 추가/업데이트 (Phase 1.7) | 기존 lesson 삭제 또는 conf 0.3 미만 강제 조정 |
| [EDIT] tasks/lessons.md — Monthly Synthesis 섹션 업데이트 (Phase 3.6, 조건부) | Synthesis 섹션 삭제 또는 원본 lesson 수정 |
| [WRITE] `~/.claude/.harness/invocations/YYYY-MM.jsonl` — Invocation Log realtime append (Phase 1.6.5) | 기존 JSONL 항목 수정 또는 삭제 |
| [WRITE] `~/.claude/.harness/invocations/YYYY-MM.jsonl` — Phase 3.7 fallback append (Phase 1.6.5 실패 시만) | session_id 중복 무시한 append (idempotency 위반) |
| [READ+EDIT] MEMORY.md Key Files 경로 3~5개 Glob 검증 → stale 즉시 수정 (Phase 3.8) | Key Files 전체 섹션 재작성 |
| [WRITE] `~/.claude/.harness/interventions/YYYY-MM.jsonl` — Intervention Log append (Phase 1.8) | 기존 항목 수정 또는 삭제 |

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| `MEMORY.md` 기존 섹션 덮어쓰기 | medium | L1+L3 |
| `STATE.md` PENDING 항목 삭제 | medium | L1+L3 |
| forge 자동 실행 (crystallization) | medium | L1+L3 |

- **L1 (Invariants)**: Invariant 1 — 핸드오프 단일 파일 유지. Invariant 4 — crystallization 제안만, 자동 실행 금지.
- **L3 (User Approval)**: STATE.md PENDING 삭제 전 트리거 충족 확인. forge 실행은 유저 명시 승인 후.

---

## Invariants (never violate)

1. **핸드오프는 단일 파일**: `memory/session-handoff-LATEST.md`만 존재. 버전 번호 파일(`session-handoff-v2.md` 등) 생성 금지. Violation → 다음 세션에서 어느 파일이 최신인지 알 수 없어 컨텍스트 복구 실패.

2. **미래 지향 작성**: 핸드오프에 "이 세션에서 한 것" 나열 금지. "다음 세션에서 해야 할 것"만 기록. Violation → 핸드오프가 changelog가 되어 실제 시작점을 잃음.

3. **보존 검증 없이 compact 안내 금지**: Phase 4 체크리스트를 하나라도 통과 못하면 compact를 안내하지 않는다. Violation → 미완료 작업이 압축에서 소실.

4. **Crystallization 제안만, 실행 금지**: Phase 1.6에서 반복 워크플로우 감지 시 `/forge` 실행 제안만 한다. 유저 승인 없이 자동 승격 금지. Violation → 불필요한 스킬이 raw 워크플로우 기반으로 생성되어 라이브러리 오염.

---

## Error Recovery 

실패 감지 시: **Stop → Classify → Apply Recovery → Report & Resume**.

| 실패 유형 | 감지 조건 | 복구 경로 |
|---------|---------|--------|
| `tool_failure` | Write/Edit 실패, 파일 크기 0, 경로 없음 | 경로 재확인 후 재시도 1회. 3회 실패 → 유저에게 에러 보고 + BROKEN 라벨 |
| `input_error` | Phase 1 추출 결과 비어있음 (세션 데이터 없음) | Discard If 체크 후 중단 또는 최소 핸드오프(현 상태만) 생성 |
| `missing_data` | MEMORY.md / context-log.md 파일 미존재 | 파일 생성 (빈 템플릿) 후 재시도. 생성 불가 시 유저 보고 |
| `logic_inconsistency` | Phase 4 체크리스트 실패 + Phase 1 완료 충돌 | Phase 1 재실행. 재실행 후도 실패 → PARTIAL 라벨, 구체 결함 명시 |

## Truthful Reporting

이 스킬은 핸드오프 저장 후 상태 보고 시:
1. **no mock deception**: "저장 완료" 표기 전 실제 파일 크기·줄수 재확인 (Write 결과 검증).
2. **no test façade**: Phase 4 보존 검증 체크리스트 중 실제 skip한 항목은 `⚠️ SKIPPED: reason` 명시. 통과 위장 금지.
3. **no silent brokenness**: 최종 상태 라벨 — `WORKING` (5 Phase 전부 완료) / `PARTIAL` (일부 누락, 구체 결함 bullet) / `BROKEN` (핸드오프 저장 실패). 모호 상태로 종료 금지.

---

## Output

- **`memory/session-handoff-LATEST.md`** — 미완료 항목 + 미결 의사결정 + 잔존 이슈만 포함. 200줄 이내.
- **메모리 파일** — 신규/stale MEMORY.md 항목 업데이트 (해당 시)
- **대화창 안내** — compact 준비 완료 확인 + `/compact` 실행 지시

---

## Rationalization Table

| 합리화 | 반박 |
|--------|------|
| "완료된 항목도 참조용으로 남겨두면 좋지 않을까" | 아니다. 완료된 항목이 남으면 핸드오프가 changelog가 된다. git history가 보존하므로 삭제가 정확한 동작. |
| "Phase 4 체크리스트 하나가 NO지만 어차피 괜찮을 것 같아서..." | Invariant 3 위반. 체크리스트가 존재하는 이유가 정확히 이 순간이다. NO 상태에서 compact 안내 금지. |
| "session-handoff-v2.md로 저장하면 이전 것도 안 잃는데..." | Invariant 1 위반. git history가 이전 버전을 보존한다. 버전 번호 파일은 "최신이 어느 것?" 혼란을 만들어 컨텍스트 복구를 실패시킨다. |
| "Phase 1.6에서 반복 감지됐는데 바로 forge 돌려서 스킬 만들어버리자" | Invariant 4 위반. 유저가 실제 반복할 작업인지 판단해야 함. 자동 승격은 1회성 탐색까지 스킬화해서 라이브러리 오염. 제안만, 실행은 유저 승인 후. |
| "세션이 짧아서 Phase 1.5는 넘어가도 될 것 같은데" | Phase 1.5는 2분이면 된다. 영구 사실 하나를 놓치면 다음 세션이 다시 발견해야 한다. 실행할 것. |
| "반복 워크플로우 감지됐지만 시그니처가 너무 단순해서 그냥 넘어가자" | Phase 1.6 "불발 조건"에 해당하면 정상. 하지만 3회+ 반복됐는데 "단순"으로 분류하려는 충동은 대개 측정 귀찮음. context-log.md `[ref:N]` 누적으로 다음 세션에 재평가되게 기록 남길 것. |
| "이 세션은 완벽해서 Reflexion할 게 없어" | Phase 1.7는 "반성 없음" 도 정당한 결과다. 하지만 완벽 세션은 드물다. 유저 불만 신호 한 번이라도 있었으면 lesson이 없을 수 없다. "없다"는 분석 skip이 아니라 분석 결과가 없어야 허용. |
| "Reflexion에서 나온 lesson은 내일 추가할게" | Invariant 위반. lesson은 세션 종료 전에 기록해야 다음 세션이 사용할 수 있다. compact 후에는 근거 맥락이 사라진다. |

---

## 짝

이 스킬은 세션 라이프사이클의 닫기 절반이다.
`/session-start` → 작업 → `/session-checkpoint`

둘 다 설치하거나 둘 다 설치하지 않는다 — 짝으로 설계됨.

---

## Examples

### ✅ GOOD — 미래 지향 핸드오프 + 보존 검증 통과
```markdown
## 지금 해야 할 것 (우선순위 순)
1. **MEMORY.md 다이어트** — Key Files 섹션 트리밍. `wc -c` → 24KB 미만 목표
2. **Few-shot 5개** — code-reviewer/verification/brainstorming/subagent-dev/session-checkpoint

## 미결 의사결정
- 2-R3 연결 방식: dashboard 신규 탭 vs Telegram `/research QUERY` · urgency: H

## 잔존 이슈
- daily_collect FDR slow run 원인 미추적 (yfinance 1.2.0 timeout 의심) · risk: M
```
Phase 4 체크리스트: ✅ 미완결 의사결정 기록 ✅ 핸드오프만으로 시작 가능 ✅ 완료 항목 삭제
최종 상태: WORKING

### ❌ BAD — 완료 항목 나열 + 다음 세션 무용
```markdown
## 오늘 한 일
- Financial Report 탭 15번째 통합 완료 (commit 2660e8c)
- SSL v1.6 마이그레이션 15개 완료
- KOSDAQ .KQ concurrent workers 검증 완료
- pre-push 3개 Critical/High 수정
```
→ "한 일 목록"은 changelog이지 핸드오프가 아님. 다음 세션이 무엇을 해야 할지 알 수 없음. Invariant 2 위반.
