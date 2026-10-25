[English](../README.md) | [한국어](README.ko.md) | 🌐 **日本語** | [中文](README.zh.md) | [Español](README.es.md)

# sovereign-skills v6.5.15

Claude Codeプロジェクトのライフサイクル全体をカバーする23個のスキル — セットアップから日常ワークフロー、コードレビュー、セッション管理、ガバナンスまで。各スキルは単体で使用可能で、全シーケンスで全工程をカバーします。

> **v6.5.15の変更点:** スキルを2つ追加 — `ssot-audit`（1つの事実を含むすべてのコピーを探し、正本を特定する）と `skill-trigger-auditor`（スキルとコマンドが正しくルーティングされるかを点検する）。バグ修正: `pre-push` は、先にコミットして後からpushしてもテストとリントを飛ばさなくなった。`project-check` はハイフン入りのAPIキー（`sk-ant-…`、`sk-proj-…`）も検出するようになった。`setup` のhook例は `bash` + `jq` が不要になり、Windowsでも動く。その他のスキルの改善: `code-autopsy` は各指摘にNEWまたはPRE-EXISTINGの印とエビデンス階層を付ける。セッション系スキルは日付を過ぎたハンドオフ項目に印を付ける。`integration-intake` はリポジトリを再レビューする前に自分の過去の判定を照会する。22スキルすべてについて通読監査も行った。同梱スクリプトはどのインストール先からも見つかり（`${CLAUDE_SKILL_DIR}`）、Python 3.9+ と macOS で動き、任意の外部エージェントには表示とフォールバックが付き、共有ファイル形式は [docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md) に文書化した。詳細は [CHANGELOG.md](../CHANGELOG.md)。

---

## クイックスタート

**新規プロジェクト（15分）：**
```
/project-init       →  CLAUDE.md + ROADMAP + .gitignore + .env.example
/setup              →  rules/ + hooks + memory/ + エージェントルーティング + チーム
日常：
  /session-start      セッション開始時
  /scope              機能実装前（IN/OUT/終了基準を定義）
  /freeze             実装前（編集可能領域を宣言）
  /goal-lock          目標をロック、PLAN→DO→VERIFYループを強制
  /stepback           いつでも — 方向確認、10行
  /next-action        いつでも — 現在の状態を読み、次のアクション上位3件を提案
  /code-autopsy       12Qコードレビュー + 重要度スコア + デプロイ判定
  /pre-push           push前（シークレットスキャン + AIレビュー）
  /session-checkpoint セッション終了時
```

**既存プロジェクト（5分）：**
```
/project-check      →  4次元スコア + 深刻度別ギャップリスト
/collab-audit       →  作業パターンから作る14セクションのAIコラボレーション診断
```

**ガバナンスと監査（必要時）：**
```
/integration-intake →  外部スキル/エージェント/ルール/プラグイン導入前 — 5項目スクリーニングゲート
/full-audit         →  領域全体（コードベース/ドキュメント/スキル/メモリ/設定）の網羅監査 + カバレッジマップ
/clean-room         →  タスクに安全隣接要素と安全な作業が混在する時
/eval-leakage-audit →  eval/metric/holdoutを信頼する前 — 循環的自己確認でないか点検
/doc-drift          →  読み込まれたコンテキスト（CLAUDE.md/MEMORY.md/skills）を古い/矛盾した表現で監査
/ssot-audit         →  1つの事実が複数ファイルに — 正本を見つけて統合
```

**自分でスキルを書く場合：**
```
/skill-trigger-auditor →  スキルのdescriptionを変更する前に — ルーティングの衝突と誤発火を検出
/skill-ops             →  編集前にスキルのスナップショット/ロールバック、実際に使われているスキルを確認
/project-overview      →  複数プロジェクトを一枚で見渡す状況マップ
```

---

## スキル一覧

### セットアップフェーズ

| スキル | 機能 |
|--------|------|
| [project-init](../project-init/) | インタビュー方式のプロジェクトスキャフォールディング — テンプレートではなく意思決定からCLAUDE.md、ROADMAP、.gitignore、.env.exampleを生成 |
| [setup](../setup/) | Claude Codeインフラ + エージェントチーム — rules、hooks、memory、ルーティング、エージェントインストールを一括で |

### 日常ワークフロー

