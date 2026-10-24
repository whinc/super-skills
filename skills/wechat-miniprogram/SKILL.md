---
name: wechat-miniprogram
description: "Implement and verify WeChat Mini Program and Mini Game work: locate source and config, compile, preview and upload, automate pages and canvas, read console/network evidence, and integrate CloudBase. Use when a project has project.config.json, app.json, or WXML/WXSS, or when the user mentions 小程序, 小游戏, 微信开发者工具/wechatide, or building Taro/uni-app into WeChat."
---

# 小程序开发与验证

小程序任务读取本页。先辨别微信、支付宝等目标平台；下述工具流程针对微信，其他平台按其官方工具适配，不能直接套用 `wx.*` API。

## 内置微信开发者工具工作流

需要创建/导入微信项目、编译、预览上传、模拟器自动化、日志截图或云开发时，读取[微信工具入口](references/wechat-devtools/index.md)，再只读相应专题。本 skill 依据微信开发者工具 Skill 的工具协议整理，不要求另外安装原 Skill；协议版本见[环境与版本](references/wechat-devtools/environment.md)。小程序和小游戏都可进入，但页面、画布和构建工具的适用范围按对应参数核实。

这套新接口要求 Electron 版开发者工具；版本门槛、安装渠道与版本关系见[环境与版本](references/wechat-devtools/environment.md)。版本号达标或 GUI 已安装，都只是候选证据，接口是否可用以状态检查为准。缺少这套新接口时，只有依赖它的 IDE 操作暂停；普通源码修改、配置编辑和既有 `miniprogram-ci` 工作流照常继续。

## 找到源码和目标配置

- 原生微信项目检查 `project.config.json`、`miniprogramRoot`、`app.json`、页面/组件和 WXML/WXSS。Taro、uni-app 等先读依赖、构建脚本及框架配置，修改源码再编译到微信目标目录，不直接修补将被覆盖的产物。
- 确认 AppID、基础库、渲染模式、分包、启动页及参数；本地私有配置可能覆盖共享配置，按实际生效值判断。AppID 是应用标识，不等于 AppSecret、上传私钥或登录态；不要复制别的项目身份来消除错误。
- API、组件和隐私权限按基础库及框架版本核实。检查页面/组件生命周期、异步状态更新与卸载清理，事件绑定、返回导航和重复点击。微信端通过不能自动推导 H5 或其他小程序端通过。

## 调试与联调

优先复用可用的微信开发者工具及其 CLI/MCP；先确认安装、登录状态、工具能力和项目路径。没有相应工具时完成源码、类型与构建检查，不虚构模拟器结果。

使用新版 `wechatide` 接口时遵循内置入口的状态检查和异步任务规则；旧 `cli`/`cli.bat` 或 `miniprogram-ci` 不冒充同一命令集。已经可用的旧预览链仍按其自身能力使用。

接口联调分别核对请求参数、身份会话、合法域名/网络条件、后端环境与返回状态。开发者工具关闭域名校验后的成功，不证明手机可用；假数据与真实后端结果分别标明。覆盖任务相关的未登录、失败重试及空数据状态，不能只看页面展示。

## 预览与交付

`miniprogram-ci` 可执行编译相关的预览、上传和 npm 构建，使用前检查项目、AppID、上传私钥文件和后台 IP 配置等实际前提；调用参数查本机版本与官方文档，优先沿用项目设置和打包忽略规则。私钥仅通过文件路径交给本地程序，不读取到对话。

| 已完成动作 | 允许得出的结论 |
| --- | --- |
| 框架构建/静态检查 | 对应检查通过，尚未验证微信运行 |
| 开发者工具启动并操作 | 模拟器中所测路径通过，注明基础库和页面 |
| 成功生成预览二维码 | 可供扫码预览，不代表手机已运行或交互通过 |
| 手机扫码进入目标页并操作 | 记录设备/微信环境及实际验证路径 |
| 上传开发版本 | 上传成功；不等于体验版设置、审核或正式发布完成 |

用户要求手机验证且具备工具时继续到目标页面与交互；需用户扫码时给出二维码文件、入口参数和简短验收步骤，将未执行部分如实保留。一次预览成功不能代替真实接口与运行时验证。

官方入口：[项目配置](https://developers.weixin.qq.com/miniprogram/dev/devtools/projectconfig.html)、[CI 文档](https://developers.weixin.qq.com/miniprogram/dev/devtools/ci.html)、[微信官方 CI 仓库](https://github.com/wechat-miniprogram/miniprogram-ci-dist)、[官方示例工程](https://github.com/wechat-miniprogram/miniprogram-demo)。文档不可访问时，可查官方仓库与本地工具帮助，不能把未读到的内容当作已核实。
