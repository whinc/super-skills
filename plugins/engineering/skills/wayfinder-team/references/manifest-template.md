# wayfinder-team manifest 与终态

公共字段、状态机、DAG、并发冲突保护、失败传播、独立核验和 fail-closed 规则唯一来源是 `docs/agents/agent-team-protocol.md`。本 reference 只提供 wayfinder-team 的输入指针：`input.kind: map-issues`，sources 为一个 `map.md` 与其同目录 `issues/`。

确认后的 manifest 必须记录 `project`、输入 sources、主 Agent coordinator、`protectedPaths`、`evidenceDir`、每个 issue 的 `id`/tracker/`dependsOn`/`allowedPaths`/verify/evidence/status。探索子 agent 必须调用 `/wayfinder`；resolved 必须同时有 `## Answer`、`Status: resolved` 和 evidence。需要实现代码或配置的 issue 使用 `blocked`，reason 和 evidence 必须齐全。

完整终态事件格式与 JSON 示例请直接读取 `docs/agents/agent-team-protocol.md`，不要在此复制另一份协议。
