# 微信小程序上传脚本

## 前置条件

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

### 3. 配置 IP 白名单

- 微信公众平台 → 开发设置 → 小程序代码上传 → IP 白名单
- 添加 CI 服务器的出口 IP
- 本地开发可临时关闭白名单，但生产环境**强烈建议开启**

### 4. 确认项目配置

- **编译产物目录**：项目根目录 `/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo`
- **project.config.json 位置**：项目根目录

---

## 安全注意事项

- ❌ 密钥文件**绝对不能**提交到代码仓库
- ✅ 在 `.gitignore` 中添加 `*.key` 和 `private.*.key`
- ✅ 在 CI/CD 中使用 secrets 管理密钥内容
- ✅ `ci-artifacts/` 目录已添加到 `.gitignore`（如包含敏感日志）
- ✅ 生产环境已开启 IP 白名单

---

## 完整脚本

创建 `scripts/upload.js`：

```js
#!/usr/bin/env node

/**
 * 微信小程序上传脚本
 * 使用 miniprogram-ci 上传代码至微信后台
 *
 * 环境变量：
 *   MP_APPID            - 小程序 AppID（必填）
 *   MP_PRIVATE_KEY_PATH - 上传密钥路径（必填）
 *   MP_PROJECT_PATH     - 编译产物目录（必填）
 *   MP_ROBOT            - 机器人编号 1-30（默认 1）
 *
 * 命令行参数：
 *   --version <版本号>  必填
 *   --desc <描述>       必填
 *   --pack-npm          可选，上传前执行 npm 构建
 *
 * 用法：
 *   node scripts/upload.js --version 1.0.0 --desc "修复登录问题"
 *   node scripts/upload.js --version 1.0.0 --desc "新功能" --pack-npm
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
  outputDir: path.resolve(process.cwd(), 'ci-artifacts/uploads'),
};

// ─────────────────────────────────────────────────────────────────────────────
// 命令行解析
// ─────────────────────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const result = { version: null, desc: null, packNpm: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--version' && args[i + 1]) result.version = args[++i];
    else if (args[i] === '--desc' && args[i + 1]) result.desc = args[++i];
    else if (args[i] === '--pack-npm') result.packNpm = true;
    else if (args[i] === '--help' || args[i] === '-h') { printHelp(); process.exit(0); }
  }
  return result;
}

function printHelp() {
  console.log(`
用法: node scripts/upload.js [选项]

选项:
  --version <版本号>   必填，如 1.0.0
  --desc <描述>        必填，版本描述
  --pack-npm           上传前执行 npm 构建
  --help               显示帮助
