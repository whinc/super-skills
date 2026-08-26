# implement-fast manifest

manifest 是主 Agent 确认后的调度快照；执行细节由 `implement-fast` 和对应 skill 负责。

```yaml
project: "/absolute/path/to/project"
input:
  kind: direct-task # direct-task | wayfinder-map | spec-tickets
  source: null
coordinator:
  role: main-agent
  sharedContext: true
  dispatch: agent-team
team:
  maxConcurrency: 4
  pathConflictPolicy: block
maxRepairRounds: 2
protectedPaths:
  - coverage/
  - .scratch/runs/
  - .claude/scheduled_tasks.lock
evidenceDir: .scratch/runs/implement-fast
tickets:
  - id: "01"
    type: task
    tracker: ".scratch/feature/issues/01-build.md"
    goal: "完成第一个任务"
    prompt: "先调用 /implement；只处理当前 ticket。"
    allowedPaths: [src/example.ts, src/example.test.ts]
    verify: ["npm test -- --runInBand"]
    dependsOn: []
    status: pending
```

## 输入映射

- `direct-task`：主 Agent 从用户描述生成 `id`、目标、依赖、范围、验证和 tracker，经确认后创建 team。
- `wayfinder-map`：`source` 指向 `map.md`；读取同目录 `issues/NN-*.md`，按 `docs/agents/issue-tracker.md` 解析 `Type:`、`Status:`、`Blocked by:`。sub agent 只调用 `/wayfinder`，持续探索并将每个 issue 更新为 `Status: resolved`；全部 child issue resolved 才完成。
- `spec-tickets`：`source` 指向 `spec.md`；逐个读取 `.scratch/<feature>/issues/NN-*.md`，保留 spec 验收、范围、依赖和 tracker 映射，不把 spec 当作 ticket。sub agent 先调用 `/implement`。

## 调度约束

- `dependsOn` 是 DAG；主 Agent 只释放前置 ticket 已核验为 `done` 的任务。
- 同轮候选若 `allowedPaths` 相同、存在父子路径、glob 交集或范围不确定，禁止并行；其它 ready task 最大化并发。
- AgentTeam 成员共享上下文、状态和 evidence；主 Agent 是唯一派发和解锁者。
- 失败/阻塞由主 Agent 写入共享上下文并通知成员，只沿依赖后代传播 `blocked`；独立分支继续。恢复需用户批准。
- 代码 ticket 需独立 commit、`changedFiles`、verification 和 evidence；map issue 需 Answer、tracker `resolved` 和探索 evidence。

## 终态协议

sub agent 完成对应的 `/implement` 或 `/wayfinder` 流程后，只报告一次：

```json
{"event":"TICKET_DONE","ticket":"01","status":"done","commit":"abc1234","changedFiles":["src/example.ts"],"verification":[{"command":"npm test -- --runInBand","result":"passed","evidence":".scratch/runs/implement-fast/01-test.log"}],"evidence":[".scratch/runs/implement-fast/01-test.log"],"summary":"通过验收","reason":null}
```

`event` 只能为 `TICKET_DONE`、`TICKET_FAILED`、`TICKET_BLOCKED`；`status` 只能为 `done`、`failed`、`blocked`。失败/阻塞必须提供 `reason`、已运行验证和 evidence。主 Agent 独立核验 commit、changedFiles、Git 基线、tracker、verification 和 evidence；核验通过后才解锁后继。