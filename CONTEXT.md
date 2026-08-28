# Super Skills — AgentTeam 编排

本仓库维护 ClaudeCode/CodeBuddy 的 skill 集合，其中 engineering 插件的 wayfinder-team 与 implement-team 基于原生 AgentTeam 并发派发子 agent。本词汇表约定团队编排的领域语言。

## 语言

### 团队编排

**主 Agent（Coordinator）**：
AgentTeam 中唯一的派发者、依赖解锁者和独立核验者。
_Avoid_: leader、boss、调度器

**Teammate**：
由主 Agent 派发的子 agent，只处理自己被分配的执行单元，不能解锁后继。
_Avoid_: sub-agent（泛指时可用）、worker

**Ticket**：
AgentTeam 中的唯一执行单元，对应一个实现 ticket（implement-team）或探索 child issue（wayfinder-team）。
_Avoid_: 任务、工单

**Map**：
wayfinder 的探索地图文件（`map.md`），只读；对地图的补充以新增 issue 文件形式进行，不直接改写 Map。
_Avoid_: 把 Map 当作执行单元

### Context 卫生

**Context 卫生**：
保持主 Agent context 只含决策所需最小信息的一组协议约束：结果不过程、大内容落盘、指针化共享上下文。

**双轨落盘**：
evidence 等可复核产物写入项目内 evidenceDir（`.scratch/runs/agent-team/<runId>/`）；过程性大输出（日志、中间产物）写入系统临时目录（`$TMPDIR/agent-team/<runId>/`），不值得长期保留。

**Evidence**：
可复核的任务证据（命令、路径、文件），必须落盘且随 repo 保留。
_Avoid_: 日志、输出（过程性内容不是 Evidence）

**终态事件**：
Teammate 报告结果的唯一一次结构化消息，只能是 `TICKET_RESOLVED`、`TICKET_FAILED` 或 `TICKET_BLOCKED`；字段有硬上限，不含执行过程。
_Avoid_: 进度汇报、完成报告、心跳

**CONFLICT 升级**：
Teammate 在运行中发现文件冲突时发送的唯一合法中途消息，请求主 Agent 协调（等待、串行重派或指引避让）；仅 implement-team 使用，冲突期间 Ticket 保持 `running`。

**指针化共享上下文**：
共享上下文中只允许写入一行事件摘要加文件指针；详情落盘到 evidenceDir，需要时由读取方自行打开。

**Run Report**：
收尾时主 Agent 生成到 evidenceDir 的全量明细文件；对话中只输出简表（Ticket / 状态 / commit / 一行结论）加 Report 路径。
_Avoid_: 在对话中全量汇总

### 保护边界

**protectedPaths**：
禁止任何 Teammate 触碰的路径（用户既有改动、coverage、锁），独立于任务范围存在，防的是误伤用户工作区而非 Teammate 之间打架。
_Avoid_: allowedPaths（已移除的概念：静态任务范围声明，被 CONFLICT 升级取代）
