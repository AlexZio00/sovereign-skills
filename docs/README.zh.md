[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | 🌐 **中文** | [Español](README.es.md)

# sovereign-skills v6.5.15

覆盖 Claude Code 项目完整生命周期的 23 个技能 — 从初始设置到日常工作流、代码审查、会话管理、治理。每个技能可独立使用，完整序列覆盖所有环节。

> **v6.5.15 变更：** 新增两个技能 — `ssot-audit`（找出同一事实的所有副本并确定唯一权威来源）和 `skill-trigger-auditor`（检查技能和命令是否被正确路由）。缺陷修复：先提交、之后再推送时，`pre-push` 不再跳过测试和 lint；`project-check` 现在能识别带连字符的 API 密钥（`sk-ant-…`、`sk-proj-…`）；`setup` 的 hook 示例不再依赖 `bash` + `jq`，在 Windows 上也能运行。其他技能的升级：`code-autopsy` 为每条发现标注 NEW 或 PRE-EXISTING 并给出证据等级；会话类技能会标出日期已过的交接项；`integration-intake` 在重新审查某个仓库之前，先查询自己此前的判定。全部 22 个技能还经过了一次通读审计：内置脚本在任何安装位置都能被找到（`${CLAUDE_SKILL_DIR}`），可在 Python 3.9+ 和 macOS 上运行，可选的外部智能体都有标注和后备方案，共享文件格式已写入 [docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md)。详见 [CHANGELOG.md](../CHANGELOG.md)。

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
  /next-action        随时 — 读取当前状态，提出前3项下一步行动
  /code-autopsy       12Q代码审查 + 严重性评分 + 部署判定
  /pre-push           push 前（密钥扫描 + AI 审查）
  /session-checkpoint 会话结束时
```

**已有项目（5分钟）：**
```
/project-check      →  4 维度评分 + 按严重度排序的差距列表
/collab-audit       →  基于你的工作模式生成 14 节 AI 协作诊断
```

**治理与审计（按需）：**
```
/integration-intake →  采用外部技能/智能体/规则/插件前 — 5 项筛选门
/full-audit         →  对整个区域（代码库/文档/技能/记忆/配置）的详尽审计 + 持久覆盖图
/clean-room         →  当任务混合了安全相关内容与真正安全的工作时
/eval-leakage-audit →  在信任某个eval/metric/holdout前 — 检查是否循环自我确认
/doc-drift          →  审计已加载上下文（CLAUDE.md/MEMORY.md/skills）中的过时/矛盾措辞
/ssot-audit         →  一个事实散落在多个文件中 — 找到权威来源，再合并
```

**如果你自己编写技能：**
```
/skill-trigger-auditor →  修改技能 description 之前 — 找出路由冲突和误触发
/skill-ops             →  编辑前为技能做快照/回滚，查看哪些技能真正在被使用
/project-overview      →  一张图掌握多个项目的状态
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
| [scope](../scope/) | 实现前定义 IN/OUT/退出标准。Quick 模式（3 个问题）或 Full 模式（分层规格）。Full 模式附带 `coverage_check.py`（需求↔任务核对） |
| [freeze](../freeze/) | 声明可编辑区域 — 其余冻结。防止实现过程中的范围蔓延 |
| [goal-lock](../goal-lock/) | 智能体纪律引擎 — 锁定目标，强制 PLAN→DO→VERIFY→FINALIZE→OUTPUT 循环，检测 16 种成功伪装模式 |
| [pre-push](../pre-push/) | 强制 pre-push 管道 — 密钥扫描（14 种模式）、构建/测试、lint、并行 AI 代码审查。检查这次 push 实际携带的内容（已暂存的改动 + 尚未推送的提交）。发现 Critical/High 时阻止 push |

### 视角转换

| 技能 | 功能 |
|------|------|
| [stepback](../stepback/) | 一次性视角重置 — 1个抽象重构问题 + 3项快速检查（范围偏移、副作用、更优方案）以及继续/停止的判定，10行以内。工作中随时可用 |
| [next-action](../next-action/) | 读取交接文件/git/lessons/STATE，按影响力提出前3项下一步行动。仅提议，不执行。随时可用 |

### 会话管理

| 技能 | 功能 |
|------|------|
| [session-start](../session-start/) | 加载上次会话的交接文件，回顾经验教训，健康检查，输出带优先操作的"就绪"信号。标出日期已过的交接项 |
| [session-checkpoint](../session-checkpoint/) | compact 前保存会话上下文 — 交接文件、记忆更新、教训提取、反思（什么出了问题，下次如何改进）。把带未来日期的项目放进单独的"Scheduled checks"列表 |

### 代码审查

| 技能 | 功能 |
|------|------|
| [code-autopsy](../code-autopsy/) | 12Q量化代码审查（v7.3） — 4轴评分（Security/Stability/Robustness/Operability）、严重性锚点、部署判定（SHIP/FIX/RISKY/BLOCK）、Factuality Gate。每条发现都标注 NEW 或 PRE-EXISTING 并带有证据等级。有实证依据（Johnson 2019、Parnas 1972）。作为独立提示词可在任何LLM中使用 |

### 质量

| 技能 | 功能 |
|------|------|
| [agent-qa-testing](../agent-qa-testing/) | 使用 agent-qa 验证、运行和分析 Web／移动端回归测试，结合高级 memidex 记忆与自我改进能力 |
| [project-check](../project-check/) | 从 4 个维度扫描现有项目：基础设施、安全、质量、测试框架。按严重度排序差距 |
| [collab-audit](../collab-audit/) | 14 节 AI 协作审计 — 分析实际工作模式（非问卷），生成行为画像、盲点和成长方向。所需会话数据由 `extract_session_meta.py` 生成 |

### 运维

| 技能 | 功能 |
|------|------|
| [skill-ops](../skill-ops/) | 技能/智能体运维中枢 — 快照/回滚 + 使用状况 + 调用追踪 + 质量评分，4 种模式。附带 `skill_snapshot.py` 和 `skill_health_bucket.py` |
| [project-overview](../project-overview/) | 从已注册项目的会话交接文件生成确定性跨项目状态地图，并报告超过 7 天的快照 |
| [skill-trigger-auditor](../skill-trigger-auditor/) | **v6.5.15 新增。** 审计技能、智能体和斜杠命令的路由是否存在冲突和误触发，并用留出集（holdout）触发测试为 description 的修改把关。可选的探针会度量真实的 Skill 工具调用 |

### 治理

| 技能 | 功能 |
|------|------|
| [full-audit](../full-audit/) | 对整个区域（代码库/文档/技能/记忆/配置）的详尽审计 — 确定性扫描+内容审查双层方法、防误报kill-test、植入式金丝雀、持久化覆盖图 |
| [integration-intake](../integration-intake/) | 外部模式（技能/智能体/规则/插件/MCP）采纳的5项筛选闸门 — 与现有资产的重复检查、引入内容的provenance/注入检查、一行许可证说明，以及对此前判定的台账查询 |
| [clean-room](../clean-room/) | 将安全敏感请求切分为安全范围，由完全隔离的fresh-context子智能体执行 — 对抗性验证通过 + descope ledger |
| [eval-leakage-audit](../eval-leakage-audit/) | 审计eval/metric/holdout是否真正确保了独立的外部真值，还是循环自我确认 — 28 种模式的分类法，两个黄金用例。只读 |
| [doc-drift](../doc-drift/) | 审计Claude Code加载到上下文中的记忆/文档(CLAUDE.md/MEMORY.md/skills/agents/commands)，发现过时声明、相互矛盾和风险/模糊措辞 — 生成优先级修复清单 |
| [ssot-audit](../ssot-audit/) | **v6.5.15 新增。** 在仓库或笔记文件夹中找出同一事实、数值或决策的所有副本，确定唯一权威来源（只读），并且只在你批准之后才合并重复内容 |

---

## 生命周期流程

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

## 安装

### 方法 A：复制技能（最简单）

每个技能都是一个独立目录，其中包含一个 `SKILL.md` 文件。复制你需要的即可：

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

在 Claude Code 中输入触发命令（如 `/goal-lock`）即可调用技能。Claude 会读取 SKILL.md 并按其中的指示执行。

### 方法 C：Codex

Codex 会在仓库级、用户级（`$HOME/.agents/skills`）、管理员级和系统级扫描 `.agents/skills/<skill-name>/SKILL.md` 来发现技能 —— 不需要单独的智能体定义文件。安装方式与 Claude Code 相同，只是路径换成 `.agents/skills/`：

```bash
# 用户级（所有项目均可用）
cp -r goal-lock ~/.agents/skills/goal-lock/

# 仓库级（仅限本项目）
cp -r goal-lock .agents/skills/goal-lock/
```

每个技能还**可选地**附带 `agents/openai.yaml` —— 这是供 ChatGPT 桌面应用使用的 UI/策略元数据（显示名称、描述、图标/品牌色，以及默认值为 `true` 的 `allow_implicit_invocation` 标志）。Codex 发现或运行技能并不需要它，只有需要这份元数据时才把它和 `SKILL.md` 一起复制过去：

```bash
cp -r goal-lock/agents .agents/skills/goal-lock/agents/
```

完整的发现机制与元数据规范请参见[官方 Codex 技能文档](https://learn.chatgpt.com/docs/build-skills)。

### 方法 D：Cursor / 其他智能体

SKILL.md 的内容是通用 markdown —— 支持读取 markdown 指令的任何 LLM 都可以使用。将 `SKILL.md` 复制到你所用智能体的指令路径中即可。

### 要求

- **Claude Code**：CLI、桌面应用或网页应用（[claude.ai/code](https://claude.ai/code)）
- **Codex**：OpenAI Codex —— 直接从 `.agents/skills/` 读取 `SKILL.md`；`agents/openai.yaml` 是可选的 UI 元数据
- **Cursor / 其他**：支持读取 markdown 指令的任何智能体
- 技能目录：`~/.claude/skills/`（Claude Code）或智能体专属路径
- 内置辅助脚本（若干技能内的 `scripts/*.py`）需要 Python 3.9+。技能以 `${CLAUDE_SKILL_DIR}/scripts/<name>.py` 调用它们，Claude Code 会把该值替换为技能自己的文件夹；在其他智能体中，请换成你安装技能的文件夹。脚本无法运行时，各技能会说明是回退到手动步骤还是停止
- `pre-push` 同时包含 `scan_secrets.py`（首选）和 `scan_secrets.pl`（Perl 后备）。可选：`ruff`（对改动行做 lint）和 `gitleaks`（第二个密钥扫描引擎，仅作警告）

### 会话类技能读写的文件

`session-start`、`session-checkpoint`、`next-action`、`project-overview`、`skill-ops` 和 `collab-audit` 共用几个纯文本文件：会话交接文件、`tasks/lessons.md`、`~/.claude/STATE.md`、`memory/MEMORY.md`、上下文日志和调用日志。这些文件都不是必需的 —— 文件缺失时，技能会跳过对应步骤。格式见：[docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md)。

### 本仓库未包含的可选智能体和技能

部分技能可以把工作交给本仓库**不**提供的智能体或技能。SKILL.md 中的每处提及都标注为可选并带有后备方案，因此缺少它们不会出问题：

| 名称 | 使用它的技能 | 缺少时 |
|------|------------|--------|
| `code-reviewer`、`security-reviewer`、`database-reviewer`、`build-error-resolver` | pre-push | `/setup` 可以生成这些智能体；否则 pre-push 执行内联审查（code-autopsy FAST MODE），并把智能体步骤标记为 SKIPPED |
| `refactor-cleaner` | pre-push | 跳过该步骤 |
| `doubt-reviewer` | scope（Full 模式）、goal-lock | 使用带对抗性提示的通用子智能体，或在报告中标记为 SKIPPED |
| `verification`、`brainstorming`、`check-harness`、`memory-dream`、`forge` | 各处的 see-also / 路由说明 | 仅为指引 —— 没有它们技能也能运行 |

---

## 智能体设计模式覆盖

这些技能对应已发表目录（[Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)）中的 18 种智能体设计模式：

| 模式 | 实现技能 | 方法 |
|------|---------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | 完整生命周期链 |
| **Parallel Execution** | pre-push | 并行 AI 代码审查智能体 |
| **Loop (Retry)** | goal-lock | VERIFY 失败 → PLAN 重新进入，有上限 |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | 独立的审查者子智能体（可选 —— 见上文）或内联审查；12Q 结构化审查；full-audit 的 Phase 2 扇出审查者环节；eval-leakage-audit 评判某个eval是否确保了独立真值还是循环自我确认 |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE 通过 |
| **Coordinator/Router** | setup | 生成智能体路由规则 |
| **Plan-and-Execute** | goal-lock, scope | 执行前可审查的计划 |
| **ReAct** | project-check | 调查 → 评分 → 路径建议 |
| **Reflexion** | session-checkpoint | Phase 1.7：失败分析 → 下一会话教训 |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES，Critical/High 阻止推送；integration-intake 采用前的 5 项筛选门 |
| **Custom Logic** | pre-push | 确定性密钥扫描（Python，Perl 后备）+ AI 审查 |
| **Event-Driven** | session-start | 会话打开时触发，加载先前状态 |
| **Guardrails/Safety** | goal-lock, clean-room | 检测 16 种成功伪装模式；clean-room 将安全相关范围切出到隔离的子智能体运行 |
| **Memory Management** | session-checkpoint, doc-drift | 交接文件 + 记忆更新 + 教训提取；doc-drift 审计加载到上下文中的记忆/文档中的过时声明、矛盾和风险措辞 |
| **Goal Setting** | goal-lock | GOAL + DONE EVIDENCE 输入表 |
| **Step-Back Abstraction** | stepback | DeepMind step-back：具体 → 抽象原则 |
| **Prioritization** | next-action | 把来自交接文件/git/lessons/STATE 的候选行动按影响力排序 |
| **Evaluation & Monitoring** | skill-ops, skill-trigger-auditor, project-overview | 每个技能的使用状况；在留出提示词上的路由精确率/召回率；跨项目的过期快照报告 |

---

## 设计原则

1. **访谈优于模板** — 不生成空骨架，而是通过提问和决策生成充实的内容
2. **验证优于信任** — 完成证据必须执行，不能假设。"应该能通过"不是验证
3. **先定范围再写代码** — 修改文件前定义 IN/OUT/退出标准。不修改的部分冻结
4. **诚实报告** — WORKING / PARTIAL / BROKEN 标签。没有静默故障，没有 mock 欺骗
5. **会话连续性** — 以交接开始，以检查点结束。上下文跨会话存续

---

## 技能间的连接关系

各技能通过 frontmatter 中的 `see_also`（相关技能）和 `not_for`（误用防护）声明彼此关系。主要关系：

| 技能 | 连接对象 | 关系 |
|------|---------|------|
| `scope` | `goal-lock`, `freeze` | scope 定义要构建什么，freeze 锁定可编辑区域，goal-lock 强制执行循环 |
| `freeze` | `scope`, `goal-lock` | freeze 是连接 scope 规划与 goal-lock 循环强制的手动区域锁定 |
| `goal-lock` | `scope`, `freeze` | goal-lock 是在 scope/freeze 划定边界内运作的执行期纪律层 |
| `stepback` | `next-action` | stepback 检查方向（"是否在解决正确的问题"），next-action 推荐行动（"按影响力下一步是什么"） |
| `next-action` | `session-start`, `stepback` | next-action 读取当前状态提出建议，session-start 恢复上一会话的状态 |
| `session-start` | `session-checkpoint` | 生命周期配对 — 打开和关闭会话 |
| `session-checkpoint` | `session-start`, `setup` | 关闭会话，setup 打开新项目 |
| `code-autopsy` | `pre-push` | code-autopsy 是深入的按需 12Q 审查，pre-push 是每次 push 前运行的快速自动化流水线 |
| `skill-ops` | `project-overview` | skill-ops 管理技能/智能体的生命周期（快照/回滚/使用状况），project-overview 汇总多个项目的状态 |
| `integration-intake` | `full-audit` | integration-intake 为单次外部资产采用决策把关，full-audit 扫描整个区域（包括你现有的技能/智能体清单）的漂移或缺口 |
| `full-audit` | `code-autopsy`, `project-check` | full-audit 是更广的多区域扫描 + 持久覆盖图，code-autopsy 保持文件级/12Q，project-check 保持 4 维度评分 |
| `clean-room` | `goal-lock` | clean-room 在任务范围中途混入安全相关内容与安全工作时触发，goal-lock 是它所打断的 PLAN→DO→VERIFY 循环 |
| `doc-drift` | `full-audit` | doc-drift 只审计加载到上下文中的记忆/文档（CLAUDE.md/MEMORY.md/skills/agents）的漂移与矛盾，full-audit 用覆盖图扫描整个区域 |
| `eval-leakage-audit` | `full-audit`, `code-autopsy` | eval-leakage-audit 检查某个eval/metric/holdout是否循环论证（度量完整性），full-audit 和 code-autopsy 审查的是代码/区域，而非该eval的独立性 |
| `ssot-audit` | `doc-drift`, `full-audit` | ssot-audit 跨文件追踪同一个事实并选出权威来源；doc-drift 检查已加载上下文中的漂移；full-audit 扫描整个区域 |
| `skill-trigger-auditor` | `skill-ops`, `doc-drift` | skill-trigger-auditor 检查技能是否在正确的提示词上触发；skill-ops 追踪技能是否被使用并负责回滚；doc-drift 检查技能文本中的过时声明 |
| `project-check` | `setup`, `collab-audit` | project-check 为仓库的设置打分并列出差距（由 setup 补齐）；collab-audit 看的是你如何与 AI 协作，而不是仓库本身 |

图示（箭头 = "交接给" / "提供信息给"）：

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (随时，任何阶段)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (读取状态并推荐)
                                   │
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift / ssot-audit
                       (按需治理与审计，任何阶段)
                                   │
         skill-ops / skill-trigger-auditor / project-overview
                 (面向技能作者和多项目环境)
```

---

## 变更日志

完整版本历史（v3.0 → 最新）见 [CHANGELOG.md](../CHANGELOG.md)。

## 许可证

MIT — 参见 [LICENSE](../LICENSE)。

## 贡献

欢迎 Issue 和 PR。如果您创建了适合生命周期的技能，请提交 PR。

## 联系

定制技能开发请 DM [@AlexZio00](https://x.com/AlexZio00)
