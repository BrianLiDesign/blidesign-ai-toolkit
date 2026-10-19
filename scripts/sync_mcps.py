#!/usr/bin/env python3
"""Install profile-selected MCP definitions into Claude Code, Cursor, or Claude Desktop.

Use Codex bootstrap for Codex. This installer stages versioned plugin payloads outside
the checkout, preserves unrelated settings, and backs up changed configuration files.
It does not install native analysis engines, authenticate accounts, or start services.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sync_skills import ROOT, load_json, plugin_paths_for_profile
from verify import validate_plugin


def build_servers(plugin_dirs: list[Path], runtime_root: Path, *, windows: bool) -> dict:
    servers = {}
    for plugin in plugin_dirs:
        path = plugin / "mcp.json"
        if not path.exists():
            continue
        validate_plugin(plugin, plugin.name)
        version = load_json(plugin / "plugin.json")["version"]
        installed = (runtime_root / plugin.name / version).resolve()
        for name, source in load_json(path)["mcpServers"].items():
            if name in servers:
                raise ValueError(f"Duplicate MCP server name: {name}")
            server = copy.deepcopy(source)
            if server["type"] == "stdio":
                server["args"] = [
                    str(installed / arg[2:]) if arg.startswith("./") else arg
                    for arg in server.get("args", [])
                ]
                if "cwd" in server:
                    server["cwd"] = str(installed / server["cwd"][2:])
                command = server["command"]
                if windows and command == "npx":
                    server["command"] = "cmd.exe"
                    server["args"] = ["/d", "/c", "npx", *server["args"]]
                else:
                    server["command"] = shutil.which(command) or command
            servers[name] = server
    return servers


def update_config(path: Path, servers: dict, *, replace: bool, dry_run: bool) -> Path | None:
    data = load_json(path) if path.exists() else {}
    if not isinstance(data, dict) or not isinstance(data.get("mcpServers", {}), dict):
        raise ValueError("Existing configuration and mcpServers must be JSON objects")
    existing = data.get("mcpServers", {})
    conflicts = [name for name, server in servers.items() if name in existing and existing[name] != server]
    if conflicts and not replace:
        raise ValueError(f"Existing definitions differ: {', '.join(conflicts)}. Review with --dry-run and use --replace to back up and replace them.")
    if all(existing.get(name) == server for name, server in servers.items()):
        return None
    if dry_run:
        print(f"[dry-run] merge {', '.join(servers)} into {path}")
        return None
    backup = None
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = path.with_name(f"{path.name}.{stamp}.bak")
        shutil.copy2(path, backup)
    data["mcpServers"] = {**existing, **servers}
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, choices=["claude-code", "cursor", "claude-desktop"])
    parser.add_argument("--config", type=Path, help="Explicit configuration path (required for Claude Desktop)")
    parser.add_argument("--profile", default="development", choices=["minimal", "development", "full"])
    parser.add_argument("--plugin", action="append", default=[], help="Add an optional marketplace plugin (repeatable)")
    parser.add_argument("--runtime-root", type=Path, default=Path.home() / ".blidesign" / "ai-toolkit" / "plugins")
    parser.add_argument("--replace", action="store_true", help="Back up and replace conflicting named definitions")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        plugins = plugin_paths_for_profile(args.profile)
        known = {entry["name"]: ROOT / entry["source"]["path"] for entry in load_json(ROOT / ".agents/plugins/marketplace.json")["plugins"]}
        for name in args.plugin:
            if name not in known:
                raise ValueError(f"Unknown marketplace plugin: {name}")
            if known[name] not in plugins:
                plugins.append(known[name])
        servers = build_servers(plugins, args.runtime_root.expanduser(), windows=os.name == "nt")
        if not servers:
            print("No MCP servers selected.")
            return 0
        claude_root = os.environ.get("CLAUDE_CONFIG_DIR")
        if args.host == "claude-desktop":
            if not args.config:
                raise ValueError("Claude Desktop requires --config with its actual configuration path")
            if any(server["type"] != "stdio" for server in servers.values()):
                raise ValueError("Configure remote Claude Desktop connectors in the application UI")
            for server in servers.values():
                server.pop("type")
                server.pop("cwd", None)
        if args.config:
            target = args.config.expanduser()
        elif args.host == "claude-code":
            target = Path(claude_root).expanduser() / ".claude.json" if claude_root else Path.home() / ".claude.json"
        else:
            target = Path.home() / ".cursor/mcp.json"
        # Validate conflicts before staging any payloads or changing the live config.
        update_config(target, servers, replace=args.replace, dry_run=True)
        for plugin in plugins:
            if not (plugin / "mcp.json").exists():
                continue
            version = load_json(plugin / "plugin.json")["version"]
            destination = args.runtime_root.expanduser() / plugin.name / version
            if args.dry_run:
                print(f"[dry-run] stage {plugin.name}@{version} -> {destination}")
            else:
                shutil.copytree(plugin, destination, dirs_exist_ok=True)
        if not args.dry_run:
            backup = update_config(target, servers, replace=args.replace, dry_run=False)
            if backup:
                print(f"Configuration backup: {backup}")
            print(f"Registered {', '.join(servers)} for {args.host}. Reload the host; remote servers need compatible authentication.")
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.exit(1, f"MCP sync failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
