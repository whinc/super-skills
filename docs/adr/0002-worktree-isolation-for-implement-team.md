---
status: accepted
---

# implement-team 改用 ticket worktree 隔离 + 集成分支落回

2026-09-11 决定：implement-team 的并发模型从"共享工作区 + 运行时 CONFLICT 升级"改为"每 ticket 独立 git worktree + 集成分支"。Teammate 按派发 prompt 给出的路径自行 `git worktree add`（`$TMPDIR/agent-team/<runId>/wt/<ticket>`，分支 `agent-team/<runId>/<ticket>`，base 为集成分支 tip），只在自己的 worktree 提交；主 Agent 独立核验后在集成 worktree 里把 ticket 分支合并进集成分支（`agent-team/<runId>`）；合并冲突时派 Merger teammate 解决，主 Agent 复核并重跑该 ticket 的 verify；收尾跑可选 `integrationVerify`，再把集成分支 `--no-ff` 落回目标分支，成功清理、失败保留现场。调度同时改为事件驱动：任一终态事件核验解锁后立即补派后继，不等同批任务齐终态。

## Considered Options

- **维持共享工作区 + CONFLICT 升级**（ADR-0001）：否决——共享工作区下 `git add -A` 会把他人未完成改动卷进 commit，污染"commit 属于本 ticket"的证据链；冲突升级还要占用主 Agent context，与 context 卫生目标相悖。
- **依赖 runtime 的 `isolation: worktree`**：不可行——该能力只由自定义 agent frontmatter 启用，skill 目录无法随包分发 agent 定义（skills CLI 渠道），派发也没有 per-call 隔离开关；故由 teammate 自行创建 worktree。
- **合并冲突即标 blocked、等用户处置**：否决——单点冲突会打断整条 run 并需要用户介入，与"最大化减少人工主轮介入"目标冲突。
- **只交付集成分支、不自动落回**：否决——比既有"实现直接落在当前分支"的语义多一次人工介入；改为自动落回、失败保留现场并给出手动命令。

## Consequences

- 主工作区全程不被 teammate 触碰（唯一例外是 evidence 落盘）；用户未提交改动不进入集成分支。
- 移除 `CONFLICT` 升级通道：文件级编辑竞争被 worktree 结构性消除，合并冲突有 Merger 通道，其余异常走 `TICKET_BLOCKED`；"只报一次终态"成为绝对规则。
- wayfinder-team 不上 worktree：探索产物是决策、答案与证据，不产生代码提交。
- worktree 机制只随 implement-team 分发（`references/worktree-merge.md`）；公共 protocol 仍两份全等。
- 前置条件：目标项目是 git 仓库；worktree 注册表残留用 `git worktree prune` 清理。

**2026-09-11 追加**：worktree 隔离落地后，manifest 中因共享工作区而存在的限制一并移除——`maxConcurrency` 硬上限（frontier 任务全部并发派发）与 `protectedPaths`（禁区清单冗余，teammate 已不触碰主工作区）。manifest 同时删去恒定样板（`coordinator` 块）与可由 `tempDir` 推导的集成 worktree 路径字段。
