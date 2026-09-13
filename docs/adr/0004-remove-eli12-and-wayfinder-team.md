---
status: accepted
---

# 移除 eli12 与 wayfinder-team，仓库收敛为单编排线

2026-09-13 决定：移除 `eli12`（12 岁读者讲解）与 `wayfinder-team`（地图探索编排）两个 skill，仓库 skill 集合从 5 个收敛为 3 个：`react-effects`、`implement-team`、`memory-compact`。

eli12 是独立讲解类 skill，不再使用；wayfinder-team 面向 `map.md` child issues 的并发探索，实际未被使用，却持续产生维护成本：与 implement-team 共享的 `agent-team-protocol.md` 需两份副本字节一致（配套 sibling 一致性测试与协议 token 检查器），任何协议改动都要双份同步。移除后团队编排收敛为 implement-team 单线，「协议副本同步」纪律随之终结。

## Considered Options

- **保留但不再维护**：否决——死 skill 仍在两条分发渠道对用户可见（插件渠道整仓分发），且双副本同步与 eval 成本不会消失。
- **只从本仓库剥离、本机保留安装副本**：否决——用户即唯一用户，无外部消费方，保留副本只会造成「仓库无、本机有」的版本漂移。
- **保留 wayfinder-team 但简化协议同步纪律**：否决——同步成本的根部是第二个消费方本身；只要 skill 在，协议文本与 eval 就得随 implement-team 联动。

## Consequences

- 上游 mattpocock 的 `/wayfinder`、`/implement` 单 issue/ticket skill 不受影响，仍可独立使用；本仓库只是不再提供其上的多 issue 编排层。
- `agent-team-protocol.md` 仅存 implement-team 一份；wayfinding 专属条款（`## Answer`、探索证据）与探索向措辞删除。
- implement-team 的 sibling 字节一致测试删除；针对 `/wayfinder` 的负向断言与 LEGACY 名称 token 保留（仍防 implement-team 误引探索 skill 与旧名回归）。
- 已发布分发渠道中 eli12 / wayfinder-team 从下个版本起消失：Claude Code 插件按 commit SHA 更新即移除；Skills CLI 用户装过这两者需手动 `npx skills remove`。
- 本机安装副本（项目级 `.codebuddy/skills/`、全局 `~/.agents/skills/wayfinder-team` 及两处符号链接）同步卸载。
