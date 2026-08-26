---
name: implement-fast
description: "使用 AgentTeam 按依赖安全并发处理直接任务、map issues 或 spec tickets：按输入分支读取对应 reference，主 Agent 负责协调和核验。"
disable-model-invocation: true
---

# Implement fast

## 目标

把一个用户任务或一组 issue/ticket 转成依赖图，由主 Agent 通过原生 `TeamCreate` 创建一个 AgentTeam 并安全并发执行。成员共享（shared）team 上下文、状态和证据；主 Agent 是唯一 coordinator、派发者和解锁者。

## 输入分流

一次只处理一种输入；同时发现多种来源时，请用户选择。识别输入后，只读取对应的分支 reference，再执行本文件的共享协议：

- `direct-task`：用户直接给出待实现目标，读取 `references/direct-task.md`；
- `wayfinder-map`：输入包含 `map.md` 及其 issue map，读取 `references/wayfinder-map.md`；
- `spec-tickets`：输入包含 `spec.md` 与实现 tickets，读取 `references/spec-tickets.md`。

`references/manifest-template.md` 是 manifest 和完整终态格式的唯一来源；需要终态字段或 JSON 示例时读取它。

## 计划门禁

主 Agent 创建 team 前记录：项目路径、Git 分支、modified/untracked/staged 基线、`protectedPaths`、coverage/锁/evidence 路径、输入文件和 ticket 状态。

校验以下条件：ID 唯一；依赖存在且无环；tracker 可写；验证命令可识别；`allowedPaths` 明确。范围无法判断时标记为不确定并阻止并行。

一次性展示并确认：输入来源、coordinator policy、ticket 依赖、并发组、范围、验收、tracker 更新、保护边界、Git 基线、evidence 和 `maxRepairRounds`。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区。

## 派发协议

确认后只创建一个 AgentTeam，并将主 Agent 设为 coordinator。每个 sub agent prompt 必须包含：

- issue/ticket 原文、目标、类型、唯一 ID 和 tracker；
- 已完成依赖及保护边界；
- `allowedPaths`、`verify`、evidence 和 `maxRepairRounds`；
- 对应输入 reference 指定的 skill：direct/spec 调用 `/implement`；map 只调用 `/wayfinder` 并持续探索至 `resolved`；
- 当前任务范围、终态格式和 tracker 更新要求。

sub agent 只处理当前任务并报告一次终态。终态事件只能是 `TICKET_DONE`、`TICKET_FAILED` 或 `TICKET_BLOCKED`，至少包含 `ticket`、`status`、`commit`、`changedFiles`、`verification`、`evidence`、`summary`；失败/阻塞另含 `reason`。完整字段和 JSON 示例见 `references/manifest-template.md`。缺失、重复、格式错误、ID 不匹配或异常退出均由主 Agent fail-closed，保留现场。

## DAG 调度

状态：

```text
pending → running → verifying → done
                    ├→ failed
                    └→ blocked
```

每轮选择所有 `dependsOn` 已由主 Agent 核验为 `done` 的 ready task。规范化后检查同轮候选的 `allowedPaths`：相同路径、文件与父子目录、glob 交集或不确定范围都禁止并行；其余独立分支必须最大化并发。

sub agent 不解锁后继任务。只有主 Agent 完成核验后，ticket 才进入 `done`。

## 失败协调与核验

主 Agent 收到失败/阻塞或发现核验失败时，立即将终态、reason、日志、验证和 evidence 写入共享 team 上下文并通知成员；只沿依赖后代标记 `blocked`，独立分支继续。恢复需用户批准，并由主 Agent 重新建立基线后派发修复任务。

主 Agent 独立核验：

- 代码 ticket 的 commit 存在、属于当前 ticket，且 changedFiles 只在 `allowedPaths`；
- Git 基线、protectedPaths、staging、coverage 和锁未受污染；
- verification 命令、evidence 和 tracker 状态可复核；
- map issue 有 Answer 且 `Status: resolved`。

通过后写入共享上下文、释放依赖并调度下一轮。调度器不替 sub agent 合并或 cherry-pick commit，不自动 retry、reset、rollback、stash 或删除证据。

## 收尾

主 Agent 回收已完成 team task，保留共享上下文和 evidence，并汇总每项的 tracker、状态、commit、changedFiles、verification、evidence、失败/阻塞原因和未完成依赖。已完成任务不重复启动。