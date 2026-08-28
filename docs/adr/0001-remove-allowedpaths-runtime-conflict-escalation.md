# 移除 allowedPaths，改用运行时 CONFLICT 升级

AgentTeam 编排协议此前要求每个 ticket 声明 `allowedPaths`，主 Agent 在调度期做路径冲突检查（fail-closed：路径交集即禁止并行），核验时再校验 changedFiles 是否越界。实践中 glob 交集检测不可靠且给 ticket 作者增加负担；AgentTeam 已具备 teammate 与主 Agent 的双向通信，冲突可以在运行时更准确地暴露。

2026-08-28 决定：移除 `allowedPaths` 及调度期路径冲突检查，同轮所有 ready ticket 在 `maxConcurrency` 上限内全量并发；teammate 运行中发现文件冲突时发送 `CONFLICT` 升级消息（唯一合法的中途消息，仅 implement-team），由主 Agent 决策（等待、串行重派或指引避让），冲突期间 ticket 保持 `running`。核验中 `changedFiles` 降级为纯记录，不再做范围校验；Git 基线与 `protectedPaths` 防污染检查保留——`protectedPaths` 防的是 teammate 误伤用户工作区，与 teammate 之间打架是不同语义，冲突升级覆盖不了。

## Considered Options

- **保留 allowedPaths 作为建议性提示**：否决——不强制即无效，半吊子约束。
- **静态 fail-closed（现状）**：否决——glob 交集检测 prone 失败，不确定范围一律禁并行，牺牲并发。
- **完全不限并发**：否决——放大冲突频率与资源占用，保留 `maxConcurrency: 4` 硬上限。

## Consequences

- wayfinder-team 无 CONFLICT 豁免：探索型 teammate 不写代码，tracker 按 issue 天然隔离；`map.md` 只读，对地图的补充以新增 issue 文件进行。
- 协议同时纳入 context 卫生约束（双轨落盘、终态事件硬上限、指针化共享上下文、run report），见 `docs/agents/agent-team-protocol.md`。
