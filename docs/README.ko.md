[English](../README.md) | 🌐 **한국어** | [日本語](README.ja.md) | [中文](README.zh.md) | [Español](README.es.md)

# sovereign-skills v6.5.15

Claude Code 프로젝트 전체 라이프사이클을 위한 23개 스킬 — 셋업부터 일일 워크플로우, 코드 리뷰, 세션 관리, 거버넌스까지. 각 스킬은 독립 사용 가능하며, 전체 시퀀스는 모든 단계를 커버합니다.

> **v6.5.15 변경사항:** 스킬 2개 추가 — `ssot-audit`(하나의 사실이 들어 있는 모든 사본을 찾아 정본을 지정)와 `skill-trigger-auditor`(스킬과 명령이 올바르게 라우팅되는지 점검). 버그 수정: `pre-push`는 먼저 커밋하고 나중에 push해도 테스트와 린트를 건너뛰지 않는다. `project-check`는 하이픈이 들어간 API 키(`sk-ant-…`, `sk-proj-…`)도 잡아낸다. `setup`의 hook 예제는 더 이상 `bash` + `jq`가 필요 없어 Windows에서도 동작한다. 나머지 스킬의 개선: `code-autopsy`는 각 발견 사항에 NEW 또는 PRE-EXISTING 표시와 증거 등급을 붙인다. 세션 스킬은 날짜가 지난 핸드오프 항목을 표시한다. `integration-intake`는 리포를 다시 검토하기 전에 자신의 이전 판정을 먼저 조회한다. 22개 스킬 전체에 정독 감사도 했다: 번들 스크립트는 어느 설치 위치에서나 찾을 수 있고(`${CLAUDE_SKILL_DIR}`), Python 3.9+와 macOS에서 실행되며, 선택적 외부 에이전트에는 표시와 대체 수단이 붙었고, 공유 파일 형식은 [docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md)에 문서화했다. 자세한 내용은 [CHANGELOG.md](../CHANGELOG.md).

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
/collab-audit       →  작업 패턴으로 만드는 14개 섹션 AI 협업 진단
```

**거버넌스 및 감사 (필요 시):**
```
/integration-intake →  외부 스킬/에이전트/룰/플러그인 도입 전 — 5항목 스크리닝 게이트
/full-audit         →  전체 영역(코드베이스/문서/스킬/메모리/설정) 전수감사 + 커버리지맵
/clean-room         →  요청에 안전인접 요소와 안전한 작업이 섞여 있을 때
/eval-leakage-audit →  eval/metric/holdout을 신뢰하기 전 — 순환 자기확인 여부 점검
/doc-drift          →  로드된 컨텍스트(CLAUDE.md/MEMORY.md/skills) 감사 — 구식/모순 표현
/ssot-audit         →  하나의 사실이 여러 파일에 — 정본을 찾고 통합
```

**직접 스킬을 만든다면:**
```
/skill-trigger-auditor →  스킬 description을 바꾸기 전 — 라우팅 충돌과 오발동 탐지
/skill-ops             →  편집 전 스킬 스냅샷/롤백, 실제로 쓰이는 스킬 확인
/project-overview      →  여러 프로젝트를 한눈에 보는 현황 지도
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
| [scope](../scope/) | 구현 전 IN/OUT/종료 기준 정의. Quick 모드 (3개 질문) 또는 Full 모드 (레이어드 스펙). Full 모드에 `coverage_check.py`(요구사항↔태스크 대조) 포함 |
| [freeze](../freeze/) | 수정 가능 영역 선언 — 나머지는 동결. 구현 중 범위 변경 방지 |
| [goal-lock](../goal-lock/) | 에이전트 규율 엔진 — 목표 잠금, PLAN→DO→VERIFY→FINALIZE→OUTPUT 루프 강제, 16가지 성공 위장 패턴 탐지 |
| [pre-push](../pre-push/) | 필수 pre-push 파이프라인 — 시크릿 스캔 (14패턴), 빌드/테스트, 린트, 병렬 AI 코드 리뷰. push가 실제로 담고 있는 것(스테이징된 변경 + 아직 올라가지 않은 커밋)을 검사. Critical/High 발견 시 push 차단 |

