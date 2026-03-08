# 微信小程序 NPM 打包脚本

## 前置检查项

### 1. 安装 miniprogram-ci

```bash
ls node_modules/miniprogram-ci 2>/dev/null && echo "已安装" || echo "未安装"
```

若未安装，执行安装：
```bash
npm install miniprogram-ci --save-dev
```

### 2. 确认项目配置

- **编译产物目录**：项目根目录 `/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo`
- **project.config.json 位置**：项目根目录
- **小程序代码目录**：`miniprogram/`

### 3. 检查是否存在 npm 依赖

确认项目中使用了 npm 模块，需要构建 `miniprogram_npm` 目录。

---

## 完整脚本

创建 `scripts/pack-npm.js`：

```js
#!/usr/bin/env node

/**
 * 微信小程序 NPM 打包脚本
 * 使用 miniprogram-ci 构建 npm 依赖至 miniprogram_npm 目录
 *
 * 环境变量：
 *   MP_APPID        - 小程序 AppID（必填）
 *   MP_PROJECT_PATH - 编译产物目录（必填）
 *
 * 用法：
 *   node scripts/pack-npm.js
 */

const ci = require('miniprogram-ci');
const fs = require('fs');
const path = require('path');

// ─────────────────────────────────────────────────────────────────────────────
// 配置
// ─────────────────────────────────────────────────────────────────────────────

const CONFIG = {
  appid: process.env.MP_APPID,
  projectPath: process.env.MP_PROJECT_PATH,
};

// ─────────────────────────────────────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────────────────────────────────────

function validateConfig() {
  const required = { MP_APPID: CONFIG.appid, MP_PROJECT_PATH: CONFIG.projectPath };
  const missing = Object.entries(required).filter(([, v]) => !v).map(([k]) => k);
  if (missing.length) {
    console.error(`❌ 缺少环境变量: ${missing.join(', ')}`);
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

// ─────────────────────────────────────────────────────────────────────────────
// 主流程
// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  console.log('🔍 校验配置...');
  validateConfig();

  console.log('\n📋 NPM 打包配置:');
  console.log(`   AppID:       ${CONFIG.appid}`);
  console.log(`   项目路径:    ${path.resolve(CONFIG.projectPath)}`);

  const project = new ci.Project({
    appid: CONFIG.appid,
    type: 'miniProgram',
    projectPath: path.resolve(CONFIG.projectPath),
    ignores: ['node_modules/**/*'],
  });

  console.log('\n🚀 打包依赖...');
  try {
    const result = await ci.packNpm(project, {
      reporter: (msg) => console.log(`   ${msg}`),
    });

    console.log('\n✅ NPM 打包完成！');
    console.log(`📦 结果: ${JSON.stringify(result)}`);
  } catch (err) {
    console.error(`\n❌ NPM 打包失败: ${err.message}`);
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
    "ci:pack-npm": "node scripts/pack-npm.js"
  }
}
```

---

## 使用方式

### 本地执行

```bash
# 设置环境变量并执行
MP_APPID=wxefceab5e78138b13 \
MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo \
npm run ci:pack-npm
```

### 使用 .env 文件

创建 `.env` 文件：
```env
MP_APPID=wxefceab5e78138b13
MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo
```

**提醒**：将 `.env` 添加到 `.gitignore`。
