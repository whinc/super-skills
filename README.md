# AI Skills Collection

让 AI 编程代理获得特定技术领域的专家知识。基于 [Skills](https://github.com/vercel-labs/skills) 规范，支持 Claude Code、Gemini CLI、Codex、Cursor、GitHub Copilot、Windsurf、Cline、OpenCode、CodeBuddy、Continue、Trae、Qwen Code 等 40+ 种 AI 编程代理。

## Skills

| 名称 | 描述 |
|------|------|
| [miniprogram-automation](./skills/miniprogram-automation/SKILL.md) | 使用 `miniprogram-automator` 为微信小程序生成自动化脚本模板，覆盖页面跳转、元素交互、Mock、截图验证 |
| [miniprogram-ci](./skills/miniprogram-ci/SKILL.md) | 使用 `miniprogram-ci` 为微信小程序生成 CI 脚本，覆盖 pack-npm、预览、上传流程 |
| [react-effects](./skills/react-effects/SKILL.md) | 检测并修正 React useEffect 反模式，提供 12 种场景的正确替代方案 |

## 安装

使用 Skills CLI 安装，详细用法请参考 [官方文档](https://skills.sh/docs/cli)：

```bash
# 安装整个仓库
npx skills add whinc/super-skills

# 只安装单个 skill
npx skills add whinc/super-skills --skill react-effects
```

## 贡献

欢迎提交 PR。

## 许可证

MIT
