#!/usr/bin/env python3
"""检查 SKILL.md 中 tmux 会话和 pane 写入协议。"""

from pathlib import Path
import re
import sys


WRITE = re.compile(r"^\s*tmux\s+(new-window|send-keys|kill-window)\b")
READ = re.compile(r"^\s*tmux\s+capture-pane\b")
SESSION_CHECK = re.compile(r"^\s*tmux\s+has-session\b")
DISPLAY = re.compile(r"^\s*tmux\s+display-message\b")
LIST_WINDOWS = re.compile(r"^\s*tmux\s+list-windows\b")
LITERAL = re.compile(r"^\s*tmux\s+send-keys\b.*\s-l\s+--\s+")
BAD_SUBMIT = re.compile(
    r"^\s*tmux\s+send-keys\b.*\s-l(?:\s|$).*\s(?:Enter|Tab)\s*$"
)
SUBMIT = re.compile(
    r"^\s*tmux\s+send-keys\b(?!.*\s-l(?:\s|$)).*\s(Enter|Tab)\s*$"
)
DESTRUCTIVE = re.compile(r"^\s*tmux\s+(kill-session|kill-server)\b")
TARGET = re.compile(r"(?:^|\s)-t\s+(\S+)")


def shell_lines(path: Path):
    """读取 sh 代码块，并合并反斜杠续行。"""
    in_shell = False
    pending = None
    pending_line = None
    for line_no, raw_line in enumerate(path.read_text().splitlines(), 1):
        if raw_line.startswith("```sh"):
            in_shell = True
            continue
        if in_shell and raw_line.startswith("```"):
            if pending is not None:
                yield pending_line, pending
                pending = None
            in_shell = False
            continue
        if not in_shell:
            continue
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if pending is not None:
            pending = f"{pending[:-1].rstrip()} {line}"
        else:
            pending = line
            pending_line = line_no
        if not line.endswith("\\"):
            yield pending_line, pending
            pending = None


def target_of(line: str):
    match = TARGET.search(line)
    return match.group(1) if match else None


def fail(line_no: int, message: str, line: str) -> int:
    print(f"协议失败：第 {line_no} 行{message}：{line}")
    return 1


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[1] / "SKILL.md"
    pending_read = False
    pending_submit_read = False
    body_target = None
    capture_target = None
    has_session = False
    new_window_seen = False
    new_pane_identified = False
    new_pane_read = False
    pending_cleanup_list = False
    writes = 0

    for line_no, raw_line in shell_lines(path):
        line = raw_line.strip().rstrip("\\").rstrip()
        if DESTRUCTIVE.match(line):
            return fail(line_no, "禁止销毁整个 tmux session/server", line)
        if SESSION_CHECK.match(line):
            has_session = True
            continue
        if READ.match(line):
            if "-S -30" not in line:
                return fail(line_no, "capture-pane 必须带 -S -30", line)
            pending_read = True
            capture_target = target_of(line)
            if new_window_seen and new_pane_identified and not new_pane_read:
                if capture_target != '"$pane_id"':
                    return fail(line_no, "新 window 创建后必须读取 pane_id", line)
                new_pane_read = True
            continue
        if DISPLAY.match(line):
            if not has_session:
                return fail(line_no, "display-message 前缺少 has-session", line)
            if new_window_seen:
                new_pane_identified = True
            continue
        if LIST_WINDOWS.match(line):
            if not has_session:
                return fail(line_no, "list-windows 前缺少 has-session", line)
            if pending_cleanup_list:
                pending_cleanup_list = False
            continue
        if BAD_SUBMIT.match(line):
            return fail(line_no, "提交键不得使用 -l（会把 Enter/Tab 当作字面文本）", line)
        if LITERAL.match(line):
            if new_window_seen and not new_pane_read:
                return fail(line_no, "首次写入前缺少新 pane 的 capture-pane", line)
            if not pending_read:
                return fail(line_no, "正文写入前缺少 capture-pane", line)
            body_target = target_of(line)
            if capture_target != body_target:
                return fail(line_no, "正文写入目标与前置 capture-pane 不一致", line)
            pending_read = False
            pending_submit_read = True
            writes += 1
            continue
        if SUBMIT.match(line):
            if not pending_read or not pending_submit_read:
                return fail(line_no, "提交键前缺少正文后的 capture-pane", line)
            if target_of(line) != body_target:
                return fail(line_no, "提交键目标与正文目标不一致", line)
            pending_read = False
            pending_submit_read = False
            writes += 1
            continue
        if WRITE.match(line):
            if not has_session:
                return fail(line_no, "tmux 写入前缺少 has-session", line)
            if line.startswith("tmux new-window"):
                if target_of(line) != '"$session"':
                    return fail(line_no, "new-window 必须创建在目标 session", line)
                if capture_target != '"$mainPane"':
                    return fail(line_no, "new-window 前缺少 mainPane 的 capture-pane", line)
                pending_read = False
                new_window_seen = True
                new_pane_identified = False
                new_pane_read = False
                writes += 1
                continue
            if line.startswith("tmux kill-window"):
                if target_of(line) != '"$window_id"':
                    return fail(line_no, "kill-window 必须只关闭本次创建的 window", line)
                if capture_target != '"$pane_id"' or not pending_read:
                    return fail(line_no, "kill-window 前缺少对应 pane 的 capture-pane", line)
                pending_read = False
                pending_cleanup_list = True
                writes += 1
                continue
            if not pending_read:
                return fail(line_no, "写入前缺少 capture-pane", line)
            pending_read = False
            writes += 1

    if pending_submit_read:
        print("协议失败：正文写入后缺少 Enter/Tab 提交键")
        return 1
    if new_window_seen and not new_pane_read:
        print("协议失败：new-window 后缺少新 pane 的 capture-pane")
        return 1
    if pending_cleanup_list:
        print("协议失败：kill-window 后缺少同 session 的 list-windows")
        return 1
    if writes == 0:
        print("协议失败：未找到 tmux 写入命令")
        return 1

    print(f"协议通过：检查 {writes} 个 tmux 写入命令；会话、pane 读取和提交顺序有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
