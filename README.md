# super-skills

一套可复用的 [AI agent skill](https://github.com/vercel-labs/skills) 集合，为特定工程任务提供聚焦的领域知识。所有 skill 遵循 [Skills 规范](https://skills.sh/docs/cli)，按插件分组组织，可通过 Skills CLI 或 Claude Code 插件市场安装。

## Skill 一览

### Web 开发

| Skill | 描述 |
|-------|------|
| [react-effects](./plugins/web/skills/react-effects/SKILL.md) | 检测并修正 React `useEffect` 反模式。覆盖 12 种常见场景，为每种场景给出更简单、更高性能的正确替代方案。 |

### 工程工作流

| Skill | 描述 |
|-------|------|
| [implement-team](./plugins/engineering/skills/implement-team/SKILL.md) | PRD/spec 实现编排层：经用户确认后，把 `.scratch/<feature>/issues/` 实现 tickets 按依赖 DAG 安全地最大化并发派发到共享 AgentTeam。每个 ticket 调用 `/implement`，主 Agent 独立核验证据。 |
| [wayfinder-team](./plugins/engineering/skills/wayfinder-team/SKILL.md) | 地图探索编排层：经用户确认后，把 `map.md` 的 child issues 派发到共享 AgentTeam 并发探索。每个 issue 调用 `/wayfinder`；需要代码或配置变更的 issue 标记 `blocked`，不自动实现。 |

### 学习与讲解

| Skill | 描述 |
|-------|------|
| [eli12](./plugins/learning/skills/eli12/SKILL.md) | 面向好奇的 12 岁读者解释任意主题，使用清晰的可视化、简短段落和 HTML artifact。 |

## 安装

使用 Skills CLI 安装，完整命令参考见[官方文档](https://skills.sh/docs/cli)。

```bash
# 从本仓库为 CodeBuddy Code 安装全部插件分组
npx skills add . -a codebuddy --yes

# 或只安装单个 skill
npx skills add . --skill react-effects
npx skills add . --skill eli12
npx skills add . --skill implement-team
npx skills add . --skill wayfinder-team
```

> [!NOTE]
> `plugins/*/skills/` 目录有任何变化后，需要重新运行安装命令，才能在本地实际生效。

### Claude Code 插件

本地校验各插件的 manifest：

```bash
claude plugin validate ./plugins/web
claude plugin validate ./plugins/engineering
claude plugin validate ./plugins/learning
```

通过 Git 市场安装一个或多个分组，并在仓库更新时同步更新：

```text
/plugin marketplace add whinc/super-skills
/plugin install web@super-skills
/plugin install engineering@super-skills
/plugin install learning@super-skills
```

> [!IMPORTANT]
> 请通过 Git 源或本地目录添加市场，不要直接使用 `marketplace.json` 的 URL——仅下载 manifest 时，Claude Code 无法解析相对路径 `source: "./plugins/<group>"`。

## 与 mattpocock/skills 的关系

本仓库是独立维护的 skill 集合，不替代 [`mattpocock/skills`](https://github.com/mattpocock/skills)：

- `mattpocock/skills` 提供单 ticket 的 `/implement` 工作流，负责实现、测试、审查和提交。
- 本仓库的 `implement-team` 是其上的多 ticket 编排层：拆分与派发由共享 AgentTeam 完成，单个 ticket 的执行仍由 `/implement` 承担。
- 本仓库的 `wayfinder-team` 是 `/wayfinder` 的多 issue 探索编排层。
- 直接实现单一任务时无需团队：直接调用 `/implement` 即可。
- 其余 skill（如 `react-effects`、`eli12`）是独立领域 skill，不依赖 `mattpocock/skills`。

## 项目结构

```text
plugins/
├── web/            # Web 开发技能分组
│   └── skills/react-effects/
├── engineering/    # 工程工作流技能分组
│   ├── skills/implement-team/
│   └── skills/wayfinder-team/
└── learning/       # 学习讲解技能分组
    └── skills/eli12/
docs/
└── agents/         # AgentTeam 协议、领域与 issue tracker 约定
```