### 관점 전환

| 스킬 | 기능 |
|------|------|
| [stepback](../stepback/) | 원샷 관점 리셋 — 1개 추상적 리프레이밍 질문 + 3가지 빠른 점검 (범위 이탈, 사이드이펙트, 더 나은 접근)과 계속/중단 판정을 10줄 이내로. 작업 중 언제든 사용 |
| [next-action](../next-action/) | 핸드오프/git/lessons/STATE 읽고 임팩트순 상위3개 다음 행동 제안. 제안만, 실행 안 함. 언제든 사용 |

### 세션 관리

| 스킬 | 기능 |
|------|------|
| [session-start](../session-start/) | 이전 세션 핸드오프 로드, 교훈 리뷰, 건강 검진, 우선순위 액션과 함께 "준비" 신호 출력. 날짜가 이미 지난 핸드오프 항목을 표시 |
| [session-checkpoint](../session-checkpoint/) | compact 전 세션 컨텍스트 저장 — 핸드오프 파일, 메모리 업데이트, 교훈 추출, 반성 (뭐가 잘못됐고, 다음에 어떻게 할지). 미래 날짜 항목은 별도의 "Scheduled checks" 목록에 보관 |

### 코드 리뷰

| 스킬 | 기능 |
|------|------|
| [code-autopsy](../code-autopsy/) | 12Q 정량 코드 리뷰 (v7.3) — 4축 점수 (Security/Stability/Robustness/Operability), 심각도 앵커, 배포 판정 (SHIP/FIX/RISKY/BLOCK), Factuality Gate. 각 발견 사항에 NEW 또는 PRE-EXISTING 표시와 증거 등급이 붙는다. 실증 근거 기반 (Johnson 2019, Parnas 1972). 독립 프롬프트로 어떤 LLM에서든 사용 가능 |

### 품질

| 스킬 | 기능 |
|------|------|
| [agent-qa-testing](../agent-qa-testing/) | agent-qa로 웹·모바일 회귀 테스트를 검증·실행·분석. 고급 memidex 메모리와 자기 개선 기능 활용 |
| [project-check](../project-check/) | 기존 프로젝트를 4개 차원으로 스캔: 인프라, 보안, 품질, 하네스. 심각도순 갭 정렬 |
| [collab-audit](../collab-audit/) | 14개 섹션 AI 협업 감사 — 실제 작업 패턴(설문 아님)을 분석해 행동 프로필, 사각지대, 성장 방향 생성. 필요한 세션 데이터는 `extract_session_meta.py`가 만든다 |

### 운영

| 스킬 | 기능 |
|------|------|
| [skill-ops](../skill-ops/) | 스킬/에이전트 운영 허브 — 스냅샷/롤백 + 사용률 + 호출 추적 + 품질 점수, 4모드. `skill_snapshot.py`와 `skill_health_bucket.py` 포함 |
| [project-overview](../project-overview/) | 등록된 프로젝트들의 세션 핸드오프로부터 결정론 크로스프로젝트 현황 지도를 생성하고, 7일이 지난 스냅샷을 보고 |
| [skill-trigger-auditor](../skill-trigger-auditor/) | **v6.5.15 신규.** 스킬·에이전트·슬래시 명령의 라우팅 충돌과 오발동을 감사하고, description 변경을 홀드아웃 트리거 테스트로 관문 처리. 선택 사항인 프로브는 실제 Skill 도구 호출을 측정 |

### 거버넌스

