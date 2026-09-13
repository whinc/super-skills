## Agent skills

### Issue tracker

Issues and specs live as Local Markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.

### Skill packaging

Skill 以自包含目录分发：Skills CLI 只复制 skill 目录本身，仓库根路径引用安装后必然失效；Claude Code 插件渠道打包整个仓库根（plugin 根即仓库根），但 skill 同样不得依赖仓库根文件。引用必须落在本 skill 目录内；跨 skill 共享的文档在每个 skill 内各存一份，改动时同步全部副本。本地 CodeBuddy 加载 `.codebuddy/skills/` 的安装副本，改完 skill 后运行 `npx skills add . -a codebuddy --yes` 刷新，并运行该 skill 的 `evals/` 验证。
