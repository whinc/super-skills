# worktree 隔离与合并（implement-team 专有）

本文件是 implement-team 的隔离与集成机制来源，建立在 `references/agent-team-protocol.md` 的公共 manifest、调度、终态与 context 卫生之上。任务范围不做静态声明；隔离由 ticket worktree 提供，冲突防护由集成分支与 Merger 提供。

## 集成分支

确认门禁通过后，主 Agent 从落回目标分支的当前 HEAD 创建集成分支（manifest `branches.integration`）与集成 worktree（`<tempDir>/integration`）。所有合并、解锁与收尾集成验证都在集成 worktree 内执行；主工作区全程不被 teammate 触碰，未提交改动不进入集成分支。

## Ticket worktree

每个 teammate 在派发 prompt 给出的路径上自行创建并工作：

- 路径 `<tempDir>/wt/<ticket>`；分支 `agent-team/<runId>/<ticket>`；base 为派发时集成分支的 tip（`git worktree add <path> -b <branch> <integrationBranch>`）。
- 派发 prompt 在公共字段外追加：worktree 路径、ticket 分支名、集成分支名、工作区纪律、evidence 的主工作区绝对路径。
- 纪律：tracker 只有主 Agent 写（派发时写 `running`，核验后写终态）；票面与 evidence 用主工作区绝对路径；除 evidence 落盘外不触碰主工作区。
- 清理：核验并合并成功后，主 Agent `git worktree remove` 并删除 ticket 分支；`failed`/`blocked` 的 worktree 保留，路径写入 report 等用户处置；收尾执行 `git worktree prune`。

## 合并与冲突

核验通过后，主 Agent 在集成 worktree 内合并 ticket 分支（`git merge --no-ff`），输出重定向落盘；合并成功才写 tracker `Status: resolved` 并解锁后继。

合并冲突时：

1. `git merge --abort`，保持集成 worktree 与集成分支干净；
2. 派一个 Merger teammate 在集成 worktree 内重新合并并解决冲突，只解决冲突、不附加功能；
3. Merger 只报告一次 `MERGE_RESOLVED`（含 merge commit 与重跑的 verify）或 `MERGE_BLOCKED`（含 reason 与 evidence），字段与硬上限同终态事件；
4. 主 Agent 复核 merge commit 并重跑该 ticket 的 verify，通过才写 `Status: resolved` 并解锁后继；`MERGE_BLOCKED` 或复核未通过时该 ticket 保持 `blocked`，只沿依赖后代传播。

## 集成验证与落回

全部任务终态后：

1. `integrationVerify` 非空时，主 Agent 在集成 worktree 内执行一次，输出落盘 `evidenceDir/integration-verify.log`；结果只进 report，不改 ticket 状态。
2. 落回：确认主工作区当前分支等于 manifest `branches.landing`（不一致则保持现场并报告），然后把集成分支 `git merge --no-ff` 进落回目标分支，输出落盘。失败（合并冲突或工作区脏）时 `git merge --abort` 保持现场，并向用户给出手动落回命令。
3. 清理：落回成功后删除集成 worktree、已合并的 ticket worktree/分支与集成分支；落回失败则全部保留。

report 在公共字段外追加：集成验证结果、合并记录（ticket → merge commit）、落回结果与 SHA、保留的 worktree 路径。
