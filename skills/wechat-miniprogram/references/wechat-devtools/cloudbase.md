# 微信云开发：查询、部署和消息推送

处理微信小程序/小游戏云环境、云函数、数据库、存储或消息推送时按需读取。本页基于微信开发者工具 Skill 的 `cloudbase-operator` 与消息推送参考整理，属于通用小程序开发能力。

## 目标、授权与状态

- 按[环境与连接](environment.md)连接当前可用的工具。下文使用工具 schema 的参数名；实际 CLI 选项通过对应工具的 `--help` 核对，不凭驼峰/下划线自动猜选项。
- 固定 `appid + env`，再操作资源。`appid` 可来自用户或已核对的生效项目配置；仅有工程路径时先 `cloud_env_list(project=<绝对路径>)`。若同时传 `appid` 和 `project`，该工具优先采用 `appid`。
- 已明确选择的环境沿用。未明确时先列环境并确认目标，不能以“第一个”“只有一个”或名称像 dev 为由自行选择；不猜测环境 ID。任务已授权且目标、范围明确后继续执行，不对每一步重复聊天确认。
- 部署、修改数据库、上传/删除存储、推送配置变更会影响外部资源。仅在用户已授权的范围内提交，遵守 IDE/工具本身的确认机制；返回 `taskId` 时按[入口的异步规则](index.md)查询原任务。拒绝、确认超时或取消后不重新提交；传输中断、超时而写入结果未知时，先查原任务和目标状态，避免重复写入。
- 身份沿用宿主登录态或本地凭据文件接口。密钥、私钥、登录票据和临时凭据不进入对话、命令参数、源码、日志或模型记忆。不要复制网页会话、底层 CGI 参数或未公开接口绕过 IDE 权限。

## 环境与云函数

| 目的 | 工具 | 关键 schema 参数 |
| --- | --- | --- |
| 列环境 | `cloud_env_list` | `appid` 或 `project`；优先明确 AppID |
| 列云函数 | `cloud_fn_list` | `env`，以及 `appid` 或 `project` |
| 查函数状态 | `cloud_fn_info` | 上述参数和 `names`，后者为逗号分隔的函数名字符串 |
| 完整部署一个函数 | `cloud_fn_deploy` | `appid`、`env`、绝对目录 `path`；可选布尔参数 `remote-npm-install` |
| 增量部署 | `cloud_fn_inc_deploy` | `appid`、`env`、`path`、`file`；`file` 是相对该函数目录的文件或目录路径 |

需要定位既有函数时，先 list，再 info。函数目录名就是部署目标函数名，不把包含多个函数的父目录当作单函数目录。依赖需要云端 npm 安装时开启 `remote-npm-install`，同时核对函数 `package.json`；不能仅凭本地 `node_modules` 存在就认为云端依赖就绪。依赖清单变化时优先完整部署，避免增量文件上传遗漏安装步骤。

部署受理不等于部署完成；以最终任务结果和目标函数状态判断。有授权且需要验证业务行为时，继续检查真实调用、日志及失败路径，不把“函数部署成功”当作整条业务链成功。未开通环境或无权限时报告实际前提，不循环重试。

## 云数据库

以下工具显式传 `appid + env`，再指定集合。读取先使用窄条件、必要字段和限量结果，避免把无关用户数据带入上下文。

| 工具 | action / 参数 |
| --- | --- |
| `cloud_db_read_struct` | `action`: `listCollections`、`describeCollection`、`checkCollection`、`listIndexes`、`checkIndex`；按操作填 `collectionName`、`indexName`，可用 `limit`、`offset` |
| `cloud_db_read_doc` | `collectionName`；可选 `query`、`projection`、`sort`、`limit`、`offset`。`sort` 是数组，例如 `[{"key":"createdAt","direction":-1}]` |
| `cloud_db_write_struct` | `action`: `createCollection`、`updateCollection`、`deleteCollection`；`collectionName`；更新时 `updateOptions` 使用 `CreateIndexes`/`DropIndexes`，其内部结构以实际帮助为准 |
| `cloud_db_write_doc` | `action`: `insert`、`update`、`delete`；`collectionName`。插入用 `documents` 数组；更新/删除用 `query`；更新内容放 `update`，可用 `isMulti` 和更新时的 `upsert` |

先查结构，再读取与目标匹配的文档。更新优先使用 `$set`、`$inc`、`$unset` 等操作符，保留无关字段。更新/删除前明确过滤范围；空过滤条件、多条操作、删除集合或索引不能由工具默认值替用户决定。不要因重试而再次执行非幂等的插入或 `$inc`。

