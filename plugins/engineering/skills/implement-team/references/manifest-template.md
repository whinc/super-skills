# implement-team manifest 与终态

公共字段、状态机、DAG、并发冲突保护、失败传播、独立核验和 fail-closed 规则唯一来源是 `docs/agents/agent-team-protocol.md`。本 reference 只提供 implement-team 的输入指针：`input.kind: prd-spec-input`，sources 可含 `prd.md`、`spec.md` 和实际 `.scratch/<feature>/issues/`。

确认后的 manifest 必须记录 `project`、输入 sources、主 Agent coordinator、`protectedPaths`、`evidenceDir`、每个 ticket 的 `id`/tracker/`dependsOn`/`allowedPaths`/verify/evidence/status，以及公共协议要求的终态事件。实现 ticket 子 agent 必须调用 `/implement`；`resolved` 必须有 evidence 并回写 `Status: resolved`。

完整终态事件格式与 JSON 示例请直接读取 `docs/agents/agent-team-protocol.md`，不要在此复制另一份协议。
