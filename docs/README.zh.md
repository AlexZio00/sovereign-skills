[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | 🌐 **中文** | [Español](README.es.md)

# sovereign-skills v6.5

覆盖 Claude Code 项目完整生命周期的 20 个技能 — 从初始设置到日常工作流、代码审查、会话管理、治理。每个技能可独立使用，完整序列覆盖所有环节。

> **v6.5 变更：** 新增：`eval-leakage-audit`（通过8种模式的分类法，审计eval/metric/holdout是否真正确保了独立的外部真值，还是循环自我确认 — 只读）、`doc-drift`（审计Claude Code加载到上下文中的记忆/文档 — CLAUDE.md/MEMORY.md/skills/agents/commands — 发现过时声明、相互矛盾和风险/模糊措辞三类问题，生成优先级修复清单）。更新：`project-init`（修复了在区分大小写的文件系统上可能导致技能加载失败的`skill.md`→`SKILL.md`命名错误，并将Phase 3模板外部化到`references/templates.md`）、`pre-push` → v3.6（新增两种密钥扫描模式 — f11 diff中的提示注入字符串、f12非PyPI供应链索引URL — 以及Step 0 Hook流水线健康检查）、`scope`（新增Mid-Task Scope Drift十倍发现规则）、`collab-audit`（新增Step 0.6来源卫生过滤器，排除自动派生的子智能体/线程会话，避免被误认为有机用户会话）、`full-audit`/`integration-intake`（均新增Safety Layers章节；`integration-intake`还新增了Phase 1.8 M轴表面选择步骤 — 在路由前判断某个模式应归属哪个表面（提示词/规则/钩子/技能）），`goal-lock`（新增`migration`任务模板）、`project-overview`（新增Rationalization Table）、`stepback`（新增Dominant Variable章节 + frontmatter字段）。
>
> **v6.4 变更：** 新增：`full-audit`（对整个区域的详尽审计 — 确定性扫描+内容审查、持久化覆盖图、防误报kill-test）、`integration-intake`（外部技能/智能体/规则/插件采纳的5项筛选闸门，含provenance/注入检查）、`clean-room`（将安全敏感请求切分为安全范围，由完全隔离的fresh-context子智能体执行 — 改编自LilMGenius/paperthin的"autobahn"技能（MIT许可），新增文件系统层隔离与ledger记录时机升级）。更新：`goal-lock`（长任务检查点处重新回显CONSTRAINTS/SCOPE-Exclude）、`session-checkpoint`（新增Attestation阶段 — 内置`handoff_attestation.py`的证据链收据日志，供下次会话SessionStart钩子检测交接文件篡改）。
>
> **v6.3 变更：** 新增：`skill-ops`（快照/回滚 + 使用状况 + 调用追踪中枢）、`next-action`（读取交接文件/git/lessons/STATE，按影响力提出前3项下一步行动）、`project-overview`（确定性跨项目状态地图）。`code-autopsy` → v7.1（各问题子检查深化）、`pre-push` → v3.5（供应链IOC 9种模式）、`goal-lock`/`session-checkpoint`/`session-start`/`scope`/`stepback`/`freeze` 全部强化。原有12个技能全部新增 `not_for`/`see_also` frontmatter 以提升可发现性。

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
/code-autopsy       →  12Q代码审查（可作为独立提示词在任何LLM中使用）
/collab-audit       →  14 节 AI 协作诊断
```

**治理（按需）：**
```
/integration-intake →  采用外部技能/智能体/规则/插件前 — 5 项筛选门
/full-audit         →  对整个区域（代码库/文档/技能/记忆/配置）的详尽审计 + 持久覆盖图
/clean-room         →  当任务混合了安全相关内容与真正安全的工作时
/eval-leakage-audit →  在信任某个eval/metric/holdout前 — 检查是否循环自我确认
/doc-drift          →  审计已加载上下文（CLAUDE.md/MEMORY.md/skills）中的过时/矛盾措辞
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
| [goal-lock](../goal-lock/) | 智能体纪律引擎 — 锁定目标，强制 PLAN→DO→VERIFY→FINALIZE→OUTPUT 循环，检测 13 种成功伪装模式 |
| [pre-push](../pre-push/) | 强制 pre-push 管道 — 密钥扫描（12 种模式）、构建/测试、lint、并行 AI 代码审查。发现 Critical/High 时阻止 push |

### 代码审查

| 技能 | 功能 |
|------|------|
| [code-autopsy](../code-autopsy/) | **更新 v7.1。** 12Q量化代码审查 — 4轴评分（Security/Stability/Robustness/Operability）、严重性锚定表、部署判定（SHIP/FIX/RISKY/BLOCK）、Factuality Gate、CapCode评分gaming检测、CEF伪装错误检测。作为独立提示词可在任何LLM中使用 |

### 视角转换

| 技能 | 功能 |
|------|------|
| [stepback](../stepback/) | **更新。** 一次性视角重置 — 1个抽象重构问题 + 3项快速检查（范围偏移、副作用、更优方案），10行以内。工作中随时可用 |
| [next-action](../next-action/) | **新增。** 读取交接文件/git/lessons/STATE，按影响力提出前3项下一步行动。仅提议，不执行。随时可用 |

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

### 运维

| 技能 | 功能 |
|------|------|
| [skill-ops](../skill-ops/) | **新增。** 技能/智能体运维中枢 — 快照/回滚 + 使用状况 + 调用追踪，3 种模式 |
| [project-overview](../project-overview/) | **新增。** 从已注册项目的会话交接文件生成确定性跨项目状态地图 |

### 治理

| 技能 | 功能 |
|------|------|
| [full-audit](../full-audit/) | **新增。** 对整个区域（代码库/文档/技能/记忆/配置）的详尽审计 — 确定性扫描+内容审查双层方法、防误报kill-test、持久化覆盖图 |
| [integration-intake](../integration-intake/) | **新增。** 外部模式（技能/智能体/规则/插件/MCP）采纳的5项筛选闸门 — 与现有资产的重复检查 + 引入内容的provenance/注入检查 |
| [clean-room](../clean-room/) | **新增。** 将安全敏感请求切分为安全范围，由完全隔离的fresh-context子智能体执行 — 对抗性验证通过 + descope ledger |
| [eval-leakage-audit](../eval-leakage-audit/) | **新增。** 通过8种模式的分类法，审计eval/metric/holdout是否真正确保了独立的外部真值，还是循环自我确认。只读 |
| [doc-drift](../doc-drift/) | **新增。** 审计Claude Code加载到上下文中的记忆/文档(CLAUDE.md/MEMORY.md/skills/agents/commands)，发现过时声明、相互矛盾和风险/模糊措辞 — 生成优先级修复清单 |

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
│  /integration-intake （采用外部资产前）                 │
│  /full-audit       （整个区域的详尽审计）              │
│  /clean-room       （安全相关范围切分）                │
│  /eval-leakage-audit （eval循环逻辑检查）              │
│  /doc-drift        （已加载上下文的漂移审计）          │
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

- **Claude Code**：CLI、桌面应用或网页应用（[claude.ai/code](https://claude.ai/code)）
- **Codex**：OpenAI Codex（支持 `npx skills`）
- **Cursor**：Cursor IDE（支持技能插件）
- 技能目录：`~/.claude/skills/`（Claude Code）或智能体专属路径
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
- **goal-lock** — 具有 PLAN→DO→VERIFY→FINALIZE→OUTPUT 循环的智能体纪律引擎。检测 13 种成功伪装模式（测试删除、mock 包装、阈值放松等）。小改动用 Quick 模式（3 字段），其他用 Full 模式（7 字段）。

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

这 20 个技能中的 17 个（原始生命周期集合、v6.4 治理类新增技能、v6.5 审计类新增技能 — v6.3 的运维类新增技能尚未映射）实现了 25 种已知智能体设计模式中的 17 种（[Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)）：

| 模式 | 实现技能 | 方法 |
|------|---------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | 完整生命周期链 |
| **Parallel Execution** | pre-push | 并行 AI 代码审查智能体 |
| **Loop (Retry)** | goal-lock | VERIFY 失败 → PLAN 重新进入，有上限 |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | 独立 code-reviewer + security-reviewer；12Q 结构化审查；full-audit 的 Phase 2 扇出审查者环节；eval-leakage-audit 评判某个eval是否确保了独立真值还是循环自我确认 |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE 通过 |
| **Coordinator/Router** | setup | 生成智能体路由规则 |
| **Plan-and-Execute** | goal-lock, scope | 执行前可审查的计划 |
| **ReAct** | project-check | 调查 → 评分 → 路径建议 |
| **Reflexion** | session-checkpoint | Phase 1.7：失败分析 → 下一会话教训 |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES，Critical/High 阻止推送；integration-intake 采用前的 5 项筛选门 |
| **Custom Logic** | pre-push | 确定性密钥扫描（Perl）+ AI 审查 |
| **Event-Driven** | session-start | 会话打开时触发，加载先前状态 |
| **Guardrails/Safety** | goal-lock, clean-room | 检测 13 种成功伪装模式；clean-room 将安全相关范围切出到隔离的子智能体运行 |
| **Memory Management** | session-checkpoint, doc-drift | 交接文件 + 记忆更新 + 教训提取；doc-drift 审计加载到上下文中的记忆/文档中的过时声明、矛盾和风险措辞 |
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
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift
                       (按需治理，任何阶段)
```

---

## 许可证

MIT — 参见 [LICENSE](../LICENSE)。

## 贡献

欢迎 Issue 和 PR。如果您创建了适合生命周期的技能，请提交 PR。

## 联系

定制技能开发请 DM [@AlexZio00](https://x.com/AlexZio00)
