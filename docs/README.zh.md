[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | 🌐 **中文** | [Español](README.es.md)

# claude-code-skills v6.0

覆盖 Claude Code 项目完整生命周期的 10 个技能 — 从初始设置到日常工作流，再到会话管理。每个技能可独立使用，完整序列覆盖所有环节。

> **v6.0 变更：** 从 13 个整合为 10 个。`harness-init` + `team-init` → `setup`。`brief` + `adr` → `scope`。`retro` 并入 `session-checkpoint`。移除 `token-audit`（使用 `npx ccusage` CLI）。新增：`goal-lock` — 智能体纪律引擎。

---

## 快速开始

**新项目（15分钟）：**
```
/project-init       →  CLAUDE.md + ROADMAP + .gitignore + .env.example
/setup              →  rules/ + hooks + memory/ + 智能体路由 + 团队
日常：
  /session-start      会话开始时
  /scope              实现功能前（定义 IN/OUT/退出标准）
  /freeze             实现前（声明可编辑区域）
  /goal-lock          锁定目标，强制 PLAN→DO→VERIFY 循环
  /pre-push           push 前（密钥扫描 + AI 审查）
  /session-checkpoint 会话结束时
```

**已有项目（5分钟）：**
```
/project-check      →  4 维度评分 + 按严重度排序的差距列表
/collab-audit       →  13 节 AI 协作诊断
```

---

## 技能列表

### 设置阶段

| 技能 | 功能 |
|------|------|
| [project-init](../project-init/) | 基于访谈的项目脚手架 — 不是模板，而是通过决策生成 CLAUDE.md、ROADMAP、.gitignore、.env.example |
| [setup](../setup/) | Claude Code 基础设施 + 智能体团队 — 一次完成 rules、hooks、memory、路由和智能体安装 |

### 日常工作流

| 技能 | 功能 |
|------|------|
| [scope](../scope/) | 实现前定义 IN/OUT/退出标准。Quick 模式（3 个问题）或 Full 模式（分层规格） |
| [freeze](../freeze/) | 声明可编辑区域 — 其余冻结。防止实现过程中的范围蔓延 |
| [goal-lock](../goal-lock/) | **新增。** 智能体纪律引擎 — 锁定目标，强制 PLAN→DO→VERIFY→FINALIZE→OUTPUT 循环，检测 11 种成功伪装模式 |
| [pre-push](../pre-push/) | 强制 pre-push 管道 — 密钥扫描（12 种模式）、构建/测试、lint、并行 AI 代码审查。发现 Critical/High 时阻止 push |

### 会话管理

| 技能 | 功能 |
|------|------|
| [session-start](../session-start/) | 加载上次会话的交接文件，回顾经验教训，健康检查，输出带优先操作的"就绪"信号 |
| [session-checkpoint](../session-checkpoint/) | compact 前保存会话上下文 — 交接文件、记忆更新、教训提取、反思（什么出了问题，下次如何改进） |

### 质量

| 技能 | 功能 |
|------|------|
| [project-check](../project-check/) | 从 4 个维度扫描现有项目：基础设施、安全、质量、测试框架。按严重度排序差距 |
| [collab-audit](../collab-audit/) | 13 节 AI 协作审计 — 分析实际工作模式（非问卷），生成行为画像、盲点和成长方向 |

---

## 生命周期流程

```
┌──────────────────── 设置（一次）────────────────────┐
│  /project-init  →  /setup                            │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────── 日常循环 ───────────────────────┐
│  /session-start                                       │
│       ↓                                               │
│  /scope → /freeze → /goal-lock → 工作 → /pre-push    │
│       ↓                                               │
│  /session-checkpoint                                  │
└───────────────────────────────────────────────────────┘
         ↓
┌──────────────────── 按需 ──────────────────────────┐
│  /project-check    （健康审计）                        │
│  /collab-audit     （行为诊断）                        │
└──────────────────────────────────────────────────────┘
```

---

## 安装

### 方法 A：复制技能（最简单）

```bash
# 安装所有技能
git clone https://github.com/AlexZio00/claude-code-skills.git
cd claude-code-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# 或安装单个技能
cp -r goal-lock ~/.claude/skills/
```

### 方法 B：插件（支持市场分发）

每个技能都包含 `.claude-plugin/plugin.json` 元数据。如果您的市场支持基于 Git 的插件，请指向此仓库。

在 Claude Code 中输入触发命令（如 `/goal-lock`）即可运行技能。

### 要求

- [Claude Code](https://claude.ai/code) CLI、桌面应用或网页应用
- 技能目录：`~/.claude/skills/`（Claude Code 自动创建）
- `pre-push` 需要 Perl（`scan_secrets.pl` 已包含）

---

## 设计原则

1. **访谈优于模板** — 不生成空骨架，而是通过提问和决策生成充实的内容
2. **验证优于信任** — 完成证据必须执行，不能假设。"应该能通过"不是验证
3. **先定范围再写代码** — 修改文件前定义 IN/OUT/退出标准。不修改的部分冻结
4. **诚实报告** — WORKING / PARTIAL / BROKEN 标签。没有静默故障，没有 mock 欺骗
5. **会话连续性** — 以交接开始，以检查点结束。上下文跨会话存续

---

## 许可证

MIT — 参见 [LICENSE](../LICENSE)。

## 贡献

欢迎 Issue 和 PR。如果您创建了适合生命周期的技能，请提交 PR。

## 联系

定制技能开发请 DM [@AlexZio00](https://x.com/AlexZio00)
