# direct-task 输入

当用户直接给出一个待实现目标，且没有现成 `map.md` 或 `spec.md` 时，使用本分支。

## 建立 ticket 草案

从用户描述拆出可独立验收的 ticket，并为每项补齐：

- `id`：唯一标识；
- 目标与验收结果；
- `dependsOn`：前置 ticket ID；
- `allowedPaths`：允许修改的路径；
- `verify`：可执行的验证命令；
- `tracker`：状态与证据写入位置；
- 执行 skill；
- evidence 位置。

在进入主 skill 的计划门禁前展示草案，确认依赖、并发组、范围、验收、tracker、保护边界和 evidence。用户确认后才创建 AgentTeam。

## 派发

每个 direct ticket 的 sub agent 先调用 `/implement`，只处理当前 ticket，并按主 skill 的终态协议报告一次。主 Agent 仍负责依赖调度、核验和解锁。