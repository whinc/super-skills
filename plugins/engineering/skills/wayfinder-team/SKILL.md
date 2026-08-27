---
name: wayfinder-team
description: "针对 map.md 及同目录 issues 的团队探索编排：经确认后用原生 AgentTeam 安全并发派发 /wayfinder 并核验 Answer 与状态。"
disable-model-invocation: true
---

# Wayfinder team

## 职责与边界

本 skill 只处理一个 `map.md` 与其同目录 `issues/` 下的 child issues。不得读取或接收 PRD/spec 实现 tickets，也不处理 direct-task。每个 child issue 是唯一执行单元；map 本身不是 ticket。团队使用原生 `TeamCreate` 创建一个 `AgentTeam`，主 Agent 是唯一 coordinator、派发者、依赖解锁者和独立核验者；成员共享 team 上下文但不能自行解锁后继。

公共 manifest、终态事件、DAG、allowedPaths 冲突保护、失败传播、核验和 fail-closed 规则见 `docs/agents/agent-team-protocol.md` 与 `references/manifest-template.md`。

## 输入评估与确认门禁

1. 只读取指定 `map.md`、同目录 `issues/` 的 child issue；保留 issue 原文、`Type:`、`Status:`、`Blocked by:`、tracker 路径、问题范围、evidence 和地图 Decisions-so-far 指针。不得把 map 当成单一任务。
2. 检查 issue ID 唯一、依赖存在且无环、tracker 可写、验证/探索命令可识别、`allowedPaths` 明确；范围不确定时标记不确定并禁止并行。记录项目路径、Git 分支、modified/untracked/staged 基线、protectedPaths、coverage/锁/evidence 路径。
3. 展示输入来源、coordinator policy、issue DAG、并发组、探索范围、完成条件、tracker 更新、保护边界、Git 基线、evidence 和 `maxRepairRounds`，等待用户确认。确认前不创建 team、不启动 sub agent、不修改 tracker 或工作区；确认后才创建一个原生 `AgentTeam`。

## 探索派发与完成条件

确认后主 Agent 按 DAG 为每个 child issue 派发一次。prompt 必须包含 issue 原文、唯一 ID、tracker、已完成依赖、`allowedPaths`、验证/探索命令、保护边界、终态格式和当前地图上下文。子 agent 只能调用 `/wayfinder`，只探索当前 issue，不调用实现技能，不实现代码或配置，不解锁后继。

探索或地图补充 issue 可以 `resolved`，但必须在 tracker 写入 `## Answer`、`Status: resolved` 和可复核证据（命令、路径或共享上下文引用）。需要代码实现/配置变更的 issue 必须 `blocked`，写明 reason 和证据；不自动调用实现技能或偷偷修改代码。只有主 Agent 独立核验 Answer、Status、证据后才释放后继。

## DAG、并发与失败传播

状态流转为 `pending → running → verifying → resolved`，失败或阻塞转为 `failed`/`blocked`。每轮选择所有依赖已核验为 `resolved` 的 ready issue。规范化 `allowedPaths` 后，同路径、文件与父子目录、glob 交集或不确定范围禁止并行；无冲突独立分支必须最大化并发。coverage、锁、evidence、protectedPaths 和用户既有改动受保护。

收到 `failed`/`blocked` 或核验失败时，主 Agent 将 reason、日志、验证和 evidence 写入共享上下文，只沿依赖后代传播 `blocked`，独立分支继续。恢复需用户批准并重建基线，不自动 retry、reset、rollback、stash、合并或删除证据。缺失、重复、格式错误、ID 不匹配、tracker 未更新、验证/evidence 不可复核或异常退出均 fail-closed。

## 收尾

map 完成要求所有 child issue tracker 都是 `Status: resolved`，且每项均有 `## Answer` 与证据。主 Agent 回收已完成 team task，保留共享上下文与 evidence，汇总 tracker、状态、Answer、verification、evidence、失败/阻塞原因和未完成依赖；已完成 issue 不重复启动。

## References

- map 与 child issue 规则：`references/map-issues.md`
- manifest 与终态协议指针：`references/manifest-template.md`
- 公共 AgentTeam 协议：`docs/agents/agent-team-protocol.md`