| 스킬 | 기능 |
|------|------|
| [full-audit](../full-audit/) | 전 영역(코드베이스/문서/스킬/메모리/설정) 전수감사 — 결정론 스윕 + 내용리뷰 2계층 방법론, 오탐방지 kill-test, 시딩된 카나리, 영속 커버리지맵 |
| [integration-intake](../integration-intake/) | 외부 패턴(스킬/에이전트/룰/플러그인/MCP) 도입 5항목 스크리닝 게이트 — 기존 자산 대비 중복 검사, 도입 콘텐츠 provenance/인젝션 검사, 라이선스 확인 한 줄, 이전 판정 장부 조회 |
| [clean-room](../clean-room/) | 위험인접 요청을 안전 스코프로 분리해 완전히 격리된 fresh-context 서브에이전트가 실행 — 적대적 검증 패스 + descope ledger |
| [eval-leakage-audit](../eval-leakage-audit/) | eval/metric/holdout이 실제로 독립된 외부 그라운드트루스를 확보하는지, 아니면 순환 자기확인인지 감사 — 28-패턴 taxonomy, 골든 케이스 2개. 읽기 전용 |
| [doc-drift](../doc-drift/) | Claude Code가 컨텍스트로 로드하는 메모리/문서(CLAUDE.md/MEMORY.md/skills/agents/commands)를 구식 주장·상호 모순·위험/모호 표현으로 감사 — 우선순위 수정 목록 생성 |
| [ssot-audit](../ssot-audit/) | **v6.5.15 신규.** 리포나 노트 폴더 전체에서 하나의 사실·값·결정이 들어 있는 모든 사본을 찾아 정본을 지정(읽기 전용)하고, 사용자가 승인한 뒤에만 중복을 통합 |

---

## 라이프사이클 흐름

```
┌─────────────────── Setup (once) ────────────────────┐
│  /project-init  →  /setup                           │
└─────────────────────────────────────────────────────┘
         ↓
┌──────────────────── Daily Loop ─────────────────────┐
│  /session-start                                     │
│       ↓                                             │
│  /scope → /freeze → /goal-lock → work               │
│       → /stepback (anytime) → /code-autopsy         │
│       → /pre-push                                   │
│       ↓                                             │
│  /session-checkpoint                                │
└─────────────────────────────────────────────────────┘
         ↓
┌───────────────────── On Demand ─────────────────────┐
│  /stepback         (perspective reset — anytime)    │
│  /next-action      (top-3 next actions from state)  │
│  /project-check    (health audit)                   │
│  /code-autopsy     (12Q code review — any LLM)      │
│  /collab-audit     (behavioral diagnostic)          │
│  /integration-intake (before adopting external work)│
│  /full-audit       (exhaustive area audit)          │
│  /clean-room       (safety-adjacent scope carve-out)│
│  /eval-leakage-audit (eval circular-logic check)    │
│  /doc-drift        (loaded-context drift audit)     │
│  /ssot-audit       (one fact, many copies)          │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────── Skill authors / multi-project ───────────┐
│  /skill-ops        (snapshot, rollback, usage)      │
│  /skill-trigger-auditor (routing collisions)        │
│  /project-overview (cross-project status map)       │
└─────────────────────────────────────────────────────┘
```

---

## 설치

### 방법 A: 스킬 복사 (가장 간단)

각 스킬은 `SKILL.md` 파일이 들어 있는 독립 디렉토리입니다. 필요한 것만 복사하세요:

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

스킬은 Claude Code에서 트리거 명령어(예: `/goal-lock`)를 입력해 실행합니다. Claude가 SKILL.md를 읽고 지시를 따릅니다.

### 방법 C: Codex

Codex는 리포지토리·유저(`$HOME/.agents/skills`)·관리자·시스템 레벨에서 `.agents/skills/<skill-name>/SKILL.md`를 스캔해 스킬을 찾습니다 — 별도 에이전트 정의가 필요 없습니다. Claude Code와 같은 방식으로 설치하되, 경로만 `.agents/skills/`로 바꾸면 됩니다:

```bash
# 유저 레벨 (모든 프로젝트에서 사용 가능)
cp -r goal-lock ~/.agents/skills/goal-lock/

# 리포 레벨 (이 프로젝트 한정)
cp -r goal-lock .agents/skills/goal-lock/
```

