# Super Skills — AgentTeam 编排

本仓库维护 ClaudeCode/CodeBuddy 的 skill 集合，其中 engineering 插件的 wayfinder-team 与 implement-team 基于原生 AgentTeam 并发派发子 agent。本词汇表约定团队编排与 memory 压缩的领域语言。

## 语言

### 团队编排

**主 Agent（Coordinator）**：
AgentTeam 中唯一的派发者、依赖解锁者和独立核验者。
_Avoid_: leader、boss、调度器

**Teammate**：
由主 Agent 派发的子 agent，只处理自己被分配的执行单元，不能解锁后继。
_Avoid_: sub-agent（泛指时可用）、worker

**Frontier**：
当前所有依赖已被主 Agent 核验为 `resolved`、且自身尚未进入执行的任务集合。frontier 上的任务全部并发派发；任一任务核验解锁后继时立即补派，不等同批其他任务终态。
_Avoid_: ready ticket、ready issue、待办列表、波次同步

**Ticket**：
AgentTeam 中的唯一执行单元，对应一个实现 ticket（implement-team）或探索 child issue（wayfinder-team）。
_Avoid_: 任务、工单

**Map**：
wayfinder 的探索地图文件（`map.md`），只读；对地图的补充以新增 issue 文件形式进行，不直接改写 Map。
_Avoid_: 把 Map 当作执行单元

**等待与唤醒**：
派发后主 Agent 结束当前回合等待终态通知，不轮询；每收到一个终态事件即处理，任一 Ticket 仍在 `running` 时不得收尾或宣称完成。
_Avoid_: 轮询、进度心跳

### Worktree 隔离（仅 implement-team）

**集成分支**：
一次 run 的工作分支（`agent-team/<runId>`），从落回目标分支的 HEAD 创建；所有 Ticket 分支合并进它，收尾由它落回目标分支。
_Avoid_: 主分支、feature 分支

**集成 worktree**：
集成分支的检出目录（`<tempDir>/integration`），主 Agent 合并、核验解锁与收尾集成验证的唯一场所；主工作区全程不被触碰。

**Ticket worktree**：
每个 Ticket 独立的工作检出与分支（`agent-team/<runId>/<ticket>`），Teammate 自行创建并只在此提交；隔离的是 Teammate 之间的编辑竞争，不是安全沙箱。
_Avoid_: 共享工作区、全局检出

**主工作区**：
用户的当前检出。Teammate 只在 Ticket worktree 内工作，对主工作区唯一的写操作是用绝对路径落盘 Evidence。
_Avoid_: protectedPaths（已移除：共享工作区时代的禁区清单，被 worktree 隔离取代）

**Merger**：
合并冲突时派出的解决者 Teammate，只解决冲突、不附加功能；报告 `MERGE_RESOLVED` 或 `MERGE_BLOCKED`，结果由主 Agent 复核并重跑该 Ticket 的 verify。
_Avoid_: 把 Merger 当作实现者

**落回**：
收尾时把集成分支 `git merge --no-ff` 进目标分支的动作；失败（冲突或工作区脏）保持现场，并向用户给出手动落回命令。
_Avoid_: 自动合并、发布

### Context 卫生

**Context 卫生**：
保持主 Agent context 只含决策所需最小信息的一组协议约束：结果不过程、大内容落盘、指针化共享上下文。

**双轨落盘**：
evidence 等可复核产物写入项目内 evidenceDir（`.scratch/runs/agent-team/<runId>/`）；过程性大输出（日志、中间产物）写入系统临时目录（`$TMPDIR/agent-team/<runId>/`），不值得长期保留。

**Evidence**：
可复核的任务证据（命令、路径、文件），必须落盘且随 repo 保留。
_Avoid_: 日志、输出（过程性内容不是 Evidence）

**终态事件**：
Teammate 报告结果的唯一一次结构化消息，只能是 `TICKET_RESOLVED`、`TICKET_FAILED` 或 `TICKET_BLOCKED`（Merger 用 `MERGE_RESOLVED`/`MERGE_BLOCKED`）；字段有硬上限，不含执行过程。
_Avoid_: 进度汇报、完成报告、心跳

**指针化共享上下文**：
共享上下文中只允许写入一行事件摘要加文件指针；详情落盘到 evidenceDir，需要时由读取方自行打开。

**Run Report**：
收尾时主 Agent 生成到 evidenceDir 的全量明细文件；含每个 Ticket 的状态与证据、集成验证结果、合并记录、落回 SHA 与保留的 worktree 路径。对话中只输出简表（Ticket / 状态 / commit / 一行结论）加 Report 路径。
_Avoid_: 在对话中全量汇总

### Memory 卫生

**Memory 存储（Memory store）**：
harness 提供给 agent 的跨会话持久记忆；形态可以是单文件、目录+索引（索引只放一行指针，正文在主题文件）或 memory API，`memory-compact` 不假设具体路径与产品。
_Avoid_: 记忆文件、Context（对话上下文）

**压缩（Memory compaction）**：
`memory-compact` 按 rubric 对每个条目做 keep/merge/delete/promote，批量提案经一次确认后写回；跨文档的 promote 只进报告建议，不写 memory 之外的文件。
_Avoid_: 摘要、总结

**主入口上限**：
作用于主入口文件的 200 行 / 25KB 双上限——单文件存储即该文件，目录+索引存储即索引；任一达到即需压缩，终态须同时低于两者；主题文件不受尺寸上限约束。
_Avoid_: 总容量、全仓配额
