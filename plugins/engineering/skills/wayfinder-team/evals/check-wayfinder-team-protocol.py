#!/usr/bin/env python3
"""检查 wayfinder-team 的 map 输入与 AgentTeam 协议。"""

from pathlib import Path
import sys


REQUIRED = (
    "name: wayfinder-team",
    "description:",
    "disable-model-invocation: true",
    "input.kind: map-issues",
    "map.md",
    "同目录 `issues/`",
    "TeamCreate",
    "AgentTeam",
    "唯一 coordinator",
    "派发者",
    "解锁者",
    "独立核验者",
    "frontier",
    "/wayfinder",
    "## Answer",
    "Status: resolved",
    "evidence",
    "blocked",
    "DAG",
    "maxConcurrency",
    "maxRepairRounds",
    "protectedPaths",
    "只沿依赖后代传播",
    "独立核验",
    "fail-closed",
    "等待用户确认",
    "确认前不创建 team",
    "不确定",
    "全量并发",
    "references/agent-team-protocol.md",
)
LEGACY = ("implement-" + "fast", "implement-" + "tmux", "wayfinder-" + "map", "spec-" + "tickets")


def check_protocol(text: str) -> list[str]:
    errors = [f"缺少协议字段：{token}" for token in REQUIRED if token not in text]
    if "/implement" in text:
        errors.append("wayfinder-team 只调用 /wayfinder，不调用实现 skill")
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
    print("协议通过：wayfinder-team 输入、frontier 调度、终态、核验和公共协议有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
