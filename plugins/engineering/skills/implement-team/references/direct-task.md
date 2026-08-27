# direct-task 边界

直接任务不是 `implement-team` 的团队输入。用户只给出待实现目标且没有 PRD/spec tickets 时，直接调用 `/implement`，不创建 `TeamCreate` 或 `AgentTeam`，也不拆成团队 tickets。该边界用于避免把单 ticket 工作误转为团队编排。
