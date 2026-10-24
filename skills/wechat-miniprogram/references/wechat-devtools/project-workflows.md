# 微信项目、编译与预览

基于本机 `wechatide-skill` 的工作流和工具 schema 整理（版本见[环境与版本](environment.md)）。需要调用工具时，先按 [入口](index.md) 与 [环境准备](environment.md) 确认兼容性、身份和调用方式；纯源码编辑不因此依赖 IDE。以下示例中的客户端名与绝对路径需替换为当前环境值，参数以已安装版本的 `--help` 为准。凭据只走环境篇的本地安全通道，不放入命令示例或模型上下文。

## 创建、导入、开窗是不同步骤

| 意图 | 做法与结果 |
| --- | --- |
| 从零建项目 | 创建源码与配置；这一步还没有导入 IDE 或打开模拟器 |
| 查看 IDE 项目列表 | `project_list`；`scope` 可取 `miniprogram`、`other`、`all`，默认主列表也可能包含小游戏 |
| 导入已有目录 | `project_import --project`；仅登记到项目列表，`alreadyImported: true` 也表示成功 |
| 打开项目 | `open_project_window --project`；默认 `liteMode` 只有模拟器；需要编辑器/调试器时用 `--window-mode fullMode` |
| 关闭项目窗口 | `close_project_window --project`；仍保留列表项；不是退出整个 IDE |
| 移除列表项 | `project_remove --project`；不删磁盘源码，但可能关闭该项目窗口；按用户请求范围执行 |
| 导入分享片段 | `import_minicode --link` 下载并登记；检查返回目录里的配置、依赖脚本及网络/文件操作，再开窗执行 |
| 分享片段 | `share_minicode --project` 会对外分享代码；只在分享目标已获授权时执行 |

`--project` 是包含 `project.config.json` 的本地项目绝对路径，不是页面文件或随便选的父目录。Taro/uni-app 项目先遵守 [小程序源码与产物规则](../../SKILL.md)，将 IDE 指向实际微信目标工程，不能修改随后会被框架覆盖的生成文件。

创建原生小程序时，配置 `compileType: miniprogram`，准备 `app.json` 的页面列表、应用文件及目标页面文件；小游戏使用 `compileType: game`、`game.json` 与 `game.js`。目录、入口和模板以用户项目为准。配置合并与私有覆盖见 [项目配置](project-config.md)。

可以先完成不需要账号的本地源码工作。第一次调用需项目身份的 IDE 工具时，使用用户已提供或已确认的 AppID；缺失时用 `get_user_appids --type miniprogram` 查询，小游戏的查询过滤值是 `minigame`，不是配置中的 `game`。列表有多个候选不能自行换用另一个项目身份。云开发还需明确环境，见 [云开发](cloudbase.md)。

```bash
wechatide -c '<clientName>' project_import --project '/absolute/path/to/project'
wechatide -c '<clientName>' open_project_window --project '/absolute/path/to/project' --window-mode fullMode
```

不要因为要预览就额外导入或开窗；预览工具通常可直接处理项目路径。不要重复打开已有窗口。

## 编译与刷新：按实际返回结果判断

| 目标 | 工具与关键参数 | 能证明什么 |
| --- | --- | --- |
| 编译并进入指定小程序页 | `simulator_open_page`：`project`、`page`，可选 `query`、数值型 `scene` | 已触发编译/开页；还需读取错误、当前页或截图确认结果 |
| 重新编译/刷新模拟器 | `simulator_refresh`：`project` | 只证明刷新被触发，工具不返回编译结果 |
| 分析单文件模板/样式编译 | `compile_wxml` / `compile_wxss`：`project`、`filePath` | 对应文件的编译摘要，不代表整包构建、页面运行或真机通过 |
| 构建 npm 产物 | `build_npm`：`project`，可选 `compile-type` | 生成或改动本地 npm 构建产物；不是单纯检查，也不是安装 npm 依赖 |

