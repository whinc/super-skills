# super-skills

个人工程思考沉淀成的 skill 集合，供编码 agent 使用：React 反模式修正、会话交接给后台 agent 续跑、微信小程序开发与验证、agent memory 定期压缩。所有 skill 遵循 [Skills 规范](https://skills.sh/docs/cli)。

## Skill 一览

- **[react-effects](./skills/react-effects/SKILL.md)**: 检测并修正 React `useEffect` 反模式。覆盖 12 种常见场景，为每种场景给出更简单、更高性能的正确替代方案。
- **[codebuddy-handoff](./skills/codebuddy-handoff/SKILL.md)**（命令 `/cbc-handoff`）: CodeBuddy 会话交接：把当前对话压缩成脱敏摘要，用 `codebuddy --bg` 启动新的后台 agent 立即接续，用户用 `codebuddy agents` 管理。
- **[wechat-miniprogram](./skills/wechat-miniprogram/SKILL.md)**: 微信小程序/小游戏开发与验证：定位源码与配置、编译预览上传、模拟器自动化与 console/network 诊断、云开发联调；构建、模拟器、手机三类证据分开报告。模拟器、预览、上传走新版 `wechatide` 接口，需 Electron 版微信开发者工具 **2.02.2607152+**；纯源码、配置与构建工作不受此限。
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
