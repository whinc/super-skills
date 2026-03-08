# miniprogram-ci 预览脚本

## 前置检查项

在运行脚本前，请确保以下条件已满足：

1. **安装 miniprogram-ci**：项目中需安装 `miniprogram-ci` 依赖
   ```bash
   npm install miniprogram-ci --save-dev
   ```

2. **上传密钥配置**：
   - 在微信公众平台下载小程序代码上传密钥
   - 路径：微信公众平台 -> 开发管理 -> 开发设置 -> 小程序代码上传密钥
   - 将密钥文件保存到安全位置

3. **IP 白名单**（可选）：
   - 如果开启了 IP 白名单，需要将 CI 服务器 IP 加入白名单
   - 或者关闭 IP 白名单限制

4. **环境变量配置**：需要设置以下环境变量
   - `MP_APPID`：小程序的 AppID（必需）
   - `MP_PRIVATE_KEY_PATH`：上传密钥文件路径（必需）
   - `MP_PROJECT_PATH`：项目路径（可选，默认当前目录）
   - `MP_ROBOT`：机器人编号 1-30（可选，默认 1）

5. **项目配置正确**：确保 `project.config.json` 存在且配置正确

## 完整脚本

创建文件 `scripts/preview.js`：

```javascript
/**
 * miniprogram-ci 预览脚本
 * 生成小程序预览二维码
 */

const ci = require('miniprogram-ci');
const path = require('path');
const fs = require('fs');

// 从环境变量读取配置
const appid = process.env.MP_APPID;
const privateKeyPath = process.env.MP_PRIVATE_KEY_PATH;
const projectPath = process.env.MP_PROJECT_PATH || process.cwd();
const robot = parseInt(process.env.MP_ROBOT) || 1;

// 从命令行参数读取可选配置
const args = process.argv.slice(2);
let pagePath = '';
let searchQuery = '';

// 解析命令行参数
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--page' && args[i + 1]) {
    pagePath = args[i + 1];
    i++;
  } else if (args[i] === '--query' && args[i + 1]) {
    searchQuery = args[i + 1];
    i++;
  }
}

// 参数校验
function validateConfig() {
  const errors = [];

  if (!appid) {
    errors.push('缺少环境变量 MP_APPID');
  }

  if (!privateKeyPath) {
    errors.push('缺少环境变量 MP_PRIVATE_KEY_PATH');
  } else if (!fs.existsSync(privateKeyPath)) {
    errors.push(`密钥文件不存在: ${privateKeyPath}`);
  }

  if (errors.length > 0) {
    console.error('配置错误：');
    errors.forEach(err => console.error(`  - ${err}`));
    console.error('\n请设置必要的环境变量：');
    console.error('  export MP_APPID=wxxxxxxxxxxx');
    console.error('  export MP_PRIVATE_KEY_PATH=/path/to/private.key');
    process.exit(1);
  }

  console.log('配置信息：');
  console.log(`  AppID: ${appid}`);
  console.log(`  密钥路径: ${privateKeyPath}`);
  console.log(`  项目路径: ${projectPath}`);
  console.log(`  机器人编号: ${robot}`);
  if (pagePath) console.log(`  指定页面: ${pagePath}`);
  if (searchQuery) console.log(`  页面参数: ${searchQuery}`);
}

// 确保输出目录存在
function ensureOutputDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

async function preview() {
  validateConfig();

  // 创建项目实例
  const project = new ci.Project({
    appid: appid,
    type: 'miniProgram',
    projectPath: projectPath,
    privateKeyPath: privateKeyPath,
    ignores: ['node_modules/**/*'],
  });

  // 准备输出目录和文件
  const outputDir = path.join(projectPath, 'ci-artifacts', 'previews');
  ensureOutputDir(outputDir);

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const qrcodePath = path.join(outputDir, `preview-${timestamp}.png`);

  console.log('\n开始生成预览...');

  try {
    // 构建预览选项
    const previewOptions = {
      desc: `CI 预览 - ${new Date().toLocaleString()}`,
      setting: {
        es6: true,
        es7: true,
        minify: true,
        autoPrefixWXSS: true,
        minifyWXML: true,
        minifyWXSS: true,
        minifyJS: true,
      },
      qrcodeFormat: 'image',
      qrcodeOutputDest: qrcodePath,
      robot: robot,
      onProgressUpdate: (info) => {
        console.log('进度:', info.message || info);
      },
    };

    // 添加可选的页面路径和参数
    if (pagePath) {
      previewOptions.pagePath = pagePath;
    }
    if (searchQuery) {
      previewOptions.searchQuery = searchQuery;
    }

    const result = await ci.preview(project, previewOptions);

    console.log('\n预览生成成功！');
    console.log(`二维码已保存到: ${qrcodePath}`);
    
    if (result.pluginInfo && result.pluginInfo.length > 0) {
      console.log('\n使用的插件：');
      result.pluginInfo.forEach(plugin => {
        console.log(`  - ${plugin.pluginAppid}: ${plugin.version}`);
      });
    }

    // 保存预览信息
    const infoPath = path.join(outputDir, `preview-${timestamp}.json`);
    const previewInfo = {
      timestamp: new Date().toISOString(),
      appid: appid,
      robot: robot,
      pagePath: pagePath || '',
      searchQuery: searchQuery || '',
      qrcodePath: qrcodePath,
    };
    fs.writeFileSync(infoPath, JSON.stringify(previewInfo, null, 2));
    console.log(`预览信息已保存到: ${infoPath}`);

    return result;
  } catch (error) {
    console.error('\n预览生成失败：');
    console.error(error.message || error);
    process.exit(1);
  }
}

// 执行
preview();
```

## package.json scripts 配置

在 `package.json` 中添加以下脚本：

```json
{
  "scripts": {
    "ci:preview": "node scripts/preview.js",
    "ci:preview:page": "node scripts/preview.js --page",
    "ci:preview:dev": "MP_PROJECT_PATH=. MP_ROBOT=1 node scripts/preview.js"
  }
}
```

## 使用方式

### 基本使用

```bash
# 设置环境变量
export MP_APPID=wxxxxxxxxxxx
export MP_PRIVATE_KEY_PATH=/path/to/private.key
export MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo
export MP_ROBOT=1

# 生成预览
npm run ci:preview
```

### 指定页面和参数

```bash
# 预览指定页面
npm run ci:preview -- --page pages/index/index

# 预览指定页面并带参数
npm run ci:preview -- --page pages/detail/detail --query "id=123&type=test"
```

### 使用 .env 文件

1. 创建 `.env` 文件：
   ```
   MP_APPID=wxxxxxxxxxxx
   MP_PRIVATE_KEY_PATH=/path/to/private.key
   MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo
   MP_ROBOT=1
   ```

2. 安装 dotenv 并在脚本开头添加：
   ```javascript
   require('dotenv').config();
   ```

## 输出说明

脚本执行成功后，会在 `ci-artifacts/previews/` 目录下生成：

1. `preview-{timestamp}.png` - 预览二维码图片
2. `preview-{timestamp}.json` - 预览信息记录

## 注意事项

1. **密钥安全**：上传密钥文件不要提交到代码仓库，建议添加到 `.gitignore`
2. **机器人编号**：不同机器人编号可以用于区分不同开发者或环境
3. **二维码有效期**：预览二维码有时效限制（通常 30 分钟）
4. **编译设置**：脚本中的 `setting` 选项可根据项目需要调整
5. **IP 白名单**：首次使用需确认 IP 白名单配置
