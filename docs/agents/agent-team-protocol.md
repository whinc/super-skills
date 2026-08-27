# AgentTeam 公共协议

本协议是团队型 skill 的公共 manifest、调度和终态来源。各 skill 只定义自己的输入边界与子 agent skill，不复制或改写本协议的终态约束。

## Manifest

主 Agent 在用户确认后保存一份调度快照：

```yaml
project: "/absolute/path/to/project"
input:
  kind: prd-spec-input # prd-spec-input | map-issues
  sources: []
coordinator:
  role: main-agent
  sharedContext: true
  dispatch: native-TeamCreate-AgentTeam
team:
  maxConcurrency: 4
  pathConflictPolicy: fail-closed
maxRepairRounds: 0
protectedPaths: []
evidenceDir: ".scratch/runs/agent-team"
tickets: []
```

每个 ticket 必须保留唯一 `id`、原文 tracker、`dependsOn`、`allowedPaths`、`verify`、`evidence` 和当前 `status`。状态为 `pending`、`running`、`verifying`、`resolved`、`failed` 或 `blocked`。

## 协调与 DAG

只创建一个原生 `TeamCreate` 得到的 `AgentTeam`。主 Agent 是唯一 coordinator、派发者、解锁者和核验者；成员共享 team 上下文，但不能解锁后继或代替主 Agent 改派任务。每轮挑选所有依赖已由主 Agent 核验为 `resolved` 的 ready ticket。

规范化 `allowedPaths` 后，同轮 ticket 出现相同路径、文件与父子目录、glob 交集或任一范围不确定时，禁止并行并 fail-closed；没有冲突的独立分支应最大化并发。DAG 必须检查唯一 ID、依赖存在、无环和 tracker 可写。

某 ticket `failed` 或 `blocked` 时，主 Agent 将事件、原因、日志、验证和 evidence 写入共享上下文，并只沿依赖后代传播 `blocked`；独立分支继续。不要把失败扩散到无依赖分支，不自动 reset、rollback、stash、删除证据或重试。恢复必须重新取得用户批准并重建基线。

## 终态与独立核验

子 agent 只报告一次终态事件：

```json
{"event":"TICKET_RESOLVED","ticket":"01","status":"resolved","commit":"abc1234","changedFiles":["src/example.ts"],"verification":[{"command":"python3 -m unittest","result":"passed","evidence":".scratch/runs/agent-team/01.log"}],"evidence":[".scratch/runs/agent-team/01.log"],"summary":"验收通过","reason":null}
```

事件只能是 `TICKET_RESOLVED`、`TICKET_FAILED` 或 `TICKET_BLOCKED`；状态只能是 `resolved`、`failed` 或 `blocked`。`resolved` 必须有非空 evidence，并把 tracker 的 `Status: resolved` 回写；失败和阻塞必须有 reason、已运行验证和 evidence。重复、缺字段、ID 不匹配、tracker 未更新、验证/evidence 不可复核或异常退出均 fail-closed。

主 Agent 独立复核 commit、changedFiles 与 `allowedPaths`，Git 基线、protectedPaths、staging、coverage/锁、验证命令、evidence 和 tracker；核验通过后才释放依赖。wayfinding issue 额外必须有 `## Answer`、`Status: resolved` 和探索证据。所有未核验或证据缺失的结果都保持阻塞，不得宣称完成。
