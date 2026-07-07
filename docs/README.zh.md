[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | 🌐 **中文** | [Español](README.es.md)

# sovereign-skills v6.3

覆盖 Claude Code 项目完整生命周期的 12 个技能 — 从初始设置到日常工作流、代码审查、会话管理。每个技能可独立使用，完整序列覆盖所有环节。

> **v6.2 变更：** 新增：`code-autopsy` — 12Q 定量代码审查，4 轴评分、严重度锚点、部署判定、CapCode/CEF 元检测。新增：`stepback` — 一次性视角重置。此前 10 个技能全部升级。

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
  /stepback           随时 — 方向确认，10行
  /code-autopsy       12Q代码审查 + 严重性评分 + 部署判定
  /pre-push           push 前（密钥扫描 + AI 审查）
  /session-checkpoint 会话结束时
```

**已有项目（5分钟）：**
```
/project-check      →  4 维度评分 + 按严重度排序的差距列表
/code-autopsy       →  12Q代码审查（可作为独立提示词在任何LLM中使用）
/collab-audit       →  14 节 AI 协作诊断
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
| [goal-lock](../goal-lock/) | 智能体纪律引擎 — 锁定目标，强制 PLAN→DO→VERIFY→FINALIZE→OUTPUT 循环，检测 11 种成功伪装模式 |
| [pre-push](../pre-push/) | 强制 pre-push 管道 — 密钥扫描（12 种模式）、构建/测试、lint、并行 AI 代码审查。发现 Critical/High 时阻止 push |

### 代码审查

| 技能 | 功能 |
|------|------|
| [code-autopsy](../code-autopsy/) | 12Q量化代码审查 — 4轴评分（Security/Stability/Robustness/Operability）、严重性锚定表、部署判定（SHIP/FIX/RISKY/BLOCK）、Factuality Gate、CapCode评分gaming检测、CEF伪装错误检测。作为独立提示词可在任何LLM中使用 |

### 视角转换

| 技能 | 功能 |
|------|------|
| [stepback](../stepback/) | **新增。** 一次性视角重置 — 1个抽象重构问题 + 3项快速检查（范围偏移、副作用、更优方案），10行以内。工作中随时可用 |

### 会话管理

| 技能 | 功能 |
|------|------|
| [session-start](../session-start/) | 加载上次会话的交接文件，回顾经验教训，健康检查，输出带优先操作的"就绪"信号 |
| [session-checkpoint](../session-checkpoint/) | compact 前保存会话上下文 — 交接文件、记忆更新、教训提取、反思（什么出了问题，下次如何改进） |

### 质量

| 技能 | 功能 |
|------|------|
| [project-check](../project-check/) | 从 4 个维度扫描现有项目：基础设施、安全、质量、测试框架。按严重度排序差距 |
| [collab-audit](../collab-audit/) | 14 节 AI 协作审计 — 分析实际工作模式（非问卷），生成行为画像、盲点和成长方向 |


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
│  /scope → /freeze → /goal-lock → 工作                 │
│       → /stepback (随时) → /code-autopsy → /pre-push   │
│       ↓                                               │
│  /session-checkpoint                                  │
└───────────────────────────────────────────────────────┘
         ↓
┌──────────────────── 按需 ──────────────────────────┐
│  /stepback         （视角重置 — 随时）                  │
│  /project-check    （健康审计）                        │
│  /collab-audit     （行为诊断）                        │
└──────────────────────────────────────────────────────┘
```

---

## 安装

### 方法 A：复制技能（最简单）

```bash
# 安装所有技能
git clone https://github.com/AlexZio00/sovereign-skills.git
cd sovereign-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# 或安装单个技能
cp -r goal-lock ~/.claude/skills/
```

### 方法 B：市场（sovereign-plugins）

本仓库是 Claude Code 市场。注册一次即可浏览和安装技能：

```bash
# 在 Claude Code 中添加 sovereign-plugins 市场
# 设置 → 插件 → 添加市场 → https://github.com/AlexZio00/sovereign-skills.git
```

每个技能也包含独立的 `.claude-plugin/plugin.json` 元数据。

在 Claude Code 中输入触发命令（如 `/goal-lock`）即可运行技能。

### 方法 C: Codex / Cursor (npx)

各技能包含 `agents/openai.yaml` 文件：

```bash
# Codex 技能安装
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent codex -g -y

# Cursor 技能安装
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent cursor -g -y

# Claude Code 安装（方法 A 的替代）
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent claude-code -g -y
```

SKILL.md 内容是通用的 — 支持读取 markdown 指令的任何 LLM 都可以使用。

### 要求

- [Claude Code](https://claude.ai/code) CLI、桌面应用或网页应用
- 技能目录：`~/.claude/skills/`（Claude Code 自动创建）
- `pre-push` 需要 Perl（`scan_secrets.pl` 已包含）

---

## v6.2 变更

### 新增功能
- **stepback** — 一次性视角重置。生成 1 个抽象重构问题（DeepMind step-back 模式）+ 3 个快速检查（范围偏移、副作用、更优方案），10 行以内。只读、无智能体、无代码。在实现过程中随时使用，检查是否在正确的级别解决了正确的问题。来源：team-attention/hoyeon。

### 更新内容
- **code-autopsy** — 添加元检测门：CapCode 分数游戏检测上限指标、CEF 约束规避虚假错误检测。
- **collab-audit** — 13→14 节。新增第 12 节：思考水平轨迹（信息请求者→思考设计师的 5 级模型 + 时间变化追踪 + AI 属性修正）。
- **goal-lock** — 添加 Ralph Wiggum 早期完成检测（第 12 种伪装模式）+ VERIFY 阶段验证可追踪性（所有声明必须追踪到实际工具调用）。
- **session-checkpoint** — 添加交接文件清晰性自检（交接文件编写后的 2 个锚点问题）。
- **session-start** — 添加上下文衰变防止（旧交接文件条目的滑动窗口）。
- **pre-push** — 添加新增依赖的 3-IOC 供应链检查。
- **scope** — 添加禁忌字段（选定方案不适用的条件）。
- **freeze** — 添加 Thaw Protocol（正式解冻工作流 + 爆炸范围检查 + 3 次解冻警告）。
- **project-init** — 扩展 `.env.example` 模板（OAuth、外部服务、监控部分）+ 安全基准线说明。
- **project-check** — 添加分数增量跟踪（当前 vs 之前扫描结果对比）。
- **setup** — 为 Tier 0 违规测试失败添加 Redesign Protocol（3 选项升级）。

---

## v6.1 变更

### 新增功能
- **code-autopsy** — 12Q 量化代码审查提示词（Code Autopsy v7.0）。从设计到可观测性的 12 个分析问题。4 轴复合评分（Security × 0.35 + Stability × 0.30 + Robustness × 0.20 + Operability × 0.15）。带加权公式的严重性锚定表。带 CRITICAL 硬上限的部署判定。Factuality Gate（报告前自验证）。跨文件影响分析。Quick 模式和 Diff 模式。证据：Google eng-practices、Johnson et al. 2019、Parnas 1972。在任何 LLM 中作为独立提示词工作 — 不限于 Claude Code。

---

## v6.0 变更

### 新增功能
- **goal-lock** — 具有 PLAN→DO→VERIFY→FINALIZE→OUTPUT 循环的智能体纪律引擎。检测 11 种成功伪装模式（测试删除、mock 包装、阈值放松等）。小改动用 Quick 模式（3 字段），其他用 Full 模式（7 字段）。

### 合并
- `harness-init` + `team-init` → **setup** — 基础设施和智能体团队一步到位
- `brief` + `adr` → **scope** — 集成 ADR 功能的范围定义
- `retro` → **session-checkpoint** — 回顾现在是 session-checkpoint 内的 Phase 1.7 Reflexion

### 移除
- `token-audit` — 改用 `npx ccusage` 直接或从模式构建 ccusage 技能
- `adr`（独立） — 已合并到 scope 中
- `retro`（独立） — 已合并到 session-checkpoint 中

### 升级
- 所有技能：添加 Dominant Variable、Key Assumptions、Error Recovery、Safety Layers
- 所有技能：带动作标签的 Scope Boundary（[READ]/[WRITE]/[BASH]/[AGENT]）
- `session-checkpoint`：Memento CoT 压缩、Reflexion、Invocation 日志
- `pre-push`：大 diff 确定性捆绑、Discard If 条件
- `collab-audit`：反模式标志、Key Assumptions

---

## 智能体设计模式覆盖

这 12 个技能实现了 25 种已知智能体设计模式中的 17 种（[Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)）：

| 模式 | 实现技能 | 方法 |
|------|---------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | 完整生命周期链 |
| **Parallel Execution** | pre-push | 并行 AI 代码审查智能体 |
| **Loop (Retry)** | goal-lock | VERIFY 失败 → PLAN 重新进入，有上限 |
| **Review & Critique** | pre-push, code-autopsy | 独立 code-reviewer + security-reviewer；12Q 结构化审查 |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE 通过 |
| **Coordinator/Router** | setup | 生成智能体路由规则 |
| **Plan-and-Execute** | goal-lock, scope | 执行前可审查的计划 |
| **ReAct** | project-check | 调查 → 评分 → 路径建议 |
| **Reflexion** | session-checkpoint | Phase 1.7：失败分析 → 下一会话教训 |
| **Human-in-the-Loop** | goal-lock, pre-push | STOP RULES，Critical/High 阻止推送 |
| **Custom Logic** | pre-push | 确定性密钥扫描（Perl）+ AI 审查 |
| **Event-Driven** | session-start | 会话打开时触发，加载先前状态 |
| **Guardrails/Safety** | goal-lock | 检测 11 种成功伪装模式 |
| **Memory Management** | session-checkpoint | 交接文件 + 记忆更新 + 教训提取 |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE 输入表 |
| **Step-Back Abstraction** | stepback | DeepMind step-back：具体 → 抽象原则 |

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
