[English](../README.md) | 🌐 **한국어** | [日本語](README.ja.md) | [中文](README.zh.md) | [Español](README.es.md)

# sovereign-skills v6.5.5

Claude Code 프로젝트 전체 라이프사이클을 위한 20개 스킬 — 셋업부터 일일 워크플로우, 코드 리뷰, 세션 관리, 거버넌스까지. 각 스킬은 독립 사용 가능하며, 전체 시퀀스는 모든 단계를 커버합니다.

> **v6.5 변경사항:** 신규: `eval-leakage-audit`(eval/metric/holdout이 실제로 독립된 외부 그라운드트루스를 확보하는지, 아니면 순환 자기확인인지 8-패턴 taxonomy로 감사 — 읽기 전용), `doc-drift`(Claude Code가 컨텍스트로 로드하는 메모리/문서 — CLAUDE.md/MEMORY.md/skills/agents/commands — 를 구식 주장·상호 모순·위험/모호 표현 3종으로 감사해 우선순위 수정 목록 생성). 업데이트: `project-init`(대소문자 구분 파일시스템에서 스킬 로드 실패를 유발할 수 있는 `skill.md`→`SKILL.md` 오탈자 수정 + Phase 3 템플릿을 `references/templates.md`로 외부화), `pre-push` → v3.6(시크릿 스캐너 패턴 2종 추가 — f11 diff 내 프롬프트 인젝션 문자열, f12 non-PyPI 공급망 인덱스 URL — + Step 0 Hook 파이프라인 건강 점검), `scope`(Mid-Task Scope Drift 10배 발견 규칙 추가), `collab-audit`(Step 0.6 소스 위생 필터 추가 — 자동파생 서브에이전트/스레드 세션을 유기적 유저 세션으로 오인하지 않도록 제외), `full-audit`/`integration-intake`(둘 다 Safety Layers 섹션 추가; `integration-intake`는 Phase 1.8 M-axis 표면선택 단계도 추가 — 패턴이 어느 표면(프롬프트/룰/훅/스킬)에 있어야 하는지 라우팅 전에 판단), `goal-lock`(`migration` 태스크 템플릿 추가), `project-overview`(Rationalization Table 추가), `stepback`(Dominant Variable 섹션 + frontmatter 필드 추가).
>
> **v6.4 변경사항:** 신규: `full-audit`(전 영역 전수감사 — 결정론 스윕+내용리뷰, 영속 커버리지맵, 오탐방지 kill-test), `integration-intake`(외부 스킬/에이전트/룰/플러그인 도입 5항목 스크리닝 게이트, provenance/인젝션 검사 포함), `clean-room`(위험인접 요청을 안전 스코프로 분리해 완전히 격리된 fresh-context 서브에이전트가 실행 — LilMGenius/paperthin의 "autobahn" 스킬을 MIT 라이선스 하에 적응, 파일시스템 격리+ledger 기록시점 업그레이드 포함). 업데이트: `goal-lock`(장기작업 체크포인트마다 CONSTRAINTS/SCOPE-Exclude 재확인 재출력), `session-checkpoint`(신규 Attestation 단계 — `handoff_attestation.py` 번들 포함 evidence-chain receipt 로그, 다음 세션 SessionStart 훅의 핸드오프 변조 탐지용).
>
> **v6.3 변경사항:** 신규: `skill-ops`(스냅샷/롤백 + 사용률 + 호출 추적 허브), `next-action`(핸드오프/git/lessons/STATE 읽고 임팩트순 상위3개 다음 행동 제안), `project-overview`(결정론 크로스프로젝트 현황 지도). `code-autopsy` → v7.1(질문별 세부 체크 강화), `pre-push` → v3.5(공급망 IOC 9패턴), `goal-lock`/`session-checkpoint`/`session-start`/`scope`/`stepback`/`freeze` 전부 강화. 기존 12개 스킬 전부에 `not_for`/`see_also` frontmatter 추가로 발견성 개선.

---

## 빠른 시작

