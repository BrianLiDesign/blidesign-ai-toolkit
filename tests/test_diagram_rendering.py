"""Exercise renderer failure boundaries without requiring optional installed applications."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/toolkit-workflows/skills"
SCRIPT = SKILLS / "engineering-visuals/scripts/render_diagram.py"
VISUALS = ["engineering-visuals", "engineering-diagrams", "architecture-diagrams",
           "dependency-graphs", "editable-diagrams"]

# Deliberately independent fixture: responds to public CLI paths and source controls.
RENDERER = '''import pathlib, subprocess, sys, time
source = pathlib.Path(sys.argv[sys.argv.index("-i") + 1])
output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
mode = source.read_text()
if mode == "fail":
    output.write_text("partial")
    sys.exit(3)
if mode == "sleep":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
    (source.parent / "child.pid").write_text(str(child.pid))
    time.sleep(20)
if mode == "empty":
    sys.exit(0)
if mode == "bad":
    output.write_text("not an image")
else:
    output.write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>Example</text></svg>')
'''


class DiagramRenderingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "input & literal.mmd"
        self.source.write_text("ok")
        self.renderer = self.directory / "fixture renderer.py"
        self.renderer.write_text(RENDERER)
        self.output = self.directory / "export.svg"

    def run_helper(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--engine", "mermaid", "--input", str(self.source),
             "--output", str(self.output), "--executable", sys.executable,
             "--mermaid-cli", str(self.renderer), *extra],
            capture_output=True, text=True, timeout=15,
        )

    def test_renders_literal_paths_without_claiming_domain_or_visual_validation(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = json.loads(result.stdout)
        self.assertEqual(evidence["status"], "rendered")
        self.assertEqual(evidence["domainCheck"], "not-performed")
        self.assertEqual(evidence["visualInspection"], "not-performed")
        self.assertIn("Example", self.output.read_text())
        self.assertEqual(self.source.read_text(), "ok")

    def test_renderer_failures_never_replace_previous_export(self):
        for mode in ["fail", "empty", "bad"]:
            with self.subTest(mode=mode):
                self.source.write_text(mode)
                self.output.write_text("previous export")
                result = self.run_helper("--overwrite")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.output.read_text(), "previous export")
                self.assertFalse(list(self.directory.glob(".diagram-*")))

    def test_existing_export_needs_explicit_replacement(self):
        self.output.write_text("previous export")
        self.assertNotEqual(self.run_helper().returncode, 0)
        self.assertEqual(self.output.read_text(), "previous export")
        self.assertEqual(self.run_helper("--overwrite").returncode, 0)

    def test_source_and_renderer_cannot_be_overwritten_even_through_hardlinks(self):
        for protected in [self.source, self.renderer]:
            with self.subTest(protected=protected.name):
                os.link(protected, self.output)
                before = protected.read_bytes()
                result = self.run_helper("--overwrite")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(protected.read_bytes(), before)
                self.output.unlink()

    def test_missing_tool_and_invalid_timeouts_leave_no_export(self):
        for extra in [["--executable", str(self.directory / "absent")],
                      ["--timeout", "0"], ["--timeout", "nan"], ["--timeout", "inf"]]:
            with self.subTest(extra=extra):
                self.assertNotEqual(self.run_helper(*extra).returncode, 0)
                self.assertFalse(self.output.exists())

    def test_invalid_output_format_is_rejected(self):
        self.output = self.directory / "source.html"
        self.assertNotEqual(self.run_helper().returncode, 0)
        self.assertFalse(self.output.exists())

    def test_shell_wrapper_is_rejected_without_executing_it(self):
        wrapper = self.directory / "untrusted.cmd"
        wrapper.write_text("echo SHOULD_NOT_EXECUTE")
        wrapper.chmod(0o755)
        result = self.run_helper("--executable", str(wrapper))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("native executable", result.stderr)
        self.assertFalse(self.output.exists())

    def test_editable_example_has_resolved_connectors_and_editable_geometry(self):
        document = ET.parse(SKILLS / "editable-diagrams/assets/request.drawio")
        for page in document.findall("diagram"):
            cells = page.findall("mxGraphModel/root/mxCell")
            identifiers = [cell.get("id") for cell in cells]
            self.assertEqual(len(identifiers), len(set(identifiers)))
            vertices = {cell.get("id") for cell in cells if cell.get("vertex") == "1"}
            self.assertGreaterEqual(len(vertices), 2)
            edges = [cell for cell in cells if cell.get("edge") == "1"]
            self.assertTrue(edges)
            for cell in cells:
                if cell.get("parent"):
                    self.assertIn(cell.get("parent"), identifiers)
                if cell.get("vertex") == "1" or cell.get("edge") == "1":
                    self.assertIsNotNone(cell.find("mxGeometry"))
            for edge in edges:
                self.assertIn(edge.get("source"), vertices)
                self.assertIn(edge.get("target"), vertices)

    def test_timeout_cleans_up_owned_child_process(self):
        self.source.write_text("sleep")
        result = self.run_helper("--timeout", "2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timed out", result.stderr)
        child_pid = int((self.directory / "child.pid").read_text())
        if os.name == "nt":
            probe = subprocess.run(["tasklist", "/FI", f"PID eq {child_pid}", "/FO", "CSV", "/NH"],
                                   capture_output=True, text=True, check=True)
            self.assertNotIn(f'"{child_pid}"', probe.stdout)
        else:
            # A reaped/absent process or a zombie awaiting adoption cannot continue rendering.
            probe = subprocess.run(["ps", "-o", "stat=", "-p", str(child_pid)],
                                   capture_output=True, text=True)
            self.assertTrue(probe.returncode != 0 or probe.stdout.strip().startswith("Z"))
        self.assertFalse(self.output.exists())

    def test_synced_specialists_retain_all_relative_documentation_links(self):
        target = self.directory / "synced"
        result = subprocess.run([sys.executable, str(ROOT / "scripts/sync_skills.py"),
                                 "--profile", "development", "--target", str(target)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in VISUALS:
            self.assertTrue((target / name / "SKILL.md").is_file())
            for document in (target / name).rglob("*.md"):
                for link in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                    if "://" not in link and not link.startswith("#"):
                        self.assertTrue((document.parent / link.split("#")[0]).is_file(),
                                        f"Broken synced link in {document}: {link}")


if __name__ == "__main__":
    unittest.main()
