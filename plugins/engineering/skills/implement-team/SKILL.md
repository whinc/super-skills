---
name: implement-team
description: "针对 PRD/spec 与 .scratch/<feature>/issues/ 实现 tickets 的并发实施编排：AgentTeam 并发派发 /implement 提速，context 卫生防主 Agent 膨胀掉质量；经用户确认后启动。"
disable-model-invocation: true
---

# Implement team

针对 `prd.md`、`spec.md` 与实际 `.scratch/<feature>/issues/` 的实现 tickets（三类输入可任意组合）做并发实施编排，manifest 的 `input.kind: prd-spec-input`。每个 ticket 是唯一执行单元；PRD、spec 和多个 ticket 各自独立，不合并成单一执行单元。用户只有单个实现目标时走 direct-task 边界：直接调用 `/implement`，不创建 `TeamCreate` 或 `AgentTeam`。文件冲突的处理方式是 CONFLICT 升级（仅本 skill 有）。

前置：目标项目用 `.scratch/<feature>/issues/` 存放 tickets；`/implement` 由 `mattpocock/skills` 提供，需预先安装。

公共机制——manifest、frontier 调度、context 卫生、CONFLICT 升级、终态事件、独立核验、fail-closed——唯一来源是 `references/agent-team-protocol.md`，本 skill 只定义输入边界与步骤。团队用原生 `TeamCreate` 创建一个 `AgentTeam`：主 Agent 是唯一 coordinator、派发者、解锁者和独立核验者；成员共享 team 上下文，解锁后继始终由主 Agent 执行。

## Steps

1. **输入评估**：读取存在的 `prd.md`、`spec.md` 与 `.scratch/<feature>/issues/` 下每个 ticket 的原文、`Status:`、`Blocked by:`/`dependsOn`、验收、verify 命令和 evidence 路径，臆造的 ticket 不进入 DAG。检查 ticket ID 唯一、依赖存在且无环、tracker 可写；范围不确定的 ticket 做标记。记录项目路径、Git 分支、工作区基线（modified/untracked/staged）与 `protectedPaths`。完成判据：DAG 合法，基线与保护边界已记录。

2. **PRD/spec 合并**：同时存在两者时，逐项合并范围、验收、非目标和约束。冲突项输出矩阵（来源、冲突内容、影响、选项）与推荐方案；无冲突时输出合并评估与缺口。完成判据：合并结果与推荐已呈现给用户。

3. **确认门禁**：没有任何实现 tickets 时，只完成输入评估并停止。有 tickets 时按 manifest 字段逐项展示（输入 sources、合并结果、ticket DAG、`maxConcurrency`、`protectedPaths`、evidence 路径、`maxRepairRounds`），等待用户确认。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区；确认后才创建一个原生 `AgentTeam` 并落盘 manifest。完成判据：用户明确确认。

4. **frontier 派发**：每轮把 frontier 上的 ticket（依赖已核验 `resolved`）在 `maxConcurrency` 上限内全量并发派发。prompt 遵循 context 卫生，只含 ticket ID、tracker 文件路径、`protectedPaths`、verify 命令、evidence 约定、终态格式和一行目标摘要；ticket 原文由 teammate 自行 Read。每个 teammate 只调用 `/implement`，只处理当前 ticket；运行中文件冲突走 CONFLICT 升级。完成判据：本轮 frontier 全部派发。

5. **独立核验**：teammate 报告终态后，主 Agent 按 protocol 独立核验（commit 存在且属于当前 ticket、Git 基线与 `protectedPaths` 未被污染、验证命令/evidence 可复核、tracker 已回写 `Status: resolved`），核验通过才解锁后继。失败只沿依赖后代传播 `blocked`，独立分支继续。完成判据：本轮终态全部核验并回写 tracker。

6. **收尾**：全部 ticket 终态后，回收已完成 team task，按 protocol 生成 `evidenceDir/report.md` 全量明细，对话中只输出简表（ticket / 状态 / commit / 一行结论）加 report 路径。已完成 ticket 不重复启动。完成判据：report.md 落盘且简表已输出。

## References

- 公共协议（manifest 字段、frontier、context 卫生、CONFLICT、终态、核验、fail-closed）：`references/agent-team-protocol.md`
