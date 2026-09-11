# 验收测试清单 — retro 硬化（自包含检查 + 打包规则）

日期：2026-09-11 ｜ 变更：C1 自包含 lint + wayfinder token、C2/C3 AGENTS.md Skill packaging、D .gitignore
执行：2026-09-11 由 lint-auditor / docs-auditor 两个并行只读子 agent 完成

状态标记：`[ ]` 待执行 ｜ `[x]` 通过 ｜ `[!]` 失败 ｜ `[N/A]` 不适用

## A. C1 检查有效性 — lint-auditor ✅ 4/4

- [x] **A1** 6 个 eval 脚本全部通过（2 checker exit 0；单测 integration 9+6 / 8+7 全 OK）
- [x] **A2** 负向实验：干净副本 `Ran 9 tests OK`；注入 `docs/...` 引用后 `test_references_stay_inside_the_skill_folder` FAIL（AssertionError match=' docs/'），lint 有效
- [x] **A3** wayfinder checker 的 `.scratch/<effort>/` 为必需 token：临时副本改为"任意目录"后报"缺少协议字段"，exit 1；`test_requires_input_location_convention` 机制验证通过
- [x] **A4** 集成测试用例数：implement 9、wayfinder 8，与预期一致

## B. C2/C3/D 文档与卫生 — docs-auditor ✅ 3/3

- [x] **B1** AGENTS.md 小节陈述与实际一致：marketplace.json source 均为 `./plugins/<group>`；`.codebuddy/skills/` 实存 4 个安装副本；刷新命令在 `.scratch/` 历史中已使用
- [x] **B2** `.gitignore:9` 含 `.DS_Store`，`git check-ignore` 命中；`git status` 不再列出该文件
- [x] **B3** 独立 grep（含阳性对照）确认 `plugins/` 下 6 个 md（4 skill + references）无 `docs/`、`../`、`/Users/`、`/home/` 引用

## 结论

**验收通过**（7 PASS，0 FAIL）。自包含边界现在有自动化回归防线（lint + token），打包规则写入 AGENTS.md，本地安装漂移与 `.DS_Store` 卫生已处理。
