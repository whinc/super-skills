#!/usr/bin/env python3
"""回归测试 implement-tmux 的静态会话协议检查。"""

from pathlib import Path
import subprocess
import tempfile
import unittest


CHECKER = Path(__file__).with_name("check-tmux-protocol.py")


VALID = r'''```sh
tmux has-session -t "$session"
tmux display-message -p -t "$mainPane" '#{session_name}\t#{pane_id}'
tmux capture-pane -p -t "$mainPane" -S -30
new_window_record="$(tmux new-window -d -P -F '#{window_id}\t#{pane_id}' -t "$session" -n "ticket-01" -c "$project" \
  "$agent_command --permission-mode bypassPermissions")"
IFS=$'\t' read -r window_id pane_id <<EOF
$new_window_record
EOF
tmux display-message -p -t "$pane_id" '#{session_name}\t#{pane_id}'
tmux capture-pane -p -t "$pane_id" -S -30
tmux send-keys -t "$pane_id" -l -- "$prompt"
tmux capture-pane -p -t "$pane_id" -S -30
tmux send-keys -t "$pane_id" Enter
tmux capture-pane -p -t "$mainPane" -S -30
tmux capture-pane -p -t "$pane_id" -S -30
tmux kill-window -t "$window_id"
tmux list-windows -t "$session" -F '#{window_id}\t#{window_name}\t#{pane_id}'
```'''


class TmuxProtocolTests(unittest.TestCase):
    def run_checker(self, content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", suffix=".md") as fixture:
            fixture.write(content)
            fixture.flush()
            return subprocess.run(
                ["python3", str(CHECKER), fixture.name],
                capture_output=True,
                text=True,
            )

    def assert_rejected(self, content: str, message: str):
        result = self.run_checker(content)
        self.assertNotEqual(result.returncode, 0, message)

    def test_valid_session_window_pane_flow(self):
        result = self.run_checker(VALID)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_requires_session_check_before_window_listing(self):
        content = VALID.replace(
            'tmux has-session -t "$session"\n',
            '',
            1,
        )
        self.assert_rejected(content, "缺少 has-session 应失败")

    def test_requires_target_session_check(self):
        content = VALID.replace(
            'tmux has-session -t "$session"',
            'tmux has-session -t "$other_session"',
            1,
        )
        self.assert_rejected(content, "has-session 未校验目标 session 应失败")

    def test_requires_pane_read_after_window_creation(self):
        content = VALID.replace(
            'tmux capture-pane -p -t "$pane_id" -S -30\n',
            '',
            1,
        )
        self.assert_rejected(content, "创建 window 后未读取 pane 应失败")

    def test_requires_matching_submit_target(self):
        content = VALID.replace(
            'tmux send-keys -t "$pane_id" Enter',
            'tmux send-keys -t "$mainPane" Enter',
            1,
        )
        self.assert_rejected(content, "提交目标不一致应失败")

    def test_requires_window_listing_after_cleanup(self):
        content = VALID.replace(
            'tmux list-windows -t "$session" -F \'#{window_id}\\t#{window_name}\\t#{pane_id}\'\n',
            '',
            1,
        )
        self.assert_rejected(content, "清理后未列出窗口应失败")

    def test_rejects_destructive_session_commands(self):
        content = VALID.replace(
            'tmux has-session -t "$session"',
            'tmux kill-server',
            1,
        )
        self.assert_rejected(content, "销毁整个 server 应失败")

    def test_rejects_literal_submit_key(self):
        content = VALID.replace(
            'tmux send-keys -t "$pane_id" Enter',
            'tmux send-keys -t "$pane_id" -l -- Enter',
            1,
        )
        self.assert_rejected(content, "literal Enter 应失败")

    def test_rejects_snake_case_main_pane(self):
        self.assert_rejected(VALID.replace("$mainPane", "$main_pane"), "main_pane 应失败")

    def test_rejects_empty_target(self):
        content = VALID.replace(
            'tmux capture-pane -p -t "$mainPane" -S -30',
            'tmux capture-pane -p -t "" -S -30',
            1,
        )
        self.assert_rejected(content, "空 pane 目标应失败")

    def test_rejects_window_name_as_route(self):
        content = VALID.replace(
            'tmux capture-pane -p -t "$pane_id" -S -30',
            'tmux capture-pane -p -t "$window_name" -S -30',
            1,
        )
        self.assert_rejected(content, "窗口名称不得路由消息")

    def test_requires_new_window_double_identity_output(self):
        content = VALID.replace(
            "-P -F '#{window_id}\\t#{pane_id}'",
            "-P -F '#{pane_id}'",
            1,
        )
        self.assert_rejected(content, "new-window 必须同时输出 window_id 和 pane_id")

    def test_requires_kill_window_id(self):
        content = VALID.replace(
            'tmux kill-window -t "$window_id"',
            'tmux kill-window -t "$window_name"',
            1,
        )
        self.assert_rejected(content, "kill-window 必须使用 window_id")


if __name__ == "__main__":
    unittest.main()