`);
}

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

function saveResult(result, args) {
  ensureDir(CONFIG.outputDir);
  const filename = `upload-${args.version}-${timestamp()}.json`;
  const filepath = path.join(CONFIG.outputDir, filename);
  const data = {
    timestamp: new Date().toISOString(),
    version: args.version,
    desc: args.desc,
    robot: CONFIG.robot,
    result,
  };
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  console.log(`📄 结果已保存: ${filepath}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// 主流程
// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();

  if (!args.version) { console.error('❌ 必须指定 --version'); process.exit(1); }
  if (!args.desc) { console.error('❌ 必须指定 --desc'); process.exit(1); }

  console.log('🔍 校验配置...');
  validateConfig();

  console.log('\n📋 上传配置:');
  console.log(`   AppID:       ${CONFIG.appid}`);
  console.log(`   项目路径:    ${path.resolve(CONFIG.projectPath)}`);
  console.log(`   机器人编号:  ${CONFIG.robot}`);
  console.log(`   版本号:      ${args.version}`);
  console.log(`   版本描述:    ${args.desc}`);
  console.log(`   packNpm:     ${args.packNpm ? '是' : '否'}`);

  const project = new ci.Project({
    appid: CONFIG.appid,
    type: 'miniProgram',
    projectPath: path.resolve(CONFIG.projectPath),
    privateKeyPath: path.resolve(CONFIG.privateKeyPath),
    ignores: ['node_modules/**/*'],
  });

  if (args.packNpm) {
    console.log('\n📦 执行 npm 构建...');
    try {
      await ci.packNpm(project, { reporter: console.log });
      console.log('✅ npm 构建完成');
    } catch (err) {
      console.error(`❌ npm 构建失败: ${err.message}`);
      process.exit(1);
    }
  }

  console.log('\n🚀 上传代码...');
  try {
    const result = await ci.upload({
      project,
      version: args.version,
      desc: args.desc,
      robot: CONFIG.robot,
      setting: { es6: true, es7: true, minify: true, autoPrefixWXSS: true },
      onProgressUpdate: console.log,
    });

    console.log('\n✅ 上传成功！');
    if (result?.subPackageInfo) {
      console.log('\n📦 包大小:');
      result.subPackageInfo.forEach(p => console.log(`   ${p.name || '主包'}: ${(p.size / 1024 / 1024).toFixed(2)} MB`));
    }
    saveResult({ success: true, ...result }, args);
  } catch (err) {
    console.error(`\n❌ 上传失败: ${err.message}`);
    if (err.message.includes('invalid ip')) console.error('💡 请将当前 IP 添加到微信后台白名单');
    saveResult({ success: false, error: err.message }, args);
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
    "ci:upload": "node scripts/upload.js",
    "ci:upload:npm": "node scripts/upload.js --pack-npm"
  }
}
```

---

## 使用方式

### 基础上传

```bash
MP_APPID=wxefceab5e78138b13 \
MP_PRIVATE_KEY_PATH=./private.wxefceab5e78138b13.key \
MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo \
MP_ROBOT=1 \
npm run ci:upload -- --version 1.0.0 --desc "修复登录问题"
```

### 上传前构建 npm

```bash
MP_APPID=wxefceab5e78138b13 \
MP_PRIVATE_KEY_PATH=./private.wxefceab5e78138b13.key \
MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo \
MP_ROBOT=1 \
npm run ci:upload:npm -- --version 1.0.0 --desc "新功能上线"
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

上传结果将保存到 `ci-artifacts/uploads/` 目录，文件名格式为 `upload-{version}-{timestamp}.json`，内容包含：

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0",
  "desc": "版本描述",
  "robot": 1,
  "result": {
    "success": true,
    "subPackageInfo": [...]
  }
}
```

---

## 命令行参数速查

| 参数 | 必填 | 说明 |
|------|------|------|
| `--version <v>` | ✅ | 版本号 |
| `--desc <d>` | ✅ | 版本描述 |
| `--pack-npm` | ❌ | 上传前执行 npm 构建 |

---

## 环境变量速查

| 环境变量 | 必填 | 说明 |
|---------|------|------|
| `MP_APPID` | ✅ | 小程序 AppID |
| `MP_PRIVATE_KEY_PATH` | ✅ | 密钥文件路径 |
| `MP_PROJECT_PATH` | ✅ | 编译产物目录 |
| `MP_ROBOT` | ❌ | 机器人编号（默认 1） |

---

## CI/CD 集成示例（GitHub Actions）

```yaml
name: Deploy Mini Program

on:
  push:
    tags:
      - 'v*'

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Write private key
        run: echo "${{ secrets.MP_PRIVATE_KEY }}" > private.key

      - name: Upload to WeChat
        env:
          MP_APPID: ${{ secrets.MP_APPID }}
          MP_PRIVATE_KEY_PATH: ./private.key
          MP_PROJECT_PATH: .
          MP_ROBOT: 1
        run: |
          VERSION=${GITHUB_REF_NAME#v}
          npm run ci:upload -- --version "$VERSION" --desc "CI 自动上传"

      - name: Cleanup
        if: always()
        run: rm -f private.key
```
