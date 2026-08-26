#!/usr/bin/env python3
"""回归测试 implement-fast 的 AgentTeam 协议检查。"""

from pathlib import Path
import subprocess
import tempfile
import unittest


CHECKER = Path(__file__).with_name("check-fast-protocol.py")
SKILL = Path(__file__).parents[1] / "SKILL.md"


VALID = """# Implement fast

TeamCreate creates one AgentTeam. The main-agent coordinator owns shared context.
Every sub agent must call /implement before executing a task.

Inputs: direct task, map.md, spec.md and tickets.
Each ticket has dependsOn, allowedPaths, Status: and resolved tracker state.
Use pending → running → verifying → done.
TICKET_DONE, TICKET_FAILED, TICKET_BLOCKED are the terminal messages.
主 Agent 只沿依赖后代传播失败；不确定范围禁止并行。确认前不创建 team。
"""


BUNDLE_REFERENCES = {
    "direct-task.md": "# direct-task\n先调用 /implement；ticket 包含 dependsOn。",
    "wayfinder-map.md": "# wayfinder-map\n读取 map.md，使用 /wayfinder，更新 Status: resolved。",
    "spec-tickets.md": "# spec-tickets\n读取 spec.md，先调用 /implement。",
    "manifest-template.md": "## 终态协议\nTICKET_DONE TICKET_FAILED TICKET_BLOCKED",
}
BUNDLE_SKILL = VALID + "\n".join(
    f"references/{name}" for name in BUNDLE_REFERENCES
)


class FastProtocolTests(unittest.TestCase):
    def run_checker(self, content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", suffix=".md") as fixture:
            fixture.write(content)
            fixture.flush()
            return self.run_checker_path(Path(fixture.name))

    def run_checker_path(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(CHECKER), str(path)],
            capture_output=True,
            text=True,
        )

    def run_bundle_checker(self, skill: str = BUNDLE_SKILL, references=None):
        references = BUNDLE_REFERENCES if references is None else references
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references_dir = root / "references"
            references_dir.mkdir()
            (root / "SKILL.md").write_text(skill)
            for name, content in references.items():
                (references_dir / name).write_text(content)
            return self.run_checker_path(root / "SKILL.md")

    def assert_rejected(self, content: str, message: str):
        result = self.run_checker(content)
        self.assertNotEqual(result.returncode, 0, message)

    def test_valid_agent_team_protocol(self):
        result = self.run_checker(VALID)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_skill_bundle_passes(self):
        result = self.run_checker_path(SKILL)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bundle_checks_references_and_pointers(self):
        result = self.run_bundle_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        missing = dict(BUNDLE_REFERENCES)
        del missing["direct-task.md"]
        result = self.run_bundle_checker(references=missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("direct-task.md", result.stdout)

        result = self.run_bundle_checker(skill=BUNDLE_SKILL.replace("references/direct-task.md", ""))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("指针", result.stdout)

    def test_banned_terms_are_checked_in_references(self):
        references = dict(BUNDLE_REFERENCES)
        references["direct-task.md"] += "\ntmux send-keys"
        result = self.run_bundle_checker(references=references)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tmux", result.stdout.lower())

    def test_rejects_tmux_residue(self):
        self.assert_rejected(VALID + "\ntmux send-keys", "不得残留旧调度协议")

    def test_requires_implement_skill(self):
        self.assert_rejected(VALID.replace("/implement", "manual implementation"), "必须调用 /implement")

    def test_requires_dependency_and_path_fields(self):
        self.assert_rejected(VALID.replace("dependsOn", "dependency"), "必须声明 dependsOn")
        self.assert_rejected(VALID.replace("allowedPaths", "paths"), "必须声明 allowedPaths")

    def test_requires_tracker_resolution(self):
        self.assert_rejected(VALID.replace("resolved", "finished"), "必须核验 resolved")

    def test_requires_shared_coordinator(self):
        self.assert_rejected(VALID.replace("shared context", "private context"), "必须声明共享上下文")
        self.assert_rejected(VALID.replace("coordinator", "worker"), "必须声明主 Agent 协调者")

    def test_requires_confirmation_gate(self):
        self.assert_rejected(VALID.replace("确认前不创建 team。", "立即创建 team。"), "确认前不得创建 team")

    def test_requires_failure_cascade_rule(self):
        self.assert_rejected(VALID.replace("只沿依赖后代传播失败", "停止全部任务"), "失败必须按依赖后代传播")


if __name__ == "__main__":
    unittest.main()
