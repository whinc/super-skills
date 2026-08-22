# implement-tmux manifest 模板

manifest 是编排器的授权边界。使用绝对路径，`tickets` 数组顺序就是严格执行顺序。

```yaml
project: /absolute/path/to/project
session: project-session
maxRepairRounds: 2
protectedPaths:
  - .claude/scheduled_tasks.lock
  - coverage/
  - 用户已有未提交改动（启动时由基线记录）
tickets:
  - id: "01"
    tracker: /absolute/path/to/issue-01.md
    prompt: |
      处理 ticket 01。只修改 allowedPaths，完成后写入 resultFile。
    allowedPaths:
      - src/example.ts
      - src/example.test.ts
    verify:
      - npm test -- --runInBand
    resultFile: /absolute/path/to/run/01.result.json

  - id: "02"
    dependsOn: ["01"]
    tracker: /absolute/path/to/issue-02.md
    promptFile: /absolute/path/to/issue-02-prompt.md
    allowedPaths:
      - src/next.ts
    verify:
      - npm run typecheck
    resultFile: /absolute/path/to/run/02.result.json
```

## 字段规则

- `project` 必须存在且是目标 Git 工作区。
- `session` 必须是已存在的 tmux session。
- `tickets` 至少包含一项；每项 `id` 唯一，且 `prompt` 与 `promptFile` 二选一。
- `allowedPaths`、`verify` 和 `resultFile` 必须明确。
- `dependsOn` 用于依赖检查和恢复判断，不改变严格串行调度；同一时刻只运行一个 ticket。
- `protectedPaths` 优先级高于 `allowedPaths`；发生重叠时暂停并请求用户处理。
- `resultFile` 建议先写临时文件，再原子移动为最终文件，避免主窗口读取半成品。

## 结果文件协议

agent 必须写入以下 JSON 结构，并在最后输出对应终态标记：

```json
{
  "ticket": "01",
  "status": "done",
  "commit": "abc1234",
  "changedFiles": ["src/example.ts"],
  "verification": [
    {
      "command": "npm test -- --runInBand",
      "result": "passed",
      "evidence": ".scratch/runs/01-test.log"
    }
  ],
  "evidence": [".scratch/runs/01-test.log"],
  "summary": "完成当前 ticket 并通过验收"
}
```

`status` 只能是 `done`、`failed` 或 `blocked`：

- `done`：代码和验收均通过，且有 commit/证据可供主窗口独立核验。
- `failed`：代码、断言、配置、测试或产物失败。
- `blocked`：tmux、DevTools、automator、外部构建或其他环境/工具不可用。

主窗口只读取这个最终结果和必要的失败/阻塞取证，不读取 ticket 的持续过程输出。
