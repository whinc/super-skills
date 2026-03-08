# 微信小程序预览脚本

## 前置检查项

### 1. 安装 miniprogram-ci

```bash
ls node_modules/miniprogram-ci 2>/dev/null && echo "已安装" || echo "未安装"
```

若未安装，执行安装：
```bash
npm install miniprogram-ci --save-dev
```

### 2. 获取上传密钥

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入：开发管理 → 开发设置 → 小程序代码上传
3. 点击「生成」下载密钥文件（`private.*.key`）

**安全提醒：**
- ❌ 密钥文件**绝对不能**提交到代码仓库
- ✅ 在 `.gitignore` 中添加 `*.key` 和 `private.*.key`
- ✅ 在 CI/CD 中使用 secrets 管理密钥内容

### 3. 配置 IP 白名单

- 微信公众平台 → 开发设置 → 小程序代码上传 → IP 白名单
- 添加 CI 服务器的出口 IP
- 本地开发可临时关闭白名单，但生产环境**强烈建议开启**

### 4. 确认项目配置

- **编译产物目录**：项目根目录 `/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo`
- **project.config.json 位置**：项目根目录

---

## 完整脚本

创建 `scripts/preview.js`：

```js
#!/usr/bin/env node

/**
 * 微信小程序预览脚本
 * 使用 miniprogram-ci 生成预览二维码
 *
 * 环境变量：
 *   MP_APPID            - 小程序 AppID（必填）
 *   MP_PRIVATE_KEY_PATH - 上传密钥路径（必填）
 *   MP_PROJECT_PATH     - 编译产物目录（必填）
 *   MP_ROBOT            - 机器人编号 1-30（默认 1）
 *
 * 可选环境变量：
 *   MP_PAGE_PATH        - 预览打开的页面路径
 *   MP_SEARCH_QUERY     - 页面查询参数
 *
 * 用法：
 *   node scripts/preview.js
 *   MP_PAGE_PATH=pages/detail/index MP_SEARCH_QUERY="id=123" node scripts/preview.js
 */

const ci = require('miniprogram-ci');
const fs = require('fs');
const path = require('path');

// ─────────────────────────────────────────────────────────────────────────────
// 配置
// ─────────────────────────────────────────────────────────────────────────────

const CONFIG = {
  appid: process.env.MP_APPID,
  privateKeyPath: process.env.MP_PRIVATE_KEY_PATH,
  projectPath: process.env.MP_PROJECT_PATH,
  robot: parseInt(process.env.MP_ROBOT, 10) || 1,
  pagePath: process.env.MP_PAGE_PATH || '',
  searchQuery: process.env.MP_SEARCH_QUERY || '',
  outputDir: path.resolve(process.cwd(), 'ci-artifacts/previews'),
};

// ─────────────────────────────────────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────────────────────────────────────

function validateConfig() {
  const required = { 
    MP_APPID: CONFIG.appid, 
    MP_PRIVATE_KEY_PATH: CONFIG.privateKeyPath, 
    MP_PROJECT_PATH: CONFIG.projectPath 
  };
  const missing = Object.entries(required).filter(([, v]) => !v).map(([k]) => k);
  if (missing.length) {
    console.error(`❌ 缺少环境变量: ${missing.join(', ')}`);
    process.exit(1);
  }
  if (CONFIG.robot < 1 || CONFIG.robot > 30) {
    console.error('❌ MP_ROBOT 必须在 1-30 之间');
    process.exit(1);
  }
  if (!fs.existsSync(path.resolve(CONFIG.privateKeyPath))) {
    console.error(`❌ 密钥文件不存在: ${CONFIG.privateKeyPath}`);
    process.exit(1);
  }
  if (!fs.existsSync(path.resolve(CONFIG.projectPath))) {
    console.error(`❌ 项目路径不存在: ${CONFIG.projectPath}`);
    process.exit(1);
  }
  const configFile = path.join(path.resolve(CONFIG.projectPath), 'project.config.json');
  if (!fs.existsSync(configFile)) {
    console.error(`❌ project.config.json 不存在: ${configFile}`);
    process.exit(1);
  }
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

// ─────────────────────────────────────────────────────────────────────────────
// 主流程
// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  console.log('🔍 校验配置...');
  validateConfig();

  ensureDir(CONFIG.outputDir);
  const qrcodePath = path.join(CONFIG.outputDir, `preview-${timestamp()}.png`);

  console.log('\n📋 预览配置:');
  console.log(`   AppID:       ${CONFIG.appid}`);
  console.log(`   项目路径:    ${path.resolve(CONFIG.projectPath)}`);
  console.log(`   机器人编号:  ${CONFIG.robot}`);
  if (CONFIG.pagePath) console.log(`   页面路径:    ${CONFIG.pagePath}`);
  if (CONFIG.searchQuery) console.log(`   查询参数:    ${CONFIG.searchQuery}`);
  console.log(`   二维码输出:  ${qrcodePath}`);

  const project = new ci.Project({
    appid: CONFIG.appid,
    type: 'miniProgram',
    projectPath: path.resolve(CONFIG.projectPath),
    privateKeyPath: path.resolve(CONFIG.privateKeyPath),
    ignores: ['node_modules/**/*'],
  });

  console.log('\n🚀 生成预览...');
  try {
    const result = await ci.preview({
      project,
      desc: `Preview by robot ${CONFIG.robot} at ${new Date().toLocaleString()}`,
      setting: { es6: true, es7: true, minify: true, autoPrefixWXSS: true },
      qrcodeFormat: 'image',
      qrcodeOutputDest: qrcodePath,
      robot: CONFIG.robot,
      ...(CONFIG.pagePath && { pagePath: CONFIG.pagePath }),
      ...(CONFIG.searchQuery && { searchQuery: CONFIG.searchQuery }),
    });

    console.log('\n✅ 预览成功！');
    console.log(`📱 二维码: ${qrcodePath}`);
    if (result?.subPackageInfo) {
      console.log('\n📦 包大小:');
      result.subPackageInfo.forEach(p => console.log(`   ${p.name || '主包'}: ${(p.size / 1024 / 1024).toFixed(2)} MB`));
    }
  } catch (err) {
    console.error(`\n❌ 预览失败: ${err.message}`);
    if (err.message.includes('invalid ip')) console.error('💡 请将当前 IP 添加到微信后台白名单');
    process.exit(1);
  }
}

main();
```

