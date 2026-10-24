# 微信项目配置：共享文件与本机覆盖

修改 AppID、源码目录、基础库、编译设置、域名校验或 npm 打包关系时读取。本页依据用户提供的微信开发者工具 Skill 中 `project-config` 场景和字段表整理；具体支持范围以当前开发者工具与[官方项目配置文档](https://developers.weixin.qq.com/miniprogram/dev/devtools/projectconfig.html)为准。

## 直接修改文件

这类任务使用本地文件工具即可，不需要调用 `wechatide`，也不需要为了编辑 JSON 检查安装、启动 IDE 或登录。不要使用已废弃的配置读写工具。随后确实需要编译、预览或上传时，再按[环境与连接](environment.md)准备工具。

1. 在工程根目录找到 `project.config.json`，同时检查是否存在 `project.private.config.json`。框架项目还要确定生成配置的来源，避免下次构建覆盖修改。
2. 理解共同字段和 private 覆盖后的实际值，尤其是 `appid`、基础库、`setting`。私有文件中已有的同名设置优先；不能只读共享文件就判断生效环境。
3. 按下表选择文件，合并所需字段并保持合法 JSON，保留无关字段与用户修改。不要重写整个配置为示例模板。
4. 检查私有覆盖是否令修改失效，说明修改的文件、字段和需重新编译/打开项目的事项。只改配置不等于已经验证运行结果。

| 文件 | 写入内容 | 处理原则 |
| --- | --- | --- |
| `project.config.json` | 团队共享设置，以及影响编译、上传产物的配置 | 产物开关写这里；不要用本机 private 文件代替团队配置 |
| `project.private.config.json` | 当前机器的调试和开发偏好 | 同名字段优先；不存在且任务确实需要本机设置时才创建 |

## 常见 `setting` 字段

以下名称均位于 `setting` 内，不要误写成顶层字段。上游要求 `es6` 与 `enhance` 同开同关；遇到已有项目刻意采用不同配置时先核对工具版本和构建约定，不顺手改动。

| 目的 | 文件 | 字段与值类型 |
| --- | --- | --- |
| 合法域名和 TLS 检查 | private | `urlCheck: boolean` |
| 保存后热重载 | private | `compileHotReLoad: boolean` |
| Skyline 调试 | private | `skylineRenderEnable: boolean` |
| 预览/真机调试的包体积支持 | private | `bigPackageSizeSupport: boolean` |
| 体验评分、开发期文件与质量检查 | private | `autoAudits`、`ignoreDevUnusedFiles`、`ignoreCodeQuality`，均为 boolean |
| API Hook 与 JSON 错误显示 | private | `useApiHook`、`checkInvalidKey`，均为 boolean |
| ES6 和增强编译 | common | `es6`、`enhance`，均为 boolean |
| 上传时压缩 | common | `minified`、`minifyWXSS`、`minifyWXML`，均为 boolean |
| 样式自动补全、SWC、上传过滤 | common | `postcss`、`swc`、`ignoreUploadUnusedFiles`，均为 boolean |
| sourcemap 与代码保护 | common | `uploadWithSourceMap`、`uglifyFileName`，均为 boolean；按项目调试/发布要求选择 |
| 编译插件 | common | `useCompilerPlugins: string[]`，例如 `["typescript", "less"]`；关闭为 `false` |
| 手动 npm 构建映射 | common | `packNpmManually: boolean` 与 `packNpmRelationList: object[]`；后者仅在前者为 true 时生效 |

此处的 common 指共享配置。仅修改与任务相关的字段；例如安装 npm 依赖失败，不应靠关闭质量检查解决。

## 路径、身份和基础库

这些通常是共享配置的顶层字段：

| 字段 | 核对内容 |
| --- | --- |
| `appid` | 应用标识；若 private 已配置，核对覆盖后的真实目标。它不是 AppSecret，不能替换别的 AppID 来绕过权限错误 |
| `compileType` | `miniprogram`、`plugin` 或 `game`，与当前工程一致 |
| `miniprogramRoot` | 相对工程根目录的小程序源码位置；未配置时为工程根目录。定位 `app.json`、页面和组件后再改 |
| `pluginRoot` | 插件源码目录；用于 `compileType=plugin` |
| `cloudfunctionRoot`、`cloudbaseRoot` | 对应云函数/CloudBase 工程根目录；仅修改路径不会自动开通环境或部署 |
| `libVersion` | 基础库版本；上游记录 `latest`、`trial`、`widelyUsed` 这三个别名写在 private 无效。复现问题时记录实际解析出的基础库版本 |
| `packOptions` | `ignore`/`include` 打包规则，include 优先；修改后可能需要重开工程 |
| `watchOptions.ignore` | 不展示/监听的 glob 列表；修改后需要重开工程 |
| `scripts.beforeCompile`、`scripts.beforePreview`、`scripts.beforeUpload` | IDE 对应动作前执行的本地 shell 命令；先检查已有脚本实际行为，再决定是否触发该动作 |

`packOptions.ignore/include` 的规则项包含 `type` 与 `value`。上游列出的 `type` 为 `folder`、`file`、`suffix`、`prefix`、`regexp`、`glob`；路径规则相对 `miniprogramRoot`，不能误按仓库根目录解释。复杂 npm 映射、Babel 等对象结构按现有配置和当前官方文档填写，不从字段名猜结构。

## 调试开关不是线上能力

- `urlCheck=false` 只改变开发工具的校验行为，不会配置小程序后台合法域名，也不能证明手机的网络请求、证书或 TLS 已通过。
- `skylineRenderEnable=true` 是调试开关，不能代替应用/页面渲染配置、基础库兼容检查及手机验证。
- `bigPackageSizeSupport` 不能作为正式上传或平台包体积要求已满足的证据。
- AppID、云目录、基础库或编译开关写入成功，只证明配置已修改。后续按[小程序验证](../../SKILL.md)区分构建、模拟器、预览二维码和真机结果。
- 不在配置文件、脚本、文档或日志中填入 AppSecret、上传私钥、登录凭据；需要身份时通过已有宿主登录态或本地程序接受的凭据文件路径处理，不读回对话。

返回[微信开发者工具入口](index.md)。
