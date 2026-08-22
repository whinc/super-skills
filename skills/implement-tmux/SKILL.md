---
name: implement-tmux
description: "使用原生 tmux CLI 将一组 ticket 交给独立 cbc agent 严格串行执行；主窗口只消费结构化终态并独立核验 Git，失败或环境阻塞时停止链路。"
disable-model-invocation: true
---

# Implement tmux

## 目标

将一组实现 ticket 交给独立的 `cbc` agent 自动执行。共享工作区采用严格串行模型：任何时刻只有一个 ticket 处于 `running` 或 `verifying`，即使 ticket 之间没有前置依赖也按 manifest 顺序逐项执行。

运行时只依赖原生 `tmux` CLI 管理 window 和 pane：创建、写入 prompt、读取最终结果、关闭本次创建的 window。`smux` 与 `tmux-bridge` 不属于本 skill 的运行时依赖。

主窗口只消费最终结构化结果，不读取 agent 的中间过程、思考过程或持续输出。中间日志留在 ticket window 或 manifest 指定的证据路径中；只有结果缺失、失败/阻塞取证或用户明确要求时，才读取 pane 尾部的少量输出。

## 输入契约

开始前读取 `references/manifest-template.md`，校验用户提供的 manifest。manifest 是授权边界，至少明确：

- `project`：目标 Git 工作区的绝对路径。
- `session`：已存在的 tmux session 名称。
- `tickets`：固定顺序的 ticket 数组，每项包含唯一 id、tracker、完整 prompt、允许修改范围、验收命令和结果文件路径。
- `protectedPaths`：用户已有改动、coverage、lock 文件等保护项。
- `maxRepairRounds`：代码失败的最大修复—重跑轮数，默认 `2`。

`dependsOn` 只用于依赖检查和恢复判断，不改变严格串行调度。缺少项目路径、顺序、允许范围或结果路径时，先补齐输入，不猜测授权边界。

## 状态机

每个 ticket 沿以下路径推进：

```text
pending → running → verifying → done
                    ├→ failed
                    └→ blocked
```

- `done`：结果和独立 Git/证据核验全部通过。
- `failed`：代码、断言、配置、测试或产物失败；当前 ticket 可在上限内进行有依据的修复—重跑。
- `blocked`：tmux、DevTools、automator、外部构建或其他环境/工具不可用；保留证据并停止链路。

`failed` 和 `blocked` 都停止后续 ticket。链路恢复前不跳过失败项，也不把 blocked 改写成 passed。

## 执行步骤

### 1. 建立基线

在主窗口记录 session、已有窗口和 pane、工作区改动、暂存区以及保护路径：

```sh
tmux has-session -t "$session"
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
git -C "$project" status --short --untracked-files=all
git -C "$project" diff --cached --name-only
```

将基线保存到本次运行状态。已有改动属于保护边界，后续核验不得让它们进入当前 ticket 的 staging 或 commit。

**完成条件：** session 存在；基线清单已保存；保护项和暂存边界明确；本次创建的 window 集合为空。

### 2. 创建并启动当前 ticket

从固定顺序中选择第一个尚未核验完成的 ticket，并确认其 `dependsOn` 均为 `done`。同一时刻不创建第二个 ticket window。

创建 window 后立即保存真实的 `window_id` 和 `pane_id`，不依赖会重排的数字索引：

```sh
tmux new-window -d -t "$session" -n "ticket-<ID>" -c "$project" \
  'cbc --permission-mode bypassPermissions'
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
```

用 literal 模式发送完整 prompt，再单独发送 Enter：

```sh
tmux send-keys -t "$pane_id" -l -- "$prompt"
tmux send-keys -t "$pane_id" Enter
```

prompt 要求 agent：

