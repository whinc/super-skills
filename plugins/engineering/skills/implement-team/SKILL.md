---
name: implement-team
description: "针对 PRD/spec 与 .scratch/<feature>/issues/ 实现 tickets 的并发实施编排：每 ticket 独立 worktree + AgentTeam 并发派发 /implement，主 Agent 独立核验、合并进集成分支并落回；context 卫生防主 Agent 膨胀掉质量；经用户确认后启动。"
disable-model-invocation: true
---

# Implement team

针对 `prd.md`、`spec.md` 与实际 `.scratch/<feature>/issues/` 的实现 tickets（三类输入可任意组合）做并发实施编排，manifest 的 `input.kind: prd-spec-input`。每个 ticket 是唯一执行单元。用户只有单个实现目标时走 direct-task 边界：直接调用 `/implement`，不创建 `TeamCreate` 或 `AgentTeam`。每个 ticket 在独立 worktree 与分支上执行，合并与落回由主 Agent 在集成分支完成。

前置：目标项目用 `.scratch/<feature>/issues/` 存放 tickets；`/implement` 由 `mattpocock/skills` 提供，需预先安装。

公共机制——manifest、frontier 调度、等待与唤醒、context 卫生、终态事件、独立核验、fail-closed——唯一来源是 `references/agent-team-protocol.md`；worktree 生命周期、合并冲突处置、集成验证与落回的唯一来源是 `references/worktree-merge.md`。输入评估完成后、创建 team 前各读一次，本 skill 只定义输入边界与步骤。

## Steps

1. **输入评估**：读取存在的 `prd.md`、`spec.md` 与实际 `.scratch/<feature>/issues/` 下每个 ticket 的原文、`Status:`、`Blocked by:`/`dependsOn`、verify 命令和 evidence 路径，臆造的 ticket 不进入 DAG。检查 ticket ID 唯一、依赖存在且无环、tracker 可写。记录项目路径、Git 分支（落回目标）与工作区基线（modified/untracked/staged）。

2. **PRD/spec 合并**：同时存在两者时，逐项合并范围、验收、非目标和约束。冲突项输出矩阵（来源、冲突内容、影响、选项）与推荐方案；无冲突时输出合并评估与缺口。

3. **确认门禁**：没有任何实现 tickets 时，只完成输入评估并停止。有 tickets 时按 manifest 字段逐项展示（含集成分支与集成 worktree 路径、`integrationVerify`、落回目标分支，以及"工作区未提交改动不会进入集成分支"的提示），等待用户确认。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区；确认后才用原生 `TeamCreate` 创建一个 `AgentTeam`、落盘 manifest，并创建集成分支与集成 worktree。

4. **派发-核验-合并循环**：按 protocol 的等待与唤醒规则，把 frontier 上的 ticket 全部并发派发，派发 prompt 按 protocol 与 worktree-merge.md 瘦身。每收到一个终态事件立即独立核验，通过后在集成 worktree 里合并该 ticket 分支、回写 `Status: resolved` 并立即补派新解锁的 ticket；合并冲突走 Merger 流程。失败只沿依赖后代传播 `blocked`，独立分支继续。

5. **收尾**：全部 ticket 终态后，回收已完成 team task，执行 `integrationVerify`、落回与 worktree 清理，按 protocol 生成 `evidenceDir/report.md` 全量明细（含集成验证结果、合并记录、落回结果与 SHA、保留的 worktree 路径），对话只输出简表加 report 路径。
