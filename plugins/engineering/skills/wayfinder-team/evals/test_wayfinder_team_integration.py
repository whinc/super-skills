#!/usr/bin/env python3
"""wayfinder-team 的 map 输入、终态、DAG 和隔离集成测试。"""

from dataclasses import dataclass, field
from pathlib import Path
import re
import unittest


@dataclass
class Issue:
    issue_id: str
    status: str = "claimed"
    depends_on: list[str] = field(default_factory=list)


def parse_blocked(text: str) -> list[str]:
    match = re.search(r"Blocked by:\s*([^\n]+)", text, re.IGNORECASE)
    if not match or match.group(1).strip().lower().startswith("none"):
        return []
    return [item.strip().split(":", 1)[0] for item in match.group(1).split(",") if item.strip()]


def parse_issues(files: dict[str, str]) -> list[Issue]:
    issues = []
    for path, text in sorted(files.items()):
        match = re.search(r"(?:^|/)\s*(\d{2})-", path)
        status = re.search(r"^Status:\s*(\w+)", text, re.MULTILINE)
        issues.append(Issue(match.group(1), status.group(1) if status else "claimed", parse_blocked(text)))
    return issues


def can_resolve(issue_text: str, evidence: list[str]) -> bool:
    return "## Answer" in issue_text and re.search(r"^Status:\s*resolved$", issue_text, re.MULTILINE) is not None and bool(evidence)


def ready_round(issues: list[Issue], resolved: set[str], max_concurrency: int = 4) -> list[Issue]:
    selected = []
    for issue in issues:
        if len(selected) >= max_concurrency:
            break
        if issue.status == "resolved" or issue.issue_id in resolved or not set(issue.depends_on) <= resolved:
            continue
        selected.append(issue)
    return selected


def propagate_failure(issues: list[Issue], failed: str) -> set[str]:
    blocked = set()
    changed = True
    while changed:
        changed = False
        for issue in issues:
            if issue.issue_id == failed or issue.issue_id in blocked:
                continue
            if failed in issue.depends_on or any(parent in blocked for parent in issue.depends_on):
                issue.status = "blocked"
                blocked.add(issue.issue_id)
                changed = True
    return blocked


class WayfinderTeamIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parents[1]
        self.skill = (self.root / "SKILL.md").read_text()
        self.references = {path.name: path.read_text() for path in (self.root / "references").glob("*.md")}

    def test_only_map_and_same_directory_issues_are_parsed(self):
        issues = parse_issues({"issues/01-research.md": "Type: research\nStatus: claimed\nBlocked by: none", "issues/02-prototype.md": "Type: prototype\nStatus: resolved\nBlocked by: 01"})
        self.assertEqual([issue.issue_id for issue in issues], ["01", "02"])
        self.assertEqual(issues[1].depends_on, ["01"])
        self.assertIn("只处理一个 `map.md` 与其同目录 `issues/`", self.skill)
        self.assertIn("map 本身不是 ticket", self.skill)

    def test_resolution_requires_answer_status_and_evidence(self):
        resolved = "## Answer\n结论\nStatus: resolved"
        self.assertTrue(can_resolve(resolved, [".scratch/runs/01.log"]))
        self.assertFalse(can_resolve(resolved, []))
        self.assertFalse(can_resolve("Status: resolved", ["evidence.log"]))
        self.assertIn("## Answer", self.references["map-issues.md"])
        self.assertIn("Status: resolved", self.skill)
        self.assertIn("evidence", self.skill)

    def test_code_or_config_changes_are_blocked_without_automatic_implementation(self):
        self.assertIn("代码实现/配置变更的 issue 必须 `blocked`", self.skill)
        self.assertIn("不自动调用实现技能", self.skill)
        self.assertNotIn("/implement", self.skill)
        self.assertNotIn("/implement", self.references["map-issues.md"])

    def test_confirmation_precedes_team_creation(self):
        self.assertIn("确认前不创建 team", self.skill)
        self.assertIn("确认后才创建一个原生 `AgentTeam`", self.skill)

    def test_dag_maximizes_concurrency_within_cap_without_path_checks(self):
        issues = [Issue("01"), Issue("02"), Issue("03"), Issue("04"), Issue("05"), Issue("06")]
        self.assertEqual([issue.issue_id for issue in ready_round(issues, set())], ["01", "02", "03", "04"])
        self.assertEqual([issue.issue_id for issue in ready_round(issues, set(), max_concurrency=2)], ["01", "02"])
        gated = [Issue("01"), Issue("02"), Issue("03", depends_on=["01"]), Issue("04", depends_on=["01"])]
        self.assertEqual([issue.issue_id for issue in ready_round(gated, set())], ["01", "02"])
        self.assertEqual([issue.issue_id for issue in ready_round(gated, {"01"})], ["02", "03", "04"])
        self.assertIn("maxConcurrency", self.skill)
        self.assertNotIn("allowedPaths", self.skill)

    def test_failure_only_blocks_descendants(self):
        issues = [Issue("01"), Issue("02", depends_on=["01"]), Issue("03", depends_on=["02"]), Issue("04")]
        self.assertEqual(propagate_failure(issues, "01"), {"02", "03"})
        self.assertEqual(issues[3].status, "claimed")
        self.assertIn("只沿依赖后代传播", self.skill)
        self.assertIn("独立分支继续", self.skill)
        self.assertIn("独立核验", self.skill)
        self.assertIn("docs/agents/agent-team-protocol.md", self.references["manifest-template.md"])


if __name__ == "__main__":
    unittest.main()
