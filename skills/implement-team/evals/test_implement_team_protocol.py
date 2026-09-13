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
等待与唤醒 唯一执行单元 冲突矩阵无冲突 等待用户确认 没有任何实现 tickets
只完成输入评估并停止 确认前不创建 team /implement dependsOn
DAG 只沿依赖后代传播 全部并发派发
独立核验 fail-closed Status: resolved evidence
references/agent-team-protocol.md references/worktree-merge.md
worktree 集成分支 Merger integrationVerify 立即补派
TICKET_RESOLVED TICKET_BLOCKED context 卫生 终态事件 evidenceDir tempDir
"""


class ImplementTeamProtocolTests(unittest.TestCase):
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

    def test_requires_confirmation_and_ticket_gate(self):
        result = self.run_checker(VALID.replace("确认前不创建 team", "直接创建 team"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("没有任何实现 tickets", "有 tickets"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_frontier_and_dispatch_contract(self):
        result = self.run_checker(VALID.replace("frontier", "ready ticket"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("全部并发派发", "按批派发"))
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID.replace("立即补派", "等待同批终态"))
        self.assertNotEqual(result.returncode, 0)

    def test_requires_worktree_isolation_contract(self):
        for old, new in (("worktree", "共享工作区"), ("集成分支", "当前分支"), ("Merger", "手工合并"), ("integrationVerify", "无需验证")):
            with self.subTest(old=old):
                result = self.run_checker(VALID.replace(old, new))
                self.assertNotEqual(result.returncode, 0)

    def test_requires_implement_and_safety_fields(self):
        for old, new in (("/implement", "手工实现"), ("dependsOn", "dependency"), ("fail-closed", "开放通过")):
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

    def test_rejects_exploration_skill_and_allowedpaths(self):
        result = self.run_checker(VALID + " /wayfinder")
        self.assertNotEqual(result.returncode, 0)
        result = self.run_checker(VALID + " allowedPaths: []")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
