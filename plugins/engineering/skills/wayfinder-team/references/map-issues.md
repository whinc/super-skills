# map.md 与 child issues 输入

本分支只读取同一目录的 `map.md` 与 `issues/NN-*.md`。map 保存 Notes、Decisions-so-far 和 Fog；每个 child issue 是独立探索 ticket，记录 `Type:`、`Status:`、`Blocked by:` 和问题原文。按 `docs/agents/issue-tracker.md` 解析 tracker。

## Frontier 与解析

依赖全部 `resolved` 的、未解决且未认领的 issue 才是 frontier。主 Agent 先检查唯一 ID、依赖无环、tracker 可写和范围边界，再按公共 DAG 规则安全并发。子 agent 只能调用 `/wayfinder`。

## 终态

探索或地图补充 issue 只有在 tracker 追加 `## Answer`、写入 `Status: resolved` 并保存可复核证据后才能 resolved；主 Agent 独立核验后才解锁后继。需要代码实现或配置变更的 issue 必须写 reason 与证据并标记 `blocked`，不要自动调用实现技能。失败只沿依赖后代传播，独立分支继续。
