Type: research
Status: resolved

## Question

盘点当前仓库所有微信小程序相关资产和引用，确认应移除的源目录、评测 workspace、demo、安装生成副本/链接、锁文件条目、配置/文档引用；同时确认非小程序 skills 与其评测资产应保留。结果必须使用仓库相对路径，并给出实现清理时不可遗漏的文件清单。

## Comments

## Answer

盘点结论（全部为仓库相对路径；仓库根目录无 package.json/node_modules，仅有 skills-lock.json 一个锁文件）。

### 应移除 —— 小程序源 skills

- `skills/miniprogram-automation/`（含 `SKILL.md`、`evals/evals.json`）
- `skills/miniprogram-ci/`（含 `SKILL.md`、`evals/evals.json`）

### 应移除 —— 小程序评测 workspace（git 跟踪、仍存在于工作区）

- `miniprogram-automation-workspace/`（`iteration-1/` 下 3 个 eval、`skill-snapshot/`）
- `miniprogram-ci-workspace/`（`iteration-1/` 下 3 个 eval、`skill-snapshot-SKILL.md`）

### 应移除 —— 安装生成副本/链接（git 跟踪、工作区已删除，清理时用 `git rm` 固化删除）

- `.agents/skills/miniprogram-automation/`（2 个普通文件：`SKILL.md`、`evals/evals.json`）
- `.agents/skills/miniprogram-ci/`（2 个普通文件：`SKILL.md`、`evals/evals.json`）
- `.claude/skills/miniprogram-automation`（符号链接 → `../../.agents/skills/miniprogram-automation`）
- `.claude/skills/miniprogram-ci`（符号链接 → `../../.agents/skills/miniprogram-ci`）
- `.codebuddy/skills/miniprogram-automation`（符号链接 → 同 `.claude` 指向的 `.agents` 目标）
- `.codebuddy/skills/miniprogram-ci`（符号链接 → 同 `.claude` 指向的 `.agents` 目标）

### 应移除 —— 锁文件条目

- `skills-lock.json`：含 `miniprogram-automation` 与 `miniprogram-ci` 两条（`source: /Users/whincwu/WeChatProjects/wechat-miniprogram-skills`，local）。工作区已整文件删除；若仅清小程序条目则删这两项，若全部安装副本均不保留则整文件删除（其中 `commit-work`、`crafting-effective-readmes`、`implement-tmux` 为非小程序条目）。

### 应移除 —— 配置/文档引用

- `CODEBUDDY.md` 第 3 行（`miniprogram-demo/` 作为 miniprogram-ci 评测基准）、第 5 行（miniprogram-ci skill 行为规则）→ 删除；第 1/2/4/6 行为通用规则，保留。
- `README.md`：EN 表格第 17-18 行与 ZH 表格第 65-66 行的 `miniprogram-automation`、`miniprogram-ci` 两行；EN 安装命令第 32-33 行与 ZH 第 80-81 行的 `--skill miniprogram-*` → 删除。
- `AGENTS.md`、`docs/agents/domain.md`、`docs/agents/issue-tracker.md`：无小程序引用，无需改动。

### demo 结论

- `miniprogram-demo/` 不在本仓库：历史上是 git 子模块，commit `00229dc` 已移除其引用，无 `.gitmodules`/submodule 配置残留；实际 demo 位于外部仓库 `wechat-miniprogram-skills`。仓库内无该目录可删，仅需清理上述 `CODEBUDDY.md` 引用。

### 应保留 —— 非小程序 skills 与评测资产

- `skills/react-effects/`（含 `evals/evals.json`）、`skills/eli12/`（含 `evals/evals.json`）、`skills/implement-tmux/`（含 `references/`）
- `react-effects-workspace/`（react-effects 的评测 workspace）
- `docs/`、`AGENTS.md`、`.scratch/remove-miniprogram-add-claude-plugin/`（本次任务工作区）

### 实现提醒

- 工作区另有一批与小程序无关的既有删除：`.agents/skills/commit-work/`、`.agents/skills/crafting-effective-readmes/`、`.agents/skills/eli12`、`.agents/skills/implement-tmux`、`.claude/skills/eli12`、`.codebuddy/skills/eli12`、`.codebuddy/skills/implement-tmux`、`.codebuddy/skills/commit-work`、`.codebuddy/skills/crafting-effective-readmes`（均为非小程序安装副本）。清理提交请用精确 `git rm` 路径，避免 `git add -A` 把无关删除一并提交。
