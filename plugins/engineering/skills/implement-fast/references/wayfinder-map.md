# wayfinder-map 输入

当用户提供 `map.md` 或其所在目录的 issue map 时，使用本分支。只加载本文件处理 map 专属规则。

## 读取与解析

读取指定 `map.md`、同目录 `issues/` 下的 child issue，并按 `docs/agents/issue-tracker.md` 解析 `Type:`、`Status:` 和 `Blocked by:`。每个 child issue 是独立 ticket；保留 issue 原文、已有答案和 tracker 路径，不把 map 当成单一 ticket。

## 探索与收敛

每个 issue 的 sub agent 只调用 `/wayfinder`，持续探索代码、文档和依赖，直到当前 issue 有足够答案。随后按 issue 类型写入 `## Answer`，更新 tracker 的 `Status: resolved`，并把探索证据写入共享 team 上下文。

map 的完成条件是所有 child issue 的 tracker `Status:` 都为 `resolved`。主 Agent 独立核验 Answer、状态和证据后，才把 issue 记为 `done` 并释放后继依赖；通用 DAG、失败传播和终态规则以主 skill 为准。