#!/usr/bin/env python3
"""implement-team 的输入映射、确认门禁、DAG 和失败传播集成测试。"""

from dataclasses import dataclass, field
from pathlib import Path
import re
import unittest


@dataclass
class Ticket:
    ticket_id: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"


def parse_dependencies(text: str) -> list[str]:
    match = re.search(r"(?:Blocked by|dependsOn):\s*([^\n]+)", text, re.IGNORECASE)
    if not match or match.group(1).strip().lower() in {"none", "无"}:
        return []
    return [part.strip().split(":", 1)[0] for part in re.split(r"[,;]", match.group(1)) if part.strip()]


def parse_tickets(files: dict[str, str]) -> list[Ticket]:
    result = []
    for path, text in sorted(files.items()):
        match = re.search(r"(?:^|/)\s*(\d{2})-", path)
        result.append(Ticket(match.group(1), parse_dependencies(text)))
    return result


def merge_sources(prd: str | None, spec: str | None) -> dict[str, object]:
    if not prd and not spec:
        return {"sources": [], "conflicts": [], "needs_confirmation": False}
    conflicts = []
    if prd and spec and "验收:" in prd and "验收:" in spec and prd.split("验收:", 1)[1].strip() != spec.split("验收:", 1)[1].strip():
        conflicts.append({"field": "验收", "prd": prd, "spec": spec})
    return {"sources": [source for source, value in (("prd.md", prd), ("spec.md", spec)) if value], "conflicts": conflicts, "needs_confirmation": True}


def frontier_round(tickets: list[Ticket], resolved: set[str], max_concurrency: int = 4) -> list[Ticket]:
    selected = []
    for ticket in tickets:
        if len(selected) >= max_concurrency:
            break
        if ticket.status != "pending" or ticket.ticket_id in resolved or not set(ticket.depends_on) <= resolved:
            continue
        selected.append(ticket)
    return selected


def propagate_failure(tickets: list[Ticket], failed: str) -> set[str]:
    blocked = set()
    changed = True
    while changed:
        changed = False
        for ticket in tickets:
            if ticket.ticket_id == failed or ticket.ticket_id in blocked:
                continue
            if failed in ticket.depends_on or any(parent in blocked for parent in ticket.depends_on):
                ticket.status = "blocked"
                blocked.add(ticket.ticket_id)
                changed = True
    return blocked


class ImplementTeamIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parents[1]
        self.skill = (self.root / "SKILL.md").read_text()

    def test_prd_spec_are_merged_and_always_confirmed(self):
        result = merge_sources("范围\n验收: A", "约束\n验收: B")
        self.assertEqual(result["sources"], ["prd.md", "spec.md"])
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertTrue(result["needs_confirmation"])
        self.assertTrue(merge_sources("范围", "约束")["needs_confirmation"])
        self.assertIn("矩阵", self.skill)
        self.assertIn("无冲突", self.skill)
        self.assertIn("等待用户确认", self.skill)
        self.assertIn("input.kind: prd-spec-input", self.skill)

    def test_tickets_are_required_and_actual_issue_files_are_units(self):
        tickets = parse_tickets({".scratch/f/issues/01-a.md": "Blocked by: none", ".scratch/f/issues/02-b.md": "dependsOn: 01"})
        self.assertEqual([ticket.ticket_id for ticket in tickets], ["01", "02"])
        self.assertEqual(tickets[1].depends_on, ["01"])
        self.assertIn("实际 `.scratch/<feature>/issues/`", self.skill)
        self.assertIn("没有任何实现 tickets", self.skill)
        self.assertIn("只完成输入评估并停止", self.skill)
        self.assertIn("唯一执行单元", self.skill)

    def test_confirmation_precedes_team_creation(self):
        self.assertLess(self.skill.index("确认前不创建 team"), self.skill.index("确认后才用原生 `TeamCreate`"))

    def test_direct_task_boundary_stays_outside_team(self):
        self.assertIn("direct-task", self.skill)
        self.assertIn("直接调用 `/implement`", self.skill)
        self.assertIn("不创建 `TeamCreate` 或 `AgentTeam`", self.skill)

    def test_frontier_maximizes_concurrency_within_cap(self):
        tickets = [Ticket("01"), Ticket("02"), Ticket("03"), Ticket("04"), Ticket("05"), Ticket("06")]
        self.assertEqual([ticket.ticket_id for ticket in frontier_round(tickets, set())], ["01", "02", "03", "04"])
        self.assertEqual([ticket.ticket_id for ticket in frontier_round(tickets, set(), max_concurrency=2)], ["01", "02"])
        gated = [Ticket("01"), Ticket("02"), Ticket("03", ["01"]), Ticket("04", ["01"])]
        self.assertEqual([ticket.ticket_id for ticket in frontier_round(gated, set())], ["01", "02"])
        self.assertEqual([ticket.ticket_id for ticket in frontier_round(gated, {"01"})], ["02", "03", "04"])
        self.assertIn("frontier", self.skill)
        self.assertIn("CONFLICT", self.skill)
        self.assertIn("maxConcurrency", self.skill)
        self.assertNotIn("allowedPaths", self.skill)

    def test_failure_only_propagates_to_descendants(self):
        tickets = [Ticket("01"), Ticket("02", ["01"]), Ticket("03", ["02"]), Ticket("04")]
        self.assertEqual(propagate_failure(tickets, "01"), {"02", "03"})
        self.assertEqual(tickets[3].status, "pending")
        self.assertIn("只沿依赖后代传播", self.skill)
        self.assertIn("独立分支继续", self.skill)

    def test_agent_skill_and_tracker_protocol_are_isolated(self):
        self.assertIn("/implement", self.skill)
        self.assertNotIn("/wayfinder", self.skill)
        self.assertIn("Status: resolved", self.skill)
        self.assertIn("evidence", self.skill)
        self.assertIn("fail-closed", self.skill)
        self.assertIn("references/agent-team-protocol.md", self.skill)

    def test_protocol_ships_and_matches_sibling_copy(self):
        protocol = self.root / "references" / "agent-team-protocol.md"
        self.assertTrue(protocol.exists())
        sibling = self.root.parent / "wayfinder-team" / "references" / "agent-team-protocol.md"
        if sibling.exists():
            self.assertEqual(protocol.read_text(), sibling.read_text())

    def test_references_stay_inside_the_skill_folder(self):
        outside = re.compile(r"(^|[^\w/.])docs/|\.\./|/Users/|/home/")
        for path in sorted(self.root.rglob("*.md")):
            self.assertIsNone(outside.search(path.read_text()), f"{path} 引用了 skill 目录外的路径")


if __name__ == "__main__":
    unittest.main()
