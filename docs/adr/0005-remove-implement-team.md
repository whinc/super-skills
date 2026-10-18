---
status: accepted
---

# 移除 implement-team，仓库不再提供多 ticket 编排层

2026-10-18 决定：移除 `implement-team`（PRD/spec 多 ticket 并发实现编排），并删除只描述它的 `docs/adr/0001`、`docs/adr/0002`。仓库 skill 集合从 4 个收敛为 3 个：`react-effects`、`codebuddy-handoff`、`memory-compact`。

implement-team 是仓库里维护面最大的 skill：一份公共协议（`agent-team-protocol.md`）、一套 worktree 合并机制（`worktree-merge.md`），外加协议 token 检查器与协议/集成测试。它承担的是「上游单 ticket 执行 skill 之上的并发编排」，而这层能力可以由用户按 ticket 直接调用上游 `/implement` 得到；为它持续维护协议文本、worktree 生命周期与 eval 不再划算。

## Considered Options

- **保留但不再维护**：否决——死 skill 仍会在两条分发渠道对用户可见（插件渠道整仓分发），协议与 eval 的腐烂成本不会消失。
- **只删 SKILL.md、保留 references 与 evals**：否决——没有消费方的协议文本与测试只会持续产生误导与维护噪音。
- **把 worktree 合并文档提升为通用参考**：否决——该机制只服务于 implement-team 的派发协议，脱离它没有独立价值。

## Consequences

- 已发布分发渠道中 implement-team 从下个版本起消失：Claude Code 插件按 commit SHA 更新即移除；Skills CLI 用户需手动 `npx skills remove implement-team`。
- 本机项目级安装副本（`.codebuddy/skills/implement-team`）与 `skills-lock.json` 条目同步卸载。
- worktree 隔离模型随 skill 一并消失；ADR-0001 / ADR-0002 删除，其记录职责由本文承担。
- 上游 mattpocock 的 `/implement` 单 ticket skill 不受影响，仍可独立使用。
- 剩余三个 skill 互不依赖；`CONTEXT.md` 只保留会话交接与 Memory 卫生两节。
