# 回归脚本模板：mock `wx.request` + 监听 `console/exception` + 验证列表页渲染

下面按**独立 Node.js 脚本优先**的方式给出模板。这个场景只是做一次回归验证，先不要急着包成 Jest；等脚本本身跑稳定，再按同样结构迁移到 `beforeAll/afterAll/test`。

## 我准备怎么做

- 用 `miniprogram-automator` 启动微信开发者工具里的小程序
- 在**跳转到列表页之前**用 `miniProgram.mockWxMethod('request', ...)` mock `wx.request`
- 监听 `console` 和 `exception` 事件，收集运行时异常
- 跳到列表页，等待稳定选择器出现，校验列表是否按 mock 数据渲染
- 无论成功还是失败，都在 `finally` 里做清理：**恢复 mock、解绑监听、关闭小程序**

## 前置检查

1. `projectPath` 要写成**微信开发者工具实际打开的目录**，不一定是源码仓库根目录。
2. 确认微信开发者工具已开启 **CLI / HTTP 调用** 或自动化相关安全设置。
3. 确认 CLI 路径正确：
   - macOS 常见值：`/Applications/wechatwebdevtools.app/Contents/MacOS/cli`
4. 确认列表页路径和稳定选择器：
   - 页面路径示例：`/pages/list/index`
   - 列表项选择器示例：`.list-item`
5. 如果列表页是 `tabBar` 页面，把下面的 `reLaunch` 改成 `switchTab`。

## 完整脚本骨架

```js
const automator = require('miniprogram-automator')

const CLI_PATH = process.env.WECHAT_DEVTOOLS_CLI || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli'
const PROJECT_PATH = process.env.MINIPROGRAM_PROJECT_PATH || '/absolute/path/to/devtools-project'
const LIST_PAGE = process.env.MINIPROGRAM_LIST_PAGE || '/pages/list/index'
const LIST_ITEM_SELECTOR = process.env.MINIPROGRAM_LIST_ITEM_SELECTOR || '.list-item'

const MOCK_LIST = [
  { id: 1, title: 'Mock Item A' },
  { id: 2, title: 'Mock Item B' },
]

function createMockRequestResult() {
  return {
    data: {
      code: 0,
      list: MOCK_LIST,
    },
    statusCode: 200,
    header: {
      'content-type': 'application/json',
    },
    cookies: [],
    errMsg: 'request:ok',
  }
}

function attachRuntimeListeners(miniProgram) {
  const consoleEvents = []
  const exceptionEvents = []

  const handleConsole = (payload) => {
    consoleEvents.push(payload)
  }

  const handleException = (payload) => {
    exceptionEvents.push(payload)
  }

  miniProgram.on('console', handleConsole)
  miniProgram.on('exception', handleException)

  const detach = () => {
    if (!miniProgram) return

    if (typeof miniProgram.off === 'function') {
      miniProgram.off('console', handleConsole)
      miniProgram.off('exception', handleException)
      return
    }

    if (typeof miniProgram.removeListener === 'function') {
      miniProgram.removeListener('console', handleConsole)
      miniProgram.removeListener('exception', handleException)
    }
  }

  return {
    consoleEvents,
    exceptionEvents,
    detach,
  }
}

async function installRequestMock(miniProgram) {
  await miniProgram.mockWxMethod('request', (options = {}) => {
    const result = createMockRequestResult()

    Promise.resolve().then(() => {
      if (typeof options.success === 'function') options.success(result)
      if (typeof options.complete === 'function') options.complete(result)
    })

    return {
      abort() {},
      onHeadersReceived() {},
      offHeadersReceived() {},
      onChunkReceived() {},
      offChunkReceived() {},
    }
  })
}

function getConsoleErrors(consoleEvents) {
  return consoleEvents.filter((event) => {
    const level = event?.type || event?.level
    return level === 'error'
  })
}

async function assertListRendered(page) {
  await page.waitFor(LIST_ITEM_SELECTOR)
  await page.waitFor(100)

  const items = await page.$$(LIST_ITEM_SELECTOR)
  if (items.length !== MOCK_LIST.length) {
    throw new Error(`列表项数量不符合预期，期望 ${MOCK_LIST.length}，实际 ${items.length}`)
  }

  const texts = await Promise.all(items.map((item) => item.text()))

  if (!texts[0] || !texts[0].includes(MOCK_LIST[0].title)) {
    throw new Error(`首个列表项文案异常：${texts[0] || '<empty>'}`)
  }

  if (!texts[1] || !texts[1].includes(MOCK_LIST[1].title)) {
    throw new Error(`第二个列表项文案异常：${texts[1] || '<empty>'}`)
  }
}

async function main() {
  let miniProgram
  let mockInstalled = false
  let detachListeners = () => {}

  try {
    miniProgram = await automator.launch({
      cliPath: CLI_PATH,
      projectPath: PROJECT_PATH,
    })

    const { consoleEvents, exceptionEvents, detach } = attachRuntimeListeners(miniProgram)
    detachListeners = detach

    // 关键点：如果页面在 onLoad/onShow 里首屏就发请求，mock 必须先装，再跳页。
    await installRequestMock(miniProgram)
    mockInstalled = true

    const page = await miniProgram.reLaunch(LIST_PAGE)

    await assertListRendered(page)

    const consoleErrors = getConsoleErrors(consoleEvents)
    if (consoleErrors.length > 0) {
      throw new Error(`检测到 console error：${JSON.stringify(consoleErrors)}`)
    }

    if (exceptionEvents.length > 0) {
      throw new Error(`检测到 exception：${JSON.stringify(exceptionEvents)}`)
    }

    console.log('回归通过：mock 数据已渲染，且未捕获 console error / exception')
  } finally {
    // 清理必须放 finally：即使中途断言失败，也要恢复环境。
    detachListeners()

    if (miniProgram && mockInstalled) {
      await miniProgram.restoreWxMethod('request').catch(() => {})
    }

    if (miniProgram) {
      await miniProgram.close().catch(() => {})
    }
  }
}

main().catch((error) => {
  console.error('[regression failed]', error)
  process.exit(1)
})
```

