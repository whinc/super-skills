# 自定义组件 `form-panel` 内输入框自动化脚本模板

以下示例按 `miniprogram-automator` 风格编写，重点是：**先进入页面，再先选中组件实例，再进入组件内部找 `input`，输入手机号后读取 `value` 或 `data` 做校验。**

## 脚本模板

```js
const automator = require('miniprogram-automator')

async function fillPhoneInFormPanel({
  projectPath,
  pagePath = '/pages/form/index',
  panelSelector = 'form-panel',
  inputSelector = 'input',
  phone = '13800138000',
}) {
  const miniProgram = await automator.launch({ projectPath })

  try {
    const page = await miniProgram.reLaunch(pagePath)
    await page.waitFor(300)

    // 1) 先找到自定义组件实例
    const panel = await page.$(panelSelector)
    if (!panel) {
      throw new Error(`未找到组件：${panelSelector}`)
    }

    // 2) 再在组件作用域内查找 input
    const input = await panel.$(inputSelector)
    if (!input) {
      throw new Error(`未找到组件内输入框：${inputSelector}`)
    }

    // 3) 输入手机号
    await input.tap()
    await input.input(phone)
    await page.waitFor(100)

    // 4) 读取 value 或 data 做验证
    const value = typeof input.value === 'function' ? await input.value() : undefined
    const data = typeof input.data === 'function' ? await input.data() : undefined

    const passed =
      value === phone ||
      data?.value === phone ||
      data?.phone === phone

    if (!passed) {
      throw new Error(
        `校验失败：value=${JSON.stringify(value)}, data=${JSON.stringify(data)}`
      )
    }

    return { value, data }
  } finally {
    await miniProgram.close()
  }
}

fillPhoneInFormPanel({
  projectPath: '/path/to/your/miniprogram',
  pagePath: '/pages/form/index',
  panelSelector: 'form-panel',
  inputSelector: 'input',
  phone: '13800138000',
})
  .then((result) => {
    console.log('验证通过', result)
  })
  .catch((err) => {
    console.error(err)
    process.exit(1)
  })
```

## 验证方式说明

### 1. 读取 `value` 验证
最直接的方式是读取输入框当前值：

```js
const value = await input.value()
if (value !== '13800138000') {
  throw new Error('手机号输入结果不正确')
}
```

适用场景：
- 你要校验的是**输入框当前显示值**。
- 组件内部最终还是落到了原生 `input` 的 `value` 上。

### 2. 读取 `data` 验证
如果组件把输入值同步到组件内部数据，也可以读 `data`：

```js
const data = await input.data()
if (data?.value !== '13800138000' && data?.phone !== '13800138000') {
  throw new Error('组件数据未正确更新')
}
```

适用场景：
- 组件对输入值做了二次封装。
- 你不仅要看输入框表面值，还要确认**内部状态**是否已同步。

### 3. 什么时候优先用哪种方式
- 优先看**是否要验证用户看到的结果**：是的话，优先 `value()`。
- 如果业务逻辑依赖组件内部状态，再补充 `data()` 校验。
- 稳妥做法通常是：**先校验 `value()`，再视需要校验 `data()`。**

## 为什么不能直接用 `page.$` 选到组件内元素

`page.$` 的查询范围是**页面层级**。`form-panel` 是自定义组件时，组件内部的节点属于**组件自己的作用域/节点树**，不会被页面级查询直接穿透。

也就是说，下面这种写法通常不可靠，甚至会直接选不到：

```js
const input = await page.$('form-panel input')
```

原因是：
- `page.$(...)` 只在页面根作用域查找。
- 自定义组件内部节点不是页面根节点的“直接可穿透后代”。
- 组件封装会隔离内部结构，页面层选择器不能把组件内部实现细节当成普通页面节点来抓。

因此正确方式是分两步：

```js
const panel = await page.$('form-panel')
const input = await panel.$('input')
```

先拿到组件实例，再在组件实例作用域里继续查找内部元素。

## 注意事项

1. **进入页面后先等待渲染完成**  
   页面刚打开时组件可能还没挂载完成，建议在 `reLaunch` / `navigateTo` 后做一次短等待，或加显式重试。

2. **优先使用稳定选择器**  
   不要长期依赖裸 `input`。如果页面里有多个输入框，最好给组件实例或内部输入框加稳定的 `id` / `class`，避免选错。

3. **多个 `form-panel` 时不要只靠第一个命中**  
   如果页面里有多个同类组件，最好区分组件实例，例如不同 `id`，否则测试容易脆弱。

4. **注意异步更新**  
   某些组件会在 `input` 后通过 `setData`、防抖、格式化逻辑再更新值。此时输入后立刻读取可能拿到旧值，应适当等待或轮询校验。

5. **输入值可能被格式化**  
   如果组件会自动插空格、截断、过滤非数字，校验时应按实际产品逻辑比对，不要假设回读值一定和原始输入完全一致。

6. **`virtualHost` 场景要额外留意**  
   如果组件使用了 `virtualHost`，宿主标签表现可能与普通组件不同。此时更推荐在可见根节点或明确暴露的测试钩子上做定位。
