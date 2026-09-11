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
input.kind: map-issues map.md 同目录 `issues/` .scratch/<effort>/ TeamCreate AgentTeam
唯一 coordinator 派发者 解锁者 独立核验者 frontier 等待与唤醒 立即补派
/wayfinder ## Answer Status: resolved evidence blocked DAG 全部并发派发
只沿依赖后代传播 独立核验 fail-closed
等待用户确认 确认前不创建 team 不产生代码提交
references/agent-team-protocol.md integrationVerify
TICKET_RESOLVED TICKET_BLOCKED context 卫生 终态事件 evidenceDir tempDir
"""


class WayfinderTeamProtocolTests(unittest.TestCase):
    def run_checker(self, content: str, protocol: str | None = None) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile("w", suffix=".md") as fixture:
            fixture.write(content)
            fixture.flush()
            command = ["python3", str(CHECKER), fixture.name]
            if protocol is not None:
                command.append(protocol)
            return subprocess.run(command, capture_output=True, text=True)

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

    def test_requires_frontier_and_dispatch_contract(self):
        result = self.run_checker(VALID.replace("frontier", "ready ticket"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("全部并发派发", "按批派发"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("立即补派", "等待同批终态"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_resolution_fields(self):
        result = self.run_checker(VALID.replace("## Answer", "回答"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("Status: resolved", "Status: claimed"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_input_location_convention(self):
        result = self.run_checker(VALID.replace(".scratch/<effort>/", "任意目录"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_exploration_discipline_fields(self):
        for old, new in (("/wayfinder", "手工探索"), ("不产生代码提交", "允许提交"), ("fail-closed", "开放通过")):
            with self.subTest(old=old):
                result = self.run_checker(VALID.replace(old, new))
                self.assertNotEqual(result.returncode, 0)

    def test_requires_mechanism_contract_in_protocol_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md") as protocol:
            protocol.write("缺少机制字段的文本")
            protocol.flush()
            result = self.run_checker(VALID, protocol.name)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("缺少机制字段", result.stdout)

    def test_rejects_removed_mechanisms(self):
        for removed in ("maxRepairRounds: 0", "CONFLICT", "verifying", "maxConcurrency: 4", "protectedPaths: []"):
            with self.subTest(removed=removed):
                result = self.run_checker(VALID + " " + removed)
                self.assertNotEqual(result.returncode, 0)
        with tempfile.NamedTemporaryFile("w", suffix=".md") as protocol:
            protocol.write("maxRepairRounds: 0 CONFLICT verifying maxConcurrency: 4 protectedPaths: []")
            protocol.flush()
            result = self.run_checker(VALID, protocol.name)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("已移除字段", result.stdout)

    def test_rejects_implementation_skill_and_allowedpaths(self):
        result = self.run_checker(VALID + " /implement")
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID + " allowedPaths: []")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
