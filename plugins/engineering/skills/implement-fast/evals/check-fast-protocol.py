#!/usr/bin/env python3
"""检查 implement-fast 的 AgentTeam 调度协议。"""

from pathlib import Path
import re
import sys


REQUIRED = (
    "TeamCreate",
    "AgentTeam",
    "/implement",
    "map.md",
    "spec.md",
    "dependsOn",
    "allowedPaths",
    "Status:",
    "resolved",
    "shared",
    "coordinator",
    "TICKET_DONE",
    "TICKET_FAILED",
    "TICKET_BLOCKED",
    "pending → running → verifying → done",
)
BANNED = (
    re.compile(r"\bimplement-tmux\b", re.IGNORECASE),
    re.compile(r"\btmux\b", re.IGNORECASE),
    re.compile(r"严格串行"),
)
EXPECTED_REFERENCES = {
    "references/direct-task.md": ("direct-task", "/implement", "dependsOn"),
    "references/wayfinder-map.md": ("wayfinder-map", "/wayfinder", "Status:"),
    "references/spec-tickets.md": ("spec-tickets", "/implement", "spec.md"),
    "references/manifest-template.md": (
        "## 终态协议",
        "TICKET_DONE",
        "TICKET_FAILED",
        "TICKET_BLOCKED",
    ),
}


def load_documents(path: Path) -> tuple[dict[Path, str], bool]:
    target = path.resolve()
    documents = {target: target.read_text()}
    references_dir = target.parent / "references"
    is_bundle = target.name == "SKILL.md"
    if is_bundle:
        for reference in sorted(references_dir.glob("*.md")):
            documents[reference] = reference.read_text()
    return documents, is_bundle


def check_protocol(text: str) -> list[str]:
    errors = [f"缺少协议字段：{token}" for token in REQUIRED if token not in text]
    errors.extend(
        f"包含已移除的调度协议：{pattern.pattern}"
        for pattern in BANNED
        if pattern.search(text)
    )
    if "只沿反向依赖边" not in text and "只沿依赖后代" not in text:
        errors.append("缺少失败/阻塞只沿依赖后代传播规则")
    if "不确定" not in text or "禁止并行" not in text:
        errors.append("缺少不确定范围的并发保护规则")
    if "确认前" not in text or "不创建 team" not in text:
        errors.append("缺少确认前不得创建 team 的门禁")
    return errors


def check_reference_integrity(skill_path: Path, documents: dict[Path, str]) -> list[str]:
    skill_dir = skill_path.parent
    skill_text = documents[skill_path.resolve()]
    errors = []
    for relative_path, markers in EXPECTED_REFERENCES.items():
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
    print("协议通过：AgentTeam、/implement、三类输入、DAG 并发和主 Agent 协调规则有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
