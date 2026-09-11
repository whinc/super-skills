# 验收测试清单 — 对外 skills 本地引用自包含化

日期：2026-09-11 ｜ 变更：protocol 移入两个 skill 的 `references/`、删除 ADR 外链、补前置说明
执行：2026-09-11 由 ref-auditor / protocol-auditor / test-runner 三个并行只读子 agent 完成

状态标记：`[ ]` 待执行 ｜ `[x]` 通过 ｜ `[!]` 失败 ｜ `[N/A]` 不适用

## A. 对外引用自包含性 — ref-auditor ✅ 5/5

- [x] **A1** `plugins/` 全部文件中不再出现仓库根路径引用（`docs/`、`docs/adr/`、`docs/agents/`）。附注：gitignored `__pycache__/*.pyc` 内嵌旧串，不随包、不在 tracked 范围
- [x] **A2** 两份 `SKILL.md` 引用的 `references/agent-team-protocol.md` 在各自 skill 目录内实际存在（5.5K，同 sha）
- [x] **A3** `docs/adr/0001-...md` 中更新后的 protocol 路径实际存在
- [x] **A4** 前置说明各自独立且无交叉：implement-team 只提 `/implement`，wayfinder-team 只提 `/wayfinder`；两者均有 `.scratch/` 输入约定。初检 FAIL（wayfinder 未含 `.scratch/`），补 `.scratch/<effort>/` 后复验 PASS
- [x] **A5** 全仓库（排除 `.git`、`.codebuddy/`）仅 `.scratch/` 历史记录引用旧路径，`plugins/`、`docs/`、`README.md`、`CONTEXT.md`、`AGENTS.md` 零命中

## B. protocol 内容与副本 — protocol-auditor ✅ 4/4

- [x] **B1** 两份 protocol 副本字节一致（`diff` 空，MD5 均为 `e7752206192d609dfd62dd44de79875d`）
- [x] **B2** protocol 内无不可解析仓库文档标签；与 HEAD diff 仅两处删除 `（ADR-0001）`，无其他语义改动
- [x] **B3** 机制内容齐备：frontier 定义、manifest yaml 块、CONFLICT 豁免（标注仅 implement-team）、context 卫生五条、终态事件硬上限、fail-closed 清单
- [x] **B4** `CONTEXT.md` 术语与路径与 protocol 一致，无矛盾

## C. evals 与渠道自包含 — test-runner ✅ 4/4

- [x] **C1** 6 个 eval 脚本全部通过（2 checker exit 0；单测 6/8/6/7 OK）
- [x] **C2** 模拟 skills CLI 单装：仅复制单个 skill 目录到临时目录，`references/` 引用可解析，无 `docs/`、`../`、绝对路径依赖；临时副本内 evals 亦全过
- [x] **C3** 6 个 eval 的 REQUIRED token 均已改为 `references/agent-team-protocol.md`，无旧 token 残留
- [x] **C4** 两份 SKILL.md frontmatter 完整，Steps 编号连续（implement 1-6、wayfinder 1-5）

## 结论

**验收通过**（13 PASS + 1 复验修复，0 FAIL）。两个对外 skill 已自包含，单装任一 skill 不再依赖仓库内文件。

遗留说明：本机 `.codebuddy/skills/` 为 c885b93 之前的旧安装副本（gitignored），与当前源不一致；如需本地加载最新版本，重新执行 skills CLI 安装或更新。