- 只处理当前 ticket、tracker 和 `allowedPaths`，不扩大范围。
- 读取权威 spec/plan 与项目约束，保留用户已有改动。
- 遵循 manifest 指定的 Node/npm、测试和产物边界；项目约束要求外部构建时，不自行启动 build/watch。
- 代码失败最多进行 `maxRepairRounds` 轮有依据的修复—重跑。
- 工具或环境不可用时写成 `blocked`，保留证据。
- 完成、失败或阻塞时原子写入指定 `resultFile`，并在最后输出唯一终态标记：`TICKET_DONE`、`TICKET_FAILED` 或 `TICKET_BLOCKED`。
- 写完终态结果后停止继续工作。

**完成条件：** agent 收到完整 prompt；状态为 `running`；真实 pane 标识已保存；没有第二个 ticket 处于运行状态。

### 3. 只消费最终结果

主窗口等待 manifest 指定的 `resultFile`，只在文件完整出现后读取。结果文件至少符合以下结构：

```json
{
  "ticket": "唯一 ID",
  "status": "done | failed | blocked",
  "commit": "commit hash 或 null",
  "changedFiles": ["path"],
  "verification": [
    {
      "command": "...",
      "result": "passed | failed | blocked",
      "evidence": "path 或说明"
    }
  ],
  "evidence": ["path"],
  "summary": "一句话摘要"
}
```

结果文件缺失时，根据 pane/window 生命周期判断是否异常退出；只按需读取 pane 最后少量输出取证，并把无法确认的结果归为 `failed` 或 `blocked`，不默认算成功。过程输出不进入主窗口上下文。

**完成条件：** 已读取可解析的终态结果；过程输出没有被持续带回主窗口；状态转为 `verifying`。

### 4. 独立核验结果

即使 agent 报告 `TICKET_DONE`，主窗口仍执行独立核验：

```sh
git -C "$project" status --short --untracked-files=all
git -C "$project" diff --cached --name-only
git -C "$project" show --stat --oneline <commit>
git -C "$project" diff-tree --no-commit-id --name-only -r <commit>
```

逐项确认：

- commit 存在，并且是当前 ticket 的独立 commit。
- commit 文件全部位于 `allowedPaths`。
- `protectedPaths`、coverage、lock 文件和基线已有改动没有进入 staging/commit。
- tracker 的 `Status`、`Resolution`、checklist、`Comments` 与真实结果一致。
- 结果列出的测试、产物和证据确实存在，命令结论与证据一致。
- 代码/测试/产物失败归为 `failed`；工具/环境不可用才归为 `blocked`。

**完成条件：** 终态与 Git、tracker 和证据核验一致；或已明确记录失败/阻塞原因；没有未解释的 staging、commit 或保护项污染。

### 5. 清理并推进

只有 `done` 通过独立核验后，才保存最终结果并关闭本次创建的 window：

```sh
tmux kill-window -t "$window_id"
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
```

只操作本次运行记录的 `window_id`，保留用户原有窗口。然后自动启动下一个 pending ticket。`failed` 或 `blocked` 时保留当前 window、日志和改动，停止链路并等待用户介入。

**完成条件：** 成功 ticket 的 window 已关闭；下一 ticket 只在前一 ticket 核验通过后启动；失败/阻塞没有被跳过。

### 6. 恢复和整组终态

用户修复环境或明确要求重试后，先重新建立 Git 基线：

- 已核验通过的 ticket 标记 `done` 并跳过，不重复执行。
- 从第一个 `pending` ticket 继续。
- `failed`/`blocked` 只有在用户明确要求时才重置为 `pending`。
- 不自动 reset、回滚、删除日志或覆盖工作区。

主窗口最终只输出每个 ticket 的状态、commit、验证结论和证据路径。所有 ticket 都是独立核验通过的 `done` 时才报告整体完成；存在 `failed` 或 `blocked` 时分别报告整体失败或阻塞，并指出停止点和恢复要求。

**完成条件：** 每个 ticket 都有可追溯终态；本次创建的成功 window 已清理；用户原有窗口和工作区改动保持不变。
