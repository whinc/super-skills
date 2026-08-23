# implement-tmux manifest

`implement-tmux` 默认读取 `/wayfinder` 的 `map.md` 或 `/to-tickets` 的 `spec.md`，运行时生成计划并在创建第一个 window 前请求一次确认。manifest 只保存已确认的调度边界，不配置 agent 命令，也不复制 `/implement` 流程。

```yaml
project: "$PROJECT_ROOT"
session: project-session
# 可选；省略时从主窗口当前 pane 确定
mainPane: '%42'
maxRepairRounds: 2
protectedPaths:
  - .claude/scheduled_tasks.lock
  - coverage/
  - .scratch/runs/
  # 启动时已有 modified、untracked、staged 路径自动加入保护边界
tickets:
  - id: "01"
    tracker: "$PROJECT_ROOT/docs/agents/issue-01.md"
    prompt: |
      处理 ticket 01。只修改已确认的 allowedPaths。
    allowedPaths:
      - src/example.ts
      - src/example.test.ts
    verify:
      - npm test -- --runInBand
    dependsOn: []
  - id: "02"
    tracker: "$PROJECT_ROOT/docs/agents/issue-02.md"
    allowedPaths:
      - src/next.ts
    verify:
      - npm run typecheck
    dependsOn: ["01"]
```

## 字段规则

- `project` 必须是目标 Git 工作区绝对路径；`session` 必须已存在。
- `mainPane` 是接收终态的 pane；省略时由启动基线确定，不能猜测。
- `tickets` 至少一项且 `id` 唯一；数组顺序是严格执行顺序，`dependsOn` 只用于检查和恢复。
- `tracker`、`prompt`、`allowedPaths`、`verify` 可从 map/spec 和项目状态推断；不可靠时列为不确定项并阻塞。
- `protectedPaths` 优先于 `allowedPaths`；启动时已有 Git 改动自动受保护，重叠即停止。
- `verify` 必须是可识别、可执行且有 evidence 的验收命令；缺失或未知不能算通过。
- `maxRepairRounds` 缺省为 `2`。
- 不支持 `agent`、任意 worker command 或 `resultFile`；worker 由 skill 自动探测，并统一使用 `--permission-mode bypassPermissions`。
- 任何 tmux 写入前先用 `tmux capture-pane -p -t <target> -S -30` 读取目标内容；正文写入后再次读取，再单独发送 `Enter`（新会话）或 `Tab`（忙碌会话/主窗口），提交后再次读取。失败时先读取，只重发提交键一次。

## 终态消息协议

worker 在自己的 agent 会话中显式调用 `/implement`，完成 ticket 后向 `mainPane` 发送**一次单行 JSON**。主窗口忙碌时使用 Tab 排队：

```json
{"event":"TICKET_DONE","ticket":"01","status":"done","commit":"abc1234","changedFiles":["src/example.ts"],"verification":[{"command":"npm test -- --runInBand","result":"passed","evidence":".scratch/runs/01-test.log"}],"evidence":[".scratch/runs/01-test.log"],"summary":"完成当前 ticket 并通过验收"}
```

`event` 只能是 `TICKET_DONE`、`TICKET_FAILED`、`TICKET_BLOCKED`；`status` 只能是 `done`、`failed`、`blocked`。失败或阻塞时 `commit` 可为 `null`，但仍提供已运行的验证、证据和具体原因。主窗口读取一次确认消息到达，再独立核验 commit、changedFiles、staging、基线保护、验收和 evidence；无法核验不能解锁下一个 ticket。