| スキル | 機能 |
|--------|------|
| [scope](../scope/) | 実装前にIN/OUT/終了基準を定義。Quickモード（3つの質問）またはFullモード（レイヤードスペック）。Fullモードに `coverage_check.py`（要件↔タスク照合）を同梱 |
| [freeze](../freeze/) | 編集可能領域を宣言 — それ以外は凍結。実装中のスコープクリープを防止 |
| [goal-lock](../goal-lock/) | エージェント規律エンジン — 目標をロックし、PLAN→DO→VERIFY→FINALIZE→OUTPUTループを強制、16種類の成功偽装パターンを検出 |
| [pre-push](../pre-push/) | 必須pre-pushパイプライン — シークレットスキャン（14パターン）、ビルド/テスト、リント、並列AIコードレビュー。pushが実際に運ぶもの（ステージ済みの変更 + まだ送られていないコミット）を検査。Critical/High発見時にpushをブロック |

### 視点転換

| スキル | 機能 |
|--------|------|
| [stepback](../stepback/) | ワンショット視点リセット — 1つの抽象的リフレーミング質問 + 3つのクイックチェック（スコープドリフト、副作用、より良いアプローチ）と続行/中止の判定を10行以内で。作業中いつでも使用可能 |
| [next-action](../next-action/) | ハンドオフ/git/lessons/STATEを読み込み、影響度順に次のアクション上位3件を提案。提案のみ、実行はしない。いつでも使用可能 |

### セッション管理

| スキル | 機能 |
|--------|------|
| [session-start](../session-start/) | 前セッションのハンドオフをロード、教訓レビュー、ヘルスチェック、優先アクション付き「準備完了」シグナル。日付がすでに過ぎたハンドオフ項目に印を付ける |
| [session-checkpoint](../session-checkpoint/) | compact前にセッションコンテキストを保存 — ハンドオフファイル、メモリ更新、教訓抽出、リフレクション（何がうまくいかなかったか、次にどう改善するか）。未来の日付の項目は別の「Scheduled checks」リストに保管 |

### コードレビュー

| スキル | 機能 |
|--------|------|
| [code-autopsy](../code-autopsy/) | 12Q定量コードレビュー（v7.3） — 4軸スコア（Security/Stability/Robustness/Operability）、重要度アンカー、デプロイ判定（SHIP/FIX/RISKY/BLOCK）、Factuality Gate。各指摘にNEWまたはPRE-EXISTINGの印とエビデンス階層が付く。実証的根拠に基づく（Johnson 2019、Parnas 1972）。スタンドアロンプロンプトとしてあらゆるLLMで使用可能 |

### 品質

| スキル | 機能 |
|--------|------|
| [agent-qa-testing](../agent-qa-testing/) | agent-qaでWeb・モバイルの回帰テストを検証・実行・調査。高度なmemidexメモリと自己改善機能を活用 |
| [project-check](../project-check/) | 既存プロジェクトを4次元でスキャン：インフラ、セキュリティ、品質、ハーネス。深刻度順にギャップを整列 |
| [collab-audit](../collab-audit/) | 14セクションAIコラボレーション監査 — 実際の作業パターン（アンケートではなく）を分析し、行動プロファイル、盲点、成長方向を生成。必要なセッションデータは `extract_session_meta.py` が生成 |

### 運用

| スキル | 機能 |
|--------|------|
| [skill-ops](../skill-ops/) | スキル/エージェント運用ハブ — スナップショット/ロールバック + 使用状況 + 呼び出し追跡 + 品質スコアの4モード。`skill_snapshot.py` と `skill_health_bucket.py` を同梱 |
| [project-overview](../project-overview/) | 登録済みプロジェクトのセッションハンドオフから決定論的クロスプロジェクト状況マップを生成し、7日より古いスナップショットを報告 |
| [skill-trigger-auditor](../skill-trigger-auditor/) | **v6.5.15で新規追加。** スキル・エージェント・スラッシュコマンドのルーティングの衝突と誤発火を監査し、descriptionの変更をホールドアウトのトリガーテストで関門にする。任意のプローブで実際のSkillツール呼び出しを計測 |

### ガバナンス

