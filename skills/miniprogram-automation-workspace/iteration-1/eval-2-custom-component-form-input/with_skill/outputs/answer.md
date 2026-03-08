# 自定义组件 `form-panel` 内 `input` 的自动化脚本模板

## 前置检查

在跑脚本前，先确认这几个前提：

1. 已安装 `miniprogram-automator`。
2. 微信开发者工具已开启 **CLI / HTTP 调用** 或 **服务端口**。
3. `projectPath` 填的是**微信开发者工具实际打开的目录**，不是机械地写成仓库根目录；如果是 Taro / uni-app / 自定义构建链，往往应填 `dist/`、`build/`、`miniprogram/` 之类的产物目录。
4. 已知目标页面路径，例如 `/pages/form/index`。
5. 如果组件里不止一个输入框，最好准备一个更稳定的组件内选择器，例如 `.phone-input`，不要长期依赖裸 `input`。

## 可复用脚本模板

下面给的是**独立 Node.js 脚本模板**。如果你只是做页面自动化验证，这种形式比默认上 Jest 更直接。

```js
const automator = require('miniprogram-automator')

const CLI_PATH =
  process.env.WECHAT_DEVTOOLS_CLI ||
  '/Applications/wechatwebdevtools.app/Contents/MacOS/cli'
const PROJECT_PATH =
  process.env.MINIPROGRAM_PROJECT_PATH ||
  '/absolute/path/to/devtools-project'
const TARGET_PAGE =
  process.env.MINIPROGRAM_TARGET_PAGE ||
  '/pages/form/index'
const PHONE = process.env.TEST_PHONE || '13800138000'

async function run() {
  let miniProgram

  try {
    miniProgram = await automator.launch({
      cliPath: CLI_PATH,
      projectPath: PROJECT_PATH,
    })

    const page = await miniProgram.reLaunch(TARGET_PAGE)

    // 主同步手段优先用稳定选择器等待；固定等待只做兜底
    await page.waitFor('form-panel')

    // 先拿到组件宿主，再进入组件作用域查内部节点
    const panel = await page.$('form-panel')
    if (!panel) {
      throw new Error('未找到 form-panel 组件')
    }

    // 如果有更稳定的内部选择器，优先改成 panel.$('.phone-input')
    const input = await panel.$('input')
    if (!input) {
      throw new Error('未找到 form-panel 内的 input')
    }

    await input.tap()
    await input.input(PHONE)

    // 给输入后的视图更新留一个很短的兜底等待
    await page.waitFor(100)

    // 方案 A：原生输入框值，优先用 value() / property('value')
    const inputValue = await input.value()
    // 备选：const inputValue = await input.property('value')

    if (inputValue !== PHONE) {
      throw new Error(
        `input.value() 校验失败，期望 ${PHONE}，实际 ${inputValue}`
      )
    }

    // 方案 B：组件实例 data，仅在组件确实把值同步到 data 时再校验
    const panelData = await panel.data().catch(() => null)

    // 这里的 phone 字段只是示例。
    // 如果你的组件把值放在 data.form.phone，就改成对应路径。
    if (
      panelData &&
      panelData.phone !== undefined &&
      panelData.phone !== PHONE
    ) {
      throw new Error(
        `panel.data().phone 校验失败，期望 ${PHONE}，实际 ${panelData.phone}`
      )
    }

    console.log('校验通过')
    console.log({ inputValue, panelData })
  } finally {
    if (miniProgram) {
      await miniProgram.close().catch(() => {})
    }
  }
}

run().catch((error) => {
  console.error(error)
  process.exit(1)
})
```

## 运行方式

先安装依赖：

```bash
npm i miniprogram-automator
```

假设你把脚本保存为 `scripts/test-form-panel-input.js`，可以这样执行：

```bash
WECHAT_DEVTOOLS_CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli" \
MINIPROGRAM_PROJECT_PATH="/absolute/path/to/devtools-project" \
MINIPROGRAM_TARGET_PAGE="/pages/form/index" \
TEST_PHONE="13800138000" \
node ./scripts/test-form-panel-input.js
```

## 验证方式说明

### 1. 验证原生 `input` 的值：优先 `value()`

如果目标节点本身就是原生 `input` / `textarea`，应优先这样读：

```js
const value = await input.value()
// 或
const value = await input.property('value')
```

这是最直接的输入值校验方式，适合断言“用户看到的输入框当前值是不是手机号”。

### 2. 验证组件内部状态：用组件实例的 `data()`

如果你还想确认 `form-panel` 这个自定义组件有没有把手机号同步到内部状态，可以在**组件实例**上读：

```js
const panelData = await panel.data()
```

但这里要注意两点：

- `data()` 更适合验证**组件状态**，不是通用的输入框读值方法。
- 只有当组件实现里真的把手机号同步到了 `data.phone`、`data.form.phone` 等字段时，这个断言才成立；如果组件没有同步，`panel.data()` 没有对应字段并不等于输入失败。

### 3. 实战建议：主断言用 `value()`，状态断言再补 `data()`

这类场景里，推荐这样分工：

- **主断言**：`input.value()` / `input.property('value')`
- **补充断言**：`panel.data()`，用于确认组件内部状态是否同步

不要把“读原生输入框值”和“读组件内部 data”混成一个概念。

## 为什么不能直接用 `page.$('form-panel input')`

原因是：**页面级选择器不能直接穿透自定义组件边界**。

错误示例：

```js
const input = await page.$('form-panel input')
```

正确示例：

```js
const panel = await page.$('form-panel')
const input = await panel.$('input')
```

可以把 `form-panel` 理解成一个组件宿主节点。`page.$` / `page.$$` 只在页面这一层查找，不能直接越过组件边界去拿到组件内部的原生节点；要先拿到组件宿主，再用 `element.$` / `element.$$` 在这个组件作用域内继续查。

所以，这里的关键不是“CSS 写法对不对”，而是**查询作用域不对**。

## 注意事项

1. **等待策略**：优先 `page.waitFor('稳定选择器')` 或 `page.waitFor(() => 条件成立)`，不要把固定 `sleep` 当成主同步手段。
2. **组件内选择器要稳定**：如果 `form-panel` 内有多个 `input`，改用更稳定的类名或标识，例如 `.phone-input`。
3. **`projectPath` 要填对**：它应该是开发者工具实际打开的目录。构建型项目常常不是仓库根目录。
4. **先确认安全设置**：没有开启 CLI / HTTP 调用或服务端口时，`launch()` 很容易失败或超时。
5. **清理动作放进 `finally`**：无论校验成功还是失败，都要确保 `miniProgram.close()` 被调用。
6. **区分 `value()` 和 `data()`**：
   - `value()` / `property('value')`：读原生输入控件当前值
   - `data()`：读自定义组件实例内部状态
7. **输入前注意初始状态**：如果输入框有默认值、格式化逻辑或防抖同步逻辑，断言前要结合页面真实行为决定是否需要先清空、等待一次同步，或改成校验组件 data。
