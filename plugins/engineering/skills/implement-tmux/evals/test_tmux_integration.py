#!/usr/bin/env python3
"""在隔离 tmux server 中验证会话、窗口和 pane 的生命周期。"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid


class TmuxIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmux_bin = shutil.which("tmux")
        if cls.tmux_bin is None:
            raise unittest.SkipTest("未安装 tmux，跳过真实会话测试")

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory(prefix="implement-tmux-")
        self.server = f"implement-tmux-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self.session = f"test-{uuid.uuid4().hex[:8]}"
        self.env = os.environ.copy()
        self.env.pop("TMUX", None)
        # tmux socket 路径有长度限制；使用短系统临时目录，fixture 仍保存在独立目录。
        self.env["TMUX_TMPDIR"] = "/tmp"

    def tearDown(self):
        subprocess.run(
            [self.tmux_bin, "-L", self.server, "kill-server"],
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        self.tmpdir.cleanup()

    def tmux(self, *args, check=True):
        command = [self.tmux_bin, "-L", self.server, "-f", "/dev/null", *args]
        return subprocess.run(
            command,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=5,
            check=check,
        )

    def capture(self, target):
        return self.tmux("capture-pane", "-p", "-t", target, "-S", "-30").stdout

    def wait_for(self, target, text, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if text in self.capture(target):
                return
            time.sleep(0.05)
        self.fail(f"在 {target} 中未出现 {text!r}\n{self.capture(target)}")

    def list_windows(self):
        result = self.tmux(
            "list-windows",
            "-t",
            self.session,
            "-F",
            "#{window_id}\t#{window_name}\t#{pane_id}",
        )
        return result.stdout.splitlines()

    def test_worker_window_cleanup_preserves_main_session(self):
        self.tmux(
            "new-session",
            "-d",
            "-s",
            self.session,
            "-n",
            "main",
            "sh -c 'printf MAIN_READY; exec sleep 30'",
        )
        self.tmux("has-session", "-t", self.session)
        baseline = self.list_windows()
        self.assertEqual(len(baseline), 1)
        main_window, main_name, main_pane = baseline[0].split("\t")
        self.assertEqual(main_name, "main")
        self.wait_for(main_pane, "MAIN_READY")

        self.tmux(
            "new-window",
            "-d",
            "-t",
            self.session,
            "-n",
            "ticket-01",
            "sh -c 'printf WORKER_READY; IFS= read -r line; echo RECEIVED:$line; exec sleep 30'",
        )
        windows = self.list_windows()
        self.assertEqual(len(windows), 2)
        worker_window, worker_name, worker_pane = next(
            row.split("\t") for row in windows if "\tticket-01\t" in row
        )
        self.assertEqual(worker_name, "ticket-01")
        self.wait_for(worker_pane, "WORKER_READY")

        self.tmux("capture-pane", "-p", "-t", worker_pane, "-S", "-30")
        self.tmux("send-keys", "-t", worker_pane, "-l", "--", "hello-from-test")
        self.tmux("capture-pane", "-p", "-t", worker_pane, "-S", "-30")
        self.tmux("send-keys", "-t", worker_pane, "Enter")
        self.wait_for(worker_pane, "RECEIVED:hello-from-test")

        self.tmux("capture-pane", "-p", "-t", worker_pane, "-S", "-30")
        self.tmux("kill-window", "-t", worker_window)
        remaining = self.list_windows()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].split("\t")[0], main_window)
        self.assertEqual(remaining[0].split("\t")[1], "main")
        self.tmux("has-session", "-t", self.session)


if __name__ == "__main__":
    unittest.main()
