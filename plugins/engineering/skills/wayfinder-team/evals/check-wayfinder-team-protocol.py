#!/usr/bin/env python3
"""检查 wayfinder-team 的 map 输入与 AgentTeam 协议。"""

from pathlib import Path
import sys


REQUIRED = (
    "name: wayfinder-team",
    "description:",
    "disable-model-invocation: true",
    "map.md",
    "同目录 `issues/`",
    "TeamCreate",
    "AgentTeam",
    "唯一 coordinator",
    "派发者",
    "解锁者",
    "独立核验者",
    "/wayfinder",
    "探索或地图补充",
    "## Answer",
    "Status: resolved",
    "evidence",
    "代码实现/配置变更",
    "blocked",
    "不自动调用实现技能",
    "DAG",
    "maxConcurrency",
    "只沿依赖后代传播",
    "独立核验",
    "fail-closed",
    "docs/agents/agent-team-protocol.md",
)
REFERENCES = {
    "references/map-issues.md": ("map.md", "issues/", "/wayfinder", "## Answer", "blocked"),
    "references/manifest-template.md": ("input.kind: map-issues", "公共", "终态"),
}
LEGACY = ("implement-" + "fast", "implement-" + "tmux", "wayfinder-" + "map", "spec-" + "tickets")


def load_documents(path: Path) -> tuple[dict[Path, str], bool]:
    target = path.resolve()
    documents = {target: target.read_text()}
    is_bundle = target.name == "SKILL.md"
    if is_bundle:
        for reference in sorted((target.parent / "references").glob("*.md")):
            documents[reference] = reference.read_text()
    return documents, is_bundle


def check_protocol(text: str) -> list[str]:
    errors = [f"缺少协议字段：{token}" for token in REQUIRED if token not in text]
    if "/implement" in text:
        errors.append("wayfinder-team 不得包含实现 skill 调用")
    for legacy in LEGACY:
        if legacy.lower() in text.lower():
            errors.append(f"包含已移除名称：{legacy}")
    if "不确定" not in text or "全量并发" not in text:
        errors.append("缺少上限内全量并发调度与不确定范围标记")
    if "确认前" not in text or "不创建 team" not in text:
        errors.append("缺少确认前不得创建 team 的门禁")
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
    print("协议通过：wayfinder-team 输入、探索终态、DAG、核验和公共协议有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
