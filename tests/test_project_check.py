"""Exercise the packaged runner through its portable command-line interface."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "plugins/toolkit-workflows/skills/project-check/scripts/project_check.py"


class ProjectCheckTests(unittest.TestCase):
    def invoke(self, root, *args, env=None):
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--root", str(root), *args],
            capture_output=True, text=True, env=env, timeout=20,
        )
        return result, json.loads(result.stdout)

    def manifest(self, root, checks, **fields):
        data = {"schemaVersion": 1, "requiredCategories": ["test"], "checks": checks, **fields}
        (root / ".project-check.json").write_text(json.dumps(data), encoding="utf-8")

    def test_execution_records_pass_failure_and_evidence_for_each_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.manifest(root, [
                {"id": "works", "category": "test", "argv": ["{python}", "-c", "print('expected output')"]},
                {"id": "broken", "category": "test", "argv": ["{python}", "-c", "import sys; print('failure detail',file=sys.stderr); sys.exit(7)"]},
            ])
            result, report = self.invoke(root, "--run")
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(report["status"], "failed")
            self.assertEqual([c["status"] for c in report["checks"]], ["passed", "failed"])
            self.assertIn("expected output", report["checks"][0]["stdout"])
            self.assertIn("failure detail", report["checks"][1]["stderr"])
            self.assertEqual(report["checks"][1]["exitCode"], 7)
            self.assertIn("startedAt", report)
            self.assertIn("git", report)
            self.assertTrue(all(c["durationSeconds"] >= 0 for c in report["checks"]))

    def test_discovery_never_executes_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "touch SHOULD_NOT_EXIST"}}))
            (root / "package-lock.json").write_text("{}")
            result, report = self.invoke(root)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(report["executed"])
            self.assertNotIn("status", report)
            self.assertEqual(report["candidates"][0]["argv"], ["npm", "run", "test"])
            self.assertFalse((root / "SHOULD_NOT_EXIST").exists())

    def test_missing_manifest_or_category_and_skipped_check_never_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, report = self.invoke(root, "--run")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["status"], "error")
            self.manifest(root, [])
            result, report = self.invoke(root, "--run")
            self.assertEqual((result.returncode, report["status"]), (2, "partial"))
            self.assertEqual(report["missingCategories"], ["test"])
            self.manifest(root, [
                {"id": "one", "category": "test", "argv": ["{python}", "-c", "pass"]},
                {"id": "two", "category": "test", "argv": ["{python}", "-c", "pass"]},
            ])
            result, report = self.invoke(root, "--run", "--check", "one")
            self.assertEqual((result.returncode, report["status"]), (2, "partial"))
            self.assertEqual(report["checks"][1]["status"], "not_run")

    def test_validates_entire_plan_before_executing_and_rejects_unknown_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = {"id": "one", "category": "test", "argv": ["{python}", "-c", "from pathlib import Path; Path('marker').touch()"]}
            for bad in [dict(good), {**good, "id": "two", "argv": "python -c pass"}, {**good, "id": "two", "cwd": ".."}, {**good, "id": "two", "timeoutSeconds": -1}]:
                self.manifest(root, [good, bad])
                result, report = self.invoke(root, "--run")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(report["status"], "error")
                self.assertFalse((root / "marker").exists())
            self.manifest(root, [good])
            result, _ = self.invoke(root, "--run", "--check", "unknown")
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / "marker").exists())

    def test_timeout_and_missing_executable_are_failures_and_remaining_checks_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.manifest(root, [
                {"id": "slow", "category": "test", "argv": ["{python}", "-c", "import time; time.sleep(30)"], "timeoutSeconds": 0.3},
                {"id": "missing", "category": "test", "argv": ["toolkit-no-such-executable-123456"]},
                {"id": "last", "category": "test", "argv": ["{python}", "-c", "pass"]},
            ])
            result, report = self.invoke(root, "--run")
            self.assertEqual(result.returncode, 1)
            self.assertEqual([c["status"] for c in report["checks"]], ["timeout", "error", "passed"])

    def test_secrets_are_redacted_in_saved_report_stdout_and_arguments(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as output:
            root = Path(directory)
            secret = "fixture-sensitive-value-0123456789"
            self.manifest(root, [{"id": "secret", "category": "test", "argv": ["{python}", "-c", "import os,sys; print(os.environ['TOOLKIT_TEST_SECRET']); print(sys.argv[1],file=sys.stderr)", secret]}])
            target = Path(output) / "report.json"
            result, report = self.invoke(root, "--run", "--report", str(target), env={**os.environ, "TOOLKIT_TEST_SECRET": secret})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(secret, result.stdout)
            self.assertNotIn(secret, target.read_text())
            self.assertIn("<REDACTED>", report["checks"][0]["stdout"])

    def test_output_is_bounded_and_runner_works_when_copied_outside_toolkit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.manifest(root, [{"id": "verbose", "category": "test", "argv": ["{python}", "-c", "print('x'*200000);print('end of output')"]}])
            result, report = self.invoke(root, "--run")
            self.assertEqual(result.returncode, 0)
            self.assertTrue(report["checks"][0]["outputTruncated"])
            self.assertLessEqual(len(report["checks"][0]["stdout"]), 32768)
            self.assertIn("end of output", report["checks"][0]["stdout"])
            copied = root / "installed.py"
            shutil.copy2(RUNNER, copied)
            result = subprocess.run([sys.executable, str(copied), "--root", str(root), "--discover"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)["executed"])

    def test_argv_metacharacters_are_literal_and_reports_cannot_replace_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            literal = "literal; & | > should-not-run"
            self.manifest(root, [{"id": "args", "category": "test", "argv": ["{python}", "-c", "import sys; print(sys.argv[1])", literal]}])
            result, report = self.invoke(root, "--run")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(report["checks"][0]["stdout"].strip(), literal)
            result, _ = self.invoke(root, "--run", "--report", str(root / "source.py"))
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / "source.py").exists())

    @unittest.skipUnless(shutil.which("git"), "Git is not installed")
    def test_source_changes_are_detected_even_when_checkout_was_already_dirty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
            git("init")
            (root / "tracked.txt").write_text("original")
            git("add", "tracked.txt")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
            (root / "tracked.txt").write_text("already dirty")
            self.manifest(root, [{"id": "changes", "category": "test", "argv": ["{python}", "-c", "from pathlib import Path; Path('tracked.txt').write_text('changed during check')"]}])
            result, report = self.invoke(root, "--run")
            self.assertEqual(result.returncode, 2)
            self.assertTrue(report["git"]["dirty"])
            self.assertTrue(report["changedDuringRun"])
            self.assertEqual(len(report["git"]["commit"]), 40)

    def test_timeout_terminates_an_owned_child_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = "import time; from pathlib import Path; time.sleep(2); Path('leaked-child').touch()"
            parent = f"import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', {child!r}]); print('child started',flush=True); time.sleep(30)"
            self.manifest(root, [{"id": "tree", "category": "test", "argv": ["{python}", "-c", parent], "timeoutSeconds": 0.7}])
            result, report = self.invoke(root, "--run")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(report["checks"][0]["status"], "timeout")
            self.assertIn("child started", report["checks"][0]["stdout"])
            time.sleep(2)
            self.assertFalse((root / "leaked-child").exists())
