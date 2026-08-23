Type: research
Status: resolved

## Question

核实 Claude Code plugin 与 marketplace 的官方 manifest 约束：确认 `.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json` 能否在同一仓库共存，marketplace 条目使用 `source: "./"` 时所需字段、插件名称与 marketplace 名称的安装命令，以及不设置 `version` 时 Git commit 自动更新的实际规则。输出实现时必须满足的字段和 README 中必须说明的限制。

## Comments

## Answer

研究基于 Claude Code 官方文档（一手来源）：
- Plugins reference: <https://code.claude.com/docs/en/plugins-reference>
- Create and distribute a plugin marketplace: <https://code.claude.com/docs/en/plugin-marketplaces>

### 1. `plugin.json` 与 `marketplace.json` 是否能在同一仓库共存

**可以，这是官方推荐的标准结构**（marketplace 文档 walkthrough 结构）：

```
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json      # 市场清单（市场根目录）
└── plugins/
    └── quality-review-plugin/
        ├── .claude-plugin/
        │   └── plugin.json   # 插件清单（插件根目录）
        └── skills/
            └── quality-review/
                └── SKILL.md
```

- `marketplace.json` 位于**市场根目录**的 `.claude-plugin/`（"marketplace root" = 包含 `.claude-plugin/` 的目录；路径相对市场根解析，非相对 `.claude-plugin/`）。
- `plugin.json` 位于**每个插件自身根目录**的 `.claude-plugin/`。
- 插件根目录的 `.claude-plugin/` 内**只能放 `plugin.json`**；`commands/`、`agents/`、`skills/`、`hooks/` 等组件目录必须在插件根目录，不能放进 `.claude-plugin/`。
- `plugin.json` manifest 本身是**可选**的（省略时按目录结构自动发现、从目录名派生插件名）；`marketplace.json` 是市场必需。
- 若整个仓库同时作为市场和单一插件（`source: "./"`），根 `.claude-plugin/` 需同时容纳两个 manifest；官方文档未给出该双文件同目录的示例，最稳妥的做法是采用上方"根放 marketplace.json、插件放子目录"的结构。

### 2. `marketplace.json` 必填字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | kebab-case、无空格的市场标识符；用户安装时可见（`/plugin install <plugin>@<marketplace>`）。同名注册会替换旧的 |
| `owner.name` | 是 | 维护者名称 |
| `plugins` | 是 | 插件条目数组 |
| `owner.email`/`owner.url` | 否 | 联系信息 |
| `description`/`version` | 否 | 也可放在 `metadata` 下（向后兼容） |

### 3. 插件条目（`plugins[]`）必填字段与 `source: "./"`

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | kebab-case、无空格的插件标识符 |
| `source` | 是 | 字符串或对象；相对路径**必须以 `./` 开头**（指向市场根目录内的本地目录，`source: "./"` 即市场根目录本身） |

- 相对路径由 Claude Code 基于市场本地副本解析，仅当市场通过 **git 源**或**本地目录**添加时可用。
- 可选元数据：`description`、`version`、`author`、`homepage`、`repository`、`license`、`keywords`、`skills`、`commands`、`agents`、`hooks`、`mcpServers`、`lspServers` 等。
- 插件条目的 `skills`/`commands` 等路径声明在 `source` 解析到市场根（`"./"`）时会**替换默认 `skills/` 扫描**；其余情况为**追加**到默认扫描。

### 4. `plugin.json` 必填字段

- **`name` 是唯一必填字段**（若提供 manifest）；`description`、`version`、`author`、`homepage`、`repository`、`license` 均为可选。
- 组件目录（`skills/`、`commands/`、`hooks/` 等）位于插件根目录，不入 `.claude-plugin/`。

### 5. 安装命令

```
/plugin marketplace add <source>            # <source>：GitHub owner/repo、git URL、marketplace.json 直接 URL、本地目录
/plugin install <plugin-name>@<marketplace-name>
/plugin validate .                          # 校验当前目录
```

CLI 等价命令：`claude plugin marketplace add <source>`、`claude plugin marketplace list|remove|update`。示例：`/plugin install my-plugin@my-marketplace`。

### 6. 不设置 `version` 时 Git commit 自动更新规则

版本解析顺序（除 `command` 源外）：
1. `plugin.json` 的 `version`
2. `marketplace.json` 插件条目的 `version`
3. **git commit SHA**（对 `github`/`url`/`git-subdir` 源，以及 git 托管市场中的相对路径源）
4. `sha256` digest（`archive` 源）
5. `unknown`（npm 源或不在 git 仓库内的本地目录）

- **两处都省略 `version`** → 走 **Commit-SHA 版本**：版本 = 源解析到的 commit SHA，**源 commit 变化即触发更新**（官方："the simplest setup for internal or actively developed plugins"）。这正是本仓库（活跃开发、git 托管）推荐的模式。
- 若在 `plugin.json` 设置 `version` → 版本被固定，推新 commit 不触发更新，必须手动 bump；`/plugin update` 会报 "already at the latest version"。
- ⚠️ **不要在 `plugin.json` 和 marketplace 条目同时设置 `version`**：Claude Code 总是采用 `plugin.json` 的值且不告警，陈旧版本会掩盖 marketplace 里的版本。
- `command` 源始终以命令产出内容的 hash 作为版本。

### 7. 直接 URL 的限制（README 必须说明）

- 通过**直接 URL** 添加市场时，Claude Code **只下载 `marketplace.json` 文件本身，不会下载仓库/插件文件**。
- 因此插件条目的**相对路径（含 `source: "./"`）无法解析**（相对路径引用的是未下载的远端文件）。直接 URL 添加只适用于插件条目使用 git/url/archive 等非相对路径源的市场。
- 解决方案：在 git 仓库托管市场，用 **git URL**（`github`/`url`/`git-subdir`）添加——git 源克隆整个仓库，相对路径即可用。
- 附加限制（README 可一并说明）：
  - 相对路径**禁止 `../` 引用市场根目录之外**的文件。
  - 插件安装时被**复制到缓存**，无法通过 `../` 引用插件目录之外的文件。
  - git 市场的后台刷新默认禁用 git credential helpers，HTTPS 私有仓库可能无法自动认证。
  - Anthropic 保留了一批市场名（如 `claude-code-marketplace`、`anthropic-plugins` 等），第三方市场不能使用，需避开。

### 实现必须满足的字段（结论）

- 仓库根 `.claude-plugin/marketplace.json`：`name`（kebab-case、避开保留名）、`owner.name`、`plugins[]`（每个条目 `name` + `source`，本仓库用相对路径 `"./..."`）。
- 插件（若需 `plugin.json`）：至少 `name`。
- 均**省略 `version`** 以启用 git commit 自动更新。
- README 安装说明必须注明：通过 git URL 添加市场（不能用直接 URL），安装命令 `/plugin marketplace add <owner>/<repo>` 与 `/plugin install <plugin>@<marketplace>`。
