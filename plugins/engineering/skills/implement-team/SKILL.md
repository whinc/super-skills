---
name: implement-team
description: "针对 PRD/spec 与 .scratch/<feature>/issues/ 实现 tickets 的并发实施编排：AgentTeam 并发派发 /implement 提速，context 卫生防主 Agent 膨胀掉质量；经用户确认后启动。"
disable-model-invocation: true
---

# Implement team

## 职责与边界

本 skill 只处理 `prd.md`、`spec.md` 与实际 `.scratch/<feature>/issues/` 下的实现 tickets，三类输入可以任意组合。每个 ticket 是唯一执行单元；不能把 PRD、spec 或多个 ticket 合并成一个执行单元。本 skill 不处理 `map.md`，也不处理 direct-task。用户只有直接实现目标时，只调用 `/implement`，不创建 AgentTeam，规则见 `references/direct-task.md`。

团队使用原生 `TeamCreate` 创建一个 `AgentTeam`。主 Agent 是唯一 coordinator、派发者、依赖解锁者和独立核验者；成员共享 team 上下文，但不得自行解锁后继 ticket。公共 manifest、状态、终态事件、DAG、CONFLICT 升级、失败传播、context 卫生和 fail-closed 规则见 `docs/agents/agent-team-protocol.md` 与 `references/manifest-template.md`。

## 输入评估与确认门禁

1. 读取存在的 `prd.md`、`spec.md` 以及实际 `.scratch/<feature>/issues/` 中的每个 ticket，保留原文、路径、`Status:`、`Blocked by:`/`dependsOn`、目标、验收、验证命令和 evidence 路径。不能臆造不存在的 ticket。
2. 若同时存在 PRD 与 spec，先逐条合并范围、验收、非目标和约束。冲突必须输出矩阵（来源、冲突内容、影响、选项）与推荐方案并询问用户；无冲突也必须输出合并评估、缺口和推荐并等待用户确认。
3. 没有任何实现 tickets 时，只完成输入评估并停止：不得创建 team、启动 sub agent、修改 tracker 或工作区。
4. 有 tickets 时，先检查 ID 唯一、依赖存在且无环、tracker 可写、验证命令可识别；范围不确定时标记不确定。记录项目路径、Git 分支、modified/untracked/staged 基线、runId、protectedPaths、coverage/锁/evidence 路径。
5. 一次性展示输入来源、PRD/spec 合并结果、coordinator policy、ticket DAG、并发上限、范围、验收、tracker 更新、保护边界、Git 基线、evidence 和 `maxRepairRounds`。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区；只有确认后才创建一个 `AgentTeam`。

## 派发与执行

确认后主 Agent 为每个 ticket 派发一次。prompt 遵循 context 卫生：只含 ticket ID、tracker 文件路径、`protectedPaths`、verify 命令、evidence 约定、终态格式和一行目标摘要；ticket 原文由 teammate 自行 Read。每个子 agent 只能调用 `/implement`，只处理当前 ticket，不处理其他 ticket，不解锁后继。

Teammate 只报告一次终态事件，过程性消息一律禁止，进度只通过 tracker `Status:` 字段体现。Teammate 运行中发现文件冲突（编辑竞争、工作区出现非本 ticket 的改动）时发送 `CONFLICT` 升级消息请求主 Agent 协调（等待、串行重派或指引避让）；这是唯一合法的中途消息，冲突期间 ticket 保持 `running`，不发终态。

子 agent 完成后必须把 ticket 的 `Status: resolved`、`failed` 或 `blocked` 回写，并附验证与 evidence；`resolved` 没有 evidence 不合法。终态事件有硬上限（summary ≤ 2 行、changedFiles > 20 条落盘清单、verification 不含输出），超出内容按双轨落盘写入 evidenceDir 或 tempDir，事件中只留路径。主 Agent 将终态事件的一行摘要写入共享上下文并独立核验，只有核验通过才进入 `resolved` 并释放后继。任何重复、缺字段、ID 不匹配、tracker 未更新、验证失败或异常退出都 fail-closed。

## DAG 调度、保护与失败传播

状态流转为 `pending → running → verifying → resolved`，失败或阻塞转为 `failed`/`blocked`。每轮选择所有依赖已核验为 `resolved` 的 ready ticket，在 `maxConcurrency` 上限内全量并发派发；不做调度期路径检查，冲突防护由运行时 CONFLICT 升级承担（ADR-0001）。coverage、锁、evidence、protectedPaths 和用户既有改动属于保护边界。

收到 `failed`/`blocked` 或独立核验失败时，主 Agent 在共享上下文写一行事件摘要加指针（详情、日志落盘到 `evidenceDir/<ticket>.failed.md`），并只沿依赖后代传播 `blocked`，后代派发 prompt 只引用指针路径；独立分支继续。恢复需用户批准并重新建立基线，不自动 retry、reset、rollback、stash、合并或删除证据。

主 Agent 独立核验：commit 存在且属于当前 ticket，Git 基线与 protectedPaths 未被污染，staging、coverage 和锁未被改动，验证命令/evidence 可复核，tracker 状态正确。核验命令输出重定向到 `evidenceDir/<ticket>.verify.log`，context 只留一行结论。`changedFiles` 是纯记录，不做范围校验。核验不通过就保持 blocked，绝不乐观放行。

## 收尾

主 Agent 回收已完成 team task，保留共享上下文与 evidence，生成 `evidenceDir/report.md` 全量明细（每个 ticket 的 tracker、状态、commit、changedFiles、verification、evidence、失败/阻塞原因和未完成依赖）；对话中只输出简表（ticket / 状态 / commit / 一行结论）加 report 路径。已完成 ticket 不重复启动。

## References

- 输入与 PRD/spec 合并规则：`references/prd-spec.md`
- direct-task 边界：`references/direct-task.md`
- manifest 与终态协议指针：`references/manifest-template.md`
- 公共 AgentTeam 协议（含 context 卫生）：`docs/agents/agent-team-protocol.md`
- 移除静态任务范围声明、改运行时冲突升级的决策：`docs/adr/0001-remove-allowedpaths-runtime-conflict-escalation.md`
