[English](../README.md) | [한국어](README.ko.md) | 🌐 **日本語** | [中文](README.zh.md) | [Español](README.es.md)

# claude-code-skills v6.0

Claude Codeプロジェクトのライフサイクル全体をカバーする10個のスキル — セットアップから日常ワークフロー、セッション管理まで。各スキルは単体で使用可能で、全シーケンスで全工程をカバーします。

> **v6.0の変更点:** 13個から10個に統合。`harness-init` + `team-init` → `setup`。`brief` + `adr` → `scope`。`retro` → `session-checkpoint`に吸収。`token-audit`削除（`npx ccusage` CLIを使用）。新規：`goal-lock` — エージェント規律エンジン。

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
  /pre-push           push前（シークレットスキャン + AIレビュー）
  /session-checkpoint セッション終了時
```

**既存プロジェクト（5分）：**
```
/project-check      →  4次元スコア + 深刻度別ギャップリスト
/collab-audit       →  13セクションAIコラボレーション診断
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
| [goal-lock](../goal-lock/) | **新規。** エージェント規律エンジン — 目標をロックし、PLAN→DO→VERIFY→FINALIZE→OUTPUTループを強制、11種類の成功偽装パターンを検出 |
| [pre-push](../pre-push/) | 必須pre-pushパイプライン — シークレットスキャン（12パターン）、ビルド/テスト、リント、並列AIコードレビュー。Critical/High発見時にpushをブロック |

### セッション管理

| スキル | 機能 |
|--------|------|
| [session-start](../session-start/) | 前セッションのハンドオフをロード、教訓レビュー、ヘルスチェック、優先アクション付き「準備完了」シグナル |
| [session-checkpoint](../session-checkpoint/) | compact前にセッションコンテキストを保存 — ハンドオフファイル、メモリ更新、教訓抽出、リフレクション（何がうまくいかなかったか、次にどう改善するか） |

### 品質

| スキル | 機能 |
|--------|------|
| [project-check](../project-check/) | 既存プロジェクトを4次元でスキャン：インフラ、セキュリティ、品質、ハーネス。深刻度順にギャップを整列 |
| [collab-audit](../collab-audit/) | 13セクションAIコラボレーション監査 — 実際の作業パターン（アンケートではなく）を分析し、行動プロファイル、盲点、成長方向を生成 |

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
│  /scope → /freeze → /goal-lock → 作業 → /pre-push   │
│       ↓                                              │
│  /session-checkpoint                                 │
└──────────────────────────────────────────────────────┘
         ↓
┌────────────────── 随時 ────────────────────────────┐
│  /project-check    （ヘルス監査）                     │
│  /collab-audit     （行動診断）                       │
└─────────────────────────────────────────────────────┘
```

---

## インストール

### 方法A：スキルをコピー（最も簡単）

```bash
# 全スキルをインストール
git clone https://github.com/AlexZio00/claude-code-skills.git
cd claude-code-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# または個別スキルをインストール
cp -r goal-lock ~/.claude/skills/
```

### 方法B：マーケットプレイス（sovereign-plugins）

このリポジトリはClaude Codeマーケットプレイスです。一度登録すればスキルを閲覧・インストールできます：

```bash
# Claude Codeでsovereign-pluginsマーケットプレイスを追加
# 設定 → プラグイン → マーケットプレイス追加 → https://github.com/AlexZio00/claude-code-skills.git
```

各スキルに個別の`.claude-plugin/plugin.json`メタデータも含まれています。

トリガーコマンド（例：`/goal-lock`）をClaude Codeで入力するとスキルが実行されます。

### 要件

- [Claude Code](https://claude.ai/code) CLI、デスクトップアプリ、またはウェブアプリ
- スキルディレクトリ：`~/.claude/skills/`（Claude Codeが自動作成）
- `pre-push`にはPerlが必要（`scan_secrets.pl`同梱）

---

## 設計原則

1. **テンプレートよりインタビュー** — 空の骨格ではなく、質問と意思決定から充実したコンテンツを生成
2. **信頼より検証** — 完了証拠は実行するもの、仮定するものではない。「通るはず」は検証ではない
3. **コードの前にスコープ** — ファイル変更前にIN/OUT/終了基準を定義。変更しないものは凍結
4. **正直な報告** — WORKING / PARTIAL / BROKENラベル。サイレント故障もモック偽装もなし
5. **セッション継続性** — ハンドオフで開始、チェックポイントで終了。コンテキストはセッションを超えて存続

---

## ライセンス

MIT — [LICENSE](../LICENSE)を参照。

## コントリビュート

IssueとPRを歓迎します。ライフサイクルに合うスキルを作成されたら、PRを開いてください。

## 連絡先

カスタムスキル開発のDMは[@AlexZio00](https://x.com/AlexZio00)まで。
