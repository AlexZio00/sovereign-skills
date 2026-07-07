[English](../README.md) | [한국어](README.ko.md) | 🌐 **日本語** | [中文](README.zh.md) | [Español](README.es.md)

# sovereign-skills v6.3

Claude Codeプロジェクトのライフサイクル全体をカバーする15個のスキル — セットアップから日常ワークフロー、コードレビュー、セッション管理まで。各スキルは単体で使用可能で、全シーケンスで全工程をカバーします。

> **v6.3の変更点:** 新規：`skill-ops`（スナップショット/ロールバック + 使用状況 + 呼び出し追跡ハブ）、`next-action`（ハンドオフ/git/lessons/STATEを読み込み、影響度順に次のアクション上位3件を提案）、`project-overview`（決定論的クロスプロジェクト状況マップ）。`code-autopsy` → v7.1（質問ごとのサブチェック強化）、`pre-push` → v3.5（サプライチェーンIOC 9パターン）、`goal-lock`/`session-checkpoint`/`session-start`/`scope`/`stepback`/`freeze` 全て強化。既存12スキル全てに `not_for`/`see_also` frontmatterを追加し発見性を改善。

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
/code-autopsy       →  12Qコードレビュー（あらゆるLLMでスタンドアロンプロンプトとして使用可能）
/collab-audit       →  14セクションAIコラボレーション診断
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
| [scope](../scope/) | 実装前にIN/OUT/終了基準を定義。Quickモード（3つの質問）またはFullモード（レイヤードスペック） |
| [freeze](../freeze/) | 編集可能領域を宣言 — それ以外は凍結。実装中のスコープクリープを防止 |
| [goal-lock](../goal-lock/) | エージェント規律エンジン — 目標をロックし、PLAN→DO→VERIFY→FINALIZE→OUTPUTループを強制、13種類の成功偽装パターンを検出 |
| [pre-push](../pre-push/) | 必須pre-pushパイプライン — シークレットスキャン（12パターン）、ビルド/テスト、リント、並列AIコードレビュー。Critical/High発見時にpushをブロック |

### コードレビュー

| スキル | 機能 |
|--------|------|
| [code-autopsy](../code-autopsy/) | **更新 v7.1。** 12Q定量コードレビュー — 4軸スコア（Security/Stability/Robustness/Operability）、重要度アンカーテーブル、デプロイ判定（SHIP/FIX/RISKY/BLOCK）、Factuality Gate、CapCodeスコアgaming検出、CEF偽装エラー検出。スタンドアロンプロンプトとしてあらゆるLLMで使用可能 |

### 視点転換

| スキル | 機能 |
|--------|------|
| [stepback](../stepback/) | **更新。** ワンショット視点リセット — 1つの抽象的リフレーミング質問 + 3つのクイックチェック（スコープドリフト、副作用、より良いアプローチ）を10行以内で。作業中いつでも使用可能 |
| [next-action](../next-action/) | **新規。** ハンドオフ/git/lessons/STATEを読み込み、影響度順に次のアクション上位3件を提案。提案のみ、実行はしない。いつでも使用可能 |

### セッション管理

| スキル | 機能 |
|--------|------|
| [session-start](../session-start/) | 前セッションのハンドオフをロード、教訓レビュー、ヘルスチェック、優先アクション付き「準備完了」シグナル |
| [session-checkpoint](../session-checkpoint/) | compact前にセッションコンテキストを保存 — ハンドオフファイル、メモリ更新、教訓抽出、リフレクション（何がうまくいかなかったか、次にどう改善するか） |

### 品質

| スキル | 機能 |
|--------|------|
| [project-check](../project-check/) | 既存プロジェクトを4次元でスキャン：インフラ、セキュリティ、品質、ハーネス。深刻度順にギャップを整列 |
| [collab-audit](../collab-audit/) | 14セクションAIコラボレーション監査 — 実際の作業パターン（アンケートではなく）を分析し、行動プロファイル、盲点、成長方向を生成 |

### 運用

