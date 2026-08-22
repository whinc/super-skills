---
name: implement-tmux
description: "使用原生 tmux CLI 将 map/spec 中的一组 ticket 交给自动探测的 CodeBuddy Code 或 Claude Code 严格串行执行；每个 worker 调用 /implement，主窗口只消费终态消息并独立核验 Git。"
disable-model-invocation: true
---

# Implement tmux

## 目标

`implement-tmux` 是 mattpocock/skills `/implement` 的调度层，不替代单 ticket 的实现流程。它只负责从规划文档生成候选执行计划、创建隔离的 tmux window、严格串行调度 worker、消费一次性终态消息、独立核验和清理。

共享工作区中任何时刻只有一个 ticket 处于 `running` 或 `verifying`；没有依赖关系的 ticket 也不能并行。运行时只使用原生 `tmux` CLI，不依赖 `smux`、`tmux-bridge`、daemon、MCP 或自定义服务。

主窗口只处理最终结构化消息和简短核验结果。不要持续读取 worker pane、思考过程或中间日志；只有终态缺失、失败/阻塞取证或用户明确要求时，才读取少量 pane 尾部输出。

## 输入与候选计划

接受以下输入：

- `/wayfinder` 生成的 `map.md`；
- `/to-tickets` 生成的 `spec.md`；
- 可选的、已确认过的持久化 manifest；
- 用户提供的项目路径、tmux session 和显式 ticket 顺序（显式顺序可覆盖文档默认顺序）。

manifest 可选，不要求用户重复填写文档中已有信息。启动时在内存中生成一份候选计划：

1. 从 map/spec 读取 ticket id、顺序、依赖、tracker、范围和验收信息；从 tracker、项目结构、Git 状态和 `package.json` scripts 补充缺失信息。
2. 从 ticket 明确列出的文件、tracker 变更范围、spec 产物和对应测试文件推断 `allowedPaths`。不能可靠推断的路径保持不确定，不得猜测。
3. 从 ticket 验收命令和项目已有 scripts 推断 `verify`。命令必须在项目中可识别且可执行；无法识别的验收命令必须阻塞。
4. `maxRepairRounds` 缺失时使用 `2`；不把 `/implement` 的 TDD、typecheck、测试、review 或 commit 规则复制到本 skill。
5. 记录结果消息目标 `mainPane`、检测到的 worker CLI、ticket 顺序、每项范围、验收命令和保护边界。

启动前必须展示完整候选计划，并且只请求一次确认。计划至少展示：

- project、session、`mainPane` 和 agent policy；
- ticket 顺序及依赖；
- 每个 ticket 的 `allowedPaths`、`verify`、tracker 和不确定项；
- 启动时 Git 基线中的 modified、untracked、staged 路径；
- 额外 protected paths（coverage、lock、调度状态和用户声明项）；
- `maxRepairRounds: 2` 或用户明确的值；
- 终态消息使用 `tmux send-keys` 回传，不创建 `resultFile`。

在用户确认前禁止创建 ticket window、启动 worker 或修改工作区。显式顺序与 map/spec 不同时，计划必须同时展示两种顺序并在同一次确认中请求选择；用户未明确选择时才报告 `TICKET_BLOCKED`。以下任一项不能安全确定时，直接报告 `TICKET_BLOCKED` 并列出具体缺口：项目/session 不明、tracker/范围/验收无法推断，或候选范围与保护边界重叠。不要以默认路径、默认测试或猜测的依赖替代缺口。

## 状态机

```text
pending → running → verifying → done
                    ├→ failed
                    └→ blocked
```

- `done`：终态消息、commit、文件范围、staging、验收和证据全部独立核验通过。
- `failed`：代码、断言、配置、测试或产物失败；只允许按 `/implement` 的结果和计划上限进行有依据的修复—重跑。
- `blocked`：tmux、worker CLI、`/implement`、外部构建、DevTools 或其他环境/工具不可用。

`failed` 和 `blocked` 都停止后续 ticket。blocked 不得报告为 passed，也不得自动重试、reset、rollback、stash、删除日志或覆盖用户改动。

## 执行步骤

### 1. 建立启动基线

