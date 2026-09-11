#!/usr/bin/env python3
"""检查 implement-team 的输入、确认门禁与 AgentTeam 协议。"""

from pathlib import Path
import sys


REQUIRED = (
    "name: implement-team",
    "description:",
    "disable-model-invocation: true",
    "input.kind: prd-spec-input",
    "PRD",
    "spec.md",
    ".scratch/<feature>/issues/",
    "direct-task",
    "TeamCreate",
    "AgentTeam",
    "唯一 coordinator",
    "派发者",
    "解锁者",
    "独立核验者",
    "frontier",
    "唯一执行单元",
    "冲突",
    "矩阵",
    "无冲突",
    "等待用户确认",
    "没有任何实现 tickets",
    "只完成输入评估并停止",
    "确认前不创建 team",
    "/implement",
    "dependsOn",
    "CONFLICT",
    "maxConcurrency",
    "maxRepairRounds",
    "protectedPaths",
    "DAG",
    "只沿依赖后代传播",
    "独立核验",
    "fail-closed",
    "Status: resolved",
    "evidence",
    "references/agent-team-protocol.md",
)
LEGACY = ("implement-" + "fast", "implement-" + "tmux", "wayfinder-" + "map", "spec-" + "tickets")


def check_protocol(text: str) -> list[str]:
    errors = [f"缺少协议字段：{token}" for token in REQUIRED if token not in text]
    if "/wayfinder" in text:
        errors.append("implement-team 只调用 /implement，不调用探索 skill")
    if "allowedPaths" in text:
        errors.append("allowedPaths 已移除（ADR-0001）")
    for legacy in LEGACY:
        if legacy.lower() in text.lower():
            errors.append(f"包含已移除名称：{legacy}")
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[1] / "SKILL.md"
    errors = check_protocol(path.read_text())
    if errors:
        for error in errors:
            print(f"协议失败：{error}")
        return 1
    print("协议通过：implement-team 输入、确认门禁、frontier 调度、核验和公共协议有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
