# miniprogram-ci 上传脚本

## 前置条件

在运行脚本前，请确保以下条件已满足：

### 1. 安装依赖

```bash
npm install miniprogram-ci --save-dev
```

### 2. 上传密钥配置

- 在微信公众平台下载小程序代码上传密钥
- 路径：微信公众平台 -> 开发管理 -> 开发设置 -> 小程序代码上传密钥
- 将密钥文件保存到安全位置（不要提交到代码仓库）

### 3. IP 白名单配置

- 如果开启了 IP 白名单，需要将 CI 服务器 IP 加入白名单
- 或者在开发设置中关闭 IP 白名单限制

### 4. 环境变量配置

需要设置以下环境变量：

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `MP_APPID` | 是 | 小程序的 AppID |
| `MP_PRIVATE_KEY_PATH` | 是 | 上传密钥文件路径 |
| `MP_PROJECT_PATH` | 否 | 项目路径，默认当前目录 |
| `MP_ROBOT` | 否 | 机器人编号 1-30，默认 1 |

### 5. 项目配置

- 确保 `project.config.json` 存在于项目根目录
- 确保项目代码已通过本地编译测试

## 安全注意事项

1. **密钥保护**：
   - 上传密钥文件绝不能提交到代码仓库
   - 将密钥路径添加到 `.gitignore`
   - 在 CI/CD 环境中使用安全的密钥管理方式（如 GitHub Secrets、环境变量注入等）

2. **版本管理**：
   - 建议 version 遵循语义化版本规范（如 1.0.0）
   - 上传前确认版本号未被使用过
   - 建议与 git tag 保持一致

3. **审核流程**：
   - 上传后的代码需要在微信公众平台提交审核
   - 建议上传前进行充分的本地测试和预览测试

4. **权限控制**：
   - 建议不同环境使用不同的机器人编号
   - 生产环境上传应有审批流程

## 完整脚本

创建文件 `scripts/upload.js`：

```javascript
/**
 * miniprogram-ci 上传脚本
 * 将小程序代码上传到微信后台
 */

const ci = require('miniprogram-ci');
const path = require('path');
const fs = require('fs');

// 从环境变量读取配置
const appid = process.env.MP_APPID;
const privateKeyPath = process.env.MP_PRIVATE_KEY_PATH;
const projectPath = process.env.MP_PROJECT_PATH || process.cwd();
const robot = parseInt(process.env.MP_ROBOT) || 1;

// 从命令行参数读取版本和描述
const args = process.argv.slice(2);
let version = '';
let desc = '';
let packNpm = false;

// 解析命令行参数
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--version' && args[i + 1]) {
    version = args[i + 1];
    i++;
  } else if (args[i] === '--desc' && args[i + 1]) {
    desc = args[i + 1];
    i++;
  } else if (args[i] === '--pack-npm') {
    packNpm = true;
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

  if (!version) {
    errors.push('缺少版本号参数 --version');
  }

  if (!desc) {
    errors.push('缺少版本描述参数 --desc');
  }

  if (errors.length > 0) {
    console.error('配置错误：');
    errors.forEach(err => console.error(`  - ${err}`));
    console.error('\n使用方法：');
    console.error('  node scripts/upload.js --version 1.0.0 --desc "版本描述" [--pack-npm]');
    console.error('\n必需的环境变量：');
    console.error('  MP_APPID=wxxxxxxxxxxx');
    console.error('  MP_PRIVATE_KEY_PATH=/path/to/private.key');
    process.exit(1);
  }

  console.log('配置信息：');
  console.log(`  AppID: ${appid}`);
  console.log(`  密钥路径: ${privateKeyPath}`);
  console.log(`  项目路径: ${projectPath}`);
  console.log(`  机器人编号: ${robot}`);
  console.log(`  版本号: ${version}`);
  console.log(`  版本描述: ${desc}`);
  console.log(`  构建 NPM: ${packNpm ? '是' : '否'}`);
}

// 确保输出目录存在
function ensureOutputDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// 打包 NPM
async function runPackNpm(project) {
  console.log('\n开始构建 NPM...');
  try {
    const result = await ci.packNpm(project, {
      ignores: [],
      reporter: (infos) => {
        console.log('NPM 构建进度:', infos);
      },
    });
    console.log('NPM 构建完成');
    return result;
  } catch (error) {
    console.error('NPM 构建失败：', error.message || error);
    throw error;
  }
}

async function upload() {
  validateConfig();

  // 创建项目实例
  const project = new ci.Project({
    appid: appid,
    type: 'miniProgram',
    projectPath: projectPath,
    privateKeyPath: privateKeyPath,
    ignores: ['node_modules/**/*'],
  });

  // 按需执行 packNpm
  if (packNpm) {
    await runPackNpm(project);
  }

  // 准备输出目录
  const outputDir = path.join(projectPath, 'ci-artifacts', 'uploads');
  ensureOutputDir(outputDir);

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

  console.log('\n开始上传...');

  try {
    const uploadResult = await ci.upload({
      project,
      version: version,
      desc: desc,
      robot: robot,
      setting: {
        es6: true,
        es7: true,
        minify: true,
        autoPrefixWXSS: true,
        minifyWXML: true,
        minifyWXSS: true,
        minifyJS: true,
      },
      onProgressUpdate: (info) => {
        console.log('上传进度:', info.message || info);
      },
    });

    console.log('\n上传成功！');
    console.log('上传结果：');
    
    // 构建上传结果信息
    const uploadInfo = {
      success: true,
      timestamp: new Date().toISOString(),
      appid: appid,
      version: version,
      desc: desc,
      robot: robot,
      projectPath: projectPath,
      packNpm: packNpm,
    };

    // 处理返回结果
    if (uploadResult) {
      if (uploadResult.subPackageInfo) {
        console.log('\n分包信息：');
        uploadResult.subPackageInfo.forEach(pkg => {
          console.log(`  ${pkg.name}: ${(pkg.size / 1024).toFixed(2)} KB`);
        });
        uploadInfo.subPackageInfo = uploadResult.subPackageInfo;
      }

      if (uploadResult.pluginInfo && uploadResult.pluginInfo.length > 0) {
        console.log('\n使用的插件：');
        uploadResult.pluginInfo.forEach(plugin => {
          console.log(`  - ${plugin.pluginAppid}: ${plugin.version}`);
        });
        uploadInfo.pluginInfo = uploadResult.pluginInfo;
      }

      if (uploadResult.sizeInfo) {
        console.log(`\n总大小: ${(uploadResult.sizeInfo.total / 1024).toFixed(2)} KB`);
        uploadInfo.sizeInfo = uploadResult.sizeInfo;
      }
    }

    // 保存上传结果到文件
    const resultPath = path.join(outputDir, `upload-${version}-${timestamp}.json`);
    fs.writeFileSync(resultPath, JSON.stringify(uploadInfo, null, 2));
    console.log(`\n上传记录已保存到: ${resultPath}`);

    return uploadResult;
  } catch (error) {
    console.error('\n上传失败：');
    console.error(error.message || error);

    // 保存错误信息
    const errorInfo = {
      success: false,
      timestamp: new Date().toISOString(),
      appid: appid,
      version: version,
      desc: desc,
      error: error.message || String(error),
    };
    const errorPath = path.join(outputDir, `upload-error-${version}-${timestamp}.json`);
    fs.writeFileSync(errorPath, JSON.stringify(errorInfo, null, 2));
    console.log(`错误记录已保存到: ${errorPath}`);

    process.exit(1);
  }
}

// 执行
upload();
```