确认工具和 session 存在，然后在主窗口记录真实 pane、window、Git 工作区和暂存区：

```sh
tmux -V
tmux has-session -t "$session"
main_pane="${mainPane:-$(tmux display-message -p '#{pane_id}')}"
tmux display-message -p -t "$main_pane" '#{pane_id}'
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
git -C "$project" status --short --untracked-files=all
git -C "$project" diff --cached --name-only
```

把启动时所有 modified、untracked、staged 路径加入保护基线，并保存必要的内容/hash 以便后续比较。coverage、lock 文件、调度状态和用户声明的 `protectedPaths` 也加入保护边界。若 ticket 的候选范围与任何基线改动重叠，先阻塞而不是让 worker 冒险共用文件。

**完成条件：** session、`mainPane`、基线路径和本次创建 window 集合已记录；集合初始为空。

### 2. 确认候选计划并探测 worker

完成候选计划展示后，等待用户一次性明确确认。确认后、创建第一个 window 前，按固定顺序探测：

```sh
agent_command=""
for candidate in codebuddy codebuddy-code cbc claude; do
  if command -v "$candidate" >/dev/null 2>&1; then
    agent_command="$candidate"
    break
  fi
done
```

`codebuddy`、`codebuddy-code`、`cbc` 是 CodeBuddy Code 的等价命令名，`claude` 是唯一允许的 fallback。两类 CLI 都必须使用 `--permission-mode bypassPermissions`。不接受 manifest 中的任意 agent 命令，也不能回退到 Codex 或其他工具。

同时确认目标 agent 会话可使用 `/implement`。若无法在当前 agent 的 skill registry/安装目录中验证 `/implement`，报告 `TICKET_BLOCKED`，不要创建 ticket window。四个 CLI 都不存在、tmux/session 不可用或 `/implement` 不可用，也必须在 window 创建前阻塞。

**完成条件：** 已记录候选计划、用户确认、`agent_command` 和 `/implement` 可用性；或在创建 window 前明确报告 blocked。

### 3. 创建当前 ticket

按计划顺序选取第一个尚未独立核验为 `done` 的 ticket，并确认其依赖均已完成。只创建一个新 window：

```sh
tmux new-window -d -t "$session" -n "ticket-<ID>" -c "$project" \
  "$agent_command --permission-mode bypassPermissions"
```

立即保存新 window 的真实 `window_id`、`pane_id`，不要依赖会重排的数字索引。对新会话首次发送完整、自包含 prompt，必须用 literal 输入后 Enter：

```sh
tmux send-keys -t "$pane_id" -l -- "$prompt"
tmux send-keys -t "$pane_id" Enter
```

prompt 必须包含当前 ticket、tracker、已确认的 `allowedPaths`、`protectedPaths`、`verify`、`maxRepairRounds`、项目约束、`mainPane` 和终态协议，并明确要求：

- 只处理当前 ticket，不扩大范围，不触碰基线保护改动；
- **必须在自己的 agent 会话中显式调用 `/implement`**，由 `/implement` 负责 TDD、typecheck、测试、code-review 和 commit；不得复制或替代该流程；
- `/implement` 完成后只发送一次终态消息，发送后停止工作；
- 工具/环境不可用标记 `TICKET_BLOCKED`，代码/测试/产物失败标记 `TICKET_FAILED`；
- 最终消息通过 `tmux send-keys` 发往 `mainPane`，不写 `resultFile`。

忙碌的 CodeBuddy Code/Claude Code 会话收到追加 prompt 时，先 literal 输入内容，再发送 `Tab` 排队；不要用 Enter 打断当前会话。尤其是 `mainPane` 正在运行主 agent 时，worker 回传终态也必须先输入 JSON，再发送 `Tab` 排队。新 window 的首次 prompt 才使用 Enter。

### 4. 接收唯一终态消息

worker 完成后向 `mainPane` 发送一行 JSON，格式如下：

```json
{"event":"TICKET_DONE","ticket":"唯一 ID","status":"done","commit":"abc1234","changedFiles":["src/example.ts"],"verification":[{"command":"npm test -- --runInBand","result":"passed","evidence":".scratch/runs/01-test.log"}],"evidence":[".scratch/runs/01-test.log"],"summary":"完成当前 ticket 并通过验收"}
```

