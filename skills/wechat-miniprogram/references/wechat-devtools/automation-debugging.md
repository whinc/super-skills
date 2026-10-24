# 微信自动化与运行时诊断

基于本机 `wechatide-skill` 的工具协议（版本见[环境与版本](environment.md)）。仅当任务需要微信运行证据时使用本页；调用前完成 [环境准备](environment.md)，需要模拟器的操作确认项目窗口已打开。原始工具参数用 `wechatide <toolName> -h` 按 ID 核对。凭据、日志脱敏与未完成异步任务统一遵循 [入口](index.md)。

## 先区分小程序和小游戏

| 工程类型 | 自动化方式 | 不应套用的能力 |
| --- | --- | --- |
| 小程序 `miniprogram` | 页面导航、元素 selector、页面实例状态与截图 | 不使用 `automation_game_action` 操作普通小程序页面 |
| 小游戏 `game` / `gamePlugin` | 画布或截图坐标触摸、截图、受控运行时调用 | 不使用 WXML selector、页面栈、`automation_navigate`、`automation_page_action`、`automation_element_action`、`automation_runtime_info` 或页面脚本生成 |

同一项目的配置类型决定工具路线；不能因为按钮看起来相似就混用。小游戏诊断从截图、可用日志和受控 `wx.*` 查询开始，运行表达式不依赖 `Page` / `getCurrentPages()`。

## 小程序流程验证

先定义可观察结果，再做导航和交互，最后读取页面/元素证据。导航返回成功不是断言通过；直接改 data 得到正确画面，也不能证明用户路径可用。

| 意图 | 工具 | 易错参数或行为 |
| --- | --- | --- |
| 读取当前页、页栈或系统信息 | `automation_runtime_info` | 必填 `action`：`currentPage`、`pageStack`、`systemInfo` |
| 导航 | `automation_navigate` | `action` 可取 `navigateTo`、`redirectTo`、`navigateBack`、`reLaunch`、`switchTab`；按动作传 `url` 或 `delta` |
| 查元素、读页面状态 | `automation_page_action` | `querySelector(All)` 使用 `selector`；`getData` 的 `dataPath` 是 data 字段路径，不是页面路径 |
| 点击、输入、读取元素 | `automation_element_action` | 用 `selector` 与目标 `action`，例如 `tap`、`input`、`text`、`offset`；输入值用 `value`；`style` 必须另配 `name`（CSS 属性名，返回计算值）；`scrollTo` 必须同时给 `x` 和 `y`（横向不动传 0） |
| 滚动页面 | `automation_viewport_action` | `action: pageScrollTo` 和 `scrollTop`；此工具不接受 `tap` / `input` |
| 截图 | `simulator_screenshot` | 可选本地 `path`；返回文件路径和 `imageWidth` / `imageHeight` |

```bash
wechatide -c '<clientName>' automation_runtime_info --project '/absolute/path/to/project' --action currentPage
wechatide -c '<clientName>' automation_page_action --project '/absolute/path/to/project' --action querySelectorAll --selector '.submit-btn'
wechatide -c '<clientName>' automation_element_action --project '/absolute/path/to/project' --selector '.submit-btn' --action tap --wait-for-selector '.submit-btn'
wechatide -c '<clientName>' simulator_screenshot --project '/absolute/path/to/project' --wait-for-selector '.result'
wechatide -c '<clientName>' automation_element_action --project '/absolute/path/to/project' --selector '.title' --action style --name fontSize
wechatide -c '<clientName>' automation_element_action --project '/absolute/path/to/project' --selector 'scroll-view' --action scrollTo --x 0 --y 9999
wechatide -c '<clientName>' automation_evaluate --project '/absolute/path/to/project' --fn-source 'function(){ return wx.getStorageSync("k"); }'
```

`automation_evaluate` 的 `fn-source` 只收**函数源码**（`function(){ ... }`）。表达式、末尾自执行的 IIFE、以括号开头的字面量都会被参数解析拒绝并报 `Arg string terminates parameters early`；要取返回值就在函数体里 `return`。`style` 返回单个属性的计算值字符串，读多个属性要按属性逐个调用。

优先稳定 selector，找不到元素时核对当前页、选择器和渲染条件。`waitForSelector` 在操作前等待；等待导航目标页的结果，应在导航后另读目标元素/截图，不把操作前等待当成结果断言。工具的 `wait` 单位为秒，快照范围 0–10，不能不断加长等待掩盖定位错误。

`tap`、`touch*`、`longpress` 可改用 `x` + `y`，此时不同时传 selector；小程序坐标为视口 CSS 像素。其他动作仍需要 selector。优化后的截图像素不一定等于 CSS 像素，不可直接照搬坐标。坐标控件优先结合元素 `offset` 与实际视口核对。

