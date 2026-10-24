# 微信开发者工具：版本、入口与运行环境

本页适配 `wechatide-skill` **0.3.14**（2026-10-24 核对），用于调用微信开发者工具的新 `wechatide` 工具接口。它不是本 skill 的整体依赖：写代码、调整本地配置、静态检查与不依赖 IDE 的测试可以继续，只有对应的 IDE 操作受环境缺口阻塞。业务流程见[微信小程序](../../SKILL.md)。

## 版本要求：区分原安装提示、本包门槛和协议版本

| 项目 | 本次核对结果 | 使用方式 |
|---|---|---|
| 用户提供的安装说明 | Nightly Electron Build **2.02.2607032 及以上** | 是本次参考的原始要求；不能用它替代当前本包的更高检查门槛 |
| 上游 0.3.14 的安装检查 | `install-root.mjs` 的 `MIN_COMPATIBLE_VERSION` 为 **2.02.2607152**；`check-installation.mjs` 接受等于或高于该值的 Electron 版，且还要求 CLI 可用 | 仅版本号达标不代表登录、协议和每个工具均可用 |
| 上游 0.3.14 的下载选包 | `resolve-download.mjs` 仅选择**严格大于 2.02.2607152** 的包 | 新安装或兼容修复按此筛选；兼容修复优先符合门槛的 Nightly |
| 本模块适配的 Skill 协议版本 | **0.3.14**（上游根 `SKILL.md` 与 `skill.yaml` 一致） | `check_wechatide_status --skill-version` 必须传此值，与本 skill 自身版本无关 |

