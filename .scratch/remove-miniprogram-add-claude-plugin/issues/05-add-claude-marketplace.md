# 05: 添加 Claude Code plugin 与 marketplace manifests

**What to build:** 让 Claude Code 用户可以把仓库作为 Git marketplace 添加，并安装名为 `super-skills` 的 plugin；仓库提交变化应成为 marketplace 判断更新的依据，同时复用现有根 `skills/` 目录，不复制或移动 skill 内容。

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Claude Code plugin manifest 与 marketplace manifest 均存在并通过 plugin validation。
- [x] marketplace 与 plugin 均使用 `super-skills`，marketplace 的 plugin source 为当前仓库的相对路径 `./`。
- [x] 两个 manifest 均不设置固定 `version`，保留 Git commit 自动更新策略。
- [x] Claude Code 可发现根 `skills/` 中的三个保留 skills，且没有引入 commands、agents、hooks、MCP 或其他额外 plugin 组件。
- [x] manifest 仅包含通过校验所需及必要描述元数据，不包含宿主机绝对路径或敏感信息。
