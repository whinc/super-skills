# 用 `miniprogram-automator` 启动微信开发者工具并校验首页标题后截图

## 前置检查项

1. **Node.js 环境可用**
   - 建议 Node.js 16 及以上。
   - 已安装依赖：`miniprogram-automator`。

2. **微信开发者工具已安装，且能拿到 CLI 路径**
   - macOS 常见路径：`/Applications/wechatwebdevtools.app/Contents/MacOS/cli`
   - Windows 常见路径类似：`C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat`

3. **小程序项目路径正确**
   - `projectPath` 必须指向小程序项目根目录。
   - 该目录下通常应能看到 `project.config.json` 等项目文件。

4. **项目能被微信开发者工具正常打开并编译**
   - 首次运行前，建议先手动打开一次，确认没有登录、权限、依赖或编译报错问题。

5. **目标页面路径存在**
   - 本脚本会跳转到：`/pages/home/index`
   - 请确认该页面路径与项目配置一致。

6. **你知道“页面标题”的期望文案和选择器**
   - 脚本里提供了常见标题选择器兜底：`#page-title`、`.page-title`、`.title`、`.nav-title`
   - 如果你的页面标题不是这些选择器，请改成项目里的真实选择器。

7. **输出目录可写**
   - 脚本会把截图保存到当前执行目录下的 `outputs/home-index.png`。

## 完整脚本

将下面脚本保存为例如 `launch-home-check.js`，然后直接用 Node.js 运行。

```js
const automator = require('miniprogram-automator');
const path = require('node:path');
const fs = require('node:fs/promises');

const CLI_PATH =
  process.env.WECHAT_DEVTOOLS_CLI ||
  '/Applications/wechatwebdevtools.app/Contents/MacOS/cli';

const PROJECT_PATH =
  process.env.MINIPROGRAM_PROJECT_PATH ||
  process.cwd();

const TARGET_PAGE = '/pages/home/index';
const EXPECTED_TITLE = process.env.EXPECTED_TITLE || '首页';
const OUTPUT_DIR = path.resolve(process.cwd(), 'outputs');
const SCREENSHOT_PATH = path.join(OUTPUT_DIR, 'home-index.png');

const TITLE_SELECTORS = [
  '#page-title',
  '.page-title',
  '.title',
  '.nav-title',
];

const RENDER_TIMEOUT = Number(process.env.RENDER_TIMEOUT || 10000);
const POLL_INTERVAL = Number(process.env.POLL_INTERVAL || 300);

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getElementText(element) {
  if (!element) return '';

  if (typeof element.text === 'function') {
    const text = await element.text();
    return String(text || '').trim();
  }

  if (typeof element.attribute === 'function') {
    const textAttr = await element.attribute('text');
    if (textAttr) return String(textAttr).trim();

    const valueAttr = await element.attribute('value');
    if (valueAttr) return String(valueAttr).trim();
  }

  return '';
}

async function findTitle(page) {
  for (const selector of TITLE_SELECTORS) {
    const element = await page.$(selector);
    if (!element) continue;

    const text = await getElementText(element);
    if (text) {
      return { selector, text };
    }
  }

  return null;
}

async function waitForTitle(page, timeoutMs) {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    const result = await findTitle(page);
    if (result) return result;

    if (typeof page.waitFor === 'function') {
      await page.waitFor(POLL_INTERVAL);
    } else {
      await sleep(POLL_INTERVAL);
    }
  }

  throw new Error(
    `等待页面标题超时（${timeoutMs}ms）。请检查 TITLE_SELECTORS 是否与实际页面匹配：${TITLE_SELECTORS.join(', ')}`
  );
}

async function saveScreenshot(page, miniProgram, filePath) {
  const errors = [];

  if (page && typeof page.screenshot === 'function') {
    try {
      await page.screenshot({ path: filePath });
      return;
    } catch (err) {
      errors.push(`page.screenshot({ path }) 失败: ${err.message}`);
    }

    try {
      await page.screenshot(filePath);
      return;
    } catch (err) {
      errors.push(`page.screenshot(path) 失败: ${err.message}`);
    }
  }

  if (miniProgram && typeof miniProgram.screenshot === 'function') {
    try {
      await miniProgram.screenshot({ path: filePath });
      return;
    } catch (err) {
      errors.push(`miniProgram.screenshot({ path }) 失败: ${err.message}`);
    }

    try {
      await miniProgram.screenshot(filePath);
      return;
    } catch (err) {
      errors.push(`miniProgram.screenshot(path) 失败: ${err.message}`);
    }
  }

  throw new Error(`截图失败。可尝试升级 miniprogram-automator 或调整截图调用方式。\n${errors.join('\n')}`);
}

(async () => {
  let miniProgram;

  try {
    await fs.mkdir(OUTPUT_DIR, { recursive: true });

    miniProgram = await automator.launch({
      cliPath: CLI_PATH,
      projectPath: PROJECT_PATH,
    });

    const page = await miniProgram.reLaunch(TARGET_PAGE);

    if (typeof page.waitFor === 'function') {
      await page.waitFor(500);
    } else {
      await sleep(500);
    }

    const { selector, text } = await waitForTitle(page, RENDER_TIMEOUT);

    console.log(`命中的标题选择器: ${selector}`);
    console.log(`实际标题文案: ${text}`);

    if (text !== EXPECTED_TITLE) {
      throw new Error(`标题校验失败：期望「${EXPECTED_TITLE}」，实际「${text}」`);
    }

    await saveScreenshot(page, miniProgram, SCREENSHOT_PATH);
    console.log(`截图已保存: ${SCREENSHOT_PATH}`);
  } catch (error) {
    console.error('[automation-error]', error);
    process.exitCode = 1;
  } finally {
    if (miniProgram && typeof miniProgram.close === 'function') {
      await miniProgram.close();
    }
  }
})();
```