**신규 프로젝트 (15분):**
```
/project-init       →  CLAUDE.md + ROADMAP + .gitignore + .env.example
/setup              →  rules/ + hooks + memory/ + 에이전트 라우팅 + 팀
이후 매일:
  /session-start      세션 시작 시
  /scope              기능 구현 전 (IN/OUT/종료 기준 정의)
  /freeze             구현 전 (수정 가능 영역 선언)
  /goal-lock          목표 잠금, PLAN→DO→VERIFY 루프 강제
  /stepback           언제든 — 방향 점검, 10줄
  /next-action        언제든 — 현재 상태 읽고 상위3개 다음 행동 제안
  /code-autopsy       12Q 코드 리뷰 + 심각도 점수 + 배포 판정
  /pre-push           push 전 (시크릿 스캔 + AI 리뷰)
  /session-checkpoint 세션 종료 시
```

**기존 프로젝트 (5분):**
```
/project-check      →  4개 차원 점수 + 심각도별 갭 목록
/code-autopsy       →  12Q 정량 코드 리뷰 (어떤 LLM에서든 독립 프롬프트로 사용 가능)
/collab-audit       →  14개 섹션 AI 협업 진단
```

**거버넌스 (필요 시):**
```
/integration-intake →  외부 스킬/에이전트/룰/플러그인 도입 전 — 5항목 스크리닝 게이트
/full-audit         →  전체 영역(코드베이스/문서/스킬/메모리/설정) 전수감사 + 커버리지맵
/clean-room         →  요청에 안전인접 요소와 안전한 작업이 섞여 있을 때
/eval-leakage-audit →  eval/metric/holdout을 신뢰하기 전 — 순환 자기확인 여부 점검
/doc-drift          →  로드된 컨텍스트(CLAUDE.md/MEMORY.md/skills) 감사 — 구식/모순 표현
```

---

## 스킬 목록

### 셋업 단계

| 스킬 | 기능 |
|------|------|
| [project-init](../project-init/) | 인터뷰 기반 프로젝트 스캐폴딩 — 템플릿이 아닌 의사결정으로 CLAUDE.md, ROADMAP, .gitignore, .env.example 생성 |
| [setup](../setup/) | Claude Code 인프라 + 에이전트 팀 — rules, hooks, memory, 라우팅, 에이전트 설치를 한 번에 |

### 일일 워크플로우

| 스킬 | 기능 |
|------|------|
| [scope](../scope/) | 구현 전 IN/OUT/종료 기준 정의. Quick 모드 (3개 질문) 또는 Full 모드 (레이어드 스펙) |
| [freeze](../freeze/) | 수정 가능 영역 선언 — 나머지는 동결. 구현 중 범위 변경 방지 |
| [goal-lock](../goal-lock/) | 에이전트 규율 엔진 — 목표 잠금, PLAN→DO→VERIFY→FINALIZE→OUTPUT 루프 강제, 13가지 성공 위장 패턴 탐지 |
| [pre-push](../pre-push/) | 필수 pre-push 파이프라인 — 시크릿 스캔 (12패턴), 빌드/테스트, 린트, 병렬 AI 코드 리뷰. Critical/High 발견 시 push 차단 |

### 코드 리뷰

| 스킬 | 기능 |
|------|------|
| [code-autopsy](../code-autopsy/) | **신규.** 12Q 정량 코드 리뷰 — 4축 점수 (Security/Stability/Robustness/Operability), 심각도 앵커 테이블, 배포 판정 (SHIP/FIX/RISKY/BLOCK), Factuality Gate, CapCode 점수 gaming 탐지, CEF 위장 에러 탐지. 독립 프롬프트로 어떤 LLM에서든 사용 가능 |

### 관점 전환

| 스킬 | 기능 |
|------|------|
| [stepback](../stepback/) | **신규.** 원샷 관점 리셋 — 1개 추상적 리프레이밍 질문 + 3가지 빠른 점검 (범위 이탈, 사이드이펙트, 더 나은 접근) 10줄 이내. 작업 중 언제든 사용 |
| [next-action](../next-action/) | **신규.** 핸드오프/git/lessons/STATE 읽고 임팩트순 상위3개 다음 행동 제안. 제안만, 실행 안 함. 언제든 사용 |

### 세션 관리

