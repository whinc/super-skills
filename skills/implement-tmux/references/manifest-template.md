# implement-tmux 候选计划 / 可选 manifest

`implement-tmux` 默认直接读取 `/wayfinder` 的 `map.md` 或 `/to-tickets` 的 `spec.md`，运行时生成候选计划并在创建第一个 window 前请求一次确认。manifest 不是必填项；它适合保存已经确认的计划，或在恢复运行时复用。

manifest 只描述调度边界，不配置任意 agent 命令，也不复制 `/implement` 的 TDD、typecheck、测试、review 或 commit 规则。agent 由 skill 在确认后自动探测。

```yaml
project: "$PROJECT_ROOT"
session: project-session
# 可选；省略时由主窗口当前 pane 推断
mainPane: '%42'
maxRepairRounds: 2
protectedPaths:
  - .claude/scheduled_tasks.lock
  - coverage/
  - .scratch/runs/
  # 启动时所有 modified、untracked、staged 路径自动加入保护基线
tickets:
  - id: "01"
    tracker: "$PROJECT_ROOT/docs/agents/issue-01.md"
    # prompt/promptFile 可选；省略时从 tracker 和 map/spec 生成
    prompt: |
      处理 ticket 01。只修改已确认的 allowedPaths。
    allowedPaths:
      - src/example.ts
      - src/example.test.ts
    verify:
      - npm test -- --runInBand
    dependsOn: []

  - id: "02"
    dependsOn: ["01"]
    tracker: "$PROJECT_ROOT/docs/agents/issue-02.md"
    allowedPaths:
      - src/next.ts
    verify:
      - npm run typecheck
```

## 字段规则

- `PROJECT_ROOT` 必须展开为目标 Git 工作区的绝对路径；`session` 必须是已存在的 tmux session。
- `mainPane` 是接收 worker 终态消息的 pane；省略时必须在启动基线阶段从主窗口确定，不能猜测。
- `tickets` 至少一项，`id` 唯一；数组顺序是严格执行顺序。`dependsOn` 只用于依赖检查和恢复判断，不改变串行规则。
- `tracker`、`prompt/promptFile`、`allowedPaths`、`verify` 可以由 map/spec、tracker、项目结构和 package scripts 推断；推断不可靠时必须在确认前列为不确定项并阻塞，不得猜测。
- `protectedPaths` 优先级高于 `allowedPaths`。启动时已有 modified、untracked、staged 路径自动加入保护边界；发生重叠时停止，不创建 worker window。
- `verify` 必须是项目中可识别且可执行的验收命令。未知命令、缺少验收或缺少证据不能算通过。
- `maxRepairRounds` 缺失时默认为 `2`。
- 不支持 `agent`、任意 worker command 或 `resultFile` 字段。worker 只能使用自动探测的 CodeBuddy Code/Claude Code，并统一传入 `--permission-mode bypassPermissions`。

## 终态消息协议

worker 在自己的 agent 会话中显式调用 `/implement`，完成当前 ticket 后使用原生 tmux CLI 向 `mainPane` 发送**一次单行 JSON**。忙碌的主会话先输入消息，再发送 `Tab` 排队；不要创建结果文件：

```json
{"event":"TICKET_DONE","ticket":"01","status":"done","commit":"abc1234","changedFiles":["src/example.ts"],"verification":[{"command":"npm test -- --runInBand","result":"passed","evidence":".scratch/runs/01-test.log"}],"evidence":[".scratch/runs/01-test.log"],"summary":"完成当前 ticket 并通过验收"}
```

`event` 只能是 `TICKET_DONE`、`TICKET_FAILED` 或 `TICKET_BLOCKED`；`status` 只能是 `done`、`failed` 或 `blocked`。失败或阻塞时 `commit` 可以为 `null`，但仍应提供已运行的验证、证据和具体原因。

主窗口只用 `tmux capture-pane` 确认终态消息到达，然后独立核验 commit、changedFiles、staging、基线保护、验收和 evidence。缺失、格式错误或无法独立核验的消息不能解锁后续 ticket。
