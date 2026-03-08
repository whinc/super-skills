# 回归脚本模板：Mock `wx.request` + 监听 `console/exception` + 校验列表页渲染

下面给一份**简洁但完整**的脚本骨架。示例采用 **Jest + 自动化驱动** 的写法，默认你的驱动支持：

- 启动/关闭小程序
- `reLaunch` 到指定页面
- 获取页面元素并断言文本
- 通过 `evaluate(fn, arg)` 在小程序运行时注入/恢复 `wx.request`
- 通过 `on('console')` / `on('exception')` 监听运行时事件

如果你的自动化封装 API 名称略有差异，替换对应方法名即可，整体流程不要变。

## 完整脚本骨架

```js
/**
 * request-mock-console-exception.spec.js
 *
 * 目的：
 * 1. mock wx.request 返回固定列表数据
 * 2. 监听 console 和 exception
 * 3. 跳转到列表页验证渲染结果
 * 4. 结束前恢复 mock 并关闭小程序
 */

const automator = require('miniprogram-automator');

describe('列表页回归：mock request + console/exception 监听', () => {
  let miniProgram;
  let page;

  const consoleEvents = [];
  const exceptionEvents = [];
  const boundListeners = [];

  const mockResponse = {
    code: 0,
    data: [
      { id: '1001', title: 'Mock Item A' },
      { id: '1002', title: 'Mock Item B' },
    ],
  };

  function bindRuntimeEvents(app) {
    const onConsole = (payload) => {
      consoleEvents.push(payload);
    };

    const onException = (payload) => {
      exceptionEvents.push(payload);
    };

    if (typeof app.on === 'function') {
      app.on('console', onConsole);
      app.on('exception', onException);
      boundListeners.push(['console', onConsole], ['exception', onException]);
    }
  }

  function unbindRuntimeEvents(app) {
    if (typeof app.off !== 'function') return;

    for (const [eventName, handler] of boundListeners) {
      app.off(eventName, handler);
    }
    boundListeners.length = 0;
  }

  async function installRequestMock(app, mockedData) {
    await app.evaluate((payload) => {
      const g = globalThis;

      if (!g.__E2E_ORIGINAL_WX_REQUEST__) {
        g.__E2E_ORIGINAL_WX_REQUEST__ = wx.request;
      }

      g.__E2E_LAST_REQUEST_OPTIONS__ = null;

      wx.request = function mockedWxRequest(options = {}) {
        g.__E2E_LAST_REQUEST_OPTIONS__ = options;

        const response = {
          data: payload,
          statusCode: 200,
          header: { 'content-type': 'application/json' },
          cookies: [],
          errMsg: 'request:ok',
        };

        const requestTask = {
          abort() {},
          onHeadersReceived() {},
          offHeadersReceived() {},
          onChunkReceived() {},
          offChunkReceived() {},
        };

        Promise.resolve().then(() => {
          if (typeof options.success === 'function') {
            options.success(response);
          }
          if (typeof options.complete === 'function') {
            options.complete(response);
          }
        });

        return requestTask;
      };
    }, mockedData);
  }

  async function restoreRequestMock(app) {
    await app.evaluate(() => {
      const g = globalThis;

      if (g.__E2E_ORIGINAL_WX_REQUEST__) {
        wx.request = g.__E2E_ORIGINAL_WX_REQUEST__;
        delete g.__E2E_ORIGINAL_WX_REQUEST__;
      }

      delete g.__E2E_LAST_REQUEST_OPTIONS__;
    });
  }

  beforeAll(async () => {
    miniProgram = await automator.launch({
      projectPath: '/path/to/your/miniprogram',
      // cliPath: '/Applications/wechatwebdevtools.app/Contents/MacOS/cli',
      // devtools: true,
    });

    bindRuntimeEvents(miniProgram);

    // 先装 mock，再跳页面，避免页面 onLoad/onShow 首次请求逃逸。
    await installRequestMock(miniProgram, mockResponse);

    await miniProgram.reLaunch('/pages/list/index');
    page = await miniProgram.currentPage();
    await page.waitFor(1000);
  });

  afterAll(async () => {
    try {
      if (miniProgram) {
        await restoreRequestMock(miniProgram);
      }
    } finally {
      try {
        if (miniProgram) {
          unbindRuntimeEvents(miniProgram);
        }
      } finally {
        if (miniProgram) {
          await miniProgram.close();
        }
      }
    }
  });

  test('列表页应渲染 mock 数据，且无 exception', async () => {
    // 下面的选择器请替换为你项目里稳定可用的选择器
    const items = await page.$$('.list-item');

    expect(items.length).toBe(2);
    expect(await items[0].text()).toContain('Mock Item A');
    expect(await items[1].text()).toContain('Mock Item B');

    // 可选：校验发起请求时带了什么参数
    const lastRequestOptions = await miniProgram.evaluate(() => {
      return globalThis.__E2E_LAST_REQUEST_OPTIONS__ || null;
    });

    expect(lastRequestOptions).not.toBeNull();
    expect(lastRequestOptions.url).toContain('/list');

    // exception 一般直接判空
    expect(exceptionEvents).toEqual([]);

    // console 建议只过滤 error / warn，避免正常日志导致误报
    const consoleErrors = consoleEvents.filter((event) => {
      if (!event) return false;
      if (typeof event === 'string') return false;
      return event.type === 'error';
    });

    expect(consoleErrors).toEqual([]);
  });
});
```

