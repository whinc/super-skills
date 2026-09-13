# 验收测试清单 — 单 plugin 目录重构（skills 顶层化）

日期：2026-09-13 ｜ 变更：skills 提升到顶层 `skills/`、三分组归一 `super-skills`、`.claude-plugin/` 收敛 marketplace.json + plugin.json
执行：2026-09-13 静态检查 + docs-auditor / structure-auditor 两个并行只读子 agent

状态标记：`[ ]` 待执行 ｜ `[x]` 通过 ｜ `[!]` 失败 ｜ `[N/A]` 不适用

## A. 静态结构 ✅ 4/4

- [x] **A1** `claude plugin validate .` 通过（exit 0；2 warnings：无 version 符合决策，无 author 为可选补全）
- [x] **A2** 顶层 `skills/` 恰含 5 个 skill（各含 SKILL.md）；旧 `plugins/` 已移除
- [x] **A3** 全仓 grep `plugins/` 无功能性残留（唯一命中为 ADR-0003 被否决选项举例；`"plugins"` 为 marketplace schema 必需键）
- [x] **A4** 两个 manifest 正确：plugins 数组单条、`source: "./"`、无 renames、name 均 super-skills、无 version

## B. 行为验证 ✅ 2/2

- [x] **B1** implement-team 19 tests + checker exit 0；wayfinder-team 18 tests + checker exit 0（sibling 副本同步断言在移动后成立）
- [x] **B2** `npx skills add . -a codebuddy --yes`：发现并复制 5 个 skill；`diff -r --exclude=__pycache__ skills .codebuddy/skills` 无差异

## C. 人工步骤（用户执行）

- [ ] **C1** 本机首次安装（已核查：`~/.claude`、`~/.codebuddy` 均无旧 plugin 记录，无需卸载）
  ```
  /plugin marketplace add whinc/super-skills
  /plugin install super-skills@super-skills
  ```
- [ ] **C2** `/commit`（用户自跑；3 个 untracked 文件需一并纳入：`.claude-plugin/plugin.json`、`docs/adr/0003-single-plugin-layout.md`、本清单）

## 结论

**A/B 全部通过（6 PASS，0 FAIL）**，另经两个独立只读子 agent 交叉核查：文档一致性 5/5 PASS（含 README 链接、安装命令、ADR 陈述、AGENTS.md 打包表述）；结构与分发产物 7/7 PASS（含 manifest 合法性、skill 自包含、协议副本全等、本地安装副本逐字节一致、git 变更清单）。无遗留缺陷；待用户执行 C 组。