| 스킬 | 기능 |
|------|------|
| [session-start](../session-start/) | 이전 세션 핸드오프 로드, 교훈 리뷰, 건강 검진, 우선순위 액션과 함께 "준비" 신호 출력 |
| [session-checkpoint](../session-checkpoint/) | compact 전 세션 컨텍스트 저장 — 핸드오프 파일, 메모리 업데이트, 교훈 추출, 반성 (뭐가 잘못됐고, 다음에 어떻게 할지) |

### 품질

| 스킬 | 기능 |
|------|------|
| [project-check](../project-check/) | 기존 프로젝트를 4개 차원으로 스캔: 인프라, 보안, 품질, 하네스. 심각도순 갭 정렬 |
| [collab-audit](../collab-audit/) | 14개 섹션 AI 협업 감사 — 실제 작업 패턴(설문 아님)을 분석해 행동 프로필, 사각지대, 성장 방향 생성 |

### 운영

| 스킬 | 기능 |
|------|------|
| [skill-ops](../skill-ops/) | **신규.** 스킬/에이전트 운영 허브 — 스냅샷/롤백 + 사용률 + 호출 추적 3모드 |
| [project-overview](../project-overview/) | **신규.** 등록된 프로젝트들의 세션 핸드오프로부터 결정론 크로스프로젝트 현황 지도 생성 |

### 거버넌스

| 스킬 | 기능 |
|------|------|
| [full-audit](../full-audit/) | **신규.** 전 영역(코드베이스/문서/스킬/메모리/설정) 전수감사 — 결정론 스윕 + 내용리뷰 2계층 방법론, 오탐방지 kill-test, 영속 커버리지맵 |
| [integration-intake](../integration-intake/) | **신규.** 외부 패턴(스킬/에이전트/룰/플러그인/MCP) 도입 5항목 스크리닝 게이트 — 기존 자산 대비 중복 검사 + 도입 콘텐츠 provenance/인젝션 검사 |
| [clean-room](../clean-room/) | **신규.** 위험인접 요청을 안전 스코프로 분리해 완전히 격리된 fresh-context 서브에이전트가 실행 — 적대적 검증 패스 + descope ledger |
| [eval-leakage-audit](../eval-leakage-audit/) | **신규.** eval/metric/holdout이 실제로 독립된 외부 그라운드트루스를 확보하는지, 아니면 순환 자기확인인지 8-패턴 taxonomy로 감사. 읽기 전용 |
| [doc-drift](../doc-drift/) | **신규.** Claude Code가 컨텍스트로 로드하는 메모리/문서(CLAUDE.md/MEMORY.md/skills/agents/commands)를 구식 주장·상호 모순·위험/모호 표현으로 감사 — 우선순위 수정 목록 생성 |

---

## 라이프사이클 흐름

```
┌─────────────────── 셋업 (1회) ─────────────────────┐
│  /project-init  →  /setup                            │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────── 일일 루프 ──────────────────────┐
│  /session-start                                      │
│       ↓                                              │
│  /scope → /freeze → /goal-lock → 작업                │
│       → /stepback (언제든) → /code-autopsy → /pre-push│
│       ↓                                              │
│  /session-checkpoint                                 │
└──────────────────────────────────────────────────────┘
         ↓
┌─────────────────── 수시 ───────────────────────────┐
│  /stepback         (관점 리셋 — 언제든)              │
│  /project-check    (건강 감사)                       │
│  /collab-audit     (행동 진단)                       │
│  /integration-intake (외부 자산 도입 전)             │
│  /full-audit       (전체 영역 전수감사)              │
│  /clean-room       (안전인접 스코프 분리)            │
│  /eval-leakage-audit (eval 순환논리 점검)            │
│  /doc-drift        (로드된 컨텍스트 드리프트 감사)   │
└─────────────────────────────────────────────────────┘
```

---

## 설치

### 방법 A: 스킬 복사 (가장 간단)

```bash
# 전체 스킬 설치
git clone https://github.com/AlexZio00/sovereign-skills.git
cd sovereign-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# 또는 개별 스킬 설치
cp -r goal-lock ~/.claude/skills/
```

### 방법 B: 마켓플레이스 (sovereign-plugins)

