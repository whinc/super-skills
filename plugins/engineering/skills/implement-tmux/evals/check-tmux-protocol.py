#!/usr/bin/env python3
"""检查 SKILL.md 中 tmux 写入前是否读取目标 pane。"""

from pathlib import Path
import re
import sys


WRITE = re.compile(r"^\s*tmux\s+(new-window|send-keys|kill-window)\b")
READ = re.compile(r"^\s*tmux\s+capture-pane\b")
LITERAL = re.compile(r"^\s*tmux\s+send-keys\b.*\s-l\s+--\s+")
SUBMIT = re.compile(r"^\s*tmux\s+send-keys\b.*\s(Enter|Tab)\s*$")


def shell_lines(path: Path):
    in_shell = False
    for line in path.read_text().splitlines():
        if line.startswith("```sh"):
            in_shell = True
            continue
        if in_shell and line.startswith("```"):
            in_shell = False
            continue
        if in_shell:
            yield line


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[1] / "SKILL.md"
    pending_read = False
    pending_submit_read = False
    writes = 0

    for raw_line in shell_lines(path):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if READ.match(line):
            pending_read = True
            continue
        if LITERAL.match(line):
            if not pending_read:
                print(f"协议失败：正文写入前缺少 capture-pane：{line}")
                return 1
            pending_read = False
            pending_submit_read = True
            writes += 1
            continue
        if SUBMIT.match(line):
            if not pending_read or not pending_submit_read:
                print(f"协议失败：提交键前缺少正文后的 capture-pane：{line}")
                return 1
            pending_read = False
            pending_submit_read = False
            writes += 1
            continue
        if WRITE.match(line):
            if not pending_read:
                print(f"协议失败：写入前缺少 capture-pane：{line}")
                return 1
            pending_read = False
            writes += 1

    if pending_submit_read:
        print("协议失败：正文写入后缺少 Enter/Tab 提交键")
        return 1
    if writes == 0:
        print("协议失败：未找到 tmux 写入命令")
        return 1

    print(f"协议通过：检查 {writes} 个 tmux 写入命令；正文写入均有读取和 Enter/Tab 提交")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
