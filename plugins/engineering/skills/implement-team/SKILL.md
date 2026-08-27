---
name: implement-team
description: "针对 PRD/spec 与 .scratch/<feature>/issues/ 实现 tickets 的团队实施编排：经用户确认后用原生 AgentTeam 安全并发派发 /implement。"
disable-model-invocation: true
---

# Implement team

## 职责与边界

本 skill 只处理 `prd.md`、`spec.md` 与实际 `.scratch/<feature>/issues/` 下的实现 tickets，三类输入可以任意组合。每个 ticket 是唯一执行单元；不能把 PRD、spec 或多个 ticket 合并成一个执行单元。本 skill 不处理 `map.md`，也不处理 direct-task。用户只有直接实现目标时，只调用 `/implement`，不创建 AgentTeam，规则见 `references/direct-task.md`。

团队使用原生 `TeamCreate` 创建一个 `AgentTeam`。主 Agent 是唯一 coordinator、派发者、依赖解锁者和独立核验者；成员共享 team 上下文，但不得自行解锁后继 ticket。公共 manifest、状态、终态事件、DAG、并发保护、失败传播和 fail-closed 规则见 `docs/agents/agent-team-protocol.md` 与 `references/manifest-template.md`。

## 输入评估与确认门禁

1. 读取存在的 `prd.md`、`spec.md` 以及实际 `.scratch/<feature>/issues/` 中的每个 ticket，保留原文、路径、`Status:`、`Blocked by:`/`dependsOn`、目标、验收、`allowedPaths`、验证命令和 evidence 路径。不能臆造不存在的 ticket。
2. 若同时存在 PRD 与 spec，先逐条合并范围、验收、非目标和约束。冲突必须输出矩阵（来源、冲突内容、影响、选项）与推荐方案并询问用户；无冲突也必须输出合并评估、缺口和推荐并等待用户确认。
3. 没有任何实现 tickets 时，只完成输入评估并停止：不得创建 team、启动 sub agent、修改 tracker 或工作区。
4. 有 tickets 时，先检查 ID 唯一、依赖存在且无环、tracker 可写、验证命令可识别、`allowedPaths` 明确；范围不确定时标记不确定并禁止并行。记录项目路径、Git 分支、modified/untracked/staged 基线、protectedPaths、coverage/锁/evidence 路径。
5. 一次性展示输入来源、PRD/spec 合并结果、coordinator policy、ticket DAG、并发组、范围、验收、tracker 更新、保护边界、Git 基线、evidence 和 `maxRepairRounds`。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区；只有确认后才创建一个 `AgentTeam`。

## 派发与执行

确认后主 Agent 为每个 ticket 派发一次任务。prompt 必须包含 ticket 原文、唯一 ID、tracker、已完成依赖、`allowedPaths`、verify、evidence、保护边界、终态格式和当前 spec/PRD 约束。每个子 agent 只能调用 `/implement`，只处理当前 ticket，不处理其他 ticket，不解锁后继。

子 agent 完成后必须把 ticket 的 `Status: resolved`、`failed` 或 `blocked` 回写，并附验证与 evidence；`resolved` 没有 evidence 不合法。主 Agent 将终态事件写入共享上下文并独立核验，只有核验通过才进入 `resolved` 并释放后继。任何重复、缺字段、ID 不匹配、tracker 未更新、验证失败或异常退出都 fail-closed。

## DAG 调度、保护与失败传播

状态流转为 `pending → running → verifying → resolved`，失败或阻塞转为 `failed`/`blocked`。每轮选择所有依赖已核验为 `resolved` 的 ready ticket。规范化后若 `allowedPaths` 存在相同路径、文件与父子目录、glob 交集或不确定范围，则禁止并行；独立分支必须最大化并发。coverage、锁、evidence、protectedPaths 和用户既有改动属于保护边界。

收到 `failed`/`blocked` 或独立核验失败时，主 Agent 立即记录 reason、日志、verification 和 evidence，并只沿依赖后代传播 `blocked`；独立分支继续。恢复需用户批准并重新建立基线，不自动 retry、reset、rollback、stash、合并或删除证据。

主 Agent 复核 commit 存在且属于当前 ticket、changedFiles 仅在 `allowedPaths`，Git 基线与 protectedPaths 未被污染，staging、coverage 和锁未被改动，验证命令/evidence 可复核，tracker 状态正确。核验不通过就保持 blocked，绝不乐观放行。

## 收尾

主 Agent 回收已完成 team task，保留共享上下文与 evidence，汇总每个 ticket 的 tracker、状态、commit、changedFiles、verification、evidence、失败/阻塞原因和未完成依赖。已完成 ticket 不重复启动。

## References

- 输入与 PRD/spec 合并规则：`references/prd-spec.md`
- direct-task 边界：`references/direct-task.md`
- manifest 与终态协议指针：`references/manifest-template.md`
- 公共 AgentTeam 协议：`docs/agents/agent-team-protocol.md`