复杂 JSON 参数在本地构造文件，CLI 支持时用 `--query-file` 等 `--*-file` 选项传入；不要在 shell 中拼接未转义的 JSON 或敏感值。文件输入也不意味着可以把凭据写入仓库。

## 云存储

| 工具 | action | 关键参数 |
| --- | --- | --- |
| `cloud_query_storage` | `list`、`info`、`url`、`read` | `appid`、`env`、`cloudPath`；可选 `maxAge` 指定临时链接有效秒数 |
| `cloud_manage_storage` | `upload`、`download`、`delete` | `appid`、`env`、`cloudPath`；upload/download 使用 `localPath`；目录操作使用 `isDirectory` |

先 list/info 核对路径；区分云端路径、Cloud FileID 和本地路径。`download` 会写本地文件，先检查目标路径和已有文件；upload/delete 修改云端。删除目录必须明确目录范围并使用 `isDirectory`，不要误把某文件操作扩成整个前缀删除。

`url` 或上传结果中的临时链接只用于当前任务，不硬编码为永久资源地址，也不写入长期文档；不依据 `publicUrl`、`note` 等提示字段推断永久可访问。业务需要持久标识时使用工具实际返回的 FileID 等支持的标识，并按平台机制取得访问地址。

## 消息推送与客服回复

### 先查询，再配置

| 工具 | 参数与含义 |
| --- | --- |
| `cloud_query_msg_push` | `appid`、`action=list` 查询当前配置，任务针对具体环境时传 `env` 过滤；`action=listSupportedEvents` 查询合法消息/事件约束，可不传 `env` |
| `cloud_manage_msg_push` | 必填 `appid`、`env`、`function_name`、`action`；普通管理动作有 `subscribe`、`unsubscribe`、`setEnable`、`ensureCloudFunctionMode` |
| 按消息类型订阅 | `msg_type` 为 `text`、`image`、`voice`、`video`、`miniprogrampage` 时，不传 `event_types` |
| 按事件订阅 | `msg_type=event`，用 `event_types` 数组显式填写已查询到的目标事件 |
| 启停订阅 | `action=setEnable` 配合 `enable: true/false` |

同一 `(MsgType, Event)` 只能绑定一个云函数，重新绑定会替换原函数；先检查现有绑定及任务影响。**不要使用省略参数的 subscribe 示例**：该工具 `msg_type` 默认是 `event`，省略事件列表可能默认订阅虚拟支付相关事件；客服 text 任务应明确 `msg_type=text`，不能误触发其他业务订阅。

查询时注意 `pushMode`。云托管模式下，已有云函数绑定可能不生效，普通 subscribe/unsubscribe/setEnable 会被拒绝。切换回云函数模式用 `ensureCloudFunctionMode`，但模式切换可能影响现有接收端，须在当前任务授权范围内执行。

所给 schema 还枚举 `ensureContainerMode`、`setContainerCallback`，但没有声明容器回调路径参数。只有实际安装版本的工具帮助明确支持所需参数时才使用，否则走 IDE 消息推送面板；不要猜路径字段。上游提到配置版本冲突时，重新 list 读取状态，核对目标后再决定是否提交；不要编造 schema 未声明的 `version` 参数。

### 客服自动回复的验收

1. 实现接收端云函数与所需依赖。消息推送云函数的返回值不会自动成为客服回复；回复需使用 `cloud.openapi.customerServiceMessage.send`，向本次事件提供的接收对象发送，并在函数 `config.json` 声明 `permissions.openapi` 中的 `customerServiceMessage.send`。调用资格、时限和频率以当前官方能力要求和实际返回为准。
2. 部署目标函数，确认依赖在云端就绪；绑定明确的消息类型/事件。不要把完整用户消息、身份票据或整个回调载荷打印进日志。
3. 小程序按需求提供客服入口，例如 `open-type="contact"`；在合法业务场景中触发真机消息，再核对云端日志和实际收到的回复。没有工具暴露稳定日志查询能力时，在 IDE 云开发控制台的云函数日志中检查，不绕到底层 CGI。
4. 区分函数部署、绑定成功、手机触发、回复送达四项结果。`upload` 仅上传代码包，不自动证明设置体验版、提交审核或正式发布；手机快速预览和二维码路径见[小程序验证](../../SKILL.md)。

报告应保留成功/失败项、目标 `appid + env`、资源名及任务状态；对返回中无关个人数据和临时凭据做过滤。部分成功不能概括为全部成功，未知结果不能写成已回滚。

返回[微信开发者工具入口](index.md)。
