Type: grilling
Status: resolved

## Question

Claude Code 官方研究建议 marketplace 根与 plugin 根分离：仓库根 `.claude-plugin/marketplace.json`，插件目录（例如 `plugins/super-skills/`）内放 `.claude-plugin/plugin.json`。但当前仓库的 skills 位于根目录 `skills/`，且用户此前确认新增根 `.claude-plugin/plugin.json` 与根 `.claude-plugin/marketplace.json`。

需要决定最终目录布局，并明确 plugin 如何复用现有根 `skills/`：

- 方案 A：保持根目录同时放两个 manifest，marketplace 条目 `source: "./"`，plugin 直接扫描根 `skills/`；改动最小，但不是官方多插件 marketplace 示例布局。
- 方案 B：根目录只放 `marketplace.json`，新增 `plugins/super-skills/.claude-plugin/plugin.json`，并在 plugin 目录中通过 manifest 的 `skills` 路径指向 `../../skills/`；更贴近官方 marketplace 结构，但需确认路径边界与 Claude Code 校验行为。
- 方案 C：将剩余 skills 移入 `plugins/super-skills/skills/`，根目录 marketplace 条目指向该子目录；目录更标准，但会改变现有 Skills CLI 源目录布局。

请确定采用哪种布局，并同步确认 marketplace 安装名、plugin 安装名及 README 命令是否保持 `super-skills@super-skills`。

## Comments

## Answer

采用方案 A：仓库根目录同时放 `.claude-plugin/marketplace.json` 与 `.claude-plugin/plugin.json`，保留根目录 `skills/` 作为唯一 skills 源目录；marketplace 条目使用 `source: "./"`，plugin 直接发现根 `skills/`。这样保持 Skills CLI 现有目录布局，避免跨 plugin 根路径引用和大规模移动文件。marketplace 与 plugin 名称均为 `super-skills`，README 使用 `super-skills@super-skills` 安装命令，并明确 marketplace 必须通过 Git 源或本地目录添加。
