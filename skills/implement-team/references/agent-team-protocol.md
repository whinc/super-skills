# AgentTeam 公共协议

本协议是团队型 skill 的公共 manifest、调度、终态和 context 卫生来源。各 skill 只定义自己的输入边界与子 agent skill。目标：避免主 Agent context 膨胀过快导致推理质量下降。

## Frontier

**frontier** 是当前所有依赖已被主 Agent 独立核验为 `resolved`、且自身尚未进入执行的任务集合。frontier 上的任务全部并发派发；任一任务核验解锁后继时立即补派，不等同批其他任务终态。

## Manifest

主 Agent 在用户确认后保存一份调度快照：

```yaml
project: "/absolute/path/to/project"
runId: "20260828-153000"            # 时间戳，隔离多次运行的落盘目录
input:
  kind: prd-spec-input # prd-spec-input | map-issues
  sources: []
branches:                            # 仅 implement-team
  landing: "main"                    # 落回目标分支，确认门禁时记录
  integration: "agent-team/<runId>"  # 集成分支
evidenceDir: ".scratch/runs/agent-team/<runId>"   # 项目内，可复核证据
tempDir: "$TMPDIR/agent-team/<runId>"             # 系统临时目录，过程性大输出
integrationVerify: null              # 仅 implement-team：收尾集成验证命令，可留空
tickets: []
```

每个 ticket 必须保留唯一 `id`、原文 tracker 路径、`dependsOn`、`verify`、`evidence` 和当前 `status`。状态为 `pending`、`running`、`resolved`、`failed` 或 `blocked`。

## 协调与调度

只创建一个原生 `TeamCreate` 得到的 `AgentTeam`。主 Agent 是唯一 coordinator、派发者、解锁者和独立核验者；成员共享 team 上下文，解锁后继始终由主 Agent 执行。DAG 必须检查唯一 ID、依赖存在、无环和 tracker 可写。

**等待与唤醒**：派发后主 Agent 结束当前回合等待终态通知，不轮询、不重复派发；每收到一个终态事件即独立核验，通过后立即补派新解锁的任务。全部任务到达终态才进入收尾；任一任务仍在 `running` 时不得收尾或宣称完成。

任务 `failed` 或 `blocked` 时，主 Agent 在共享上下文写入**一行事件摘要 + 指针**（事件详情、日志落盘到 `evidenceDir/<ticket>.failed.md`），`blocked` 只沿依赖后代传播，独立分支继续；后代派发 prompt 只引用指针路径。恢复动作（重试、reset、rollback、stash、删除证据）仅由用户批准触发，并需重建基线。

## Context 卫生

主 Agent context 只保留决策所需最小信息：

1. **双轨落盘**：evidence 等可复核产物写 `evidenceDir`（随 repo 保留）；过程性大输出（日志、中间产物）写 `tempDir`（不值得长期保留）。任何超出硬上限的内容一律落盘，事件中只留路径。
2. **派发 prompt 瘦身**：prompt 只含 ticket ID、tracker 文件路径、子 agent skill 与 verify 命令、evidence 约定、终态格式和一行目标摘要；ticket 原文由 teammate 自行 Read。主 Agent 只在输入评估/确认门禁阶段读一次 tracker。
3. **过程消息禁令**：teammate 只报告一次终态事件，进度只通过 tracker `Status:` 字段体现（`pending → running → resolved/failed/blocked`），主 Agent 不轮询。
4. **核验输出落盘**：主 Agent 核验时命令输出重定向到 `evidenceDir/<ticket>.verify.log`，context 只留一行结论（ticket 核验通过/失败 + 原因）。
5. **Run Report**：收尾时主 Agent 生成 `evidenceDir/report.md` 全量明细（每个 ticket 的 tracker、状态、commit、changedFiles、verification、evidence、失败/阻塞原因、未完成依赖）；对话中只输出简表（ticket / 状态 / commit / 一行结论）加 report 路径。

## 终态与独立核验

子 agent 只报告一次终态事件，字段有硬上限：

```json
{"event":"TICKET_RESOLVED","ticket":"01","status":"resolved","commit":"abc1234","changedFiles":["src/example.ts"],"verification":[{"command":"python3 -m unittest","result":"passed","evidence":".scratch/runs/agent-team/<runId>/01.log"}],"evidence":[".scratch/runs/agent-team/<runId>/01.log"],"summary":"验收通过","reason":null}
```

事件只能是 `TICKET_RESOLVED`、`TICKET_FAILED` 或 `TICKET_BLOCKED`；状态只能是 `resolved`、`failed` 或 `blocked`。硬上限：`summary` ≤ 2 行；`changedFiles` 超过 20 条时完整清单落盘到 `evidenceDir/<ticket>.files.md`，事件只留清单文件路径；`verification` 只含命令、结果和 evidence 路径，不含命令输出。`resolved` 必须有非空 evidence，并把 tracker 的 `Status: resolved` 回写；失败和阻塞必须有 reason、已运行验证和 evidence。

主 Agent 独立复核：commit 存在且属于当前 ticket，Git 基线未被污染，staging、coverage 和锁未被改动，验证命令/evidence 可复核，tracker 状态正确。`changedFiles` 是纯记录，不做范围校验。核验通过后才释放依赖。

**fail-closed**：以下任一情况出现时，该 ticket 保持 `blocked`，依赖不释放，主 Agent 也不宣称完成——终态事件重复、缺字段、ID 不匹配、tracker 未更新、验证或 evidence 不可复核、异常退出、独立核验未通过。
