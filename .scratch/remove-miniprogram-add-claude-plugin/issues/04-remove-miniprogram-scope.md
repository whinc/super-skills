# 04: 移除小程序内容并收紧仓库支持范围

**What to build:** 从仓库中移除已废弃的微信小程序 skills、对应评测 workspace 及用户可见的小程序规则引用，同时保持三个非小程序 skills 和其评测资产可用且未被意外修改。

**Blocked by:** None (can start immediately)

**Status:** done

- [x] 两个微信小程序源 skill 不再存在，两个微信小程序评测 workspace 不再存在。
- [x] 用户可见的项目规则不再包含小程序 demo、CI 或 skill 行为说明。
- [x] `react-effects`、`eli12`、`implement-tmux` 及 `react-effects-workspace` 保持存在。
- [x] 未重新引入已移除的安装副本、符号链接或锁文件。
- [x] 清理范围之外的文件未被修改。