| スキル | 機能 |
|--------|------|
| [skill-ops](../skill-ops/) | **新規。** スキル/エージェント運用ハブ — スナップショット/ロールバック + 使用状況 + 呼び出し追跡の3モード |
| [project-overview](../project-overview/) | **新規。** 登録済みプロジェクトのセッションハンドオフから決定論的クロスプロジェクト状況マップを生成 |

---

## ライフサイクルフロー

```
┌────────────────── セットアップ（1回）──────────────┐
│  /project-init  →  /setup                           │
└─────────────────────────────────────────────────────┘
         ↓
┌────────────────── 日常ループ ───────────────────────┐
│  /session-start                                      │
│       ↓                                              │
│  /scope → /freeze → /goal-lock → 作業                │
│       → /stepback (いつでも) → /code-autopsy → /pre-push│
│       ↓                                              │
│  /session-checkpoint                                 │
└──────────────────────────────────────────────────────┘
         ↓
┌────────────────── 随時 ────────────────────────────┐
│  /stepback         （視点リセット — いつでも）          │
│  /project-check    （ヘルス監査）                     │
│  /collab-audit     （行動診断）                       │
└─────────────────────────────────────────────────────┘
```

---

## インストール

### 方法A：スキルをコピー（最も簡単）

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

トリガーコマンド（例：`/goal-lock`）をClaude Codeで入力するとスキルが実行されます。

### 方法C: Codex / Cursor (npx)

各スキルに `agents/openai.yaml` が含まれています：

```bash
# Codex用スキルをインストール
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent codex -g -y

# Cursor用スキルをインストール
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent cursor -g -y

# Claude Code用インストール（方法Aの代替）
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent claude-code -g -y
```

SKILL.mdの内容は汎用です — マークダウン指示を読むあらゆるLLMで動作します。

### 要件

