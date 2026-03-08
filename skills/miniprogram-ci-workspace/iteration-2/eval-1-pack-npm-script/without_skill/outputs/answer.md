# miniprogram-ci 打包 NPM 脚本

## 前置检查项

在运行脚本前，请确保以下条件已满足：

1. **安装 miniprogram-ci**：项目中需安装 `miniprogram-ci` 依赖
   ```bash
   npm install miniprogram-ci --save-dev
   ```

2. **项目配置正确**：确保 `project.config.json` 存在于项目根目录，且配置正确

3. **NPM 依赖已安装**：项目的 `node_modules` 目录存在，即已运行过 `npm install`

4. **环境变量配置**：需要设置以下环境变量
   - `MP_APPID`：小程序的 AppID
   - `MP_PROJECT_PATH`：项目路径（可选，默认为当前目录）

5. **miniprogram_npm 目录**：确保 `project.config.json` 中配置了正确的 `miniprogramNpmDistDir`（如果有自定义配置）

## 完整脚本

创建文件 `scripts/pack-npm.js`：

```javascript
/**
 * miniprogram-ci 打包 NPM 脚本
 * 用于构建小程序的 npm 依赖
 */

const ci = require('miniprogram-ci');
const path = require('path');

// 从环境变量读取配置
const appid = process.env.MP_APPID;
const projectPath = process.env.MP_PROJECT_PATH || process.cwd();

// 参数校验
function validateConfig() {
  if (!appid) {
    console.error('错误：缺少环境变量 MP_APPID');
    console.error('请设置：export MP_APPID=your_appid');
    process.exit(1);
  }

  console.log('配置信息：');
  console.log(`  AppID: ${appid}`);
  console.log(`  项目路径: ${projectPath}`);
}

async function packNpm() {
  validateConfig();

  // 创建项目实例
  const project = new ci.Project({
    appid: appid,
    type: 'miniProgram',
    projectPath: projectPath,
    ignores: ['node_modules/**/*'],
  });

  console.log('\n开始构建 NPM...');

  try {
    const result = await ci.packNpm(project, {
      ignores: [],
      reporter: (infos) => {
        console.log('构建进度:', infos);
      },
    });

    console.log('\nNPM 构建成功！');
    console.log('构建结果：');
    console.log(`  使用的包管理器: ${result.packNpmManually ? '手动' : '自动'}`);
    console.log(`  miniprogram_npm 目录: ${result.miniprogram_npm || '默认位置'}`);
    
    if (result.warnList && result.warnList.length > 0) {
      console.log('\n警告信息：');
      result.warnList.forEach((warn, index) => {
        console.log(`  ${index + 1}. ${warn}`);
      });
    }

    return result;
  } catch (error) {
    console.error('\nNPM 构建失败：');
    console.error(error.message || error);
    process.exit(1);
  }
}

// 执行
packNpm();
```

## package.json scripts 配置

在 `package.json` 中添加以下脚本：

```json
{
  "scripts": {
    "ci:pack-npm": "node scripts/pack-npm.js",
    "ci:pack-npm:dev": "MP_PROJECT_PATH=. node scripts/pack-npm.js"
  }
}
```

## 使用方式

### 方式一：设置环境变量后运行

```bash
export MP_APPID=wxxxxxxxxxxx
export MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo
npm run ci:pack-npm
```

### 方式二：使用 .env 文件（配合 dotenv）

1. 安装 dotenv：
   ```bash
   npm install dotenv --save-dev
   ```

2. 创建 `.env` 文件：
   ```
   MP_APPID=wxxxxxxxxxxx
   MP_PROJECT_PATH=/Users/whincwu/WeChatProjects/wechat-miniprogram-skills/miniprogram-demo
   ```

3. 在脚本开头添加：
   ```javascript
   require('dotenv').config();
   ```

### 方式三：CI/CD 环境中使用

在 CI/CD 配置中设置环境变量，然后直接运行：

```bash
npm run ci:pack-npm
```

## 注意事项

1. **构建产物位置**：构建后的 npm 包会输出到 `miniprogram_npm` 目录（默认在项目根目录）
2. **忽略文件**：`node_modules` 目录会被忽略，不会被打包到小程序中
3. **依赖版本**：确保使用的 npm 包支持小程序环境
4. **重复构建**：每次执行会覆盖之前的构建结果
