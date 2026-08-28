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
map.md 同目录 `issues/` TeamCreate AgentTeam
唯一 coordinator 派发者 解锁者 独立核验者 /wayfinder
探索或地图补充 ## Answer Status: resolved evidence
代码实现/配置变更 blocked 不自动调用实现技能
DAG maxConcurrency 只沿依赖后代传播 独立核验 fail-closed
确认前不创建 team 不确定 全量并发 docs/agents/agent-team-protocol.md
references/map-issues.md references/manifest-template.md
""".replace(" disable-model", "disable-model")

REFERENCES = {
    "map-issues.md": "map.md issues/ /wayfinder ## Answer blocked",
    "manifest-template.md": "input.kind: map-issues 公共 终态",
}


class WayfinderTeamProtocolTests(unittest.TestCase):
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

    def test_bundle_requires_references_and_pointers(self):
        result = self.run_checker(VALID, bundle=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        missing = dict(REFERENCES)
        del missing["map-issues.md"]
        result = self.run_checker(VALID, bundle=True, references=missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("map-issues.md", result.stdout)
        result = self.run_checker(VALID.replace("references/map-issues.md", ""), bundle=True)
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_implementation_skill_and_missing_answer(self):
        self.assertNotEqual(self.run_checker(VALID + " /implement").returncode, 0)
        self.assertNotEqual(self.run_checker(VALID.replace("## Answer", "回答")).returncode, 0)
        self.assertNotEqual(self.run_checker(VALID.replace("Status: resolved", "Status: claimed")).returncode, 0)

    def test_requires_confirmation_and_path_safety(self):
        self.assertNotEqual(self.run_checker(VALID.replace("确认前不创建 team", "直接创建 team")).returncode, 0)
        self.assertNotEqual(self.run_checker(VALID.replace("maxConcurrency", "并发无上限")).returncode, 0)
        self.assertNotEqual(self.run_checker(VALID.replace("不确定 全量并发", "自由并行")).returncode, 0)


if __name__ == "__main__":
    unittest.main()
