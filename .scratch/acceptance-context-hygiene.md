# 验收测试清单 — AgentTeam context 卫生改造

日期：2026-08-28 ｜ 依据：ADR-0001、`docs/agents/agent-team-protocol.md`、`CONTEXT.md`
执行：2026-08-28 由 doc-auditor / skill-auditor / test-runner 三个并行子 agent 完成

状态标记：`[ ]` 待执行 ｜ `[x]` 通过 ｜ `[!]` 失败 ｜ `[N/A]` 不适用

## A. 公共协议与治理文档一致性 — doc-auditor ✅ 6/6

- [x] **A1** manifest 含 `runId`、`tempDir`、`maxConcurrency: 4`、`protectedPaths`；allowedPaths 仅作移除说明，非字段定义
- [x] **A2** "Context 卫生" 一节五条齐备：双轨落盘、派发瘦身、消息禁令、核验落盘、Run Report
- [x] **A3** 终态硬上限三条齐备：summary ≤ 2 行、changedFiles > 20 落盘清单、verification 不含输出
- [x] **A4** CONFLICT 标注"仅 implement-team"，wayfinder 明确无豁免
- [x] **A5** ADR-0001 存在，含决策理由、Considered Options、Consequences
- [x] **A6** CONTEXT.md 五个术语与协议一致；allowedPaths 列入 `_Avoid_`

## B. SKILL 与 references 行为规则 — skill-auditor ✅ 5/5

- [x] **B1** implement-team：CONFLICT 机制、派发瘦身、终态硬上限、run report 齐备，无调度期路径检查要求
- [x] **B2** wayfinder-team：map.md 只读、消息禁令无豁免（不用 CONFLICT）、瘦身与 run report 齐备
- [x] **B3** 两个 manifest-template.md 不再要求 allowedPaths，含 runId/tempDir
- [x] **B4** prd-spec.md 无 allowedPaths
- [x] **B5** 两个 SKILL.md 均引用公共协议与 ADR-0001，目标文件存在

## C. 测试与安装验收 — test-runner ✅ 4 PASS + 1 N/A

- [x] **C1** wayfinder 协议检查退出码 0
- [x] **C2** implement 协议检查退出码 0
- [x] **C3** 22 个单元测试全部 OK（11 + 11）
- [x] **C4** `.codebuddy/skills/{implement-team,wayfinder-team}/SKILL.md` 与源 diff 为空
- [N/A] **C5** `.agents/` 目录不存在（安装器未保留该副本，实际安装副本为 `.codebuddy/skills/`，已由 C4 覆盖）

## 结论

**验收通过**（15 PASS + 1 N/A，0 FAIL）。改造已完整落地且本地安装副本与源一致。
