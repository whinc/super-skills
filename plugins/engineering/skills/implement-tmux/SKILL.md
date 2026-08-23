---
name: implement-tmux
description: "使用原生 tmux CLI 将 map/spec 中的 ticket 严格串行交给 CodeBuddy Code 或 Claude Code；worker 调用 /implement，主窗口消费终态并独立核验 Git。"
disable-model-invocation: true
---

# Implement tmux

## 核心边界

这是 `/implement` 的调度层：读取 `/wayfinder` 的 `map.md`、`/to-tickets` 的 `spec.md` 或已确认 manifest，逐个创建 tmux window，回收唯一终态消息，核验 commit 后再推进。共享工作区始终只有一个 ticket 处于 `running` 或 `verifying`，只使用原生 `tmux` CLI。

主窗口只消费终态 JSON 和核验结果；不读取 worker 的过程输出。终态缺失、格式错误、ticket 不匹配或 worker 异常退出都应阻塞链路。

### tmux 写入协议（硬规则）

**任何 tmux 写入操作前，先读取目标内容。**读取使用：

```sh
tmux capture-pane -p -t "$target" -S -30
```

以下写入都必须遵守该顺序：

1. `new-window` 前读取 `mainPane`；创建后读取新 pane，再发送首次 prompt。
2. 正文使用 `send-keys -l -- "$text"` 前读取目标 pane；写入正文后再次读取，再立即单独发送不带 `-l` 的提交键。`-l` 会把 `Enter` 或 `Tab` 当作字面文本输入。
3. `kill-window` 前读取目标 pane。

提交键是发送动作的一部分，不能省略；它必须是独立的、不带 `-l` 的 `Enter` 或 `Tab`，不能拼进正文命令：

```sh
# 新会话：正文后 Enter
tmux capture-pane -p -t "$pane_id" -S -30
tmux send-keys -t "$pane_id" -l -- "$prompt"
tmux capture-pane -p -t "$pane_id" -S -30
tmux send-keys -t "$pane_id" Enter

# 忙碌会话或忙碌主窗口：正文后 Tab 排队
tmux capture-pane -p -t "$target" -S -30
tmux send-keys -t "$target" -l -- "$message"
tmux capture-pane -p -t "$target" -S -30
tmux send-keys -t "$target" Tab
```

提交后再次读取目标 pane，确认正文已离开输入框。若仍停留在输入框，先再次读取，再只重发同一个提交键一次，不重复正文；再次失败即 `TICKET_BLOCKED` 并保留 pane/window。

## 执行流程

### 1. 建立基线

确认 `tmux`、目标 session 和项目存在，读取并记录真实 pane/window 与 Git 保护边界：

```sh
tmux -V
tmux has-session -t "$session"
main_pane="${mainPane:-$(tmux display-message -p '#{pane_id}')}"
tmux display-message -p -t "$main_pane" '#{pane_id}'
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
git -C "$project" status --short --untracked-files=all
git -C "$project" diff --cached --name-only
```

把启动时的 modified、untracked、staged 路径，以及 `protectedPaths`、coverage、lock 和调度状态加入保护边界。候选范围重叠时，在创建 window 前报告 `TICKET_BLOCKED`。

完成条件：`session`、`mainPane`、Git 基线和空的本次 window 集合已记录。

### 2. 生成并确认计划

从 map/spec、tracker、项目结构和 `package.json` scripts 推断每项的 `id`、顺序、依赖、`allowedPaths`、`verify` 和 tracker。无法可靠推断的项保持不确定并阻塞，不用默认路径或默认测试补齐。`maxRepairRounds` 缺省为 `2`。

一次性展示并确认：project、session、`mainPane`、agent policy、ticket 顺序/依赖、范围、验收、不确定项、Git 基线、保护边界和 `maxRepairRounds`。确认前不创建 window、不启动 worker、不修改工作区。