각 스킬은 **선택적**으로 `agents/openai.yaml`도 포함합니다 — ChatGPT 데스크톱 앱용 UI/정책 메타데이터(표시명·설명, 아이콘/브랜딩 색상, 기본값 `true`인 `allow_implicit_invocation` 플래그)입니다. Codex가 스킬을 찾거나 실행하는 데 필요하지 않으며, 이 메타데이터를 적용하고 싶을 때만 `SKILL.md`와 함께 복사하면 됩니다:

```bash
cp -r goal-lock/agents .agents/skills/goal-lock/agents/
```

전체 탐색·메타데이터 스펙은 [공식 Codex 스킬 문서](https://learn.chatgpt.com/docs/build-skills)를 참조하세요.

### 방법 D: Cursor / 기타 에이전트

SKILL.md 내용은 범용 마크다운입니다 — 마크다운 지시문을 읽는 모든 LLM에서 작동합니다. `SKILL.md`를 에이전트의 지시 경로에 복사하세요.

### 요구사항

- **Claude Code**: CLI, 데스크톱 앱, 또는 웹 앱 ([claude.ai/code](https://claude.ai/code))
- **Codex**: OpenAI Codex — `.agents/skills/`에서 `SKILL.md`를 직접 읽음; `agents/openai.yaml`은 선택적 UI 메타데이터
- **Cursor / 기타**: 마크다운 지시문을 읽는 모든 에이전트
- 스킬 디렉토리: `~/.claude/skills/` (Claude Code) 또는 에이전트별 경로
- 번들 도우미 스크립트(여러 스킬 안의 `scripts/*.py`)용 Python 3.9+. 스킬은 이를 `${CLAUDE_SKILL_DIR}/scripts/<name>.py`로 호출하며, Claude Code가 이 값을 스킬 자신의 폴더로 채웁니다. 다른 에이전트에서는 스킬을 설치한 폴더로 바꿔 쓰세요. 스크립트를 실행할 수 없을 때는 각 스킬이 수동 단계로 대체하는지 중단하는지 안내합니다
- `pre-push`는 `scan_secrets.py`(권장)와 `scan_secrets.pl`(Perl 대체)을 모두 포함합니다. 선택 사항: `ruff`(변경된 줄 린트), `gitleaks`(두 번째 시크릿 스캔 엔진, 경고만)

### 세션 스킬이 읽고 쓰는 파일

`session-start`, `session-checkpoint`, `next-action`, `project-overview`, `skill-ops`, `collab-audit`은 몇 가지 일반 텍스트 파일을 함께 씁니다: 세션 핸드오프, `tasks/lessons.md`, `~/.claude/STATE.md`, `memory/MEMORY.md`, 컨텍스트 로그, 호출 로그. 필수인 파일은 없으며, 파일이 없으면 스킬이 해당 단계를 건너뜁니다. 형식: [docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md).

### 이 저장소에 포함되지 않은 선택적 에이전트와 스킬

일부 스킬은 이 저장소가 제공하지 **않는** 에이전트나 스킬에 작업을 넘길 수 있습니다. SKILL.md의 모든 언급에는 선택 사항 표시와 대체 수단이 있으므로, 없어도 아무것도 깨지지 않습니다:

| 이름 | 사용하는 스킬 | 없을 때 |
|------|------------|--------|
| `code-reviewer`, `security-reviewer`, `database-reviewer`, `build-error-resolver` | pre-push | `/setup`이 이 에이전트들을 생성할 수 있습니다. 없으면 pre-push가 인라인 리뷰(code-autopsy FAST MODE)를 실행하고 에이전트 단계를 SKIPPED로 표시합니다 |
| `refactor-cleaner` | pre-push | 단계 건너뜀 |
| `doubt-reviewer` | scope (Full 모드), goal-lock | 적대적 프롬프트를 쓰는 범용 서브에이전트, 또는 리포트에 SKIPPED로 표시 |
| `verification`, `brainstorming`, `check-harness`, `memory-dream`, `forge` | 여러 see-also / 라우팅 메모 | 안내 문구일 뿐 — 이것들 없이도 스킬이 동작합니다 |

---

## 에이전트 설계 패턴 커버리지

이 스킬들은 공개된 카탈로그([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464))의 에이전트 설계 패턴 18개에 대응합니다:

| 패턴 | 구현 스킬 | 방법 |
|------|----------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | 전체 라이프사이클 체인 |
| **Parallel Execution** | pre-push | 병렬 AI 코드 리뷰 에이전트 |
| **Loop (Retry)** | goal-lock | VERIFY 실패 → PLAN 재입장, 상한선 있음 |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | 독립 리뷰어 서브에이전트(선택 사항 — 위 참조) 또는 인라인 리뷰; 12Q 구조화 리뷰; full-audit의 Phase 2 팬아웃 리뷰어 패스; eval-leakage-audit은 eval이 독립적 그라운드트루스를 확보하는지 순환 자기확인인지 비평 |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE 통과 |
| **Coordinator/Router** | setup | 에이전트 라우팅 규칙 생성 |
| **Plan-and-Execute** | goal-lock, scope | 실행 전 검토 가능한 계획 |
| **ReAct** | project-check | 조사 → 점수 → 경로 권장 |
| **Reflexion** | session-checkpoint | Phase 1.7: 실패 분석 → 다음 세션용 교훈 |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES, Critical/High가 push 차단; integration-intake의 도입 전 5항목 스크리닝 게이트 |
| **Custom Logic** | pre-push | 결정론 시크릿 스캔(Python, Perl 대체) + AI 리뷰 |
| **Event-Driven** | session-start | 세션 열림 시 트리거, 이전 상태 로드 |
| **Guardrails/Safety** | goal-lock, clean-room | 16가지 성공 위장 패턴 탐지; clean-room은 안전인접 스코프를 carve하여 격리된 서브에이전트로 실행 |
| **Memory Management** | session-checkpoint, doc-drift | 핸드오프 파일 + 메모리 업데이트 + 교훈 추출; doc-drift는 컨텍스트로 로드되는 메모리/문서를 구식 주장·모순·위험 표현으로 감사 |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE 입력 시트 |
| **Step-Back Abstraction** | stepback | DeepMind step-back: 구체 → 추상 원칙 |
| **Prioritization** | next-action | 핸드오프/git/lessons/STATE에서 나온 후보 행동을 임팩트순으로 정렬 |
| **Evaluation & Monitoring** | skill-ops, skill-trigger-auditor, project-overview | 스킬별 사용 건강도; 홀드아웃 프롬프트 기준 라우팅 정밀도/재현율; 프로젝트 전반의 오래된 스냅샷 보고 |

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
| `ssot-audit` | `doc-drift`, `full-audit` | ssot-audit은 하나의 사실을 여러 파일에 걸쳐 추적해 정본을 고르고, doc-drift는 로드된 컨텍스트의 드리프트를 점검하고, full-audit은 영역 전체를 훑음 |
| `skill-trigger-auditor` | `skill-ops`, `doc-drift` | skill-trigger-auditor는 스킬이 올바른 프롬프트에서 발화하는지 점검하고, skill-ops는 스킬이 쓰이는지 추적하고 롤백하며, doc-drift는 스킬 텍스트의 구식 주장을 점검 |
| `project-check` | `setup`, `collab-audit` | project-check는 리포의 셋업을 점수화해 갭을 나열하고(채우는 건 setup), collab-audit은 리포가 아니라 AI와 일하는 방식을 살펴봄 |

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
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift / ssot-audit
                      (온디맨드 거버넌스·감사, 어느 단계든)
                                   │
         skill-ops / skill-trigger-auditor / project-overview
                 (스킬 작성자와 멀티 프로젝트 환경용)
```

---

## 변경 이력

전체 버전 이력(v3.0 → 최신)은 [CHANGELOG.md](../CHANGELOG.md)를 참조하세요.

## 라이선스

MIT — [LICENSE](../LICENSE) 참조.

## 기여

이슈와 PR 환영합니다. 라이프사이클에 맞는 스킬을 만들었다면 PR을 열어주세요.

## 연락처

커스텀 스킬 개발 DM [@AlexZio00](https://x.com/AlexZio00)