`event` 只能是 `TICKET_DONE`、`TICKET_FAILED` 或 `TICKET_BLOCKED`；`status` 只能是 `done`、`failed` 或 `blocked`。消息必须包含 ticket id、commit（失败/阻塞可为 `null`）、changedFiles、每条 verification 的 command/result/evidence、evidence 列表和简短 summary。worker 只发送一次终态，不发送过程消息。

主窗口在预期终态到达后只用一次 `capture-pane` 确认单行消息已出现：

```sh
tmux capture-pane -p -t "$mainPane" -S -30
```

只解析匹配的终态 JSON，不把持续 pane 输出带回主上下文，不轮询中间输出。终态缺失、JSON 无法解析、ticket id 不匹配、字段缺失或 worker 异常退出，均为 `TICKET_BLOCKED`，并保留当前 window 和证据。不要把沉默视为成功。

### 5. 独立核验

收到 `TICKET_DONE` 也不能直接解锁下一个 ticket。主窗口独立执行：

```sh
git -C "$project" status --short --untracked-files=all
git -C "$project" diff --cached --name-only
git -C "$project" show --stat --oneline <commit>
git -C "$project" diff-tree --no-commit-id --name-only -r <commit>
```

逐项确认：

- commit 存在，是当前 ticket 的独立 commit，且 commit 文件全部位于确认过的 `allowedPaths`；
- 基线 modified/untracked/staged 路径、protected paths、coverage、lock 和调度状态没有进入 ticket staging 或 commit；启动 staging 与当前 staging 的内容/路径边界一致；
- `changedFiles` 与 commit 实际文件一致，未出现未解释的工作区污染；
- tracker 状态、checklist、Resolution/Comments（如有）与真实结果一致，但不自动修改 tracker；
- 每个 verification 命令的结果、测试/产物和 evidence 路径真实存在且可复核；代码/测试失败是 `failed`，环境不可用才是 `blocked`。

任何一项不通过都不能标记 `done`。按原因分类为 `TICKET_FAILED` 或 `TICKET_BLOCKED`，保留 window 和证据并停止链路。

### 6. 清理并推进

只有独立核验全部通过才关闭本次创建的 window：

```sh
tmux kill-window -t "$window_id"
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
```

只操作本次运行记录的真实 `window_id`，保留启动前存在的所有窗口。然后才启动下一个 pending ticket。失败或阻塞的 window 不关闭，以便检查和恢复。

### 7. 恢复和整组终态

恢复时重新建立 Git 基线并重新生成/确认计划：已独立核验的 `done` ticket 直接跳过；`failed` 或 `blocked` 只有用户明确批准重试才重置为 `pending`；不自动重放或循环重试。

最终只输出 ticket 状态、commit、验证结论和 evidence。全部 ticket 都经独立核验为 `done` 才报告整体完成；存在 `failed` 或 `blocked` 时报告停止点、原因、保留的 window 和用户需要批准的恢复动作。

## 验证 implement-tmux

发布或修改本 skill 后，优先使用可丢弃的 tmux fixture 和 fake CodeBuddy Code/Claude Code CLI，记录 window 创建、首次 Enter、忙碌会话 Tab 排队、终态消息到达、独立核验和清理。fixture 至少验证：

- CodeBuddy 检测优先级、Claude fallback、两者不可用时创建 window 前 blocked；
- map/spec 默认顺序、显式顺序冲突的一次确认门，以及确认前没有 worker window；
- 两个无依赖 ticket 仍严格串行，worker prompt 明确调用 `/implement`；
- 缺失/损坏终态、`TICKET_FAILED`、`TICKET_BLOCKED` 会停止链路并保留 window；
- `TICKET_DONE` 只有在 commit、文件范围、staging、基线保护、verification 和 evidence 全部独立通过后才启动下一个 ticket；
- 成功时只关闭本次创建的 window，恢复时跳过已核验 ticket，并要求用户明确批准重试失败/阻塞 ticket。

如果没有可用的真实 tmux fixture，使用确定性的命令转录测试覆盖同一组可观察状态转换；在未运行真实 fixture 前，不得声称真实 tmux 运行时已通过。