更新环境前从[官方下载页](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)和[Nightly 更新日志](https://developers.weixin.qq.com/miniprogram/dev/devtools/log#nightly)核对当时提供的版本、系统与架构。这里记录的是所提供 0.3.14 包的实际要求，不宣称它是官网永久门槛。若新版官方资料提高要求，先核对变更再更新本模块，不只改版本字符串。

上游选包规则中版本末位 `0 / 1 / 2` 分别指稳定版 / RC / Nightly。普通安装优先满足门槛的稳定版；缺少时上游按 RC、Nightly 回退，应说明实际渠道。现有 RC 已明确缺少所需接口，或 `agent_ahead` 后出现明确工具/参数不兼容时，转符合门槛的 Nightly；开启旧 CLI 端口不能代替此接口升级。不要猜测或拼接安装包 URL。

## 首次接入与命令不可用

本适配**没有打包上游 installer 脚本**；`skills/installer/scripts/*` 在本 skill 里不存在，安装辅助按官方下载入口处理。首次准备调用新接口，或调用失败显示命令不可用时，使用宿主可用的只读检查确认以下事项；不能仅因加载本 skill 就安装软件。

1. 确认实际安装位置。macOS 常见路径是 `/Applications/wechatwebdevtools.app`；自定义路径以用户/宿主已知信息为准，默认目录不存在不等于未安装。Windows 同样核对实际安装目录。
2. 区分运行时与版本。macOS 的旧 NW.js 标记是 `Contents/Resources/package.nw/package.json`，Electron 版本来自 `Contents/Resources/app.asar.unpacked/package.json`；Windows 对应 `code/package.nw/package.json` 与 `resources/app.asar.unpacked/package.json`。只读取所需版本字段，不转储安装目录和配置。旧 NW.js 不支持本适配；不要因工具名称相同而继续发送新接口调用。
3. 确认新入口：macOS 为 `<App>/Contents/MacOS/wechatide`，Windows 为 `<安装目录>/wechatide.cmd`。旧 `cli`、`cli.bat`、`wechatidecli` 不是同一个协议，不能作为命令的直接替身。旧流程可按其自身文档另行使用，但证据与参数必须分开。
4. PATH 找不到而安装目录入口可用时，优先使用已确认的绝对路径；不因此重新下载安装。上游软链脚本会写 `/usr/local/bin`、`~/.local/bin`、shell rc 或 Windows 用户 PATH；本模块不自动执行这些修改。
5. 只有任务确实需要 IDE 且安装缺失/不兼容，才说明具体缺口并按用户授权处理下载或安装。只要求下载时不运行安装包。按官方包选择实际系统与架构；上游 macOS 安装流程要求 `.pkg`。既有 DMG 安装若版本和入口合格，不因格式本身要求重装。Linux/无桌面环境不假装有受支持的桌面包。

`wechatide` 需要可访问本机桌面的执行环境。若宿主沙箱阻断该访问，遵循宿主权限机制；不能自行绕过隔离，也不要反复重试同一条不可用路径。继续能独立完成的代码工作，并列明待在桌面环境执行的验证。

## 每会话的状态检查

本会话首次使用这些 IDE 业务工具前检查一次。`<clientName>` 使用真实宿主产品名称，并保持与授权弹窗一致；命令参数和路径按宿主 shell 正确引用。

```text
wechatide -c <clientName> check_wechatide_status --skill-version 0.3.14
```

若 PATH 尚未就绪，用已确认的 `wechatide` 绝对路径替换命令名。上例不含凭据；如果入口启用了认证，按下一节用宿主安全配置处理。参数变化先查该已安装工具的帮助，不猜工具名或添加不存在的参数。

按**调用是否成功 → 协议版本关系 → 登录状态 → 对应入口认证**判断。通常 `equal` 或 `agent_ahead`、`loginExpired: false` 且该入口认证满足时才能继续；未知字段或检查失败不能推断成功。

| 返回/现象 | 处理 |
|---|---|
| `versionRelation: skip_check` | 补传上游协议版本 `0.3.14`；不能把跳过检查当作就绪 |
| `equal` | 继续核对登录与入口认证 |
| `agent_ahead` | 记录本模块可能领先 IDE 的具体兼容风险；其余条件满足可继续。仅出现缺工具/参数等明确兼容故障时再建议升级，不能凭此字段反复安装 |
| `agent_behind` | 返回的 `skillPath` 只作为更新资料来源；读取新版本接口与变更，更新本模块适配后重查。更新落在本 skill 目录内，IDE 安装目录保持原样，`--skill-version` 保持真实值。协议相关操作等适配完成，纯代码任务照常继续 |
| `loginExpired: true` | 使用官方登录流程并让用户完成扫码，成功后重查。不要读取登录票据或扫描本地认证文件 |
| `success: false` 且 `loginExpired: false` | 记录脱敏后的网络/状态失败，有限重试；不直接认定登录过期，也不立刻反复登录 |
| 命令不存在、入口不可执行、运行时或版本不兼容 | 回到上面的安装/入口诊断；明确卡在何处 |

同一会话、同一有效环境成功检查后，各业务步骤复用结果；登录失效、IDE 更新/重启、连接改变或明确兼容错误时再核对，不在每次编译前重复检查。保留项目绝对路径、非敏感状态和待处理任务编号；不要把认证数据写进交接记录。

## CLI 与 MCP 凭据分别处理

客户端名称授权、CLI 可选令牌、MCP Token 是不同检查，不能互相替代。

| 入口 | 上游 0.3.14 的规则 | 本适配的处理 |
|---|---|---|
| `wechatide -c` / skill-call | 未启用 CLI 令牌时不验令牌；仅 `cliTokenRequired: true`、兼容字段 `tokenRequired: true` 或 `cli_token_required` 时需要 | 不因为 `mcpTokenRequired: true` 阻止无令牌的 CLI 调用；确实要求令牌时，使用宿主安全配置或本地程序在进程内从凭据文件读取 |
| `wechatide mcp` / Inspector / MCP HTTP | 独立 MCP Token 必需；来自开发者工具「设置 → 安全」复制的 MCP 配置 | 用户在宿主安全配置界面完成配置；不得将配置中的 Token 发给模型。`mcp_token_invalid` 时更新该配置，不用 CLI 令牌代替 |

**凭据只存在于宿主安全配置或本地凭据文件。** 上游“让 Agent 记住 CLI Token”的要求在本模块不适用：对话、记忆、仓库、报告和命令文字只出现路径与状态。实际值由宿主已提供的安全认证通道传递，或由本地程序在进程内读取；工具选项按实际能力描述，`--token-file` 之类参数以该工具帮助为准。

本模块未提供凭据包装器。当前工具要求令牌而宿主安全通道/本地凭据程序尚未配置时，准确报告缺少哪个入口的认证接入，该入口暂停到认证接入就绪；不依赖该认证的项目工作照常继续。

## 完成环境接入时记录什么

只报告已确认的 IDE 版本、运行时、入口路径、协议版本关系、登录/认证是否就绪，以及执行成功的具体操作。区分“版本字段达标”“状态检查通过”和“预览/自动化实际成功”；任何一层都不能替代下一层，更不能充当手机真机验证。