---

## package.json scripts 配置

在 `package.json` 中添加以下脚本：

```json
{
  "scripts": {
    "ci:preview": "node scripts/preview.js"
  }
}
```

---

## 使用方式

### 基础用法

```bash
# 设置环境变量并执行
MP_APPID=wxefceab5e78138b13 \
MP_PRIVATE_KEY_PATH=./private.wxefceab5e78138b13.key \
MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo \
MP_ROBOT=1 \
npm run ci:preview
```

### 指定页面路径和查询参数

```bash
MP_APPID=wxefceab5e78138b13 \
MP_PRIVATE_KEY_PATH=./private.wxefceab5e78138b13.key \
MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo \
MP_ROBOT=1 \
MP_PAGE_PATH=page/API/pages/storage/storage \
MP_SEARCH_QUERY="type=demo" \
npm run ci:preview
```

### 使用 .env 文件

创建 `.env` 文件：
```env
MP_APPID=wxefceab5e78138b13
MP_PRIVATE_KEY_PATH=./private.wxefceab5e78138b13.key
MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo
MP_ROBOT=1
```

**提醒**：将 `.env` 和 `*.key` 添加到 `.gitignore`。

---

## 输出说明

预览二维码图片将生成到 `ci-artifacts/previews/` 目录，文件名格式为 `preview-{timestamp}.png`。

---

## 环境变量速查

| 环境变量 | 必填 | 说明 |
|---------|------|------|
| `MP_APPID` | ✅ | 小程序 AppID |
| `MP_PRIVATE_KEY_PATH` | ✅ | 密钥文件路径 |
| `MP_PROJECT_PATH` | ✅ | 编译产物目录 |
| `MP_ROBOT` | ❌ | 机器人编号（默认 1） |
| `MP_PAGE_PATH` | ❌ | 预览打开的页面 |
| `MP_SEARCH_QUERY` | ❌ | 页面查询参数 |
