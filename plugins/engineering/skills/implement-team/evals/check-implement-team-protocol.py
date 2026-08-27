#!/usr/bin/env python3
"""检查 implement-team 的输入、确认门禁与 AgentTeam 协议。"""

from pathlib import Path
import re
import sys


REQUIRED = (
    "name: implement-team",
    "description:",
    "disable-model-invocation: true",
    "PRD",
    "spec.md",
    ".scratch/<feature>/issues/",
    "direct-task",
    "TeamCreate",
    "AgentTeam",
    "唯一 coordinator",
    "派发者",
    "解锁者",
    "独立核验者",
    "冲突",
    "矩阵",
    "无冲突",
    "等待用户确认",
    "没有任何实现 tickets",
    "只完成输入评估并停止",
    "确认前不创建 team",
    "唯一执行单元",
    "/implement",
    "dependsOn",
    "allowedPaths",
    "DAG",
    "只沿依赖后代传播",
    "独立核验",
    "fail-closed",
    "Status: resolved",
    "evidence",
    "docs/agents/agent-team-protocol.md",
)
REFERENCES = {
    "references/prd-spec.md": ("prd.md", "spec.md", "/implement", "确认"),
    "references/direct-task.md": ("direct-task", "/implement", "不创建", "AgentTeam"),
    "references/manifest-template.md": ("input.kind: prd-spec-input", "公共", "终态"),
}
LEGACY = ("implement-" + "fast", "implement-" + "tmux", "wayfinder-" + "map", "spec-" + "tickets")


def load_documents(path: Path) -> tuple[dict[Path, str], bool]:
    target = path.resolve()
    documents = {target: target.read_text()}
    is_bundle = target.name == "SKILL.md"
    if is_bundle:
        references_dir = target.parent / "references"
        for reference in sorted(references_dir.glob("*.md")):
            documents[reference] = reference.read_text()
    return documents, is_bundle


def check_protocol(text: str) -> list[str]:
    errors = [f"缺少协议字段：{token}" for token in REQUIRED if token not in text]
    for legacy in LEGACY:
        if legacy.lower() in text.lower():
            errors.append(f"包含已移除名称：{legacy}")
    if "确认前" not in text or "不创建 team" not in text:
        errors.append("缺少确认前不得创建 team 的门禁")
    if "不确定" not in text or "禁止并行" not in text:
        errors.append("缺少不确定范围的并发保护")
    return errors


def check_reference_integrity(skill_path: Path, documents: dict[Path, str]) -> list[str]:
    skill_dir = skill_path.parent
    skill_text = documents[skill_path.resolve()]
    errors = []
    for relative_path, markers in REFERENCES.items():
        target = skill_dir / relative_path
        if relative_path not in skill_text:
            errors.append(f"主 Skill 缺少 reference 指针：{relative_path}")
        if not target.is_file():
            errors.append(f"缺少 reference 文件：{relative_path}")
            continue
        reference_text = documents.get(target.resolve(), target.read_text())
        for marker in markers:
            if marker not in reference_text:
                errors.append(f"reference {relative_path} 缺少内容：{marker}")
    return errors


def check(path: Path) -> list[str]:
    documents, is_bundle = load_documents(path)
    text = "\n".join(documents.values())
    errors = check_protocol(text)
    if is_bundle:
        errors.extend(check_reference_integrity(path, documents))
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[1] / "SKILL.md"
    errors = check(path)
    if errors:
        for error in errors:
            print(f"协议失败：{error}")
        return 1
    print("协议通过：implement-team 输入、确认门禁、DAG、核验和公共协议有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
