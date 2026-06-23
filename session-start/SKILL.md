---
skill_type: lifecycle
tools: Read
triggers:
  - "/session-start"
  - "세션 시작"
  - "이어서 해줘"
  - "어디부터"
  - "start session"
name: session-start
description: "세션 시작 시 핸드오프 로드, 레슨 리뷰, 준비 신호 출력. 트리거: '/session-start', 'start session', '세션 시작', '이어서 해줘', '어디까지 했지'. 버리는 경우: 첫 세션 (핸드오프 없음), 유저가 '새로 시작' 요청, 맥락 무관한 단발 질문."
user_invocable: true
# (제거 2026-06-10) context: !cat — CC 미지원 커스텀 태그, YAML 파서 파괴. 핸드오프 주입은 SessionStart 훅 담당
---

# Session Start

## Dominant Variable
핸드오프가 **다음에 할 것**을 담고 있는가, 아니면 **한 것 목록**인가? 한 것 목록이면 잘못 쓰인 핸드오프다. Priority 1을 즉시 파악할 수 없으면 Phase 1을 더 깊게.


## Trigger

- `/session-start`
- "세션 시작"
- "이어서 해줘"
- "어디부터"
- "start session"

## Discard If
- `memory/session-handoff-LATEST.md` 없음 (첫 세션) → 스킵, 바로 시작
- 유저가 "새로 시작" / "컨텍스트 무시" 요청 → 스킵
- 프로젝트 무관한 단발 질문 → 스킵

> **Phase 0.5는 Discard 시에도 실행**: 설정 오류는 첫 세션·단발 질문 때도 감지 필요.

---

## Key Assumptions 
1. **memory/session-handoff-LATEST.md 존재** — 깨지면: "신규 세션" 모드로 fallback. 핸드오프 합성 금지.
2. **tasks/lessons.md 존재** — 깨지면: 레슨 리뷰 Phase 스킵.
3. **settings.json 파싱 가능** — 깨지면: 헬스체크 Phase만 스킵, 나머지 정상 진행.

## Phase 0.5: 환경 헬스체크 

> 경고만 — 세션 시작 블로킹 없음. Read 도구만 사용 (수정 금지).

**체크 1 — 모델 ID** (`~/.claude/settings.json` 읽기):
- `"model"` 필드 값 확인 → 아래 목록 외의 값이면 경고 기록:
  ```
  ["opus", "sonnet", "haiku", "fable",
   "claude-opus-4-8", "claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5",
   "claude-opus-4-5", "claude-sonnet-4-5", "claude-fable-5"]
  # [1m]/[200k] 류 컨텍스트 suffix는 strip 후 비교 (예: claude-fable-5[1m] -> claude-fable-5)
  ```
- `⚠️ settings.json model ID 무효: "{value}" — 수정 필요`
- 파일 없으면 조용히 스킵

**체크 2 — Allow Entry 누적** (`~/.claude/settings.local.json` 읽기, ):
- `permissions.allow` 배열 항목 수 카운트
- 5개 초과 → `⚠️ settings.local.json allow: N개 `
- 파일 없으면 조용히 스킵

**출력 규칙**: 양쪽 클린 → **무출력** (Phase 5 환경 알림 줄 생략). 경고 있으면 Phase 5 `**환경 알림:**` 줄에 표시.

---

## Phase 1: 핸드오프 로드

`memory/session-handoff-LATEST.md` 읽기 (위에 자동 주입됨).

추출:
- **Priority 1** — 이 세션에서 가장 먼저 해야 할 것
- **미결 의사결정** — 유저 입력 대기 중인 질문
- **잔존 이슈** — 미해결 버그 또는 블로커
- **컨텍스트 메모** — 지난 세션에서 실패한 접근 (반복 방지), 중요 인과관계

파일 비어있거나 없으면: `[핸드오프 없음 — 새로 시작]` 출력 후 종료.

---

## Phase 2: 레슨 리뷰

`tasks/lessons.md` 읽기.

### 2.0 졸업 게이트 로드 (always-on — 최우선)

`## 졸업 게이트 (Graduated Gates)` 섹션 표를 추출한다. **conf 필터와 무관하게 항상 출력** — 검증된(`conf≥0.7 AND obs≥3`) 행동게이트라 매 세션 상시 노출이 목적(Loop B 자기교정 강제층). Phase 5 `**졸업 게이트:**` 줄에 각 게이트를 `트리거 → 체크` 한 줄로 압축 표기.

**성격 (유저 명시, 2026-06-04)**: 게이트는 **"출력 → 상의 → 결정"** 도구다. 트리거 행동 직전 멈춰 체크하고, 애매하면 유저와 상의한다. **자동 실행·자동 생성 아님.** 표면화가 역할이고 결정은 유저/대화에 남는다.

섹션 없으면 조용히 스킵.

### 2.1 관련 레슨 스캔

오늘 작업과 관련된 교정 규칙 스캔:
- 코드 변경 예정 → 해당 영역 교정 규칙 확인
- 커밋/푸시 예정 → 커밋 관련 규칙 확인
- 디버깅 예정 → 디버깅 안티패턴 확인

