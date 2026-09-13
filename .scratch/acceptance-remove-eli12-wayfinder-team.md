# 验收清单：移除 eli12 与 wayfinder-team

日期：2026-09-13 ｜ 变更：删 2 skill、清 implement-team wayfinder 残留、文档/manifest 更新、ADR-0004、本机安装卸载
提交：待用户自跑 `/commit`（单 commit，消息 `chore: 移除 eli12 与 wayfinder-team skill`）
结果：A/B/C 全组 PASS（3 个只读 Agent 独立核查）

## A 组 — 仓库源码面（Agent: repo-audit）

- [x] **A1** `skills/` 仅剩 `implement-team`、`memory-compact`、`react-effects`；`eli12`、`wayfinder-team` 目录不存在
- [x] **A2** tracked 文件无悬空引用。白名单外的 wayfinder/eli12 命中为零；命中全部落在：implement-team 负向断言与 LEGACY token、`docs/agents/issue-tracker.md:23` 上游 `/wayfinder`、`docs/adr/0001|0002` 历史、`.scratch/` 历史清单
- [x] **A3** `CONTEXT.md` 无 Map 词条；intro 第 3 行与 Ticket 词条为 implement-team 单数表述
- [x] **A4** `README.md` 无两 skill bullet、无空「学习与讲解」分类、intro 与 mattpocock 段准确
- [x] **A5** 两 manifest description 均为 "engineering workflows and web development"，无 "and learning"
- [x] **A6** `docs/adr/0004-remove-eli12-and-wayfinder-team.md` 存在，frontmatter / Considered Options / Consequences 与 0003 逐节对齐
- [x] **A7** implement-team 内 wayfinding/探索命中仅 checker 报错文案一处（豁免）；`test_protocol_ships` 无 sibling 死分支

## B 组 — 安装面（Agent: install-audit）

- [x] **B1** 项目 `.codebuddy/skills/` 仅 3 skill；implement-team 副本 `diff -r`（忽略 `__pycache__`/`.DS_Store`）为空
- [x] **B2** 项目 `skills-lock.json` 仅 3 条记录，无两 skill
- [x] **B3** `~/.agents/skills/`、`~/.claude/skills/`、`~/.codebuddy/skills/` 均无两 skill；上游 `wayfinder` 保留
- [x] **B4** 全局 `~/.agents/.skill-lock.json` 无两 skill 条目，implement-team / memory-compact 条目仍在

## C 组 — 验证面（Agent: verify-audit）

- [x] **C1** `python3 -m unittest test_implement_team_integration test_implement_team_protocol -v` → Ran 19 tests, OK, exit 0；checker exit 0 并打印通过文案
- [x] **C2** `claude plugin validate .` → `✔ Validation passed with warnings`，仅 version/author 两条既有 warning
- [x] **C3** `git status --short` 变更集：D 7（eli12 2 + wayfinder-team 5）+ M 6（两 manifest、CONTEXT.md、README.md、test_implement_team_integration.py、agent-team-protocol.md）+ ?? 2（ADR-0004、本清单），无意外文件

## 已知待办（非 FAIL）

- 全局 `implement-team` 副本来自 GitHub 源（lock 记录旧路径 `plugins/engineering/skills/...`），当前 clone 落后于本地仓库；待本次 commit 推送后跑 `npx skills update -g` 刷新。
