# AI Skills Collection

A collection of reusable skills that give AI coding agents focused knowledge for specific engineering tasks. The skills follow the [Skills](https://github.com/vercel-labs/skills) specification and can be installed with the Skills CLI.

## Relationship to mattpocock/skills

This repository is an independent collection, not a replacement for `mattpocock/skills`.

- `mattpocock/skills` provides the single-ticket `/implement` workflow, including the implementation, testing, review, and commit process.
- `implement-tmux` in this repository is an orchestration layer around that workflow. It reads a wayfinding map or ticket spec, runs tickets strictly one at a time in fresh tmux windows, asks each worker to invoke `/implement`, and independently verifies the resulting commit and evidence.
- The other skills in this repository are standalone domain skills and do not require `mattpocock/skills`.

## Skills

| Skill | Description |
|------|-------------|
| [react-effects](./plugins/web/skills/react-effects/SKILL.md) | Detect and correct React `useEffect` anti-patterns with practical alternatives for common scenarios. |
| [eli12](./plugins/learning/skills/eli12/SKILL.md) | Explain topics for curious 12-year-olds with clear visuals, short sections, and an HTML artifact. |
| [implement-tmux](./plugins/engineering/skills/implement-tmux/SKILL.md) | Orchestrate CodeBuddy Code or Claude Code in strictly serial tmux windows, with each worker explicitly invoking `/implement` and the main window independently verifying Git. |

## Installation

Use the Skills CLI. See the [official CLI documentation](https://skills.sh/docs/cli) for the complete command reference.

```bash
# Install all plugin groups for CodeBuddy Code from this repository
npx skills add . -a codebuddy --yes

# Install an individual skill
npx skills add . --skill react-effects
npx skills add . --skill eli12
npx skills add . --skill implement-tmux
```

### Claude Code plugins

Validate each plugin locally with:

```bash
claude plugin validate ./plugins/web
claude plugin validate ./plugins/engineering
claude plugin validate ./plugins/learning
```

To install one or more groups from the Git marketplace and receive updates when the repository changes:

```text
/plugin marketplace add whinc/super-skills
/plugin install web@super-skills
/plugin install engineering@super-skills
/plugin install learning@super-skills
```

Add this marketplace from a Git source or local directory. Do not add the `marketplace.json` file through a direct URL, because Claude Code cannot resolve the relative `source: "./plugins/<group>"` paths from a manifest-only download.

## Contributing

Pull requests are welcome. Keep each skill focused, document its invocation boundary, and update the relevant references when its behavior changes.

## License

MIT

---

# 中文版

这是一个可复用的 AI 编程 skill 集合，为特定工程任务提供聚焦的领域知识。所有 skill 遵循 [Skills](https://github.com/vercel-labs/skills) 规范，可通过 Skills CLI 安装。

## 与 mattpocock/skills 的关系

本仓库是独立维护的 skill 集合，不替代 `mattpocock/skills`。

- `mattpocock/skills` 提供单 ticket 的 `/implement` 工作流，负责实现、测试、审查和提交。
- 本仓库的 `implement-tmux` 是该工作流的编排层：读取 wayfinding map 或 ticket spec，在全新的 tmux window 中严格串行执行 ticket，要求每个 worker 调用 `/implement`，并由主窗口独立核验 commit 和证据。
- 本仓库的其他 skill 是独立的领域 skill，不依赖 `mattpocock/skills`。

## Skills

| Skill | 描述 |
|------|------|
| [react-effects](./plugins/web/skills/react-effects/SKILL.md) | 检测并修正 React `useEffect` 反模式，为常见场景提供实用替代方案。 |
| [eli12](./plugins/learning/skills/eli12/SKILL.md) | 面向好奇的 12 岁读者解释主题，使用清晰的视觉内容、简短段落和 HTML artifact。 |
| [implement-tmux](./plugins/engineering/skills/implement-tmux/SKILL.md) | 在 tmux window 中严格串行调度 CodeBuddy Code 或 Claude Code；每个 worker 显式调用 `/implement`，主窗口独立核验 Git。 |

## 安装

使用 Skills CLI 安装。完整命令参考请阅读[官方 CLI 文档](https://skills.sh/docs/cli)。

```bash
# 从当前仓库为 CodeBuddy Code 安装全部 plugin 分组
npx skills add . -a codebuddy --yes

# 安装单个 skill
npx skills add . --skill react-effects
npx skills add . --skill eli12
npx skills add . --skill implement-tmux
```

### Claude Code plugins

使用以下命令分别校验本地 plugin manifest：

```bash
claude plugin validate ./plugins/web
claude plugin validate ./plugins/engineering
claude plugin validate ./plugins/learning
```

通过 Git marketplace 选择一个或多个分组安装，并在仓库发生变化时获取更新：

```text
/plugin marketplace add whinc/super-skills
/plugin install web@super-skills
/plugin install engineering@super-skills
/plugin install learning@super-skills
```

请通过 Git 源或本地目录添加 marketplace。不要直接使用 `marketplace.json` 的 URL，因为仅下载 manifest 时，Claude Code 无法解析相对路径 `source: "./plugins/<group>"`。

## 贡献

欢迎提交 PR。请保持每个 skill 的职责聚焦，明确记录调用边界，并在行为变化时同步更新相关参考文档。

## 许可证

MIT