## package.json scripts 配置

在 `package.json` 中添加以下脚本：

```json
{
  "scripts": {
    "ci:upload": "node scripts/upload.js",
    "ci:upload:npm": "node scripts/upload.js --pack-npm",
    "ci:upload:dev": "MP_PROJECT_PATH=. MP_ROBOT=1 node scripts/upload.js"
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

# 上传
npm run ci:upload -- --version 1.0.0 --desc "首次发布"
```

### 上传前构建 NPM

```bash
npm run ci:upload -- --version 1.0.0 --desc "更新依赖" --pack-npm
```

### 使用 npm 脚本简化

```bash
# 带 npm 构建的上传
npm run ci:upload:npm -- --version 1.0.0 --desc "新功能发布"
```

### CI/CD 集成示例（GitHub Actions）

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
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Upload to WeChat
        env:
          MP_APPID: ${{ secrets.MP_APPID }}
          MP_PRIVATE_KEY_PATH: ${{ github.workspace }}/private.key
          MP_PROJECT_PATH: ${{ github.workspace }}
          MP_ROBOT: 1
        run: |
          echo "${{ secrets.MP_PRIVATE_KEY }}" > private.key
          VERSION=${GITHUB_REF#refs/tags/v}
          npm run ci:upload -- --version $VERSION --desc "Release $VERSION" --pack-npm
```

## 输出说明

脚本执行成功后，会在 `ci-artifacts/uploads/` 目录下生成：

1. `upload-{version}-{timestamp}.json` - 上传成功记录，包含版本信息、分包大小等
2. `upload-error-{version}-{timestamp}.json` - 上传失败记录（仅失败时生成）

## 常见问题

1. **上传失败 - 密钥无效**：检查密钥文件是否正确，是否与 AppID 匹配
2. **上传失败 - IP 不在白名单**：在微信公众平台添加 IP 或关闭白名单
3. **上传失败 - 版本号已存在**：使用新的版本号
4. **包体积超限**：检查分包配置，优化代码和资源
