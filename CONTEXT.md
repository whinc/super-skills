# Super Skills — 领域语言

本仓库维护 ClaudeCode/CodeBuddy 的 skill 集合。本词汇表约定会话交接与 memory 压缩的领域语言。

## 会话交接

**Handoff（会话交接）**：
把当前会话中继续工作所需的上下文压缩成一份脱敏摘要，并以该摘要为 prompt 启动一个独立后台 agent 接续当前工作。
_Avoid_: 转交、会话迁移、后台任务（泛指）

## Memory 卫生

**Memory 存储（Memory store）**：
harness 提供给 agent 的跨会话持久记忆；形态可以是单文件、目录+索引（索引只放一行指针，正文在主题文件）或 memory API，`memory-compact` 不假设具体路径与产品。
_Avoid_: 记忆文件、Context（对话上下文）

**压缩（Memory compaction）**：
`memory-compact` 按 rubric 对每个条目做 keep/merge/delete/promote，批量提案经一次确认后写回；跨文档的 promote 只进报告建议，不写 memory 之外的文件。
_Avoid_: 摘要、总结

**主入口上限**：
作用于主入口文件的 200 行 / 25KB 双上限——单文件存储即该文件，目录+索引存储即索引；任一达到即需压缩，终态须同时低于两者；主题文件不受尺寸上限约束。
_Avoid_: 总容量、全仓配额
