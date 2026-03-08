# 独立 Node.js 自动化脚本方案

## 1. 我准备怎么做

我会按 `miniprogram-automator` 的独立脚本工作流来组织答案，不默认切到 Jest：

1. 用 `automator.launch({ cliPath, projectPath })` 打开微信开发者工具。
2. 调用 `miniProgram.reLaunch('/pages/home/index')` 进入目标页面。
3. 优先用 `page.waitFor(稳定选择器)` 等待页面渲染完成，再补一个很短的兜底等待。
4. 读取页面标题文案并做断言。
5. 用 `miniProgram.screenshot()` 截图，保存到 `outputs` 目录。
6. 在 `finally` 中关闭会话，避免开发者工具自动化连接残留。

## 2. 前置检查项

在运行脚本前，先确认下面这些条件：

1. **`projectPath` 是微信开发者工具实际打开的目录**  
   不要想当然地写成源码仓库根目录。原生小程序通常是包含 `project.config.json` / `app.json` 的目录；如果你用的是 Taro、uni-app 或自定义构建链，这里往往应该填开发者工具真正打开的产物目录，比如 `dist/`、`build/`、`miniprogram/`。

2. **微信开发者工具 CLI 路径正确**  
   macOS 常见默认值：`/Applications/wechatwebdevtools.app/Contents/MacOS/cli`。

3. **已开启开发者工具安全设置**  
   打开微信开发者工具后，确认：**设置 → 安全设置 → 开启 CLI / HTTP 调用 或 服务端口**。  
   否则常见现象是 `launch` 失败、连接超时、CLI 可执行但自动化会话建不起来。

4. **目标页面路径确认无误**  
   这里脚本会跳到：`/pages/home/index`。

5. **标题选择器稳定且可直接在页面作用域找到**  
   下面脚本默认用 `.page-title` 读取标题。  
   如果你的标题在**自定义组件内部**，不要写成 `page.$('custom-comp .page-title')` 这种跨组件选择器；`page.$` 不能直接穿透组件边界，这时要先拿到组件宿主元素，再用 `element.$()` 继续查。

6. **预期标题文案明确**  
   脚本里把预期值做成了可配置变量 `EXPECTED_TITLE`，运行前改成你的真实标题，比如“首页”或“Home”。

7. **`outputs` 目录可写**  
   脚本会自动创建 `outputs` 目录，并把截图保存到里面。

8. **开发者工具已安装并已登录**  
   如果本机开发者工具还没登录，小程序项目本身就可能无法正常打开。

## 3. 完整脚本

> 建议把下面脚本保存为 `scripts/check-home-title.js`，然后在项目根目录执行。

```js
const automator = require('miniprogram-automator')
const path = require('node:path')
const fs = require('node:fs/promises')

const CLI_PATH =
  process.env.WECHAT_DEVTOOLS_CLI ||
  '/Applications/wechatwebdevtools.app/Contents/MacOS/cli'

const PROJECT_PATH =
  process.env.MINIPROGRAM_PROJECT_PATH ||
  '/absolute/path/to/devtools-project'

const TARGET_PAGE = '/pages/home/index'
const TITLE_SELECTOR = process.env.TITLE_SELECTOR || '.page-title'
const EXPECTED_TITLE = process.env.EXPECTED_TITLE || '首页'
const OUTPUT_DIR = path.resolve(process.cwd(), 'outputs')
const SCREENSHOT_PATH = path.join(OUTPUT_DIR, 'home-page.png')

async function main() {
  let miniProgram

  try {
    await fs.mkdir(OUTPUT_DIR, { recursive: true })

    miniProgram = await automator.launch({
      cliPath: CLI_PATH,
      projectPath: PROJECT_PATH,
    })

    const page = await miniProgram.reLaunch(TARGET_PAGE)

    // 优先等待稳定选择器，固定时间只做兜底
    await page.waitFor(TITLE_SELECTOR)
    await page.waitFor(300)

    const titleEl = await page.$(TITLE_SELECTOR)
    if (!titleEl) {
      throw new Error(`未找到标题元素：${TITLE_SELECTOR}`)
    }

    const actualTitle = (await titleEl.text()).trim()
    console.log('页面标题：', actualTitle)

    if (actualTitle !== EXPECTED_TITLE) {
      throw new Error(
        `标题不符合预期，期望 "${EXPECTED_TITLE}"，实际 "${actualTitle}"`
      )
    }

    await miniProgram.screenshot({
      path: SCREENSHOT_PATH,
    })

    console.log('断言通过，截图已保存：', SCREENSHOT_PATH)
  } finally {
    if (miniProgram) {
      await miniProgram.close().catch(() => {})
    }
  }
}

main().catch((error) => {
  console.error('[automator] 执行失败：', error)
  process.exit(1)
})
```