## 使用说明

### 1）安装依赖

```bash
npm i -D miniprogram-automator
```

### 2）运行脚本

#### macOS / Linux

```bash
WECHAT_DEVTOOLS_CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli" \
MINIPROGRAM_PROJECT_PATH="/你的小程序项目绝对路径" \
EXPECTED_TITLE="首页" \
node launch-home-check.js
```

#### Windows（cmd）

```bat
set WECHAT_DEVTOOLS_CLI=C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat
set MINIPROGRAM_PROJECT_PATH=D:\your-mini-program
set EXPECTED_TITLE=首页
node launch-home-check.js
```

### 3）执行结果

脚本成功后会完成以下动作：

1. 启动微信开发者工具并打开指定小程序项目
2. `reLaunch` 到 `/pages/home/index`
3. 等待页面标题出现
4. 校验标题文案是否等于 `EXPECTED_TITLE`
5. 将截图输出到 `outputs/home-index.png`

## 注意事项

1. **标题选择器需要按你的项目实际结构调整**
   - 如果页面标题不在 `#page-title`、`.page-title`、`.title`、`.nav-title` 中，直接修改 `TITLE_SELECTORS`。

2. **标题文案默认是“首页”**
   - 如果实际不是这个值，请通过环境变量 `EXPECTED_TITLE` 传入，或直接改脚本常量。

3. **首启微信开发者工具时可能需要人工确认**
   - 例如登录、授权、打开项目、信任弹窗等；这些问题不属于脚本本身逻辑。

4. **如果首页依赖异步接口渲染**
   - 可提高 `RENDER_TIMEOUT`，例如：`RENDER_TIMEOUT=15000`。

5. **截图 API 在不同版本下可能有细微差异**
   - 脚本已经对常见调用方式做了兼容尝试；如果仍失败，优先检查 `miniprogram-automator` 与微信开发者工具版本。

6. **脚本只负责自动化执行与断言**
   - 不会修改你的小程序代码；运行后新增的只有输出目录中的截图文件。
