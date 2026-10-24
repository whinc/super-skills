# 微信工具资料来源与适配版本

本 skill 移植自 [@ake/dev-god](https://skillhub.cn/skills/ake/dev-god) 1.2.4 的小程序模块（`references/miniprogram.md` 与 `references/wechat-devtools/`），2026-10-24 整理。上游模块依据用户提供的 `wechatide-skill` 本地包整合，快照基线为 **0.3.11**；本 skill 对齐本机已安装的 **0.3.14**，工具清单与协议版本按该版核对。协议版本与本 skill 自身版本相互独立，不能把本 skill 的版本传给 `check_wechatide_status --skill-version`。

| 来源 | 本 skill 位置与处理 |
| --- | --- |
| 根入口、environment-readiness、installer 说明和四个安装辅助脚本 | [环境与版本](environment.md)：静态核对兼容条件，没有复制或运行安装脚本 |
| initializer、project-manager、compiler、previewer、create-project-guide、错误指南 | [项目与交付](project-workflows.md)：区分创建/导入/开窗、编译/刷新、预览/上传 |
| automator、debugger | [自动化与调试](automation-debugging.md)：按页面/画布、截图坐标和实际副作用使用 |
| project-config、project-config-fields | [项目配置](project-config.md)：本地共享/private 配置优先级和验证边界 |
| cloudbase-operator、消息推送参考 | [CloudBase](cloudbase.md)：工具与环境绑定、读写区分及未知结果恢复 |
| tool-index | [工具索引](tool-index.md)：53 个定义（含两个废弃配置工具）；原始 `tools.yaml` 未随本 skill 分发，参数用 `wechatide <toolName> -h` 或本机已装 `wechatide-skill` 核对 |
| approval-policy、async-task-polling | [总入口](index.md)：保留工具自身交互与 taskId 规则，继承用户既有授权；凭据由宿主/本地文件隔离，不照搬让模型索取或记住 Token 的条款 |

版本门槛、安装渠道与官方下载入口见[环境与版本](environment.md)；本页只记录来源与适配关系。

这是整合快照，不声称与微信线上最新版本永远同步。新安装的 IDE 若报告适配资料落后，更新本模块资料并重新核对，不要把本 skill 目录或开发者工具安装目录直接覆盖为上游 Skill。

工具 schema 是能力目录，不是授权，不保证本机工具或云账户已就绪；本 skill 没有附带 IDE、云服务账号、上传私钥、登录态或工具安装器。知识文档和 schema 不代表已经成功登录、编译、预览或上传。上游来源未附独立许可证文件；保留来源与协议版本，不据此将第三方内容改标为本项目原创。
