#!/usr/bin/env python3
"""implement-team checker 的单元测试。"""

from pathlib import Path
import subprocess
import tempfile
import unittest


CHECKER = Path(__file__).with_name("check-implement-team-protocol.py")
SKILL = Path(__file__).parents[1] / "SKILL.md"

VALID = """---
name: implement-team
description: PRD spec implementation
disable-model-invocation: true
---
input.kind: prd-spec-input PRD spec.md .scratch/<feature>/issues/ direct-task
TeamCreate AgentTeam 唯一 coordinator 派发者 解锁者 独立核验者 frontier
唯一执行单元 冲突矩阵无冲突 等待用户确认 没有任何实现 tickets
只完成输入评估并停止 确认前不创建 team /implement dependsOn CONFLICT
maxConcurrency maxRepairRounds protectedPaths DAG 只沿依赖后代传播
独立核验 fail-closed Status: resolved evidence
references/agent-team-protocol.md
"""


class ImplementTeamProtocolTests(unittest.TestCase):
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

    def test_requires_confirmation_and_ticket_gate(self):
        result = self.run_checker(VALID.replace("确认前不创建 team", "直接创建 team"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("没有任何实现 tickets", "有 tickets"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_frontier_and_concurrency_cap(self):
        result = self.run_checker(VALID.replace("frontier", "ready ticket"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("maxConcurrency", "并发无上限"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_implement_and_safety_fields(self):
        for old, new in (("/implement", "手工实现"), ("dependsOn", "dependency"), ("CONFLICT", "自由并行"), ("fail-closed", "开放通过")):
            with self.subTest(old=old):
                result = self.run_checker(VALID.replace(old, new))
                self.assertNotEqual(result.returncode, 0)

    def test_rejects_exploration_skill_and_allowedpaths(self):
        result = self.run_checker(VALID + " /wayfinder")
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID + " allowedPaths: []")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
