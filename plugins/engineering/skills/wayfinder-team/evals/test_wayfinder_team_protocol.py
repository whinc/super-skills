#!/usr/bin/env python3
"""wayfinder-team checker 的单元测试。"""

from pathlib import Path
import subprocess
import tempfile
import unittest


CHECKER = Path(__file__).with_name("check-wayfinder-team-protocol.py")
SKILL = Path(__file__).parents[1] / "SKILL.md"

VALID = """---
name: wayfinder-team
description: map exploration
disable-model-invocation: true
---
input.kind: map-issues map.md 同目录 `issues/` TeamCreate AgentTeam
唯一 coordinator 派发者 解锁者 独立核验者 frontier /wayfinder
## Answer Status: resolved evidence blocked DAG maxConcurrency
maxRepairRounds protectedPaths 只沿依赖后代传播 独立核验 fail-closed
等待用户确认 确认前不创建 team 不确定 全量并发
docs/agents/agent-team-protocol.md
"""


class WayfinderTeamProtocolTests(unittest.TestCase):
    def run_checker(self, content: str) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile("w", suffix=".md") as fixture:
            fixture.write(content)
            fixture.flush()
            return subprocess.run(["python3", str(CHECKER), fixture.name], capture_output=True, text=True)

    def test_real_skill_passes(self):
        result = subprocess.run(["python3", str(CHECKER), str(SKILL)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_valid_protocol_passes(self):
        result = self.run_checker(VALID)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_requires_confirmation_gate(self):
        result = self.run_checker(VALID.replace("确认前不创建 team", "直接创建 team"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("等待用户确认", "自行决定"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_frontier_and_concurrency_cap(self):
        result = self.run_checker(VALID.replace("frontier", "ready ticket"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("maxConcurrency", "并发无上限"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("不确定 全量并发", "自由并行"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_resolution_fields(self):
        result = self.run_checker(VALID.replace("## Answer", "回答"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("Status: resolved", "Status: claimed"))
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_implementation_skill_and_allowedpaths(self):
        result = self.run_checker(VALID + " /implement")
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID + " allowedPaths: []")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
