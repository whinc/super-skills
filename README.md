# super-skills

个人工程思考沉淀成的 skill 集合，供编码 agent 使用：React 反模式修正、多 ticket 并发实现编排、面向 12 岁读者的讲解。所有 skill 遵循 [Skills 规范](https://skills.sh/docs/cli)，按插件分组组织。

## Skill 一览

### Web 开发

- **[react-effects](./plugins/web/skills/react-effects/SKILL.md)**: 检测并修正 React `useEffect` 反模式。覆盖 12 种常见场景，为每种场景给出更简单、更高性能的正确替代方案。

### 工程工作流

- **[implement-team](./plugins/engineering/skills/implement-team/SKILL.md)**: PRD/spec 实现编排层：经用户确认后，把 `.scratch/<feature>/issues/` 实现 tickets 按依赖 DAG 安全地最大化并发派发到共享 AgentTeam。每个 ticket 调用 `/implement`，主 Agent 独立核验证据。
- **[wayfinder-team](./plugins/engineering/skills/wayfinder-team/SKILL.md)**: 地图探索编排层：经用户确认后，把 `map.md` 的 child issues 派发到共享 AgentTeam 并发探索。每个 issue 调用 `/wayfinder`；需要代码或配置变更的 issue 标记 `blocked`，不自动实现。

### 学习与讲解

- **[eli12](./plugins/learning/skills/eli12/SKILL.md)**: 面向好奇的 12 岁读者解释任意主题，使用清晰的可视化、简短段落和 HTML artifact。

## 安装

两条路线，两种哲学，二选一。**Claude Code 插件**把整套 skill 作为托管、只读的包安装，随仓库发布自动更新——订阅而非复制。**Skills CLI** 把可编辑的 skill 文件复制到你的项目里，随你修改定制，不会在背后自动更新。两个都装会让每个 skill 出现两份，选一个。

### 路线 1：Claude Code 插件

通过 Git 市场安装一个或多个分组：

```text
/plugin marketplace add whinc/super-skills
/plugin install web@super-skills
/plugin install engineering@super-skills
/plugin install learning@super-skills
```

> [!IMPORTANT]
> 请通过 Git 源或本地目录添加市场，不要直接使用 `marketplace.json` 的 URL——仅下载 manifest 时，Claude Code 无法解析相对路径 `source: "./plugins/<group>"`。

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

本仓库独立维护，不替代 [`mattpocock/skills`](https://github.com/mattpocock/skills)：其 `/implement`、`/wayfinder` 负责单个 ticket/issue 的执行；本仓库的 `implement-team`、`wayfinder-team` 是其上的多 ticket/issue 并发编排层。其余 skill（`react-effects`、`eli12`）为独立领域 skill，无依赖。