`filePath` 相对 `miniprogramRoot` 或 `pluginRoot`，例如 `pages/index/index.wxml`，不是相对任意工作目录。单文件工具的 `compileType` 只支持 `miniprogram` / `plugin`。`build_npm` 的字段名是 `compile-type`，此快照枚举也只有 `miniprogram` / `plugin`：不要凭场景文案编造 `--compile-type game`。小游戏通过 `simulator_refresh` 验证；如需其 npm 构建，先确认当前安装版本的实际支持方式。

```bash
wechatide -c '<clientName>' simulator_open_page --project '/absolute/path/to/project' --page pages/index/index --query 'id=1&type=detail'
wechatide -c '<clientName>' simulator_refresh --project '/absolute/path/to/project'
wechatide -c '<clientName>' build_npm --project '/absolute/path/to/project' --compile-type miniprogram
```

`build_npm` 仅在项目依赖或用户目标需要时执行。刷新后仍异常，进入 [自动化与诊断](automation-debugging.md) 采集证据，不连续重复刷新来代替定位。

## 手机预览、二维码、上传

| 目标 | 工具 | 参数与边界 |
| --- | --- | --- |
| 将预览推送到开发者微信 | `auto_preview` | 必填 `project`；可选 `page-path`、`query`、字符串型 `scene`；没有二维码/信息文件的输出参数 |
| 扫码预览 | `create_preview_qrcode` | 必填 `project`；`qr-format` 为 `window` 或 `image`；需要图片文件时可指定 `qr-output`；也支持入口页/参数/场景 |
| 上传代码 | `upload` | 必填 `project`、`upload-version`；可选 `desc`；用户要求预览不等于授权上传 |

```bash
wechatide -c '<clientName>' auto_preview --project '/absolute/path/to/project' --page-path pages/index/index --query 'id=1&type=detail'
wechatide -c '<clientName>' create_preview_qrcode --project '/absolute/path/to/project' --qr-format window
wechatide -c '<clientName>' upload --project '/absolute/path/to/project' --upload-version 1.0.0 --desc '验证后的版本说明'
```

预览成功只说明推送或预览包生成成功。二维码就绪不表示手机已扫码；手机进入首页也不表示目标业务流程已通过。需要真机验收时记录设备、微信环境、入口参数及实际交互结果，沿用 [小程序交付证据](../../SKILL.md)。

官方快照将 `upload` 标为“发布体验版”，整合时按真实结果区分：**上传开发版本、设置体验版、提交审核、正式发布是不同状态**。该工具返回上传成功时，不补写其未证明的后续状态。需要其他发布步骤时，另查当前官方能力并在已授权范围内继续。

任何 `pending + taskId` 都按 [共享异步处理](index.md) 跟踪原任务；未结束前不得重发预览/上传以代替查询。拒绝或取消后停止该操作。超时先查已知任务状态，权限或账号错误先解决身份条件，不能靠连发恢复。

## 项目调用错误

官方工具已校验项目路径与身份，已有明确路径时通常直接调用，按返回错误修复；不把本节变成“每次都完整预检项目”的额外流程。创建项目、分析源码或修改配置仍可正常读取相关文件。

| 错误 | 针对性处理 |
| --- | --- |
| `PROJECT_PATH_NOT_FOUND` | 核对绝对路径是否存在、是否误指源码父目录；新建流程先把目标目录和源码建好 |
| `PROJECT_CONFIG_JSON_ERROR` | 仅检查目标配置的缺失、读取或 JSON 错误；合并修复，保留无关字段；目录明显选错时不要给大型无关目录补造配置 |
| `APPID_ERROR` | 核对有效 AppID 和当前账号权限；用户已提供身份时不另选替代；修正后重试一次，身份条件未变化不循环 |

只有失败原因发生变化且无未完成原任务时才重试。回报错误代码与必要上下文，先脱敏日志；不转储可能携带凭据的原始响应。
