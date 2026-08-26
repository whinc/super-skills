#!/usr/bin/env python3
"""回归测试 implement-fast 的 AgentTeam 协议检查。"""

from pathlib import Path
import subprocess
import tempfile
import unittest


CHECKER = Path(__file__).with_name("check-fast-protocol.py")


VALID = """# Implement fast

TeamCreate creates one AgentTeam. The main-agent coordinator owns shared context.
Every sub agent must call /implement before executing a task.

Inputs: direct task, map.md, spec.md and tickets.
Each ticket has dependsOn, allowedPaths, Status: and resolved tracker state.
Use pending → running → verifying → done.
TICKET_DONE, TICKET_FAILED, TICKET_BLOCKED are the terminal messages.
主 Agent 只沿依赖后代传播失败；不确定范围禁止并行。确认前不创建 team。
"""


class FastProtocolTests(unittest.TestCase):
    def run_checker(self, content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", suffix=".md") as fixture:
            fixture.write(content)
            fixture.flush()
            return subprocess.run(
                ["python3", str(CHECKER), fixture.name],
                capture_output=True,
                text=True,
            )

    def assert_rejected(self, content: str, message: str):
        result = self.run_checker(content)
        self.assertNotEqual(result.returncode, 0, message)

    def test_valid_agent_team_protocol(self):
        result = self.run_checker(VALID)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