**v2 메타 라인 (`> conf · seen · obs`) 활용 (2026-04-28~)**:
- `conf ≥ 0.7` (검증됨/핵심) → **본문 1줄 플래그** 우선 노출 (시그널)
- `conf 0.5` (보통/Opus 트리거) → **제목만 1줄** 노출
- `conf < 0.5` (시험적/미결) → **TOC 헤더만** 또는 스킵 (노이즈)
- `seen` 30일 이내 + `obs ≥ 3` lesson은 활성 패턴 — 우선 노출
- v2 메타 없는 legacy lesson → 보통 처리 (backward compat)

해당하는 규칙 1줄씩 플래그. 파일 없으면 조용히 스킵.

### 2.2 모델 차이 분석 리마인드 (반자동 — 결정론 체크)

> 모델별 행동 차등 보상의 분석 트리거. 설계: `docs/plans/2026-06-11-opus-fable-porting-harness-design.md` §4②. 쌓인 model 태그를 주기적으로 패턴→룰로 전환하기 위한 리마인드(완전 자동 cron은 로컬 불가).

결정론 집계 ( — 셈은 기계):
- `tasks/lessons.md`에서 `model:` 필드 보유 lesson 수 카운트 + `~/.claude/.harness/interventions/*.jsonl`에서 `"model"` 필드 보유 항목 수
- `~/.claude/memory/model-diff-ledger.md` 헤더의 `last-analysis: YYYY-MM-DD` 읽기 (없으면 가장 오래된 model 태그일 기준)
- **신규 태그** = `last-analysis` 이후 `seen`/`date`가 찍힌 태그 수

리마인드 조건 (둘 다 충족 시만):
- `(today − last-analysis) ≥ 14일` **AND** 신규 model 태그 ≥ 5건
- → Phase 5 `**모델 분석:**` 줄에 `💡 모델 차이 분석 권장 (신규 N건 / M일 경과) — "모델 차이 분석" 호출 시 집계+승격후보 보고` 출력
- 미충족(경과 부족 OR 태그 부족) → **무출력** (빈 분석 방지, 노이즈 금지)

파일/필드 없으면 조용히 스킵. model 태그가 아직 0이면 이 단계 전체 무출력 (Phase 0 미가동 = 정상).

---

## Phase 3: 글로벌 상태 확인

`C:\Users\지오\.claude\STATE.md` 읽기.

확인:
- 미결 의사결정 중 이 세션에서 해결 가능한 것?
- 활성 블로커 중 지금 건드릴 수 있는 것?

STATE.md 없으면 스킵.

---

## Phase 4: 메모리 빠른 점검

### 4.1 선택적 로드 (2-M2, 2026-04-24)

`memory/MEMORY.md` 읽되 태그 기반으로 필터링한다.

**규칙:**
- `<!-- #always -->` 태그 섹션 → 전체 로드 (핵심 정보)
- `<!-- #on-demand -->` 태그 섹션 → 헤더만 TOC로 출력 (Grep으로 필요 시 접근)
- 태그 없는 MEMORY.md → **전체 로드** (backward compat)

**실행:**
1. Grep `^##.*<!-- #always -->` → 해당 섹션 Read
2. Grep `^##.*<!-- #on-demand -->` → 헤더 리스트만 추출
3. 준비 신호 하단에 TOC 출력:
   ```
   MEMORY.md (on-demand, Grep으로 접근):
   - AI Constitution 분기 현황
   - Claude 에이전트 환경
   - Known Issues & Fixes
   ...
   ```

### 4.2 스팟 체크 (기존)

1. **Stale 참조** — 핸드오프가 파일 경로나 함수명 언급 → Glob/Grep으로 1~2개 확인. 없으면 즉시 플래그.
2. **승격 대기** — `memory/context-log.md`에서 `[ref:N]` N≥3인 항목 → 지금 MEMORY.md에 추가.

1~2개 항목만 확인. 60초 넘으면 범위를 좁혀라.

MEMORY.md 없으면 스킵.

---

## Phase 5: 준비 신호 출력

```
## Session Ready

**Priority 1:** [핸드오프의 최우선 항목 — 구체적이고 실행 가능한 것]
**Priority 2:** [두 번째 항목 (있으면)]

**미결 의사결정:** [목록, 또는 "없음"]
**활성 블로커:** [목록, 또는 "없음"]

**졸업 게이트 (행동 직전 확인 · 자동 실행 아님):**
  G1 커밋/푸시 → 이 세션 "커밋해" 명시?
  G2 "없다/완료/클린" 단언 → grep/ls 확인 + "검증함/안 봄" 2줄
  G3 Agent 디스패치 → 임무 1개 + 5섹션 골격?
  G4 패턴/최적화 제안 → Glob/Grep 호출처 실측?
  G5 한글/Win 경로 → Python pathlib?
  G6 Win stdout → ASCII/_safe_print?
  (트리거 시 멈춰 확인·상의)

**레슨 플래그:** [Phase 2에서 해당 규칙, 또는 "없음"]
**메모리 알림:** [stale 참조 또는 승격 대상, 또는 "없음"]
**모델 분석:** [Phase 2.2 리마인드 조건 충족 시만 — 미충족/태그 0건이면 이 줄 생략]

**글로벌:** [STATE.md에서 이 세션 관련 항목, 또는 "없음"]
**환경 알림:** [Phase 0.5 경고 — 클린 시 이 줄 생략]
```