- **Claude Code**: CLI、デスクトップアプリ、またはウェブアプリ（[claude.ai/code](https://claude.ai/code)）
- **Codex**: OpenAI Codex（`npx skills` 対応）
- **Cursor**: Cursor IDE（スキルプラグイン対応）
- スキルディレクトリ：`~/.claude/skills/`（Claude Code）またはエージェント別パス
- `pre-push`にはPerlが必要（`scan_secrets.pl`同梱）

---

## v6.2の変更点

### 新規追加
- **stepback** — ワンショット視点リセット。抽象的なリフレーミング質問1つ（DeepMind step-backパターン）+ クイックチェック3つ（スコープドリフト、副作用、より良いアプローチ）を10行以内で生成。読み取り専用、エージェントなし、コードなし。実装中いつでも使用して、正しい問題を正しいレベルで解いているかを確認。出典：team-attention/hoyeon。

### 更新内容
- **code-autopsy** — メタ検出ゲート追加：スコアゲーミング検出用CapCodeシーリングメトリック、制約回避型偽装エラー検出用CEF。
- **collab-audit** — 13→14セクション。新セクション12：思考レベル軌跡（情報要求者→思考設計者の5段階モデル + 時間的変化追跡 + AI属性修正）。
- **goal-lock** — Ralph Wiggum早期完了検出（12番目の偽装パターン）+ VERIFY段階の検証トレーサビリティ（すべてのクレームが実際のツール呼び出しにトレース可能であること）追加。
- **session-checkpoint** — ハンドオフ明確性自己チェック追加（ハンドオフ作成後2つのアンカー質問）。
- **session-start** — コンテキスト腐敗防止（古いハンドオフエントリ用スライディングウィンドウ）。
- **pre-push** — 新規追加依存関係の3-IOCサプライチェーンチェック追加。
- **scope** — 禁忌フィールド追加（選択したアプローチが適切でない条件）。
- **freeze** — Thaw Protocol追加（正式なアンフリーズワークフロー + ブラストラジアス確認 + 3回の警告）。
- **project-init** — `.env.example`テンプレート拡張（OAuth、外部サービス、モニタリングセクション）+ セキュリティベースラインノート。
- **project-check** — スコアデルタ追跡追加（現在 vs 以前のスキャン結果比較）。
- **setup** — Tier 0違反テスト失敗向けRedesign Protocol追加（3オプションエスカレーション）。

---

## v6.1の変更点

### 新規追加
- **code-autopsy** — 12Q定量コードレビュープロンプト（Code Autopsy v7.0）。設計から監視可能性まで12の分析質問。4軸複合スコア（Security × 0.35 + Stability × 0.30 + Robustness × 0.20 + Operability × 0.15）。加重式付き重要度アンカーテーブル。CRITICALハードキャップ付きデプロイ判定。Factuality Gate（報告前の自己検証）。ファイル間影響分析。Quickモードおよびdiffモード。根拠：Google eng-practices、Johnson et al. 2019、Parnas 1972。あらゆるLLMでスタンドアロンプロンプトとして動作 — Claude Code専用ではありません。

---

## v6.0の変更点

### 新規追加
- **goal-lock** — PLAN→DO→VERIFY→FINALIZE→OUTPUTループを備えたエージェント規律エンジン。13種類の成功偽装パターン（テスト削除、mockラッピング、閾値緩和など）を検出。小さな変更用Quickモード（3フィールド）、それ以外はFullモード（7フィールド）。

### 統合
- `harness-init` + `team-init` → **setup** — インフラとエージェントチームが1度に
- `brief` + `adr` → **scope** — ADR機能が組み込まれたスコープ定義
- `retro` → **session-checkpoint** — レトロスペクティブは現在session-checkpoint内Phase 1.7 Reflexion

### 削除
- `token-audit` — 代わりに`npx ccusage`を直接使用するか、パターンからccusageスキルをビルド
- `adr`（スタンドアロン） — scopeに吸収されました
- `retro`（スタンドアロン） — session-checkpointに吸収されました

### アップグレード
- すべてのスキル：Dominant Variable、Key Assumptions、Error Recovery、Safety Layersを追加
- すべてのスキル：アクションタグ付きScope Boundary（[READ]/[WRITE]/[BASH]/[AGENT]）
- `session-checkpoint`：Memento CoT圧縮、Reflexion、Invocationロギング
- `pre-push`：大きなdiff決定論的バンドリング、Discard If条件
- `collab-audit`：アンチパターンフラグ、Key Assumptions

---

## エージェント設計パターンカバレッジ

この15個中12個のスキル（元々のライフサイクルセット — v6.3の運用系新規スキルはまだマッピングされていません）は、25個の既知エージェント設計パターンのうち17個を実装しています（[Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)）：

| パターン | 実装スキル | 方法 |
|---------|-----------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | 完全なライフサイクルチェーン |
| **Parallel Execution** | pre-push | 並列AIコードレビューエージェント |
| **Loop (Retry)** | goal-lock | VERIFY失敗 → PLAN再入場、上限あり |
| **Review & Critique** | pre-push, code-autopsy | 独立したcode-reviewer + security-reviewer；12Q構造化レビュー |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE通過 |
| **Coordinator/Router** | setup | エージェントルーティングルール生成 |
| **Plan-and-Execute** | goal-lock, scope | 実行前にレビュー可能な計画 |
| **ReAct** | project-check | 調査 → スコア → パス推奨 |
| **Reflexion** | session-checkpoint | Phase 1.7：失敗分析 → 次セッション用教訓 |
| **Human-in-the-Loop** | goal-lock, pre-push | STOP RULES、Critical/Highがpushをブロック |
| **Custom Logic** | pre-push | 決定論的シークレットスキャン（Perl）+ AIレビュー |
| **Event-Driven** | session-start | セッション開始時にトリガー、前の状態をロード |
| **Guardrails/Safety** | goal-lock | 13種類の成功偽装パターンを検出 |
| **Memory Management** | session-checkpoint | ハンドオフファイル + メモリ更新 + 教訓抽出 |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE入力シート |
| **Step-Back Abstraction** | stepback | DeepMind step-back：具体 → 抽象原則 |

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

図（矢印 = 「引き渡す」/「情報を与える」）：

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (いつでも、どの段階でも)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (状態を読み推奨)
```

---

## ライセンス

MIT — [LICENSE](../LICENSE)を参照。

## コントリビュート

IssueとPRを歓迎します。ライフサイクルに合うスキルを作成されたら、PRを開いてください。

## 連絡先

カスタムスキル開発のDMは[@AlexZio00](https://x.com/AlexZio00)まで。
