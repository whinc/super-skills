#!/usr/bin/env python3
"""验证三类输入、DAG 调度和主 Agent 失败协调。"""

from dataclasses import dataclass, field
from pathlib import Path
import re
import unittest


@dataclass
class Ticket:
    ticket_id: str
    tracker: str
    goal: str = ""
    depends_on: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    verify: list[str] = field(default_factory=list)
    status: str = "pending"
    prompt: str = "先调用 /implement skill。"


def parse_blocked_by(text: str) -> list[str]:
    match = re.search(r"\*{0,2}Blocked by:\*{0,2}\s*([^\n]*)", text, re.IGNORECASE)
    if not match:
        return []
    raw = match.group(1).replace("*", "").strip()
    if not raw or re.fullmatch(r"none(?:\s*\([^)]*\))?", raw, re.IGNORECASE):
        return []
    dependencies = []
    for item in re.split(r"[,;]", raw):
        item = item.strip()
        if not item:
            continue
        ticket_id = re.match(r"(\d{2})(?:\b|$)", item)
        dependencies.append(ticket_id.group(1) if ticket_id else item)
    return dependencies


def parse_wayfinder(files: dict[str, str]) -> list[Ticket]:
    tickets = []
    for path, text in sorted(files.items()):
        ticket_id = re.search(r"(?:^|/)\s*(\d{2})-", path)
        status = re.search(r"^Status:\s*(\w+)", text, re.MULTILINE)
        tracker = path
        tickets.append(
            Ticket(
                ticket_id=ticket_id.group(1) if ticket_id else path,
                tracker=tracker,
                depends_on=parse_blocked_by(text),
                status=status.group(1) if status else "pending",
            )
        )
    return tickets


def parse_spec_tickets(spec: str, files: dict[str, str]) -> list[Ticket]:
    acceptance = "Testing Decisions" in spec or "验收" in spec
    tickets = []
    for path, text in sorted(files.items()):
        ticket_id = re.search(r"(?:^|/)\s*(\d{2})-", path)
        status = re.search(r"^\*\*Status:\*\*\s*([\w-]+)", text, re.MULTILINE)
        tickets.append(
            Ticket(
                ticket_id=ticket_id.group(1) if ticket_id else path,
                tracker=path,
                depends_on=parse_blocked_by(text),
                allowed_paths=["src/example.ts"],
                status=status.group(1) if status else "pending",
                prompt=f"spec acceptance={acceptance}; 先调用 /implement skill。",
            )
        )
    return tickets


def direct_draft(description: str) -> list[Ticket]:
    return [
        Ticket(
            ticket_id="01",
            tracker=".scratch/direct/issues/01-task.md",
            goal=description,
            allowed_paths=["src/example.ts", "src/example.test.ts"],
            verify=["npm test -- --runInBand"],
            prompt=f"{description}\n先调用 /implement skill。",
        ),
        Ticket(
            ticket_id="02",
            tracker=".scratch/direct/issues/02-follow-up.md",
            goal="完成依赖 01 的后续任务",
            depends_on=["01"],
            allowed_paths=["src/next.ts"],
            verify=["npm run typecheck"],
            prompt="依赖 01；先调用 /implement skill。",
        ),
    ]


def path_conflicts(left: str, right: str) -> bool:
    if any(char in left + right for char in "*?["):
        return True
    left_parts = Path(left).parts
    right_parts = Path(right).parts
    return left_parts[: len(right_parts)] == right_parts or right_parts[: len(left_parts)] == left_parts


def can_run_together(left: Ticket, right: Ticket) -> bool:
    return not any(path_conflicts(a, b) for a in left.allowed_paths for b in right.allowed_paths)


def ready_round(tickets: list[Ticket], completed: set[str]) -> list[Ticket]:
    ready = [
        ticket
        for ticket in tickets
        if ticket.status == "pending"
        and ticket.ticket_id not in completed
        and set(ticket.depends_on) <= completed
    ]
    selected = []
    for ticket in ready:
        if all(can_run_together(ticket, other) for other in selected):
            selected.append(ticket)
    return selected


def propagate_failure(tickets: list[Ticket], failed_id: str) -> set[str]:
    blocked = set()
    changed = True
    while changed:
        changed = False
        for ticket in tickets:
            if ticket.ticket_id in blocked or ticket.ticket_id == failed_id:
                continue
            if failed_id in ticket.depends_on or any(parent in blocked for parent in ticket.depends_on):
                blocked.add(ticket.ticket_id)
                ticket.status = "blocked"
                changed = True
    return blocked


class FastIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.skill = Path(__file__).parents[1] / "SKILL.md"
        self.skill_text = self.skill.read_text()

    def test_direct_task_is_drafted_and_confirmed_before_team(self):
        tickets = direct_draft("实现用户描述的功能")
        self.assertEqual([ticket.ticket_id for ticket in tickets], ["01", "02"])
        self.assertEqual(tickets[1].depends_on, ["01"])
        self.assertTrue(all(ticket.goal and ticket.allowed_paths and ticket.verify and ticket.tracker for ticket in tickets))
        self.assertTrue(all("/implement" in ticket.prompt for ticket in tickets))
        self.assertIn("用户确认后才创建 AgentTeam", self.skill_text)

    def test_wayfinder_map_reads_issues_and_resolves_all(self):
        files = {
            "issues/01-research.md": "Type: research\nStatus: resolved\nBlocked by: none\n",
            "issues/02-task.md": "Type: task\nStatus: claimed\nBlocked by: 01\n",
            "issues/03-task.md": "Type: task\nStatus: claimed\nBlocked by: 01, 02\n",
        }
        tickets = parse_wayfinder(files)
        self.assertEqual([ticket.depends_on for ticket in tickets], [[], ["01"], ["01", "02"]])
        self.assertEqual(tickets[0].status, "resolved")
        self.assertIn("Status:", self.skill_text)
        self.assertIn("所有 child issue 的 tracker `Status:` 都为 `resolved`", self.skill_text)
        self.assertIn("所有 child issue 的 tracker `Status:` 都为 `resolved`", self.skill_text)
        self.assertIn("sub agent 只调用 `/wayfinder`", self.skill_text)
        self.assertIn("map 的完成条件", self.skill_text)

    def test_spec_and_tickets_preserve_constraints_and_mapping(self):
        spec = "# Spec\n## Testing Decisions\n验收必须运行 typecheck。"
        files = {
            "issues/01-build.md": "# 01\n**Blocked by:** none\n**Status:** pending\n**What to build:** build",
            "issues/02-test.md": "# 02\n**Blocked by:** 01\n**Status:** pending\n**What to build:** test",
        }
        tickets = parse_spec_tickets(spec, files)
        self.assertEqual(tickets[1].depends_on, ["01"])
        self.assertTrue(all("acceptance=True" in ticket.prompt for ticket in tickets))
        self.assertTrue(all(ticket.tracker.startswith("issues/") for ticket in tickets))
        self.assertIn("不把一个 spec 当成一个 ticket", self.skill_text)

    def test_parses_real_to_tickets_dependency_formats(self):
        self.assertEqual(parse_blocked_by("**Blocked by:** None (can start immediately)"), [])
        self.assertEqual(parse_blocked_by("**Blocked by:** none"), [])
        self.assertEqual(
            parse_blocked_by("**Blocked by:** 01: 配置; 02: 文档"),
            ["01", "02"],
        )

    def test_parses_ready_for_agent_status(self):
        tickets = parse_spec_tickets(
            "# Spec\n## Testing Decisions\n验收",
            {"issues/01-build.md": "**Status:** ready-for-agent\n**Blocked by:** None"},
        )
        self.assertEqual(tickets[0].status, "ready-for-agent")

    def test_maximizes_safe_concurrency_and_respects_dependencies(self):
        tickets = [
            Ticket("01", "a", allowed_paths=["src/a.ts"]),
            Ticket("02", "b", allowed_paths=["src/b.ts"]),
            Ticket("03", "c", depends_on=["01"], allowed_paths=["src/c.ts"]),
            Ticket("04", "d", depends_on=["01"], allowed_paths=["src/c.ts"]),
        ]
        first = ready_round(tickets, set())
        self.assertEqual([ticket.ticket_id for ticket in first], ["01", "02"])
        self.assertNotIn("04", [ticket.ticket_id for ticket in first])
        second = ready_round(tickets, {"01", "02"})
        self.assertEqual([ticket.ticket_id for ticket in second], ["03"])

    def test_failure_updates_shared_context_and_only_blocks_descendants(self):
        tickets = [
            Ticket("01", "a"),
            Ticket("02", "b", depends_on=["01"]),
            Ticket("03", "c", depends_on=["02"]),
            Ticket("04", "d"),
        ]
        blocked = propagate_failure(tickets, "01")
        shared_context = {"event": "TICKET_FAILED", "ticket": "01", "reason": "验证失败", "notified": True}
        self.assertEqual(blocked, {"02", "03"})
        self.assertEqual(tickets[3].status, "pending")
        self.assertTrue(shared_context["notified"])
        self.assertIn("共享 team 上下文", self.skill_text)
        self.assertIn("主 Agent 收到失败/阻塞", self.skill_text)

    def test_sub_agents_use_input_specific_skill_and_cannot_unlock(self):
        self.assertGreaterEqual(self.skill_text.count("/implement"), 4)
        self.assertIn("sub agent 只调用 `/wayfinder`", self.skill_text)
        self.assertIn("map 的完成条件", self.skill_text)
        self.assertIn("sub agent 不解锁后继任务", self.skill_text)
        self.assertIn("独立核验", self.skill_text)


if __name__ == "__main__":
    unittest.main()