그 다음: `준비됐어. 어디서 시작할까?`

---

## Scope Boundary

| Does | Does NOT |
|------|----------|
| [READ] 핸드오프 + 레슨 로드 및 요약 | 코드 작성 또는 파일 수정 |
| [READ] 1~2개 stale 참조 스팟 체크 | 전체 테스트 실행 또는 프로젝트 스캔 |
| [READ] 해당 교정 규칙 플래그 | 핸드오프 파일 재작성 |
| [READ] context-log 승격 대상 MEMORY.md에 추가 | 아키텍처 또는 설계 결정 |
| [READ] settings.json 모델 ID + settings.local.json allow 엔트리 수 확인 (Phase 0.5) | CLI 버전 자동 체크 (Bash 미포함 — 터미널에서 `claude --version` 직접) |

---

## Safety Layers 

| Risky Action | Reversibility | Applied Layers |
|-------------|:-------------:|----------------|
| MEMORY.md 승격 쓰기 (ref≥3 항목) | high (git) | L1 (Invariant 1: 유일한 예외) |

- **L1 (Invariants)**: 기본 읽기 전용. 승격 쓰기 외 수정 금지.
- **L2 (Tool Restriction)**: tools: Read 전용 (frontmatter).

## Error Recovery 

| 실패 유형 | 감지 조건 | 복구 경로 |
|---------|---------|--------|
| `missing_data` | 핸드오프/lessons/MEMORY 파일 없음 | 해당 Phase 조용히 스킵 (Invariant 2). 세션 시작 차단 금지 |
| `tool_failure` | Read 도구 실패 | 해당 파일 스킵 + `⚠️ 로드 실패: [파일]` 보고 |
| `input_error` | settings.json 파싱 실패 | 헬스체크 Phase만 스킵. 나머지 Phase 정상 진행 |

## Invariants (never violate)

1. **기본적으로 읽기 전용**: session-start는 컨텍스트를 로드할 뿐 파일을 수정하지 않는다. 허용된 유일한 예외: `[ref:N≥3]` 항목을 MEMORY.md에 승격하는 것 (stale 감지 쓰기). 다른 쓰기 없음.

2. **파일 없음 = 조용히 스킵**: 핸드오프, 레슨, MEMORY.md, settings.json, settings.local.json 중 하나라도 없으면 해당 Phase를 에러 없이 스킵. 파일 부재로 세션 시작을 막지 않는다.

3. **준비 신호에 Priority 1 필수**: 출력에 반드시 구체적인 다음 액션 1개 이상을 명시한다. "세션 시작됨"만 출력하는 것은 위반 — 핸드오프에 실행 가능한 항목이 없다는 것을 명시적으로 유저에게 알려야 한다.

---

## Output

- **대화창**: 준비 신호 (우선순위 + 미결 의사결정 + 레슨 플래그)
- **쓰인 파일**: 없음 — 또는 MEMORY.md (승격 트리거된 경우만)

---

## Rationalization Table

| 합리화 | 반박 |
|--------|------|
| "핸드오프가 비어있어서 그냥 '준비됐어'라고 하면 되지" | Invariant 3 위반. 핸드오프가 진짜 비어있으면 그걸 명시해야 한다 — 그것 자체가 실행 가능한 정보다. |
| "핸드오프 읽었으니 지금 업데이트해야 할 것 같은데" | Invariant 1: session-start는 읽기 전용. 핸드오프 업데이트는 세션 종료 시 `/checkpoint-compact`에서. |
| "Phase 4 메모리 체크가 느린 것 같아서 스킵할게" | 1~2개 항목만 스팟 체크다. 느리면 너무 많이 스캔하고 있다는 신호. 범위를 좁혀서 실행. |
| "핸드오프가 없으니 코드베이스 스캔해서 만들어줄게" | Discard 조건: 핸드오프 없음 = 새로 시작. 코드베이스에서 핸드오프를 합성하지 않는다 — 저장되지 않은 컨텍스트를 만들어내는 것이다. |
| "헬스체크는 settings가 바뀔 때만 실행해도 돼" | cold-start confusion은 세션마다 발생 가능. 작년 invalid model ID 사건이 이 체크를 만든 이유다. 무출력으로 통과하면 비용 0. |
| "졸업 게이트가 떴으니 트리거 행동을 자동으로 처리하면 되겠네" | 게이트는 표면화 도구지 자동 실행 트리거가 아니다. 트리거 시점에 멈춰 확인·상의. 자동 실행/자동 생성은 유저 명시 반대 (2026-06-04). |

---

## 짝

이 스킬은 세션 라이프사이클의 시작 절반이다.
`/session-start` → 작업 → `/session-checkpoint`

둘 다 설치하거나 둘 다 설치하지 않는다 — 짝으로 설계됨.