`automation_generate_script` 从已记录操作生成脚本草稿，其 schema 只有可选的 `includeFailed`、`clearHistory`，不要编造 `project` 入参。生成后检查导入、断言、超时、路径和副作用；坐标触控不保证生成可执行的元素点击。确实需要运行脚本时，复用项目的 `miniprogram-automator` 或按当前包管理器添加所需开发依赖，不无条件执行 `npm install`；运行时可给脚本传项目路径，缺省会使用记录时路径。

## 小游戏坐标操作

先截图确定目标，操作后再截图检查结果；`automation_game_action` 支持 `tap`、`swipe`、`touchstart`、`touchmove`、`touchend`。默认 `coordinateSpace: canvas` 使用画布逻辑坐标。从截图取点时改用 `image`，并带**同一张参考图**返回的宽高，让工具换算，不自行猜缩放比例。

```bash
wechatide -c '<clientName>' simulator_screenshot --project '/absolute/path/to/game'
wechatide -c '<clientName>' automation_game_action --project '/absolute/path/to/game' --action tap --x 240 --y 680 --coordinate-space image --image-width 750 --image-height 1334
```

示例宽高和坐标仅用于说明参数，执行前必须换成当前截图值。`swipe` 使用 `startX` / `startY` / `endX` / `endY`，`duration` 单位毫秒；小游戏没有 selector 等待，只能按当前画面条件安排操作和有限的 `wait`。触摸无响应时先核对坐标空间与截图尺寸，再查日志，不盲目重复点击。

## 最小诊断证据

1. 记录实际工程、基础库/运行环境、问题页面或画布、复现步骤；小程序用 `automation_runtime_info` 读取当前页。
2. 先取相关 console / network 行和必要截图，定位编译、接口、运行时或自动化选择器问题。日志可能包含 Token、请求体与用户信息，优先在本地过滤脱敏后传给模型，避免整段导出。
3. 只根据证据执行恢复动作，回到原步骤复现验证；记录结果与仍缺的证据。模拟器验证不代替手机验证。

```bash
wechatide -c '<clientName>' get_simulator_console --project '/absolute/path/to/project' --command 'grep -i error'
wechatide -c '<clientName>' get_simulator_network --project '/absolute/path/to/project' --command 'grep -i fail'
```

日志工具的 `command` 必须为不带文件名的 grep 表达式，不能传 `all`。返回空字符串只表示没有命中行。确有必要扩大范围时可以使用 `grep -n .`，但仍应控制敏感数据进入上下文。不要拼入来源不可信的 shell 表达式。

`simulator_screenshot` 默认优化为长边 1280 的 JPEG；精确核对像素时可请求 `optimize: false` 获取原始 PNG。先查看实际图片再判断布局，截图路径本身不是视觉验收。截图可产生本地临时文件；需要持久证据时显式选择输出位置。

## 按动作识别副作用

| 工具或动作 | 执行前判断与执行后处理 |
| --- | --- |
| 页面 `getData`、元素文本/样式查询 | 通常只读，但限定读取字段，不批量收集身份、会话等无关数据 |
| `setData`、`callMethod`、点击/输入 | 会改状态或触发业务请求；`setData` 的 `patch` 是 JSON 字符串，不能当真实交互验证 |
| `automation_evaluate` | `fnSource` 是会执行的函数源码，不是纯查询；先读代码，按其网络、数据和文件等实际影响判断；不执行不可信源码 |
| `automation_wx_api` | `call` 的效果取决于 API；`mock` 改行为，测试后对同一 `method` 执行 `restore`；记录哪些结果来自 mock |
| `automation_testaccount` | `getTicket` 会返回敏感登录票据；不能为诊断随意获取。`setTicket` / `refreshTicket` 改登录上下文，处理走 [凭据约定](environment.md) |
| `debug_clear_cache` | 必填具体 `action`；按原因最小化清理，先保存证据；`clearAuth` / `clearSession` / `cleanStorageCache` 会影响身份或本地数据，不默认 `cleanAll` |
| viewport 的 `remote` / `close`、退出 IDE | 会开启真机调试或关闭工具，不夹带在普通截图/读取步骤中 |

测试账号、模拟请求及真实后端要标清；任何可能提交订单、发送消息、改云数据的点击或 API 调用仍遵守用户授权范围。出现平台确认弹窗或未完成任务，按 [共享异步处理](index.md) 保留原 `taskId`；不要通过改用脚本、反复点击或重发工具绕过确认。
