#!/usr/bin/env python3
"""Export a sanitized Codex inventory without paths, environment values, or secrets."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CODEX_COMMAND = json.loads(os.environ.get("AI_TOOLKIT_CODEX_COMMAND_JSON", '["codex"]'))


def codex_json(*arguments: str) -> Any:
    completed = subprocess.run(
        [*CODEX_COMMAND, *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"codex {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return json.loads(completed.stdout)


def build_inventory() -> dict[str, Any]:
    marketplaces = codex_json("plugin", "marketplace", "list", "--json")
    plugins = codex_json("plugin", "list", "--json")
    mcp_servers = codex_json("mcp", "list", "--json")

    skill_root = Path.home() / ".codex" / "skills"
    skills = []
    if skill_root.is_dir():
        skills = sorted(
            path.name
            for path in skill_root.iterdir()
            if path.is_dir() and path.name != ".system" and (path / "SKILL.md").is_file()
        )

    installed_plugins = plugins.get("installed", plugins if isinstance(plugins, list) else [])
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "marketplaces": sorted(
            entry["name"] for entry in marketplaces.get("marketplaces", [])
        ),
        "plugins": sorted(
            (
                {
                    "id": entry.get("pluginId"),
                    "name": entry.get("name"),
                    "marketplace": entry.get("marketplaceName"),
                    "version": entry.get("version"),
                    "enabled": bool(entry.get("enabled")),
                }
                for entry in installed_plugins
            ),
            key=lambda item: str(item["id"]),
        ),
        "skills": skills,
        "mcpServers": sorted(
            (
                {
                    "name": entry.get("name"),
                    "enabled": bool(entry.get("enabled")),
                    "transport": entry.get("transport", {}).get("type"),
                    "authStatus": entry.get("auth_status"),
                }
                for entry in mcp_servers
            ),
            key=lambda item: str(item["name"]),
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inventory.local.json"),
        help="Destination JSON file (default: inventory.local.json)",
    )
    args = parser.parse_args()

    try:
        inventory = build_inventory()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Inventory export failed: {error}", file=sys.stderr)
        return 1

    print(f"Sanitized inventory written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
