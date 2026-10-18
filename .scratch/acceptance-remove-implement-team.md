# 验收清单：移除 implement-team

日期：2026-10-18 ｜ 变更：删 implement-team skill + ADR-0001/0002，新增 ADR-0005，README/CONTEXT 收敛，本机副本卸载
结果：8/8 PASS（A 组查文档与引用，B 组查分发与本机）

## A 文档与引用

- [x] **A1 PASS** README「Skill 一览」直接平铺 3 条（:5-:9），无三级小标题；3 个链接目标均存在
- [x] **A2 PASS** README:3 首段已无编排表述；全文无 mattpocock 章节
- [x] **A3 PASS** CONTEXT.md 仅「会话交接」「Memory 卫生」两节；AgentTeam/worktree/Ticket 等零命中
- [x] **A4 PASS** ADR-0005 结构与 0003/0004 一致，事实与仓库现状相符；ADR-0001/0002 已删
- [x] **A5 PASS** 白名单（.scratch/、ADR-0004）外零引用

## B 分发与本机

- [x] **B1 PASS** `skills/` 仅 3 个目录；SKILL.md 无自身目录外路径引用
- [x] **B2 PASS** 两个插件 manifest JSON 合法，未硬编码 skill 清单，无需改动
- [x] **B3 PASS** `.codebuddy/skills/` 3 副本与源目录 `diff -r` 完全一致
- [x] **B4 PASS** `skills-lock.json` 仅 3 条且合法；全局四处安装均无 implement-team

## 观察（不影响判定）

- ADR-0005 与本草稿为 untracked，README/CONTEXT 为 unstaged，删除项已 staged；提交时统一 `git add -A` 即可。
