# PRD/spec 与实现 tickets 输入

本分支处理 `prd.md`、`spec.md` 与实际 `.scratch/<feature>/issues/` tickets 的任意组合。每个 issue 文件是一个独立实现 ticket；PRD 或 spec 只是约束来源，不是 ticket。

## 读取与映射

保留 PRD/spec 的范围、验收、非目标和约束，读取每个 ticket 的原文、`Status:`、`Blocked by:`/`dependsOn`、`allowedPaths`、验证命令、tracker 和 evidence。ticket ID 必须唯一，依赖必须存在且无环。没有 tickets 时只评估并停止。

## 合并与确认

同时存在 `prd.md` 和 `spec.md` 时，逐项合并两者内容。无论是否发现冲突，都要先输出评估并等待用户确认；有冲突时必须给出来源/内容/影响/选项矩阵和推荐方案。确认前不创建 `AgentTeam`，不启动 sub agent，不改 tracker 或工作区。

## 派发

用户确认后，主 Agent 按 DAG 派发每个 ticket。子 agent 只能调用 `/implement`，只实现当前 ticket，并按公共终态协议回写 `Status: resolved`/`failed`/`blocked`、验证和 evidence。主 Agent 独立核验后才解锁后继；失败只阻塞依赖后代，独立分支继续。