| スキル | 機能 |
|--------|------|
| [full-audit](../full-audit/) | 領域全体（コードベース/文書/スキル/メモリ/設定）の網羅的監査 — 決定論的スイープ+内容レビューの2層方式、偽陽性防止kill-test、シード済みカナリア、永続カバレッジマップ |
| [integration-intake](../integration-intake/) | 外部パターン（スキル/エージェント/ルール/プラグイン/MCP）導入の5項目スクリーニングゲート — 既存資産との重複チェック、導入コンテンツのprovenance/インジェクションチェック、ライセンス確認1行、過去の判定の台帳照会 |
| [clean-room](../clean-room/) | 安全隣接リクエストを安全スコープに切り出し、完全に隔離されたfresh-contextサブエージェントが実行 — 敵対的検証パス + descope ledger |
| [eval-leakage-audit](../eval-leakage-audit/) | eval/metric/holdoutが実際に独立した外部グラウンドトゥルースを確保しているか、循環的な自己確認かを監査 — 28パターンのtaxonomy、ゴールデンケース2件。読み取り専用 |
| [doc-drift](../doc-drift/) | Claude Codeがコンテキストに読み込むメモリ/ドキュメント(CLAUDE.md/MEMORY.md/skills/agents/commands)を古い主張・相互矛盾・危険/曖昧な表現で監査 — 優先度付き修正リストを生成 |
| [ssot-audit](../ssot-audit/) | **v6.5.15で新規追加。** リポジトリやノートフォルダ全体から、1つの事実・値・決定を含むすべてのコピーを探して正本を特定（読み取り専用）し、承認後にのみ重複を統合 |

---

## ライフサイクルフロー

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

## インストール

### 方法A：スキルをコピー（最も簡単）

各スキルは `SKILL.md` ファイルを含む独立したディレクトリです。必要なものをコピーしてください：

```bash
# 全スキルをインストール
git clone https://github.com/AlexZio00/sovereign-skills.git
cd sovereign-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# または個別スキルをインストール
cp -r goal-lock ~/.claude/skills/
```

### 方法B：マーケットプレイス（sovereign-plugins）

このリポジトリはClaude Codeマーケットプレイスです。一度登録すればスキルを閲覧・インストールできます：

```bash
# Claude Codeでsovereign-pluginsマーケットプレイスを追加
# 設定 → プラグイン → マーケットプレイス追加 → https://github.com/AlexZio00/sovereign-skills.git
```

各スキルに個別の`.claude-plugin/plugin.json`メタデータも含まれています。

スキルはClaude Codeでトリガーコマンド（例：`/goal-lock`）を入力して実行します。ClaudeがSKILL.mdを読み、その指示に従います。

### 方法C: Codex

Codexはリポジトリ・ユーザー（`$HOME/.agents/skills`）・管理者・システムの各レベルで `.agents/skills/<skill-name>/SKILL.md` をスキャンしてスキルを検出します — 個別のエージェント定義は不要です。Claude Codeと同じ方法で、パスだけ `.agents/skills/` に変えてインストールしてください：

```bash
# ユーザーレベル（すべてのプロジェクトで利用可能）
cp -r goal-lock ~/.agents/skills/goal-lock/

# リポジトリレベル（このプロジェクトのみ）
cp -r goal-lock .agents/skills/goal-lock/
```

各スキルは**任意**で `agents/openai.yaml` も同梱しています — ChatGPTデスクトップアプリ向けのUI/ポリシーメタデータ（表示名・説明、アイコン/ブランディングカラー、デフォルト`true`の `allow_implicit_invocation` フラグ）です。Codexがスキルを検出・実行するのに必須ではなく、このメタデータを使いたい場合のみ `SKILL.md` と一緒にコピーしてください：

```bash
cp -r goal-lock/agents .agents/skills/goal-lock/agents/
```