确认后按 `codebuddy`、`codebuddy-code`、`cbc`、`claude` 顺序探测 CLI；前 3 个是等价的 CodeBuddy Code 命令，`claude` 是唯一 fallback。统一使用 `--permission-mode bypassPermissions`，并确认目标会话可调用 `/implement`。任一条件不满足都在创建 window 前阻塞。

### 3. 串行执行 ticket

选取第一个依赖已完成且尚未核验为 `done` 的 ticket，只创建一个 window。创建前读取 `mainPane`：

```sh
tmux capture-pane -p -t "$mainPane" -S -30
tmux new-window -d -t "$session" -n "ticket-<ID>" -c "$project" \
  "$agent_command --permission-mode bypassPermissions"
tmux display-message -p -t "$window_id" '#{pane_id}'
tmux capture-pane -p -t "$pane_id" -S -30
```

创建后保存新 window 的真实 `window_id`、`pane_id`，并在首次 `send-keys` 前读取新 pane。使用“正文后 Enter”协议发送自包含 prompt。prompt 必须包含 ticket、tracker、`allowedPaths`、`protectedPaths`、`verify`、`maxRepairRounds`、项目约束、`mainPane` 和终态协议，并要求 worker：

- 只处理当前 ticket，不扩大范围，不触碰保护边界；
- 显式调用 `/implement`，由其负责实现、TDD、typecheck、测试、review 和 commit；
- 完成后只向 `mainPane` 发送一次终态 JSON，然后停止；
- 代码/测试/产物失败发送 `TICKET_FAILED`，工具/环境不可用发送 `TICKET_BLOCKED`。

worker 回传主窗口时，先读取 `mainPane`，再用“正文后 Tab”协议发送 JSON。主窗口忙碌时同样使用 Tab 排队；不打断当前会话。

状态只能按以下方向流转：

```text
pending → running → verifying → done
                    ├→ failed
                    └→ blocked
```

`failed` 或 `blocked` 停止后续 ticket，保留 window 和证据；只有用户明确批准才可重试。

### 4. 接收并核验终态

worker 只发送一行 JSON，格式见 `references/manifest-template.md`。预期到达后读取一次：

```sh
tmux capture-pane -p -t "$mainPane" -S -30
```

只解析匹配的终态，不轮询中间输出。收到 `TICKET_DONE` 后独立执行：

```sh
git -C "$project" status --short --untracked-files=all
git -C "$project" diff --cached --name-only
git -C "$project" show --stat --oneline <commit>
git -C "$project" diff-tree --no-commit-id --name-only -r <commit>
```

逐项确认 commit 存在且属于当前 ticket；commit 文件与 `changedFiles` 均在 `allowedPaths`；基线、protected paths、staging、coverage 和 lock 未被污染；每条 verification 的结果和 evidence 可复核；tracker 状态与结果一致。全部通过才是 `done`，否则按原因分类为 `failed` 或 `blocked`。

### 5. 清理、推进与恢复

独立核验通过后，关闭本次创建的真实 window；关闭前先读取其 pane：

```sh
tmux capture-pane -p -t "$pane_id" -S -30
tmux kill-window -t "$window_id"
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
```

只关闭本次运行创建的 window，保留既有窗口，然后启动下一个 ticket。恢复时重新建立 Git 基线和计划；已核验的 `done` 跳过，`failed`/`blocked` 只有用户批准才重置为 `pending`，不自动 reset、rollback、stash、删除日志或循环重试。

## 最小验证

发布或修改后运行以下测试，全部通过才能合并：

```sh
# 静态协议回归：检查 session/window/pane 顺序和提交键规则
python3 evals/test_tmux_protocol.py

# 真实 tmux 集成：验证隔离 server 中的窗口生命周期和 Enter 提交
python3 evals/test_tmux_integration.py
```

静态测试不依赖 tmux。集成测试未安装 tmux 时自动跳过；运行时使用独立 socket、随机 session 和 `-f /dev/null`，并只清理测试创建的 server，不操作默认 session 或既有窗口。
