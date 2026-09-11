## Agent skills

### Issue tracker

Issues and specs live as Local Markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.

### Skill packaging

Skill 以自包含目录分发（两种渠道都只打包 skill/plugin 目录），引用必须落在本 skill 目录内，仓库根路径不随包发布；跨 skill 共享的文档在每个 skill 内各存一份，改动时同步全部副本。本地 CodeBuddy 加载 `.codebuddy/skills/` 的安装副本，改完 skill 后运行 `npx skills add . -a codebuddy --yes` 刷新，并运行该 skill 的 `evals/` 验证。
