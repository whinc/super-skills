---
name: wayfinder-team
description: "针对 map.md 及同目录 issues 的并发探索编排：AgentTeam 并发派发 /wayfinder 提速，context 卫生防主 Agent 膨胀掉质量；经用户确认后启动并核验 Answer 与状态。"
disable-model-invocation: true
---

# Wayfinder team

## 职责与边界

本 skill 只处理一个 `map.md` 与其同目录 `issues/` 下的 child issues。`map.md` 只读：对地图的补充以新增 issue 文件形式进行，不得直接改写 map。不得读取或接收 PRD/spec 实现 tickets，也不处理 direct-task。每个 child issue 是唯一执行单元；map 本身不是 ticket。团队使用原生 `TeamCreate` 创建一个 `AgentTeam`，主 Agent 是唯一 coordinator、派发者、依赖解锁者和独立核验者；成员共享 team 上下文但不能自行解锁后继。

公共 manifest、终态事件、DAG、失败传播、context 卫生、核验和 fail-closed 规则见 `docs/agents/agent-team-protocol.md` 与 `references/manifest-template.md`。

## 输入评估与确认门禁

1. 只读取指定 `map.md`、同目录 `issues/` 的 child issue；保留 issue 原文、`Type:`、`Status:`、`Blocked by:`、tracker 路径、问题范围、evidence 和地图 Decisions-so-far 指针。不得把 map 当成单一任务。
2. 检查 issue ID 唯一、依赖存在且无环、tracker 可写、验证/探索命令可识别；范围不确定时标记不确定。记录项目路径、Git 分支、modified/untracked/staged 基线、runId、protectedPaths、coverage/锁/evidence 路径。
3. 展示输入来源、coordinator policy、issue DAG、并发上限、探索范围、完成条件、tracker 更新、保护边界、Git 基线、evidence 和 `maxRepairRounds`，等待用户确认。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区；确认后才创建一个原生 `AgentTeam`。

## 探索派发与完成条件

确认后主 Agent 按 DAG 为每个 child issue 派发一次。prompt 遵循 context 卫生：只含 issue ID、tracker 文件路径、`protectedPaths`、探索命令、终态格式和一行目标摘要；issue 原文由 teammate 自行 Read。子 agent 只能调用 `/wayfinder`，只探索当前 issue，不调用实现技能，不实现代码或配置，不解锁后继。

Teammate 只报告一次终态事件，过程性消息一律禁止且无豁免（探索型不使用 CONFLICT 升级），进度只通过 tracker `Status:` 字段体现。tracker 文件按 issue 天然隔离，不产生写冲突。

探索或地图补充 issue 可以 `resolved`，但必须在 tracker 写入 `## Answer`、`Status: resolved` 和可复核证据（命令、路径或共享上下文引用）。需要代码实现/配置变更的 issue 必须 `blocked`，写明 reason 和证据；不自动调用实现技能或偷偷修改代码。终态事件有硬上限（summary ≤ 2 行、超限内容按双轨落盘只留路径）。只有主 Agent 独立核验 Answer、Status、证据后才释放后继。

## DAG、并发与失败传播

状态流转为 `pending → running → verifying → resolved`，失败或阻塞转为 `failed`/`blocked`。每轮选择所有依赖已核验为 `resolved` 的 ready issue，在 `maxConcurrency` 上限内全量并发派发；不做调度期路径检查（ADR-0001）。coverage、锁、evidence、protectedPaths 和用户既有改动受保护。

收到 `failed`/`blocked` 或核验失败时，主 Agent 在共享上下文写一行事件摘要加指针（详情落盘到 `evidenceDir/<issue>.failed.md`），只沿依赖后代传播 `blocked`，后代派发 prompt 只引用指针路径；独立分支继续。恢复需用户批准并重建基线，不自动 retry、reset、rollback、stash、合并或删除证据。缺失、重复、格式错误、ID 不匹配、tracker 未更新、验证/evidence 不可复核或异常退出均 fail-closed。

## 收尾

map 完成要求所有 child issue tracker 都是 `Status: resolved`，且每项均有 `## Answer` 与证据。主 Agent 回收已完成 team task，保留共享上下文与 evidence，生成 `evidenceDir/report.md` 全量明细（tracker、状态、Answer、verification、evidence、失败/阻塞原因和未完成依赖）；对话中只输出简表（issue / 状态 / 一行结论）加 report 路径。已完成 issue 不重复启动。

## References

- map 与 child issue 规则：`references/map-issues.md`
- manifest 与终态协议指针：`references/manifest-template.md`
- 公共 AgentTeam 协议（含 context 卫生）：`docs/agents/agent-team-protocol.md`
- 移除静态任务范围声明、改运行时冲突升级的决策：`docs/adr/0001-remove-allowedpaths-runtime-conflict-escalation.md`
