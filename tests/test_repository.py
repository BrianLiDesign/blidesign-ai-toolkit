import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import digest_directory
from update_upstreams import flatten_skills, set_plugin_version, update_source_lock
from verify import VerificationError, validate_plugin, validate_source_provenance


class MarketplaceContractTests(unittest.TestCase):
    def test_marketplace_exposes_the_portable_toolkit_plugins(self) -> None:
        marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))

        self.assertEqual(marketplace["name"], "blidesign-ai-toolkit")
        entries = marketplace["plugins"]
        self.assertEqual(
            [entry["name"] for entry in entries],
            ["engineering-skills", "marketplace-maintainer", "developer-mcps"],
        )
        for entry in entries:
            self.assertEqual(entry["source"]["source"], "local")
            self.assertEqual(
                entry["source"]["path"], f"./plugins/{entry['name']}"
            )
            self.assertIn(entry["policy"]["installation"], {"AVAILABLE"})
            self.assertIn(entry["policy"]["authentication"], {"ON_INSTALL", "ON_USE"})
            self.assertTrue(entry["category"])

    def test_engineering_plugin_vendors_the_pinned_matt_pocock_collection(self) -> None:
        plugin = ROOT / "plugins" / "engineering-skills"
        skill_files = sorted((plugin / "skills").glob("*/SKILL.md"))

        self.assertEqual(len(skill_files), 37)
        self.assertTrue((plugin / "LICENSES" / "mattpocock-skills-MIT.txt").is_file())

        lock = json.loads((ROOT / "upstream" / "sources.lock.json").read_text("utf-8"))
        source = lock["sources"]["mattpocock-skills"]
        self.assertEqual(source["repository"], "https://github.com/mattpocock/skills.git")
        self.assertRegex(source["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(source["license"], "MIT")
        self.assertTrue((ROOT / source["licensePath"]).is_file())
        self.assertEqual(
            source["contentSha256"], digest_directory(ROOT / source["destination"])
        )

    def test_portable_manifests_are_canonical(self) -> None:
        for plugin_name in (
            "engineering-skills",
            "marketplace-maintainer",
            "developer-mcps",
        ):
            with self.subTest(plugin=plugin_name):
                plugin = ROOT / "plugins" / plugin_name
                portable = json.loads((plugin / "plugin.json").read_text("utf-8"))
                compatibility = json.loads(
                    (plugin / ".codex-plugin" / "plugin.json").read_text("utf-8")
                )
                self.assertEqual(
                    portable["$schema"],
                    "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                )
                for field in ("name", "version", "description", "license"):
                    self.assertEqual(portable[field], compatibility[field])
                validate_plugin(plugin, plugin_name)

    def test_manifest_validation_rejects_schema_identity_and_path_drift(self) -> None:
        cases = {
            "unsupported schema": (
                "portable",
                lambda manifest: manifest.update(
                    {"$schema": "https://example.com/plugin.schema.json"}
                ),
            ),
            "differs from portable identity": (
                "compatibility",
                lambda manifest: manifest.update({"description": "Drifted description"}),
            ),
            "must be a ./-relative path": (
                "compatibility",
                lambda manifest: manifest.update({"skills": "C:/private/skills"}),
            ),
            "version must be strict semver": (
                "portable",
                lambda manifest: manifest.update({"version": "version-two"}),
            ),
            "folder and manifest names must match": (
                "portable",
                lambda manifest: manifest.update({"name": "renamed-plugin"}),
            ),
        }
        for expected_error, (target_kind, mutate) in cases.items():
            with self.subTest(expected_error=expected_error):
                with tempfile.TemporaryDirectory() as directory:
                    plugin = Path(directory) / "marketplace-maintainer"
                    shutil.copytree(ROOT / "plugins" / "marketplace-maintainer", plugin)
                    target = plugin / "plugin.json"
                    if target_kind == "compatibility":
                        target = plugin / ".codex-plugin" / "plugin.json"
                    manifest = json.loads(target.read_text("utf-8"))
                    mutate(manifest)
                    target.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(VerificationError, expected_error):
                        validate_plugin(plugin, "marketplace-maintainer")

    def test_portable_mcp_matches_the_compatibility_configuration(self) -> None:
        plugin = ROOT / "plugins" / "developer-mcps"
        portable = json.loads((plugin / "mcp.json").read_text("utf-8"))
        server = portable["mcpServers"]["marketplaceStatus"]
        self.assertEqual(
            portable["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        )
        self.assertEqual(server["type"], "stdio")
        self.assertEqual(server["cwd"], "./")
        validate_plugin(plugin, "developer-mcps")

        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "developer-mcps"
            shutil.copytree(plugin, copied)
            (copied / "mcp.json").unlink()
            with self.assertRaisesRegex(
                VerificationError, "portable plugin with MCP requires root mcp.json"
            ):
                validate_plugin(copied, "developer-mcps")

    def test_upstream_version_updates_keep_manifests_in_sync(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory) / "engineering-skills"
            shutil.copytree(ROOT / "plugins" / "engineering-skills", plugin)
            expected = "0.2.0+codex.upstream-aaaaaaaaaaaa"
            set_plugin_version(plugin, expected)
            portable = json.loads((plugin / "plugin.json").read_text("utf-8"))
            compatibility = json.loads(
                (plugin / ".codex-plugin" / "plugin.json").read_text("utf-8")
            )
            self.assertEqual(portable["version"], expected)
            self.assertEqual(compatibility["version"], expected)
            validate_plugin(plugin, "engineering-skills")

    def test_upstream_version_update_rolls_back_both_manifests_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory) / "engineering-skills"
            shutil.copytree(ROOT / "plugins" / "engineering-skills", plugin)
            paths = (
                plugin / "plugin.json",
                plugin / ".codex-plugin" / "plugin.json",
            )
            originals = tuple(path.read_bytes() for path in paths)
            real_replace = os.replace
            failed_once = False

            def fail_second_manifest(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
                nonlocal failed_once
                if Path(destination) == paths[1] and not failed_once:
                    failed_once = True
                    raise OSError("simulated replacement failure")
                real_replace(source, destination)

            with patch("update_upstreams.os.replace", side_effect=fail_second_manifest):
                with self.assertRaisesRegex(OSError, "simulated replacement failure"):
                    set_plugin_version(plugin, "0.3.0")

            self.assertEqual(tuple(path.read_bytes() for path in paths), originals)

    def test_upstream_lock_records_digest_of_generated_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vendored = root / "vendor"
            vendored.mkdir()
            (vendored / "one.txt").write_bytes(b"one\r\n")
            lock_path = root / "sources.lock.json"
            lock_path.write_text(
                json.dumps({"sources": {"fixture": {"commit": "a" * 40}}}),
                encoding="utf-8",
            )

            update_source_lock(lock_path, "fixture", "b" * 40, vendored)

            source = json.loads(lock_path.read_text("utf-8"))["sources"]["fixture"]
            self.assertEqual(source["commit"], "b" * 40)
            self.assertEqual(
                source["contentSha256"],
                "84e2196c31ecfb330711e3d935fb68c266fb0a23478d8af0ba913470cf670f1c",
            )

    def test_upstream_transformation_materializes_lf_text_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            skill = source / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_bytes(b"---\r\nname: example\r\n---\r\n")
            stage = root / "stage"

            self.assertEqual(flatten_skills(source, stage), 1)

            self.assertEqual(
                (stage / "example" / "SKILL.md").read_bytes(),
                b"---\nname: example\n---\n",
            )

    def test_provenance_validation_detects_content_and_license_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vendored = root / "vendor"
            vendored.mkdir()
            (vendored / "one.txt").write_text("one", encoding="utf-8")
            license_path = root / "LICENSES" / "source.txt"
            license_path.parent.mkdir()
            license_path.write_text("license", encoding="utf-8")
            source = {
                "commit": "a" * 40,
                "license": "MIT",
                "licensePath": "LICENSES/source.txt",
                "destination": "vendor",
                "contentSha256": digest_directory(vendored),
            }
            validate_source_provenance(root, "fixture", source)

            for operation in ("modify", "rename", "missing", "extra"):
                with self.subTest(operation=operation):
                    fixture = root / operation
                    shutil.copytree(vendored, fixture)
                    fixture_source = {**source, "destination": operation}
                    target = fixture / "one.txt"
                    if operation == "modify":
                        target.write_text("changed", encoding="utf-8")
                    elif operation == "rename":
                        target.rename(fixture / "renamed.txt")
                    elif operation == "missing":
                        target.unlink()
                    else:
                        (fixture / "extra.txt").write_text("extra", encoding="utf-8")
                    with self.assertRaisesRegex(
                        VerificationError, "vendored content digest does not match"
                    ):
                        validate_source_provenance(root, "fixture", fixture_source)

            license_path.unlink()
            with self.assertRaisesRegex(VerificationError, "license file is missing"):
                validate_source_provenance(root, "fixture", source)

    def test_provenance_digest_detects_line_ending_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = root / "skill.md"
            text.write_bytes(b"first\r\nsecond\r\n")
            crlf_digest = digest_directory(root)
            text.write_bytes(b"first\nsecond\n")
            self.assertNotEqual(crlf_digest, digest_directory(root))

    def test_vendored_text_matches_declared_lf_checkout_policy(self) -> None:
        vendored = ROOT / "plugins" / "engineering-skills" / "skills"
        files = sorted(path for path in vendored.rglob("*") if path.is_file())
        relative_paths = [path.relative_to(ROOT).as_posix() for path in files]
        for path in files:
            content = path.read_bytes()
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn(b"\r", content, path.relative_to(ROOT).as_posix())

        attributes = subprocess.run(
            ["git", "check-attr", "eol", "--", *relative_paths],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()
        self.assertEqual(len(attributes), len(files))
        for attribute in attributes:
            self.assertTrue(attribute.endswith(": eol: lf"), attribute)

    def test_profiles_only_reference_known_marketplace_plugins(self) -> None:
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text("utf-8")
        )
        known = {entry["name"] for entry in marketplace["plugins"]}

        expected = {
            "minimal": ["marketplace-maintainer"],
            "development": [
                "engineering-skills",
                "marketplace-maintainer",
                "developer-mcps",
            ],
            "full": [
                "engineering-skills",
                "marketplace-maintainer",
                "developer-mcps",
            ],
        }
        for profile_name, expected_plugins in expected.items():
            profile = json.loads(
                (ROOT / "profiles" / f"{profile_name}.json").read_text("utf-8")
            )
            self.assertEqual(profile["marketplace"], "blidesign-ai-toolkit")
            self.assertEqual(profile["plugins"], expected_plugins)
            self.assertTrue(set(profile["plugins"]).issubset(known))
            self.assertIsInstance(profile["externalPlugins"], list)

    def test_verifier_accepts_the_repository(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Marketplace verification passed", completed.stdout)

    def test_marketplace_status_mcp_reports_repository_health(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("Node.js is not installed")
        requests = "\n".join(
            [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18"},
                    }
                ),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "marketplace_status", "arguments": {}},
                    }
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            installed_plugin = Path(directory) / "developer-mcps"
            shutil.copytree(ROOT / "plugins" / "developer-mcps", installed_plugin)
            completed = subprocess.run(
                [
                    "node",
                    str(installed_plugin / "scripts" / "marketplace_status_mcp.mjs"),
                ],
                cwd=installed_plugin,
                input=requests + "\n",
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([response["id"] for response in responses], [1, 2, 3])
        self.assertEqual(
            responses[1]["result"]["tools"][0]["name"], "marketplace_status"
        )
        status = responses[2]["result"]["structuredContent"]
        self.assertTrue(status["healthy"])
        self.assertTrue(status["codexManifestPresent"])
        self.assertTrue(status["portableManifestPresent"])
        self.assertTrue(status["portableMcpConfigPresent"])
        self.assertEqual(status["marketplace"], "blidesign-ai-toolkit")
        self.assertEqual(status["pluginCount"], 3)
        self.assertEqual(status["profileCount"], 3)
        self.assertEqual(status["vendoredSkillCount"], 37)

    def test_sync_skills_dry_run_lists_profile_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "sync_skills.py"),
                    "--profile",
                    "minimal",
                    "--target",
                    str(target),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("marketplace-maintainer", completed.stdout)
            self.assertIn("[dry-run] copy", completed.stdout)
            self.assertIn("Would sync 1 skill(s)", completed.stdout)
            self.assertFalse(target.exists())

    def test_sync_skills_copies_selected_profile_into_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "sync_skills.py"),
                    "--profile",
                    "minimal",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            skill_path = target / "marketplace-maintainer" / "SKILL.md"
            self.assertTrue(skill_path.is_file())
            self.assertFalse((target / "tdd").exists())
            self.assertIn("Synced 1 skill(s)", completed.stdout)

            completed_again = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "sync_skills.py"),
                    "--profile",
                    "minimal",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                completed_again.returncode,
                0,
                completed_again.stdout + completed_again.stderr,
            )
            self.assertTrue(skill_path.is_file())

    def test_powershell_bootstrap_dry_run_is_profile_driven(self) -> None:
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell is None:
            self.skipTest("PowerShell is not installed")
        completed = subprocess.run(
            [
                shell,
                "-NoProfile",
                "-File",
                str(ROOT / "scripts" / "bootstrap.ps1"),
                "-Profile",
                "minimal",
                "-DryRun",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("marketplace-maintainer@blidesign-ai-toolkit", completed.stdout)
        self.assertNotIn("engineering-skills@blidesign-ai-toolkit", completed.stdout)
        self.assertIn("Dry run complete", completed.stdout)

    def test_bash_bootstrap_dry_run_is_profile_driven(self) -> None:
        shell = shutil.which("bash")
        if shell is None and sys.platform == "win32":
            git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
            shell = str(git_bash) if git_bash.is_file() else None
        if shell is None:
            self.skipTest("Bash is not installed")
        completed = subprocess.run(
            [
                shell,
                str(ROOT / "scripts" / "bootstrap.sh"),
                "--profile",
                "development",
                "--dry-run",
                "--skip-external",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        for plugin in (
            "engineering-skills",
            "marketplace-maintainer",
            "developer-mcps",
        ):
            self.assertIn(f"{plugin}@blidesign-ai-toolkit", completed.stdout)
        self.assertIn("Dry run complete", completed.stdout)

    def test_inventory_export_omits_mcp_environment_and_machine_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "export_inventory.py"),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env={
                    **os.environ,
                    "AI_TOOLKIT_CODEX_COMMAND_JSON": json.dumps(
                        [
                            sys.executable,
                            str(ROOT / "tests" / "fixtures" / "fake_codex.py"),
                        ]
                    ),
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            inventory_text = output.read_text("utf-8")
            inventory = json.loads(inventory_text)
            self.assertEqual(inventory["schemaVersion"], 1)
            self.assertNotIn('"env"', inventory_text)
            self.assertNotIn('"command"', inventory_text)
            for server in inventory["mcpServers"]:
                self.assertEqual(
                    set(server), {"name", "enabled", "transport", "authStatus"}
                )

    @unittest.skipUnless(sys.platform == "win32", "PowerShell reconciliation test")
    def test_powershell_bootstrap_is_idempotent_with_a_clean_codex_state(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("Node.js is not installed")
        shell = shutil.which("pwsh") or shutil.which("powershell")
        self.assertIsNotNone(shell)
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            state_path = temporary / "codex-state.json"
            wrapper = temporary / "codex.cmd"
            wrapper.write_text(
                '@"%FAKE_CODEX_PYTHON%" "%FAKE_CODEX_SCRIPT%" %*\n',
                encoding="utf-8",
            )
            environment = {
                **os.environ,
                "PATH": f"{temporary}{os.pathsep}{os.environ['PATH']}",
                "FAKE_CODEX_PYTHON": sys.executable,
                "FAKE_CODEX_SCRIPT": str(ROOT / "tests" / "fixtures" / "fake_codex.py"),
                "FAKE_CODEX_STATE": str(state_path),
                "FAKE_PLUGIN_ROOT": str(ROOT / "plugins" / "developer-mcps"),
            }
            command = [
                str(shell),
                "-NoProfile",
                "-File",
                str(ROOT / "scripts" / "bootstrap.ps1"),
                "-Profile",
                "development",
                "-SkipExternal",
            ]
            first = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            first_state = json.loads(state_path.read_text("utf-8"))
            second = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            second_state = json.loads(state_path.read_text("utf-8"))
            self.assertEqual(first_state, second_state)
            self.assertEqual(
                second_state["plugins"],
                [
                    "developer-mcps@blidesign-ai-toolkit",
                    "engineering-skills@blidesign-ai-toolkit",
                    "marketplace-maintainer@blidesign-ai-toolkit",
                ],
            )

    @unittest.skipUnless(os.name == "posix", "POSIX Bash reconciliation test")
    def test_bash_bootstrap_is_idempotent_with_a_clean_codex_state(self) -> None:
        shell = shutil.which("bash")
        self.assertIsNotNone(shell)
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            state_path = temporary / "codex-state.json"
            wrapper = temporary / "codex"
            wrapper.write_text(
                '#!/bin/sh\nexec "$FAKE_CODEX_PYTHON" "$FAKE_CODEX_SCRIPT" "$@"\n',
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            environment = {
                **os.environ,
                "PATH": f"{temporary}{os.pathsep}{os.environ['PATH']}",
                "FAKE_CODEX_PYTHON": sys.executable,
                "FAKE_CODEX_SCRIPT": str(ROOT / "tests" / "fixtures" / "fake_codex.py"),
                "FAKE_CODEX_STATE": str(state_path),
                "FAKE_PLUGIN_ROOT": str(ROOT / "plugins" / "developer-mcps"),
            }
            command = [
                str(shell),
                str(ROOT / "scripts" / "bootstrap.sh"),
                "--profile",
                "development",
                "--skip-external",
            ]
            first = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            first_state = json.loads(state_path.read_text("utf-8"))
            second = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(first_state, json.loads(state_path.read_text("utf-8")))

    @unittest.skipUnless(sys.platform == "win32", "PowerShell ref reconciliation test")
    def test_powershell_bootstrap_can_reconcile_a_changed_remote_ref(self) -> None:
        shell = shutil.which("pwsh") or shutil.which("powershell")
        self.assertIsNotNone(shell)
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            state_path = temporary / "codex-state.json"
            wrapper = temporary / "codex.cmd"
            wrapper.write_text(
                '@"%FAKE_CODEX_PYTHON%" "%FAKE_CODEX_SCRIPT%" %*\n',
                encoding="utf-8",
            )
            environment = {
                **os.environ,
                "PATH": f"{temporary}{os.pathsep}{os.environ['PATH']}",
                "FAKE_CODEX_PYTHON": sys.executable,
                "FAKE_CODEX_SCRIPT": str(ROOT / "tests" / "fixtures" / "fake_codex.py"),
                "FAKE_CODEX_STATE": str(state_path),
            }
            base_command = [
                str(shell),
                "-NoProfile",
                "-File",
                str(ROOT / "scripts" / "bootstrap.ps1"),
                "-Source",
                "owner/repository",
                "-Profile",
                "minimal",
                "-SkipExternal",
            ]
            first = subprocess.run(
                [*base_command, "-Ref", "stable"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = subprocess.run(
                [*base_command, "-Ref", "main", "-ReconfigureMarketplace"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            state = json.loads(state_path.read_text("utf-8"))
            self.assertEqual(state["marketplaceSource"], "owner/repository")
            self.assertEqual(state["marketplaceRef"], "main")


if __name__ == "__main__":
    unittest.main()