이 리포는 Claude Code 마켓플레이스입니다. 한 번 등록하면 스킬을 탐색/설치할 수 있습니다:

```bash
# Claude Code에서 sovereign-plugins 마켓플레이스 추가
# 설정 → 플러그인 → 마켓플레이스 추가 → https://github.com/AlexZio00/sovereign-skills.git
```

각 스킬에 개별 `.claude-plugin/plugin.json` 메타데이터도 포함되어 있습니다.

트리거 명령어(예: `/goal-lock`)를 Claude Code에서 입력하면 스킬이 실행됩니다.

### 방법 C: Codex / Cursor (npx)

각 스킬에 `agents/openai.yaml`이 포함되어 있습니다:

```bash
# Codex용 스킬 설치
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent codex -g -y

# Cursor용 스킬 설치
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent cursor -g -y

# Claude Code용 설치 (방법 A 대안)
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent claude-code -g -y
```

SKILL.md 내용은 범용입니다 — 마크다운 지시문을 읽는 모든 LLM에서 작동합니다.

### 요구사항

- **Claude Code**: CLI, 데스크톱 앱, 또는 웹 앱 ([claude.ai/code](https://claude.ai/code))
- **Codex**: OpenAI Codex (`npx skills` 지원)
- **Cursor**: Cursor IDE (스킬 플러그인 지원)
- 스킬 디렉토리: `~/.claude/skills/` (Claude Code) 또는 에이전트별 경로
- `pre-push`는 Perl 필요 (`scan_secrets.pl` 포함)

---

## v6.2 변경사항

### 신규 추가
- **stepback** — 원샷 관점 리셋. 추상적 리프레이밍 질문 1개(DeepMind step-back 패턴) + 빠른 점검 3가지(범위 이탈, 사이드이펙트, 더 나은 접근)를 10줄 이내로 생성. 읽기 전용, 에이전트 없음, 코드 없음. 구현 중 언제든 사용해 올바른 문제를 올바른 수준에서 풀고 있는지 확인. 출처: team-attention/hoyeon.

### 업데이트
- **code-autopsy** — 메타탐지 게이트 추가: 점수 조작 탐지용 CapCode 천장 메트릭, 제약 회피 가짜 에러 탐지용 CEF.
- **collab-audit** — 13→14개 섹션. 새 섹션 12: 사고 수준 궤적 (정보요청자→생각 설계자 5단계 모델 + 시간 변화 추적 + AI 귀속 정정).
- **goal-lock** — Ralph Wiggum 조기 완료 탐지(12번째 위장 패턴) + VERIFY 단계 검증 추적성(모든 주장이 실제 도구 호출로 추적되어야 함).
- **session-checkpoint** — 핸드오프 명확성 자가검사 추가(핸드오프 작성 후 2개 앵커 질문).
- **session-start** — 컨텍스트 부패 방지(오래된 핸드오프 항목용 슬라이딩 윈도우).
- **pre-push** — 새로 추가된 의존성에 대한 3-IOC 공급망 점검 추가.
- **scope** — 금기 필드 추가(선택한 접근이 적합하지 않은 조건).
- **freeze** — Thaw Protocol 추가(정식 언프리즈 워크플로우 + 영향 반경 확인 + 3번 언프리즈 경고).
- **project-init** — `.env.example` 템플릿 확장(OAuth, 외부 서비스, 모니터링 섹션) + 보안 기준선 노트.
- **project-check** — 점수 델타 추적 추가(현재 vs 이전 스캔 결과 비교).
- **setup** — Tier 0 위반 테스트 실패에 대한 Redesign Protocol 추가(3가지 옵션 에스컬레이션).

---

## v6.1 변경사항

### 신규 추가
- **code-autopsy** — 12Q 정량 코드 리뷰 프롬프트(Code Autopsy v7.0). 설계부터 관찰성까지 12개 분석 질문. 4축 복합 점수(Security × 0.35 + Stability × 0.30 + Robustness × 0.20 + Operability × 0.15). 가중 수식이 있는 심각도 앵커 테이블. CRITICAL 하드 캡이 있는 배포 판정. Factuality Gate(보고 전 자체 검증). 파일 간 영향 분석. Quick 모드 및 Diff 모드. 근거: Google eng-practices, Johnson et al. 2019, Parnas 1972. 어떤 LLM에서도 독립 프롬프트로 작동 — Claude Code 전용이 아님.

---

## v6.0 변경사항

### 신규 추가
- **goal-lock** — PLAN→DO→VERIFY→FINALIZE→OUTPUT 루프가 있는 에이전트 규율 엔진. 13가지 성공 위장 패턴 탐지(테스트 삭제, mock 감싸기, 임계값 완화 등). 작은 변경용 Quick 모드(3개 필드), 나머지는 Full 모드(7개 필드).

### 병합
- `harness-init` + `team-init` → **setup** — 인프라와 에이전트 팀이 한 번에
- `brief` + `adr` → **scope** — ADR 기능이 내장된 범위 정의
- `retro` → **session-checkpoint** — 반성은 이제 session-checkpoint 내 Phase 1.7 Reflexion

### 제거
- `token-audit` — 대신 `npx ccusage` 직접 사용 또는 패턴으로 ccusage 스킬 빌드
- `adr`(독립형) — scope에 흡수됨
- `retro`(독립형) — session-checkpoint에 흡수됨

### 업그레이드
- 모든 스킬: Dominant Variable, Key Assumptions, Error Recovery, Safety Layers 추가
- 모든 스킬: 액션 태그가 있는 Scope Boundary([READ]/[WRITE]/[BASH]/[AGENT])
- `session-checkpoint`: Memento CoT 압축, Reflexion, Invocation 로깅
- `pre-push`: 큰 diff 결정론 번들링, Discard If 조건
- `collab-audit`: 안티패턴 플래그, Key Assumptions

---

## 에이전트 설계 패턴 커버리지

이 20개 중 17개 스킬(원래 라이프사이클 세트, v6.4 거버넌스 신규 스킬, v6.5 감사 신규 스킬 — v6.3 운영 신규 스킬은 아직 매핑 안 됨)은 25개의 알려진 에이전트 설계 패턴 중 17개를 구현합니다([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| 패턴 | 구현 스킬 | 방법 |
|------|----------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | 전체 라이프사이클 체인 |
| **Parallel Execution** | pre-push | 병렬 AI 코드 리뷰 에이전트 |
| **Loop (Retry)** | goal-lock | VERIFY 실패 → PLAN 재입장, 상한선 있음 |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | 독립적 code-reviewer + security-reviewer; 12Q 구조화 리뷰; full-audit의 Phase 2 팬아웃 리뷰어 패스; eval-leakage-audit은 eval이 독립적 그라운드트루스를 확보하는지 순환 자기확인인지 비평 |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE 통과 |
| **Coordinator/Router** | setup | 에이전트 라우팅 규칙 생성 |
| **Plan-and-Execute** | goal-lock, scope | 실행 전 검토 가능한 계획 |
| **ReAct** | project-check | 조사 → 점수 → 경로 권장 |
| **Reflexion** | session-checkpoint | Phase 1.7: 실패 분석 → 다음 세션용 교훈 |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES, Critical/High가 push 차단; integration-intake의 도입 전 5항목 스크리닝 게이트 |
| **Custom Logic** | pre-push | 결정론 시크릿 스캔(Perl) + AI 리뷰 |
| **Event-Driven** | session-start | 세션 열림 시 트리거, 이전 상태 로드 |
| **Guardrails/Safety** | goal-lock, clean-room | 13가지 성공 위장 패턴 탐지; clean-room은 안전인접 스코프를 carve하여 격리된 서브에이전트로 실행 |
| **Memory Management** | session-checkpoint, doc-drift | 핸드오프 파일 + 메모리 업데이트 + 교훈 추출; doc-drift는 컨텍스트로 로드되는 메모리/문서를 구식 주장·모순·위험 표현으로 감사 |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE 입력 시트 |
| **Step-Back Abstraction** | stepback | DeepMind step-back: 구체 → 추상 원칙 |

---

## 설계 원칙

1. **템플릿보다 인터뷰** — 빈 뼈대가 아닌, 질문과 결정으로 채워진 콘텐츠 생성
2. **신뢰보다 검증** — 완료 증거는 실행해야지, 가정하면 안 됨. "통과할 것 같다"는 검증이 아님
3. **코드 전에 범위** — 파일 수정 전 IN/OUT/종료 기준 정의. 안 바꾸는 건 동결
4. **정직한 보고** — WORKING / PARTIAL / BROKEN 라벨. 조용한 고장도, mock 기만도 없음
5. **세션 연속성** — 핸드오프로 시작, 체크포인트로 마감. 컨텍스트는 세션을 넘어 생존

---

## 스킬 간 연결 관계

스킬은 frontmatter의 `see_also`(관련 스킬)와 `not_for`(오용 방지 가드레일)로 관계를 선언합니다. 주요 관계:

| 스킬 | 연결 대상 | 관계 |
|------|----------|------|
| `scope` | `goal-lock`, `freeze` | scope는 무엇을 만들지 정의하고, freeze는 수정 가능 영역을 잠그고, goal-lock은 실행 루프를 강제 |
| `freeze` | `scope`, `goal-lock` | freeze는 scope의 기획과 goal-lock의 루프 강제를 잇는 수동 영역잠금 |
| `goal-lock` | `scope`, `freeze` | goal-lock은 scope/freeze가 정한 경계 안에서 작동하는 실행시점 규율 레이어 |
| `stepback` | `next-action` | stepback은 방향 점검("올바른 문제를 풀고 있나"), next-action은 행동 추천("임팩트순 다음 뭐") |
| `next-action` | `session-start`, `stepback` | next-action은 현재 상태를 읽어 추천하고, session-start는 이전 세션 상태를 복원 |
| `session-start` | `session-checkpoint` | 라이프사이클 짝 — 세션을 열고 닫음 |
| `session-checkpoint` | `session-start`, `setup` | 세션을 닫고, setup은 새 프로젝트를 엶 |
| `code-autopsy` | `pre-push` | code-autopsy는 깊이 있는 온디맨드 12Q 리뷰, pre-push는 매 push 전 실행되는 빠른 자동 파이프라인 |
| `skill-ops` | `project-overview` | skill-ops는 스킬/에이전트 라이프사이클(스냅샷/롤백/사용률)을 관리하고, project-overview는 여러 프로젝트의 현황을 집계 |
| `integration-intake` | `full-audit` | integration-intake는 외부 자산 1건의 도입 여부를 게이트하고, full-audit은 (기존 스킬/에이전트 인벤토리를 포함해) 영역 전체의 드리프트·갭을 훑음 |
| `full-audit` | `code-autopsy`, `project-check` | full-audit은 더 넓은 다영역 전수감사 + 커버리지맵을 남기고, code-autopsy는 파일 단위 12Q, project-check는 4차원 점수로 남음 |
| `clean-room` | `goal-lock` | clean-room은 작업 도중 스코프에 안전인접 요소와 안전한 작업이 섞였을 때 발화하고, goal-lock은 그것이 끼어드는 PLAN→DO→VERIFY 루프 |
| `doc-drift` | `full-audit` | doc-drift는 컨텍스트로 로드되는 메모리/문서(CLAUDE.md/MEMORY.md/skills/agents)만 드리프트·모순으로 감사하고, full-audit은 커버리지맵을 갖고 영역 전체를 전수감사 |
| `eval-leakage-audit` | `full-audit`, `code-autopsy` | eval-leakage-audit은 eval/metric/holdout이 순환논리인지(측정 무결성) 점검하고, full-audit과 code-autopsy는 eval의 독립성이 아니라 코드/영역을 리뷰 |

다이어그램 (화살표 = "넘겨준다" / "정보를 준다"):

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (언제든, 어느 단계든)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (상태 읽고 추천)
                                   │
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift
                      (온디맨드 거버넌스, 어느 단계든)
```

---

## 라이선스

MIT — [LICENSE](../LICENSE) 참조.

## 기여

이슈와 PR 환영합니다. 라이프사이클에 맞는 스킬을 만들었다면 PR을 열어주세요.

## 연락처

커스텀 스킬 개발 DM [@AlexZio00](https://x.com/AlexZio00)