## Mock 与恢复流程

1. **启动小程序后先绑定事件监听**，避免错过启动期日志和异常。
2. **在跳转列表页前安装 `wx.request` mock**，确保页面 `onLoad` / `onShow` 触发的首个请求就命中 mock。
3. mock 中保存原始 `wx.request` 到全局变量，例如 `globalThis.__E2E_ORIGINAL_WX_REQUEST__`。
4. mock 返回固定响应，并补齐最基本的 `requestTask` 空实现，避免业务代码调用 `abort` 等方法时报错。
5. 用例结束时，无论断言是否失败，都在 `afterAll -> finally` 中**优先恢复原始 `wx.request`**。
6. 恢复完成后再解绑监听、关闭小程序。

## 事件监听

推荐至少监听两类事件：

- `console`：收集 `log / warn / error`，便于排查页面渲染期间是否出现异常日志。
- `exception`：捕获运行时异常，回归脚本里通常直接断言为空。

建议做法：

- 把事件统一收集到数组：`consoleEvents`、`exceptionEvents`
- 断言时**只关注 `console.error` 或关键字**，不要把正常调试日志当失败
- 如果你的驱动不支持 `off`，至少保证测试进程内只绑定一次，避免重复监听

## 清理步骤

建议固定为下面顺序：

1. 恢复 `wx.request`
2. 清理全局测试注入变量，如 `__E2E_LAST_REQUEST_OPTIONS__`
3. 解绑 `console` / `exception` 监听
4. 关闭小程序实例 `miniProgram.close()`

其中 **恢复 mock 和关闭小程序必须放在 `finally`**，否则断言失败时很容易污染后续用例。

## 注意事项

1. **mock 要早于页面跳转**  
   如果列表页一进入就请求数据，先跳页再 mock 会导致真实请求已经发出。

2. **mock 返回结构要贴近真实 `wx.request`**  
   至少补齐：
   - `success(res)`
   - `complete(res)`
   - `statusCode`
   - `header`
   - `errMsg: 'request:ok'`
   - 基本 `requestTask` 方法

3. **不要只校验页面文案，也要校验没有异常**  
   页面看起来渲染成功，不代表运行时没有 `exception` 或 `console.error`。

4. **选择器尽量稳定**  
   优先使用约定好的列表项类名、测试标记或稳定结构，不要依赖易变文案。

5. **如果业务封装了请求层，mock 点位要一致**  
   如果页面不是直接调用 `wx.request`，而是通过 `request()`、`http()` 等封装发请求，确认最终仍然会走到被替换的 `wx.request`。

6. **并发/多用例时避免全局污染**  
   `wx.request` 是全局对象上的方法，多个用例共享一个小程序实例时，必须保证每个用例都能恢复现场。

7. **版本差异要提前适配**  
   不同自动化封装对 `evaluate`、事件监听、元素查询 API 命名可能不同。若你的框架没有 `miniProgram.evaluate`，把“注入/恢复 mock”改成你现有框架支持的运行时注入方式即可，但流程保持一致。

## 最小检查清单

- [x] 启动小程序
- [x] 绑定 `console` 监听
- [x] 绑定 `exception` 监听
- [x] mock `wx.request`
- [x] 跳转列表页
- [x] 校验列表渲染结果
- [x] 校验无异常/无错误日志
- [x] 恢复 mock
- [x] 关闭小程序
