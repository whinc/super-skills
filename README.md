# super-skills

个人工程思考沉淀成的 skill 集合，供编码 agent 使用：React 反模式修正、多 ticket 并发实现编排、agent memory 定期压缩。所有 skill 遵循 [Skills 规范](https://skills.sh/docs/cli)。

## Skill 一览

### Web 开发

- **[react-effects](./skills/react-effects/SKILL.md)**: 检测并修正 React `useEffect` 反模式。覆盖 12 种常见场景，为每种场景给出更简单、更高性能的正确替代方案。

### 工程工作流

- **[implement-team](./skills/implement-team/SKILL.md)**: PRD/spec 实现编排层：经用户确认后，把 `.scratch/<feature>/issues/` 实现 tickets 按依赖 DAG 事件驱动并发派发。每个 ticket 在独立 git worktree 中调用 `/implement`，主 Agent 独立核验后合并进集成分支、收尾落回原分支。
- **[memory-compact](./skills/memory-compact/SKILL.md)**: agent memory 定期压缩：按 keep/merge/delete/promote 清理过时、重复、任务特定与可恢复条目，批量提案经一次确认后写回，主入口保持 200 行 / 25KB 双上限。

## 安装

两条路线，两种哲学，二选一。**Claude Code 插件**把整套 skill 作为托管、只读的包安装，随仓库发布自动更新——订阅而非复制。**Skills CLI** 把可编辑的 skill 文件复制到你的项目里，随你修改定制，不会在背后自动更新。两个都装会让每个 skill 出现两份，选一个。

### 路线 1：Claude Code 插件

通过 Git 市场安装（单插件包含全部 skill）：

```text
/plugin marketplace add whinc/super-skills
/plugin install super-skills@super-skills
```

> [!IMPORTANT]
> 请通过 Git 源或本地目录添加市场，不要直接使用 `marketplace.json` 的 URL——仅下载 manifest 时，Claude Code 无法解析相对路径 `source: "./"`。

### 路线 2：Skills CLI

完整命令参考见[官方文档](https://skills.sh/docs/cli)。

```bash
npx skills@latest add whinc/super-skills
```

安装器会列出全部 skill 供你挑选，并让你选择安装到哪些 coding agent（CodeBuddy、Claude Code、Codex 等）。只装单个 skill 时：

```bash
npx skills@latest add whinc/super-skills --skill react-effects
```

仓库更新后，运行 `npx skills update` 拉取最新版本。

## 与 mattpocock/skills 的关系

本仓库独立维护，不替代 [`mattpocock/skills`](https://github.com/mattpocock/skills)：其 `/implement` 负责单个 ticket 的执行；本仓库的 `implement-team` 是其上的多 ticket 并发编排层。其余 skill（`react-effects`、`memory-compact`）为独立领域 skill，无依赖。
