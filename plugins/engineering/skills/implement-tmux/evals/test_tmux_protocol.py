#!/usr/bin/env python3
"""回归测试 implement-tmux 的静态会话协议检查。"""

from pathlib import Path
import subprocess
import tempfile
import unittest


CHECKER = Path(__file__).with_name("check-tmux-protocol.py")


VALID = r'''```sh
tmux has-session -t "$session"
tmux capture-pane -p -t "$mainPane" -S -30
tmux new-window -d -t "$session" -n "ticket-01" -c "$project" \
  "$agent_command --permission-mode bypassPermissions"
tmux display-message -p -t "$window_id" '#{pane_id}'
tmux capture-pane -p -t "$pane_id" -S -30
tmux send-keys -t "$pane_id" -l -- "$prompt"
tmux capture-pane -p -t "$pane_id" -S -30
tmux send-keys -t "$pane_id" Enter
tmux capture-pane -p -t "$pane_id" -S -30
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


if __name__ == "__main__":
    unittest.main()
