# spec-tickets 输入

当输入包含 `spec.md` 和一组实现 ticket 时，使用本分支。只加载本文件处理 spec 专属规则。

## 映射约束

读取 `spec.md` 与 `.scratch/<feature>/issues/NN-*.md` 的每个 ticket。每个 ticket 单独进入依赖图，不把一个 spec 当成一个 ticket。保留并传递：

- spec 的验收约束与范围；
- ticket 原文、依赖和 tracker 映射；
- `allowedPaths`；
- 验证命令；
- 主 skill 的终态协议要求。

## 派发

每个 spec ticket 的 sub agent 先调用 `/implement`，只处理当前 ticket，并按主 skill 的 DAG、核验、失败传播和终态规则报告一次。主 Agent 负责确认每个 ticket 的 tracker 与 spec 验收约束均已复核。