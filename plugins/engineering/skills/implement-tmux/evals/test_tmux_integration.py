#!/usr/bin/env python3
"""在隔离 tmux server 中验证固定 pane_id 路由和 fail-closed 行为。"""

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

    def send_literal(self, pane_id, text, submit="Enter"):
        self.tmux("capture-pane", "-p", "-t", pane_id, "-S", "-30")
        self.tmux("send-keys", "-t", pane_id, "-l", "--", text)
        self.tmux("capture-pane", "-p", "-t", pane_id, "-S", "-30")
        self.tmux("send-keys", "-t", pane_id, submit)

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
        main_window, main_name, mainPane = baseline[0].split("\t")
        self.assertEqual(main_name, "main")
        self.wait_for(mainPane, "MAIN_READY")

        result = self.tmux(
            "new-window",
            "-d",
            "-P",
            "-F",
            "#{window_id}\t#{pane_id}",
            "-t",
            self.session,
            "-n",
            "ticket-01",
            "sh -c 'printf WORKER_READY; IFS= read -r line; echo RECEIVED:$line; exec sleep 30'",
        )
        worker_window, workerPane = result.stdout.strip().split("\t")
        windows = self.list_windows()
        self.assertEqual(len(windows), 2)
        self.assertIn(f"{worker_window}\tticket-01\t{workerPane}", windows)
        self.wait_for(workerPane, "WORKER_READY")

        self.send_literal(workerPane, "hello-from-test")
        self.wait_for(workerPane, "RECEIVED:hello-from-test")

        self.tmux("capture-pane", "-p", "-t", workerPane, "-S", "-30")
        self.tmux("kill-window", "-t", worker_window)
        remaining = self.list_windows()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].split("\t")[0], main_window)
        self.assertEqual(remaining[0].split("\t")[1], "main")
        self.tmux("has-session", "-t", self.session)

    def test_saved_pane_routes_after_rename_and_active_pane_change(self):
        self.tmux(
            "new-session",
            "-d",
            "-s",
            self.session,
            "-n",
            "main",
            "sh -c 'printf MAIN_READY; IFS= read -r line; echo MAIN_RECEIVED:$line; exec sleep 30'",
        )
        main_window, main_name, mainPane = self.list_windows()[0].split("\t")
        self.assertEqual(main_name, "main")
        self.wait_for(mainPane, "MAIN_READY")

        worker_result = self.tmux(
            "new-window",
            "-d",
            "-P",
            "-F",
            "#{window_id}\t#{pane_id}",
            "-t",
            self.session,
            "-n",
            "worker",
            "sh -c 'printf WORKER_READY; IFS= read -r line; echo WORKER_RECEIVED:$line; exec sleep 30'",
        )
        worker_window, workerPane = worker_result.stdout.strip().split("\t")
        self.wait_for(workerPane, "WORKER_READY")

        aux_result = self.tmux(
            "split-window",
            "-d",
            "-P",
            "-F",
            "#{pane_id}",
            "-t",
            worker_window,
            "sh -c 'printf AUX_READY; exec sleep 30'",
        )
        auxPane = aux_result.stdout.strip()
        self.wait_for(auxPane, "AUX_READY")

        self.tmux("rename-window", "-t", main_window, "main-renamed")
        self.tmux("rename-window", "-t", worker_window, "worker-renamed")
        self.tmux("select-window", "-t", worker_window)
        self.tmux("select-pane", "-t", auxPane)

        self.send_literal(workerPane, "worker-after-rename")
        self.wait_for(workerPane, "WORKER_RECEIVED:worker-after-rename")
        self.assertNotIn("WORKER_RECEIVED:worker-after-rename", self.capture(mainPane))

        self.send_literal(mainPane, "main-after-rename")
        self.wait_for(mainPane, "MAIN_RECEIVED:main-after-rename")
        self.assertNotIn("MAIN_RECEIVED:main-after-rename", self.capture(workerPane))
        self.assertNotIn("MAIN_RECEIVED:main-after-rename", self.capture(auxPane))

        # worker window 已失效；固定 pane_id 发送必须失败，且不能回退到当前活跃 auxPane。
        self.tmux("kill-window", "-t", worker_window)
        invalid = self.tmux(
            "send-keys",
            "-t",
            workerPane,
            "-l",
            "--",
            "must-not-reroute",
            check=False,
        )
        self.assertNotEqual(invalid.returncode, 0)
        self.assertNotIn("must-not-reroute", self.capture(mainPane))


if __name__ == "__main__":
    unittest.main()
