"""Public installation contracts for portable MCP registrations."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_mcps import build_servers, update_config
from verify import VerificationError, validate_plugin


class McpInstallationTests(unittest.TestCase):
    def test_cli_dry_run_and_apply_stage_payloads_without_touching_other_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "host" / "config.json"
            runtime = root / "runtime"
            command = [sys.executable, str(ROOT / "scripts/sync_mcps.py"), "--host", "claude-code", "--config", str(config), "--runtime-root", str(runtime), "--profile", "minimal", "--plugin", "developer-mcps"]
            preview = subprocess.run([*command, "--dry-run"], text=True, capture_output=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertFalse(config.parent.exists())
            self.assertFalse(runtime.exists())
            config.parent.mkdir()
            config.write_text(json.dumps({"userPreference": "preserve"}), encoding="utf-8")
            applied = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            data = json.loads(config.read_text())
            self.assertEqual(data["userPreference"], "preserve")
            script = Path(data["mcpServers"]["marketplaceStatus"]["args"][0])
            self.assertTrue(script.is_file())
            self.assertEqual(script.read_bytes(), (ROOT / "plugins/developer-mcps/scripts/marketplace_status_mcp.mjs").read_bytes())
            repeated = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(json.loads(config.read_text()), data)
            self.assertEqual(len(list(config.parent.glob("*.bak"))), 1)

    def test_desktop_remote_server_is_rejected_before_any_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run([sys.executable, str(ROOT / "scripts/sync_mcps.py"), "--host", "claude-desktop", "--config", str(root / "config.json"), "--runtime-root", str(root / "runtime"), "--profile", "minimal", "--plugin", "error-monitoring"], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("application UI", result.stderr)
            self.assertEqual(list(root.iterdir()), [])

    def test_install_preserves_unrelated_settings_and_backs_up_replacements(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            original = {"theme": "dark", "mcpServers": {"personal": {"command": "own"}, "serena": {"command": "old"}}}
            path.write_text(json.dumps(original), encoding="utf-8")
            servers = {"serena": {"type": "stdio", "command": "uvx", "args": []}}
            with self.assertRaisesRegex(ValueError, "--replace"):
                update_config(path, servers, replace=False, dry_run=False)
            self.assertEqual(json.loads(path.read_text()), original)
            backup = update_config(path, servers, replace=True, dry_run=False)
            self.assertEqual(json.loads(backup.read_text()), original)
            installed = json.loads(path.read_text())
            self.assertEqual(installed["theme"], "dark")
            self.assertEqual(installed["mcpServers"]["personal"], {"command": "own"})
            self.assertEqual(installed["mcpServers"]["serena"], servers["serena"])
            self.assertIsNone(update_config(path, servers, replace=False, dry_run=False))
            self.assertEqual(len(list(path.parent.glob("*.bak"))), 1)

    def test_dry_run_writes_neither_config_nor_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new" / "config.json"
            update_config(path, {"example": {"command": "node"}}, replace=False, dry_run=True)
            self.assertFalse(path.parent.exists())

    def test_malformed_configuration_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            for original in ('{"mcpServers": []}', '[]', 'broken'):
                path.write_text(original, encoding="utf-8")
                with self.assertRaises((ValueError, TypeError)):
                    update_config(path, {"example": {}}, replace=True, dry_run=False)
                self.assertEqual(path.read_text(), original)

    def test_status_paths_are_stable_and_windows_npx_is_wrapped(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            servers = build_servers([ROOT / "plugins" / "developer-mcps", ROOT / "plugins" / "reverse-engineering"], runtime, windows=True)
            status = servers["marketplaceStatus"]
            self.assertTrue(Path(status["args"][0]).is_absolute())
            self.assertTrue(status["args"][0].startswith(str(runtime)))
            self.assertNotIn(str(ROOT), status["args"][0])
            rea = servers["rea"]
            self.assertEqual(rea["command"], "cmd.exe")
            self.assertEqual(rea["args"][:4], ["/d", "/c", "npx", "--yes"])
            self.assertIn("rea-agents@6.7.0", rea["args"])

    def test_remote_authentication_stays_with_the_host(self):
        servers = build_servers([ROOT / "plugins" / "github-integration", ROOT / "plugins" / "error-monitoring"], Path("unused"), windows=False)
        self.assertEqual(servers["github"]["url"], "https://api.githubcopilot.com/mcp/")
        self.assertEqual(servers["sentry"]["url"], "https://mcp.sentry.dev/mcp")
        self.assertTrue(all(set(server) == {"type", "url"} for server in servers.values()))

    def test_http_validation_rejects_credentials_and_compatibility_drift(self):
        import shutil

        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory) / "github-integration"
            shutil.copytree(ROOT / "plugins/github-integration", plugin)
            portable_path = plugin / "mcp.json"
            portable = json.loads(portable_path.read_text())
            for url in ["http://example.com/mcp", "https://user:pass@example.com/mcp", "https://example.com/mcp?key=private"]:
                portable["mcpServers"]["github"]["url"] = url
                portable_path.write_text(json.dumps(portable), encoding="utf-8")
                with self.assertRaisesRegex(VerificationError, "HTTPS URL"):
                    validate_plugin(plugin, plugin.name)
            portable["mcpServers"]["github"]["url"] = "https://example.com/mcp"
            portable_path.write_text(json.dumps(portable), encoding="utf-8")
            with self.assertRaisesRegex(VerificationError, "url differs"):
                validate_plugin(plugin, plugin.name)


if __name__ == "__main__":
    unittest.main()
