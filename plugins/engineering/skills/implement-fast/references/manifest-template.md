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

## 来源

本文件只定义 manifest 字段和完整终态协议。输入分支、DAG 调度、失败传播和核验规则分别由主 `SKILL.md` 及其对应 reference 定义。

## 终态协议

sub agent 完成对应的 `/implement` 或 `/wayfinder` 流程后，只报告一次：

```json
{"event":"TICKET_DONE","ticket":"01","status":"done","commit":"abc1234","changedFiles":["src/example.ts"],"verification":[{"command":"npm test -- --runInBand","result":"passed","evidence":".scratch/runs/implement-fast/01-test.log"}],"evidence":[".scratch/runs/implement-fast/01-test.log"],"summary":"通过验收","reason":null}
```

`event` 只能为 `TICKET_DONE`、`TICKET_FAILED`、`TICKET_BLOCKED`；`status` 只能为 `done`、`failed`、`blocked`。失败/阻塞必须提供 `reason`、已运行验证和 evidence。主 Agent 独立核验 commit、changedFiles、Git 基线、tracker、verification 和 evidence；核验通过后才解锁后继。