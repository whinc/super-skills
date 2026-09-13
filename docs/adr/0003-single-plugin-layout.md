---
status: accepted
---

# 取消插件分组，回归单一 plugin（仓库根即 plugin 根）

2026-09-13 决定：取消 web / engineering / learning 三个 plugin 分组（由提交 `f388a52`「拆分 Claude Code plugin 分组安装」引入），回归单 plugin `super-skills`。仓库根即 plugin 根：skill 目录提升到顶层 `skills/<name>/`，`.claude-plugin/` 同时存放 `marketplace.json` 与 `plugin.json`，marketplace 中 `source: "./"`。

分组是发布维度而非内容维度：skill 集合规模小（5 个），按组分装的粒度从未被实际使用，却带来三份 plugin.json、三条安装命令和跨 plugin 的版本协调负担（插件级 SemVer 的粒度问题即由此而来）。单 plugin 后 `skills/` 成为唯一 skill 来源目录，两条分发渠道（Claude Code 插件、Skills CLI）共用同一份目录结构，版本机制相应退化为单版本线。

## Considered Options

- **维持三分组**：否决——分装能力无人使用，多 plugin 的维护与版本协调成本却是持续支出。
- **单 plugin 但 skills 保留在子目录**（如 `plugins/super-skills/skills/`）：否决——多一层目录无收益；顶层 `skills/` 是 Skills CLI 的最高优先级扫描路径，也让 Claude Code 的 plugin 根结构最简单。
- **marketplace 加 `renames` 映射旧名**：否决——无外部用户，本地手动重装即可；若将来出现外部用户，`web`/`engineering`/`learning` → `super-skills` 的 renames 是既有机制，可随时补。

## Consequences

- Claude Code 渠道失去按组分装：安装 `super-skills` 即得到全部 5 个 skill（skill 仍按 description 触发，不做全量加载），有意接受。
- plugin 目录 = 仓库根，安装时整个仓库复制进用户插件缓存（含 `.scratch/`、`react-effects-workspace/`、`docs/`），Claude Code 无任何排除机制；只有把文件从 git 移除才能真正排除，本次接受该代价。
- `plugin.json` 不写 `version`：Claude Code 按 commit SHA 判定更新，commit 变动即用户收到更新，避免"忘记 bump 导致静默冻结"。
- 旧 plugin 名消失后已安装用户报 `plugin-not-found`；当前唯一用户（作者本人）手动卸载旧 plugin 后重装 `super-skills@super-skills`。
- 打包边界两渠道不同（Claude Code 整仓、Skills CLI 仅 skill 目录），skill 必须自包含的纪律不变；`AGENTS.md` 已同步该表述。