## Mock 与恢复流程

推荐顺序固定为：

1. `launch` 小程序
2. 安装 `console` / `exception` 监听
3. `mockWxMethod('request', ...)`
4. `reLaunch` 或 `switchTab` 到目标列表页
5. 等待页面稳定并做断言
6. 在 `finally` 里执行 `restoreWxMethod('request')`
7. 在 `finally` 里关闭小程序

最关键的是第 3 步要发生在第 4 步之前。否则页面首屏请求可能已经发出，mock 根本接不到。

## 事件监听说明

### `console` 监听

- 用来抓运行时 `console.error`，避免“UI 看起来正常，但实际上有报错”被漏掉。
- 模板里默认只把 `error` 级别当失败；如果你们团队连 `warn` 也要拦，可以把过滤条件扩大。

### `exception` 监听

- 用来抓小程序运行时抛出的异常。
- 一旦有 `exceptionEvents`，模板直接判失败，避免页面碰巧还渲染了但内部已经异常。

## 清理步骤

清理一定要写进 `finally`，不要分散在成功分支里：

```js
finally {
  detachListeners()
  await miniProgram.restoreWxMethod('request').catch(() => {})
  await miniProgram.close().catch(() => {})
}
```

建议保留这三个动作：

1. **解绑事件监听**：避免重复执行脚本时事件堆积。
2. **恢复被 mock 的 wx 方法**：避免后续脚本或手工调试被污染。
3. **关闭小程序实例**：避免开发者工具残留连接占用。

## 运行命令示例

先安装依赖：

```bash
npm i -D miniprogram-automator
```

假设你把脚本保存为 `scripts/regression-list-request-mock.js`：

```bash
WECHAT_DEVTOOLS_CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli" \
MINIPROGRAM_PROJECT_PATH="/absolute/path/to/devtools-project" \
MINIPROGRAM_LIST_PAGE="/pages/list/index" \
MINIPROGRAM_LIST_ITEM_SELECTOR=".list-item" \
node scripts/regression-list-request-mock.js
```

## 注意事项

1. **独立脚本优先**：当前需求只是回归模板，先交付可直接运行的 Node 脚本，后续再封装进 Jest。
2. **优先用 `mockWxMethod/restoreWxMethod`**：不要默认走 `evaluate()` 做运行时 patch，除非官方 mock 覆盖不了你的场景。
3. **清理必须进 `finally`**：恢复 mock、解绑监听、关闭实例缺一不可。
4. **等待策略优先 `waitFor(selector)`**：不要一上来就全靠固定 `sleep`。模板里 `waitFor(LIST_ITEM_SELECTOR)` 是主同步手段，`waitFor(100)` 只是短兜底。
5. **如果页面是 tabBar**：把 `reLaunch(LIST_PAGE)` 改成 `switchTab(LIST_PAGE)`。
6. **如果列表节点在自定义组件里**：不要直接用 `page.$('list-panel .list-item')` 试图穿透组件边界；应先拿到组件宿主，再在组件作用域内继续查。
7. **断言不要只验“有元素”**：至少同时校验数量和关键文案，避免页面渲染了旧数据也误判通过。
8. **Mock 要覆盖业务真实返回结构**：`data/statusCode/header/errMsg` 尽量和真实接口保持一致，减少“模板能跑，业务代码却分支不一致”的假通过。
9. **先确认 `projectPath`**：如果项目是 Taro、uni-app 或其他构建链，开发者工具打开的往往是 `dist/`、`build/` 或 `miniprogram/`，不是仓库根目录。
10. **安全设置别漏**：没开 CLI / HTTP 调用时，最常见症状就是 launch 失败、连接超时，或者开发者工具能开但自动化脚本连不上。

## 成功判定建议

脚本运行成功时，至少满足以下条件：

- 列表页成功打开
- 列表项数量与 mock 数据一致
- 关键文案与 mock 数据一致
- 没有捕获到 `console error`
- 没有捕获到 `exception`
- 脚本结束时已恢复 `wx.request` mock，并关闭小程序实例

如果后续你要把它升级成回归套件，再把 `main()` 内的逻辑拆进 Jest 的 `beforeAll / afterAll / test` 即可，但这一步建议在独立脚本验证稳定后再做。