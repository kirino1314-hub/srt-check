"""Exercise real Windows launchers with synthetic files; no desktop UI needed."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GOOD = "1\n00:00:01,000 --> 00:00:04,000\nTest subtitle.\n"


@unittest.skipUnless(sys.platform == "win32", "Windows launcher integration")
class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srt-launcher-", dir=ROOT)
        self.assertEqual(Path(self.temp.name).resolve().parent, ROOT.resolve())
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder / "字幕 測試.srt"
        self.source.write_text(GOOD, encoding="utf-8")
        self.env = dict(os.environ)
        # Use the test interpreter without relying on a machine's default Python.
        (self.folder / "python.cmd").write_text(f'@echo off\n"{sys.executable}" %*\n', encoding="utf-8")
        self.env["PATH"] = str(self.folder) + os.pathsep + self.env.get("PATH", "")

    def run_launcher(self, *paths):
        # All paths are controlled fixtures or the known launcher. No shell input from SRT text.
        arguments = " ".join(f'"{path}"' for path in paths)
        command = f'cmd.exe /d /s /c ""{ROOT / "Run-Demo.cmd"}" {arguments}"'
        return subprocess.run(command, cwd=self.folder, env=self.env, input="\n",
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    def test_default_demo(self):
        run = self.run_launcher()
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("clean.srt: 2 cues, 0 errors, 0 warnings", run.stdout)
        self.assertIn("review-needed.srt: 4 cues, 1 errors, 3 warnings", run.stdout)

    def test_unicode_spaced_path(self):
        before = self.source.read_bytes()
        run = self.run_launcher(self.source)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("1 cues, 0 errors, 0 warnings", run.stdout)
        self.assertEqual(self.source.read_bytes(), before)

    def test_multiple_files(self):
        second = self.folder / "second file.srt"
        second.write_text(GOOD, encoding="utf-8")
        run = self.run_launcher(self.source, second)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout.count("1 cues, 0 errors, 0 warnings"), 2)

    def test_missing_file_exit(self):
        run = self.run_launcher(self.folder / "missing.srt")
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("INPUT_ERROR", run.stdout)

    def test_broken_python_falls_back(self):
        (self.folder / "python.cmd").write_text("@echo off\necho broken-runtime 1>&2\nexit /b 1\n", encoding="ascii")
        (self.folder / "py.cmd").write_text(f'@echo off\n"{sys.executable}" %*\n', encoding="utf-8")
        run = self.run_launcher(self.source)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("1 cues, 0 errors, 0 warnings", run.stdout)
