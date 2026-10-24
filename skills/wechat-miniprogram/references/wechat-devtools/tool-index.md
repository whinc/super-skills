# 微信工具索引

只按本次任务定位工具，参数用 `wechatide <toolName> -h` 按 `id` 核对；需要完整 schema 时再读本机已装 `wechatide-skill` 的 `wechatide-tools/references/tools.yaml`。

共 53 个定义，51 个当前工具及两个已废弃工具。此清单不等于本机已具备这些工具。以下参数使用 schema 原字段名；CLI 的连字符形式及复杂 JSON 文件选项以该工具帮助为准，action 的条件必需参数还须查看相应描述。

调用规则、凭据隔离和异步任务见[总入口](index.md)。原注册表将 upload 简称为“发布体验版”，本模块以实际上传结果为准，不将其推断为已设体验版、通过审核或正式发布。

| 工具 id | 用途 | schema 标记的必需/固定字段 |
| --- | --- | --- |
| `check_wechatide_status` | 读取微信开发者工具状态 | 无；仍检查条件参数 |
| `close_project_window` | 关闭项目窗口 | `project` |
| `open_project_window` | 打开项目窗口 | `project` |
| `quit` | 退出工具 | 无；仍检查条件参数 |
| `login` | 触发扫码登录 | 无；仍检查条件参数 |
| `polling_task_result` | 查询异步任务结果 | `taskId` |
| `project_import` | 导入项目到列表 | `project` |
| `share_minicode` | 分享代码片段 | `project` |
| `import_minicode` | 导入代码片段 | `link` |
| `project_list` | 列出已导入项目 | 无；仍检查条件参数 |
| `project_remove` | 从列表删除项目 | `project` |
| `auto_preview` | 推送手机预览 | `project` |
| `build_npm` | 构建 npm | `project` |
| `create_preview_qrcode` | 获取小程序预览二维码 | `project` |
| `upload` | 上传代码包（不等于审核或正式发布） | `project`、`upload-version` |
| `simulator_open_page` | 编译并打开指定页面 | `project`、`page` |
| `simulator_refresh` | 刷新模拟器 | `project` |
| `simulator_get_device` | 查询模拟器机型与可选机型列表 | `project` |
| `simulator_set_device` | 设置模拟器机型 | `project`、`device` |
| `simulator_set_darkmode` | 切换模拟器暗黑/浅色模式 | `project`、`mode` |
| `simulator_popup` | 把模拟器弹出为独立窗口 | `project` |
| `get_simulator_console` | 读取 console | `project`、`command` |
| `get_simulator_network` | 读取 network | `project`、`command` |
| `simulator_screenshot` | 截取模拟器画面 | `project` |
| `get_user_appids` | 获取用户可管理的全部 AppID | 无；仍检查条件参数 |
| `compile_wxml` | 编译 WXML 模板 | `project`、`filePath` |
| `compile_wxss` | 编译 WXSS 样式 | `project`、`filePath` |
| `automation_element_action` | 元素级操作 | `project`、`action` |
| `automation_game_action` | 小游戏画布触摸 | `project`、`action` |
| `automation_evaluate` | 执行运行时代码，可能产生副作用 | `project`、`action`、`fnSource` |
| `automation_generate_script` | 生成 automator 脚本 | 无；仍检查条件参数 |
| `automation_navigate` | 页面导航 | `project`、`action` |
| `automation_page_action` | 页面级操作 | `project`、`action` |
| `automation_runtime_info` | 运行时信息 | `project`、`action` |
| `automation_testaccount` | 测试号及票据；敏感返回值只经安全本地通道处理 | `project`、`action` |
| `automation_viewport_action` | 页面操作 | `project`、`action` |
| `automation_wx_api` | 小程序 API 调试 | `project`、`action`、`method` |
| `debug_clear_cache` | 清理缓存 | `project`、`action` |
| `cloud_db_read_doc` | 读取云数据库内容 | `appid`、`env`、`collectionName` |
| `cloud_db_read_struct` | 读取云数据库结构 | `appid`、`env`、`action` |
| `cloud_db_write_doc` | 修改云数据库内容 | `appid`、`env`、`action`、`collectionName` |
| `cloud_db_write_struct` | 修改云数据库结构 | `appid`、`env`、`action`、`collectionName` |
| `cloud_env_list` | 列出云环境 | 无；仍检查条件参数 |
| `cloud_fn_deploy` | 部署云函数 | `appid`、`env`、`path` |
| `cloud_fn_inc_deploy` | 增量部署云函数 | `appid`、`env`、`path`、`file` |
| `cloud_fn_info` | 查询云函数信息 | `env`、`names` |
| `cloud_fn_list` | 列出云函数 | `env` |
| `cloud_query_storage` | 读取云存储 | `appid`、`env`、`action`、`cloudPath` |
| `cloud_manage_storage` | 修改云存储 | `appid`、`env`、`action`、`cloudPath` |
| `cloud_query_msg_push` | 查询消息推送 | `appid`、`action` |
| `cloud_manage_msg_push` | 管理消息推送 | `appid`、`env`、`function_name`、`action` |

## 已废弃

`project_setting_get` 与 `project_setting_update` 保留在原注册表中只为核对历史接口；不要调用它们编辑配置。按[项目配置](project-config.md)直接读取并修改实际配置文件。

## 场景入口

- 项目创建、导入、窗口、编译、预览、上传：[项目与交付](project-workflows.md)。
- 页面与小游戏操作、截图、console/network、mock：[自动化与调试](automation-debugging.md)。
- 云环境、函数、数据、存储、消息推送：[CloudBase](cloudbase.md)。
- 工具无法调用、协议或安装版本不符：[环境与版本](environment.md)。
