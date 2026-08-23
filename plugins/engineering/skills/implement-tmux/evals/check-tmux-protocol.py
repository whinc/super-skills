#!/usr/bin/env python3
"""检查 SKILL.md 中 tmux 会话、pane 路由和写入顺序协议。"""

from pathlib import Path
import re
import sys


COMMAND = re.compile(r"\btmux\s+(new-window|send-keys|kill-window|capture-pane|has-session|display-message|list-windows)\b")
READ = re.compile(r"\btmux\s+capture-pane\b")
SESSION_CHECK = re.compile(r"\btmux\s+has-session\b")
DISPLAY = re.compile(r"\btmux\s+display-message\b")
LIST_WINDOWS = re.compile(r"\btmux\s+list-windows\b")
LITERAL = re.compile(r"\btmux\s+send-keys\b.*\s-l\s+--\s+")
BAD_SUBMIT = re.compile(r"\btmux\s+send-keys\b.*\s-l(?:\s|$).*\s(?:Enter|Tab)\s*$")
SUBMIT = re.compile(r"\btmux\s+send-keys\b(?!.*\s-l(?:\s|$)).*\s(Enter|Tab)\s*$")
DESTRUCTIVE = re.compile(r"\btmux\s+(kill-session|kill-server)\b")
TARGET = re.compile(r"(?:^|\s)-t\s+(\"[^\"]*\"|'[^']*'|\S+)")


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


def require_target(line_no: int, line: str, expected: str, description: str) -> int | None:
    target = target_of(line)
    if target != expected:
        return fail(line_no, f"{description}必须使用 {expected}", line)
    return None


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[1] / "SKILL.md"
    text = path.read_text()
    if "main_pane" in text:
        print("协议失败：禁止使用 main_pane，统一使用 mainPane")
        return 1
    pending_read = False
    pending_submit_read = False
    body_target = None
    capture_target = None
    has_session = False
    new_window_seen = False
    new_pane_read = False
    pending_cleanup_list = False
    writes = 0

    for line_no, raw_line in shell_lines(path):
        line = raw_line.strip().rstrip("\\").rstrip()
        command = COMMAND.search(line)
        if command is None:
            continue
        command_name = command.group(1)
        if DESTRUCTIVE.search(line):
            return fail(line_no, "禁止销毁整个 tmux session/server", line)
        if command_name == "has-session":
            if target_of(line) != '"$session"':
                return fail(line_no, "has-session 必须校验目标 session", line)
            has_session = True
            continue
        if command_name == "capture-pane":
            if "-S -30" not in line:
                return fail(line_no, "capture-pane 必须带 -S -30", line)
            target = target_of(line)
            if target not in ('"$mainPane"', '"$pane_id"'):
                return fail(line_no, "capture-pane 必须使用 pane_id（mainPane 或 pane_id）", line)
            pending_read = True
            capture_target = target
            if new_window_seen and not new_pane_read:
                if target != '"$pane_id"':
                    return fail(line_no, "new-window 后首次 capture-pane 必须读取保存的 pane_id", line)
                new_pane_read = True
            continue
        if command_name == "display-message":
            if not has_session:
                return fail(line_no, "display-message 前缺少 has-session", line)
            target = target_of(line)
            if target and target not in ('"$mainPane"', '"$pane_id"'):
                return fail(line_no, "display-message 只能使用 pane_id 目标", line)
            continue
        if command_name == "list-windows":
            if not has_session:
                return fail(line_no, "list-windows 前缺少 has-session", line)
            if pending_cleanup_list:
                pending_cleanup_list = False
            continue
        if command_name == "new-window":
            if not has_session:
                return fail(line_no, "tmux 写入前缺少 has-session", line)
            if target_of(line) != '"$session"':
                return fail(line_no, "new-window 必须创建在目标 session", line)
            if capture_target != '"$mainPane"' or not pending_read:
                return fail(line_no, "new-window 前缺少 mainPane 的 capture-pane", line)
            if " -d " not in f" {line} " or " -P " not in f" {line} ":
                return fail(line_no, "new-window 必须使用 -d -P", line)
            if "-F '#{window_id}\\t#{pane_id}'" not in line:
                return fail(line_no, "new-window 必须用 -F 输出 window_id 和 pane_id", line)
            pending_read = False
            new_window_seen = True
            new_pane_read = False
            writes += 1
            continue
        if command_name == "send-keys":
            if not has_session:
                return fail(line_no, "tmux 写入前缺少 has-session", line)
            target = target_of(line)
            if target not in ('"$mainPane"', '"$pane_id"'):
                return fail(line_no, "send-keys 必须使用 pane_id（mainPane 或 pane_id）", line)
            if BAD_SUBMIT.search(line):
                return fail(line_no, "提交键不得使用 -l（会把 Enter/Tab 当作字面文本）", line)
            if LITERAL.search(line):
                if new_window_seen and not new_pane_read:
                    return fail(line_no, "首次写入前缺少新 pane 的 capture-pane", line)
                if not pending_read:
                    return fail(line_no, "正文写入前缺少 capture-pane", line)
                body_target = target
                if capture_target != body_target:
                    return fail(line_no, "正文写入目标与前置 capture-pane 不一致", line)
                pending_read = False
                pending_submit_read = True
                writes += 1
                continue
            if SUBMIT.search(line):
                if not pending_read or not pending_submit_read:
                    return fail(line_no, "提交键前缺少正文后的 capture-pane", line)
                if target != body_target:
                    return fail(line_no, "提交键目标与正文目标不一致", line)
                pending_read = False
                pending_submit_read = False
                writes += 1
                continue
            return fail(line_no, "无法识别 send-keys 的正文或提交键形式", line)
        if command_name == "kill-window":
            if not has_session:
                return fail(line_no, "tmux 写入前缺少 has-session", line)
            if target_of(line) != '"$window_id"':
                return fail(line_no, "kill-window 必须只关闭本次创建的 window_id", line)
            if capture_target != '"$pane_id"' or not pending_read:
                return fail(line_no, "kill-window 前缺少对应 pane_id 的 capture-pane", line)
            pending_read = False
            pending_cleanup_list = True
            writes += 1

    if pending_submit_read:
        print("协议失败：正文写入后缺少 Enter/Tab 提交键")
        return 1
    if new_window_seen and not new_pane_read:
        print("协议失败：new-window 后缺少新 pane_id 的 capture-pane")
        return 1
    if pending_cleanup_list:
        print("协议失败：kill-window 后缺少同 session 的 list-windows")
        return 1
    if writes == 0:
        print("协议失败：未找到 tmux 写入命令")
        return 1

    print(f"协议通过：检查 {writes} 个 tmux 写入命令；会话、pane_id 读取和提交顺序有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