## 4. 使用说明

### 4.1 安装依赖

如果项目里还没有安装 `miniprogram-automator`，先执行：

```bash
npm install -D miniprogram-automator
```

### 4.2 设置运行参数

建议通过环境变量传入真实配置：

```bash
export WECHAT_DEVTOOLS_CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
export MINIPROGRAM_PROJECT_PATH="/absolute/path/to/devtools-project"
export TITLE_SELECTOR=".page-title"
export EXPECTED_TITLE="首页"
```

其中：

- `WECHAT_DEVTOOLS_CLI`：微信开发者工具 CLI 路径
- `MINIPROGRAM_PROJECT_PATH`：开发者工具实际打开的项目目录
- `TITLE_SELECTOR`：页面标题元素选择器
- `EXPECTED_TITLE`：你希望断言通过的标题文案

### 4.3 执行脚本

把脚本保存为 `scripts/check-home-title.js` 后，在项目根目录执行：

```bash
node scripts/check-home-title.js
```

### 4.4 成功判定

成功时你应该看到类似输出：

```bash
页面标题： 首页
断言通过，截图已保存： /your/project/outputs/home-page.png
```

同时会在当前执行目录下生成：

```text
outputs/home-page.png
```

## 5. 注意事项

1. **等待策略不要只靠固定 sleep**  
   `page.waitFor()` 官方支持三种形式：选择器、函数、毫秒数。这里用了“稳定选择器 + 短暂兜底等待”的组合；如果你的页面依赖异步请求、骨架屏或动画，优先继续增强选择器等待，不要把主同步逻辑退化成纯定时器。

2. **截图只适用于开发者工具模拟器**  
   `miniProgram.screenshot()` 不是截图真机调试画面，运行环境应当是微信开发者工具模拟器。

3. **`page.$()` 不能直接穿透自定义组件边界**  
   如果标题在自定义组件里，应该先取组件宿主，再在组件作用域继续查。例如：

   ```js
   const card = await page.$('home-header')
   const titleEl = await card.$('.page-title')
   ```

4. **`projectPath` 不一定等于仓库根目录**  
   这是自动化脚本最常见的错误来源之一。开发者工具打开的是哪个目录，`projectPath` 就应该指向哪个目录。

5. **清理动作要放在 `finally`**  
   即使断言失败，也要确保关闭自动化连接，避免后续脚本被残留会话影响。

6. **输出目录相对当前执行目录**  
   这里的 `outputs` 是相对于 `process.cwd()` 计算的。通常建议你在项目根目录执行脚本，这样截图会落在项目根目录下的 `outputs/` 中。

7. **常见排障方向**  
   - `launch` 失败：优先检查 CLI 路径、开发者工具登录状态、安全设置是否开启。
   - 页面打开了但选不到标题：优先检查选择器是否稳定、页面是否还在异步渲染、标题是否在自定义组件内部。
   - 截图失败：优先检查是否运行在开发者工具模拟器里，以及 `outputs` 目录是否可写。
