# 07: 验证完整分发路径与最终清理

**What to build:** 以用户实际使用的分发入口验证最终仓库：Skills CLI 能发现并安装三个保留 skills，Claude Code plugin/marketplace metadata 能通过校验，且小程序内容和意外改动均已清除；输出可复核的验证证据。

**Blocked by:** 04: 移除小程序内容并收紧仓库支持范围; 05: 添加 Claude Code plugin 与 marketplace manifests; 06: 更新中英文 README 安装文档

**Status:** done

- [x] Skills CLI 本地 discovery 只发现三个保留 skills。
- [x] `npx skills add . -a codebuddy --yes` 完成且未安装任何小程序 skill。
- [x] Claude Code plugin validation 报告 manifest 有效；验证记录包含警告输出而非只记录退出码。
- [x] 从 Git 版本控制的用户可见内容中搜索不到残留的 `miniprogram` 引用。
- [x] 三个保留 skills 及非小程序评测资产仍存在且未被无关修改。
- [x] Git diff、暂存边界和工作区状态确认只包含本 feature 的预期变更。
- [x] Marketplace 端到端安装未在未推送提交上执行，作为外部 Git 源环境限制记录，不误报为通过。
