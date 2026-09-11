#!/usr/bin/env python3
"""检查 implement-team 的输入边界、确认门禁与 protocol 机制契约。"""

from pathlib import Path
import sys


SKILL_TOKENS = (
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
    "frontier",
    "maxConcurrency",
    "protectedPaths",
    "DAG",
    "只沿依赖后代传播",
    "独立核验",
    "fail-closed",
    "Status: resolved",
    "evidence",
    "references/agent-team-protocol.md",
)
PROTOCOL_TOKENS = (
    "唯一 coordinator",
    "派发者",
    "解锁者",
    "独立核验者",
    "frontier",
    "context 卫生",
    "终态事件",
    "TICKET_RESOLVED",
    "TICKET_BLOCKED",
    "fail-closed",
    "evidenceDir",
    "tempDir",
    "maxConcurrency",
    "protectedPaths",
    "CONFLICT",
    "Status: resolved",
)
LEGACY = ("implement-" + "fast", "implement-" + "tmux", "wayfinder-" + "map", "spec-" + "tickets")
REMOVED = ("maxRepairRounds",)


def check_skill(text: str) -> list[str]:
    errors = [f"缺少 SKILL 字段：{token}" for token in SKILL_TOKENS if token not in text]
    if "/wayfinder" in text:
        errors.append("implement-team 只调用 /implement，不调用探索 skill")
    if "allowedPaths" in text:
        errors.append("allowedPaths 已移除（ADR-0001）")
    for removed in REMOVED:
        if removed in text:
            errors.append(f"包含已移除字段：{removed}")
    for legacy in LEGACY:
        if legacy.lower() in text.lower():
            errors.append(f"包含已移除名称：{legacy}")
    return errors


def check_protocol(text: str) -> list[str]:
    errors = [f"缺少机制字段：{token}" for token in PROTOCOL_TOKENS if token not in text]
    for removed in REMOVED:
        if removed in text:
            errors.append(f"协议包含已移除字段：{removed}")
    for legacy in LEGACY:
        if legacy.lower() in text.lower():
            errors.append(f"协议包含已移除名称：{legacy}")
    return errors


def main() -> int:
    root = Path(__file__).parents[1]
    skill_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "SKILL.md"
    protocol_path = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "references" / "agent-team-protocol.md"
    errors = check_skill(skill_path.read_text()) + check_protocol(protocol_path.read_text())
    if errors:
        for error in errors:
            print(f"协议失败：{error}")
        return 1
    print("协议通过：implement-team 输入边界、确认门禁、frontier 调度与 protocol 机制契约有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
