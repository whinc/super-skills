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
PRD spec.md .scratch/<feature>/issues/ direct-task TeamCreate AgentTeam
唯一 coordinator 派发者 解锁者 独立核验者
冲突矩阵无冲突等待用户确认 没有任何实现 tickets 只完成输入评估并停止
确认前不创建 team 唯一执行单元 /implement dependsOn CONFLICT maxConcurrency DAG
只沿依赖后代传播 独立核验 fail-closed Status: resolved evidence
docs/agents/agent-team-protocol.md 不确定 全量并发
references/prd-spec.md references/direct-task.md references/manifest-template.md
""".replace(" disable-model", "disable-model")

REFERENCES = {
    "prd-spec.md": "prd.md spec.md /implement 确认",
    "direct-task.md": "direct-task /implement 不创建 AgentTeam",
    "manifest-template.md": "input.kind: prd-spec-input 公共 终态",
}


class ImplementTeamProtocolTests(unittest.TestCase):
    def run_checker(self, content: str, bundle: bool = False, references=None):
        if not bundle:
            with tempfile.NamedTemporaryFile("w", suffix=".md") as fixture:
                fixture.write(content)
                fixture.flush()
                return subprocess.run(["python3", str(CHECKER), fixture.name], capture_output=True, text=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref_dir = root / "references"
            ref_dir.mkdir()
            (root / "SKILL.md").write_text(content)
            for name, value in (REFERENCES if references is None else references).items():
                (ref_dir / name).write_text(value)
            return subprocess.run(["python3", str(CHECKER), str(root / "SKILL.md")], capture_output=True, text=True)

    def test_real_skill_bundle_passes(self):
        result = subprocess.run(["python3", str(CHECKER), str(SKILL)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_valid_protocol_passes(self):
        result = self.run_checker(VALID)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bundle_requires_each_reference_and_pointer(self):
        result = self.run_checker(VALID, bundle=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        missing = dict(REFERENCES)
        del missing["direct-task.md"]
        result = self.run_checker(VALID, bundle=True, references=missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("direct-task.md", result.stdout)
        result = self.run_checker(VALID.replace("references/direct-task.md", ""), bundle=True)
        self.assertNotEqual(result.returncode, 0)

    def test_requires_confirmation_and_ticket_gate(self):
        self.assertNotEqual(self.run_checker(VALID.replace("确认前不创建 team", "直接创建 team")).returncode, 0)
        self.assertNotEqual(self.run_checker(VALID.replace("没有任何实现 tickets", "有 tickets")).returncode, 0)

    def test_requires_implement_and_safety_fields(self):
        for old, new in (("/implement", "手工实现"), ("dependsOn", "dependency"), ("CONFLICT", "自由并行"), ("fail-closed", "开放通过")):
            with self.subTest(old=old):
                self.assertNotEqual(self.run_checker(VALID.replace(old, new)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
