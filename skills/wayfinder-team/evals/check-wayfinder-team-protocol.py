#!/usr/bin/env python3
"""检查 wayfinder-team 的 map 输入边界、确认门禁与 protocol 机制契约。"""

from pathlib import Path
import sys


SKILL_TOKENS = (
    "name: wayfinder-team",
    "description:",
    "disable-model-invocation: true",
    "input.kind: map-issues",
    "map.md",
    "同目录 `issues/`",
    ".scratch/<effort>/",
    "TeamCreate",
    "AgentTeam",
    "/wayfinder",
    "## Answer",
    "Status: resolved",
    "evidence",
    "blocked",
    "DAG",
    "frontier",
    "全部并发派发",
    "只沿依赖后代传播",
    "独立核验",
    "fail-closed",
    "等待用户确认",
    "确认前不创建 team",
    "不产生代码提交",
    "立即补派",
    "references/agent-team-protocol.md",
)
PROTOCOL_TOKENS = (
    "唯一 coordinator",
    "派发者",
    "解锁者",
    "独立核验者",
    "frontier",
    "全部并发派发",
    "等待与唤醒",
    "context 卫生",
    "终态事件",
    "TICKET_RESOLVED",
    "TICKET_BLOCKED",
    "fail-closed",
    "evidenceDir",
    "tempDir",
    "integrationVerify",
    "Status: resolved",
    "立即补派",
)
LEGACY = ("implement-" + "fast", "implement-" + "tmux", "wayfinder-" + "map", "spec-" + "tickets")
REMOVED = ("maxRepairRounds", "CONFLICT", "verifying", "maxConcurrency", "protectedPaths")


def check_skill(text: str) -> list[str]:
    errors = [f"缺少 SKILL 字段：{token}" for token in SKILL_TOKENS if token not in text]
    if "/implement" in text:
        errors.append("wayfinder-team 只调用 /wayfinder，不调用实现 skill")
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
    print("协议通过：wayfinder-team 输入边界、确认门禁与 protocol 机制契约有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
