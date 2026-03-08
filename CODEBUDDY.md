项目文档默认使用中文 - 专业术语、命令、路径、代码标识符保留原文
README 安装说明 - 统一引用 https://skills.sh/docs/cli 并使用 npx skills add . -a codebuddy --yes
miniprogram-demo/ - 作为 miniprogram-ci 的评测基准项目
评测提示词与文档 - 不要写宿主机绝对路径，统一使用仓库相对路径
miniprogram-ci skill - 生成可重复执行的 Node.js/命令行脚本，不直接代替用户执行 pack-npm、preview、upload
skills/ 目录有任何变化时 - 必须重新运行 npx skills add . -a codebuddy --yes 安装到本地进行实际测试
