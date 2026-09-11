---
name: wayfinder-team
description: "针对 map.md 及同目录 issues 的并发探索编排：AgentTeam 并发派发 /wayfinder 提速，context 卫生防主 Agent 膨胀掉质量；经用户确认后启动并核验 Answer 与状态。"
disable-model-invocation: true
---

# Wayfinder team

针对一个 `map.md` 与其同目录 `issues/` 的 child issues 做并发探索编排，manifest 的 `input.kind: map-issues`。`map.md` 只读，对地图的补充以新增 issue 文件形式进行；map 本身不是执行单元，每个 child issue 是。需要实现代码或配置变更的 issue 走 `blocked` 流程（见 step 4）。本 skill 与 PRD/spec 实现 tickets、direct-task 无交集。

前置：目标项目用 `.scratch/<effort>/` 存放 `map.md` 与同目录 `issues/`；`/wayfinder` 由 `mattpocock/skills` 提供，需预先安装。

公共机制——manifest、frontier 调度、context 卫生、终态事件、独立核验、fail-closed——唯一来源是 `references/agent-team-protocol.md`；输入评估完成后、创建 team 前读一次，本 skill 只定义输入边界与步骤。

## Steps

1. **输入评估**：读取 `map.md` 与同目录 `issues/` 下每个 child issue 的原文、`Type:`、`Status:`、`Blocked by:`、验证/探索命令和 evidence 路径。检查 issue ID 唯一、依赖存在且无环、tracker 可写；范围不确定的 issue 做标记。记录项目路径、Git 分支、工作区基线（modified/untracked/staged）与 `protectedPaths`。完成判据：DAG 合法，基线与保护边界已记录。

2. **确认门禁**：按 manifest 字段逐项展示，等待用户确认。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区；确认后才用原生 `TeamCreate` 创建一个 `AgentTeam` 并落盘 manifest。完成判据：用户明确确认。

3. **frontier 派发**：每轮把 frontier 上的 issue 在 `maxConcurrency` 上限内全量并发派发，派发 prompt 按 protocol 的 context 卫生瘦身。每个 teammate 只调用 `/wayfinder`，只探索当前 issue。完成判据：本轮 frontier 全部派发。

4. **独立核验**：teammate 报告终态后，主 Agent 按 protocol 独立核验 tracker 的 `## Answer`、`Status: resolved` 与可复核 evidence，通过才解锁后继。需要代码实现或配置变更的 issue 保持 `blocked`，reason 与 evidence 齐全，等用户批准后续处理。失败只沿依赖后代传播 `blocked`，独立分支继续。完成判据：本轮终态全部核验并回写 tracker。

5. **收尾**：全部 child issue `Status: resolved` 且有 `## Answer` 与 evidence 后，回收已完成 team task，按 protocol 生成 `evidenceDir/report.md` 全量明细，对话只输出简表加 report 路径。完成判据：report.md 落盘且简表已输出。
