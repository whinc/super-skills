## Destination

将仓库整理为不含微信小程序内容的 skills 集合，并同时支持 Skills CLI 与 Claude Code plugin/marketplace 安装；README 提供中英双语、可复制且可验证的安装与自动更新说明。

## Notes

- 领域：skills 包分发、Claude Code plugin/marketplace、仓库清理与文档。
- 需遵循仓库现有 `docs/agents/issue-tracker.md` 的 Local Markdown tracker 约定。
- 已确认：移除全部小程序 skills、评测 workspace、仅服务于小程序评测的 demo、安装生成副本/链接、锁文件条目和文档引用。
- 已确认：保留所有非小程序 skills。
- 已确认：新增 `.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json`，marketplace 条目使用 `source: "./"`，不固定 `version`，通过 Git commit 变化获得更新。
- 已确认：README 保留中英双语，统一引用 `https://skills.sh/docs/cli`，使用 `npx skills add . -a codebuddy --yes`，并说明 marketplace 安装与验证。

## Decisions so far

- [核实 Claude Code marketplace manifest 与自动更新约束](issues/01-verify-claude-marketplace.md)：确认 marketplace 必须通过 Git 源加载以解析相对 `source`，省略两处 `version` 时按 Git commit SHA 判断更新；研究同时发现官方推荐 marketplace 根与 plugin 子目录分离。
- [盘点小程序清理资产边界](issues/02-inventory-miniprogram-assets.md)：确认小程序源 skills、评测 workspace、相关安装副本/链接、锁文件及文档引用应移除，仓库内不存在可删除的 `miniprogram-demo`，非小程序资产保留。
- [决定 Claude Code plugin 与 marketplace 的目录布局](issues/03-decide-plugin-layout.md)：采用根目录同时放两个 manifest、保留根 `skills/`、使用 `source: "./"`；marketplace 与 plugin 均命名为 `super-skills`。

## Not yet specified

<!-- 当前目的地所需决策已明确；实现阶段需按上述决策执行并验证。 -->

## Out of scope

- 不新增其他类型的 Claude Code plugin 组件（commands、agents、hooks、MCP 等）。
- 不改造现有非小程序 skills 的行为或内容。
- 不替代 `mattpocock/skills` 的 `/implement`、`/wayfinder` 或 `/to-tickets` 工作流。