検出とメタデータの完全な仕様は[公式Codexスキルドキュメント](https://learn.chatgpt.com/docs/build-skills)を参照してください。

### 方法D: Cursor / その他のエージェント

SKILL.mdの内容は汎用マークダウンです — マークダウン指示を読むあらゆるLLMで動作します。SKILL.mdをエージェントの指示パスにコピーしてください。

### 要件

- **Claude Code**: CLI、デスクトップアプリ、またはウェブアプリ（[claude.ai/code](https://claude.ai/code)）
- **Codex**: OpenAI Codex — `.agents/skills/` から `SKILL.md` を直接読み込み。`agents/openai.yaml` は任意のUIメタデータ
- **Cursor / その他**: マークダウン指示を読むあらゆるエージェント
- スキルディレクトリ：`~/.claude/skills/`（Claude Code）またはエージェント別パス
- 同梱のヘルパースクリプト（複数のスキル内の `scripts/*.py`）にはPython 3.9+が必要。スキルは `${CLAUDE_SKILL_DIR}/scripts/<name>.py` としてこれらを呼び出し、Claude Codeがこの値をスキル自身のフォルダに置き換えます。他のエージェントでは、スキルをインストールしたフォルダに読み替えてください。スクリプトを実行できない場合、各スキルが手動の手順にフォールバックするか停止するかを説明しています
- `pre-push`は`scan_secrets.py`（推奨）と`scan_secrets.pl`（Perlフォールバック）の両方を同梱。任意：`ruff`（変更行のリント）と`gitleaks`（2つ目のシークレットスキャンエンジン、警告のみ）

### セッション系スキルが読み書きするファイル

`session-start`、`session-checkpoint`、`next-action`、`project-overview`、`skill-ops`、`collab-audit` は、いくつかのプレーンテキストファイルを共有します: セッションのハンドオフ、`tasks/lessons.md`、`~/.claude/STATE.md`、`memory/MEMORY.md`、コンテキストログ、呼び出しログ。どれも必須ではなく、ファイルがなければスキルはその手順を飛ばします。形式: [docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md)。

### このリポジトリに含まれない任意のエージェントとスキル

一部のスキルは、このリポジトリが提供**しない**エージェントやスキルに作業を渡すことがあります。SKILL.md内の各言及には任意の印とフォールバックが付いているため、なくても何も壊れません:

| 名前 | 使うスキル | なかった場合 |
|------|----------|------------|
| `code-reviewer`、`security-reviewer`、`database-reviewer`、`build-error-resolver` | pre-push | `/setup` でこれらのエージェントを生成できます。ない場合、pre-pushはインラインレビュー（code-autopsy FAST MODE）を実行し、エージェントの手順をSKIPPEDと記録します |
| `refactor-cleaner` | pre-push | 手順を飛ばす |
| `doubt-reviewer` | scope（Fullモード）、goal-lock | 敵対的プロンプトを使う汎用サブエージェント、またはレポートにSKIPPEDと記録 |
| `verification`、`brainstorming`、`check-harness`、`memory-dream`、`forge` | 各種see-also / ルーティングの注記 | 参照先の案内のみ — なくてもスキルは動きます |

---

## エージェント設計パターンカバレッジ

これらのスキルは、公開されているカタログ（[Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)）のエージェント設計パターン18個に対応しています：

| パターン | 実装スキル | 方法 |
|---------|-----------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | 完全なライフサイクルチェーン |
| **Parallel Execution** | pre-push | 並列AIコードレビューエージェント |
| **Loop (Retry)** | goal-lock | VERIFY失敗 → PLAN再入場、上限あり |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | 独立したレビュアーサブエージェント（任意 — 上記参照）またはインラインレビュー；12Q構造化レビュー；full-auditのPhase 2ファンアウトレビューパス；eval-leakage-auditはevalが独立したグラウンドトゥルースを確保しているか循環的自己確認かを批評 |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE通過 |
| **Coordinator/Router** | setup | エージェントルーティングルール生成 |
| **Plan-and-Execute** | goal-lock, scope | 実行前にレビュー可能な計画 |
| **ReAct** | project-check | 調査 → スコア → パス推奨 |
| **Reflexion** | session-checkpoint | Phase 1.7：失敗分析 → 次セッション用教訓 |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES、Critical/Highがpushをブロック；integration-intakeの導入前5項目スクリーニングゲート |
| **Custom Logic** | pre-push | 決定論的シークレットスキャン（Python、Perlフォールバック）+ AIレビュー |
| **Event-Driven** | session-start | セッション開始時にトリガー、前の状態をロード |
| **Guardrails/Safety** | goal-lock, clean-room | 16種類の成功偽装パターンを検出；clean-roomは安全隣接スコープをcarveして隔離されたサブエージェント実行に切り出す |
| **Memory Management** | session-checkpoint, doc-drift | ハンドオフファイル + メモリ更新 + 教訓抽出；doc-driftはコンテキストに読み込まれるメモリ/ドキュメントを古い主張・矛盾・危険な表現で監査 |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE入力シート |
| **Step-Back Abstraction** | stepback | DeepMind step-back：具体 → 抽象原則 |
| **Prioritization** | next-action | ハンドオフ/git/lessons/STATEから挙がった候補アクションを影響度順に並べる |
| **Evaluation & Monitoring** | skill-ops, skill-trigger-auditor, project-overview | スキルごとの使用状況の健全性；ホールドアウトプロンプトでのルーティング精度/再現率；プロジェクト横断の古いスナップショット報告 |

---

## 設計原則

1. **テンプレートよりインタビュー** — 空の骨格ではなく、質問と意思決定から充実したコンテンツを生成
2. **信頼より検証** — 完了証拠は実行するもの、仮定するものではない。「通るはず」は検証ではない
3. **コードの前にスコープ** — ファイル変更前にIN/OUT/終了基準を定義。変更しないものは凍結
4. **正直な報告** — WORKING / PARTIAL / BROKENラベル。サイレント故障もモック偽装もなし
5. **セッション継続性** — ハンドオフで開始、チェックポイントで終了。コンテキストはセッションを超えて存続

---

## スキル間の連携関係

各スキルはfrontmatterの`see_also`（関連スキル）と`not_for`（誤用防止ガードレール）で関係を宣言します。主な関係：

| スキル | 連携先 | 関係 |
|--------|--------|------|
| `scope` | `goal-lock`, `freeze` | scopeは何を作るかを定義し、freezeは編集可能領域をロックし、goal-lockは実行ループを強制する |
| `freeze` | `scope`, `goal-lock` | freezeはscopeの計画とgoal-lockのループ強制をつなぐ手動ゾーンロック |
| `goal-lock` | `scope`, `freeze` | goal-lockはscope/freezeが定めた境界内で作動する実行時規律レイヤー |
| `stepback` | `next-action` | stepbackは方向確認（「正しい問題を解いているか」）、next-actionは行動推奨（「影響度順で次は何か」） |
| `next-action` | `session-start`, `stepback` | next-actionは現在の状態を読んで推奨し、session-startは前セッションの状態を復元する |
| `session-start` | `session-checkpoint` | ライフサイクルペア — セッションを開いて閉じる |
| `session-checkpoint` | `session-start`, `setup` | セッションを閉じ、setupは新規プロジェクトを開く |
| `code-autopsy` | `pre-push` | code-autopsyは深く踏み込んだオンデマンド12Qレビュー、pre-pushは毎push前に実行される高速自動パイプライン |
| `skill-ops` | `project-overview` | skill-opsはスキル/エージェントのライフサイクル（スナップショット/ロールバック/使用状況）を管理し、project-overviewは複数プロジェクトの状況を集計する |
| `integration-intake` | `full-audit` | integration-intakeは外部資産1件の導入可否をゲートし、full-auditは（既存のスキル/エージェント在庫を含め）領域全体のドリフト・ギャップを掃く |
| `full-audit` | `code-autopsy`, `project-check` | full-auditはより広い多領域の網羅監査＋永続カバレッジマップを残し、code-autopsyはファイル単位12Q、project-checkは4次元スコアのまま |
| `clean-room` | `goal-lock` | clean-roomは作業途中でスコープに安全隣接要素と安全な作業が混在した時に発火し、goal-lockはそれが割り込むPLAN→DO→VERIFYループ |
| `doc-drift` | `full-audit` | doc-driftはコンテキストに読み込まれるメモリ/ドキュメント（CLAUDE.md/MEMORY.md/skills/agents）のみをドリフト・矛盾で監査し、full-auditはカバレッジマップ付きで領域全体を掃く |
| `eval-leakage-audit` | `full-audit`, `code-autopsy` | eval-leakage-auditはeval/metric/holdoutが循環論理か（測定の完全性）を点検し、full-auditとcode-autopsyはevalの独立性ではなくコード/領域をレビューする |
| `ssot-audit` | `doc-drift`, `full-audit` | ssot-auditは1つの事実を複数ファイルにわたって追って正本を選び、doc-driftは読み込まれたコンテキストのドリフトを点検し、full-auditは領域全体を掃く |
| `skill-trigger-auditor` | `skill-ops`, `doc-drift` | skill-trigger-auditorはスキルが正しいプロンプトで発火するかを点検し、skill-opsはスキルが使われているかを追跡してロールバックし、doc-driftはスキルの文面の古い主張を点検する |
| `project-check` | `setup`, `collab-audit` | project-checkはリポジトリのセットアップをスコア化してギャップを挙げ（埋めるのはsetup）、collab-auditはリポジトリではなくAIとの働き方を見る |

図（矢印 = 「引き渡す」/「情報を与える」）：

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (いつでも、どの段階でも)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (状態を読み推奨)
                                   │
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift / ssot-audit
                     (オンデマンドのガバナンスと監査、どの段階でも)
                                   │
         skill-ops / skill-trigger-auditor / project-overview
                 (スキル作成者と複数プロジェクト環境向け)
```

---

## 変更履歴

バージョン履歴の全体（v3.0 → 最新）は [CHANGELOG.md](../CHANGELOG.md) を参照してください。

## ライセンス

MIT — [LICENSE](../LICENSE)を参照。

## コントリビュート

IssueとPRを歓迎します。ライフサイクルに合うスキルを作成されたら、PRを開いてください。

## 連絡先

カスタムスキル開発のDMは[@AlexZio00](https://x.com/AlexZio00)まで。
