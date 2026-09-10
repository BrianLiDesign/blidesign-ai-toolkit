#!/usr/bin/env python3
"""Small stateful Codex CLI double for bootstrap and inventory contract tests."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def load_state() -> dict[str, object]:
    state_path = os.environ.get("FAKE_CODEX_STATE")
    if state_path and Path(state_path).is_file():
        return json.loads(Path(state_path).read_text(encoding="utf-8"))
    return {"marketplace": False, "plugins": []}


def save_state(state: dict[str, object]) -> None:
    state_path = os.environ.get("FAKE_CODEX_STATE")
    if state_path:
        Path(state_path).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = sys.argv[1:]
    state = load_state()

    if args[:4] == ["plugin", "marketplace", "list", "--json"]:
        marketplaces = []
        if state["marketplace"]:
            marketplaces.append({"name": "brian-ai-tools", "root": "/fake/marketplace"})
        print(json.dumps({"marketplaces": marketplaces}))
        return 0

    if args[:3] == ["plugin", "marketplace", "add"]:
        already_added = bool(state["marketplace"])
        state["marketplace"] = True
        state["marketplaceSource"] = args[3]
        state["marketplaceRef"] = (
            args[args.index("--ref") + 1] if "--ref" in args else None
        )
        save_state(state)
        print(
            json.dumps(
                {
                    "marketplaceName": "brian-ai-tools",
                    "installedRoot": "/fake/marketplace",
                    "alreadyAdded": already_added,
                }
            )
        )
        return 0

    if args[:3] == ["plugin", "marketplace", "remove"]:
        state["marketplace"] = False
        save_state(state)
        print("Marketplace removed")
        return 0

    if args[:3] == ["plugin", "marketplace", "upgrade"]:
        print("Marketplace upgraded")
        return 0

    if args[:2] == ["plugin", "add"]:
        selector = args[2]
        plugins = set(state["plugins"])
        plugins.add(selector)
        state["plugins"] = sorted(plugins)
        save_state(state)
        print(f"Added plugin {selector}")
        return 0

    if args[:3] == ["plugin", "list", "--json"]:
        installed = []
        for selector in state["plugins"]:
            name, _, marketplace = selector.partition("@")
            installed.append(
                {
                    "pluginId": selector,
                    "name": name,
                    "marketplaceName": marketplace,
                    "version": "0.1.0",
                    "enabled": True,
                    "source": {
                        "source": "local",
                        "path": os.environ.get("FAKE_PLUGIN_ROOT", ""),
                    },
                }
            )
        print(json.dumps({"installed": installed, "available": []}))
        return 0

    if args[:3] == ["mcp", "list", "--json"]:
        enabled = "developer-mcps@brian-ai-tools" in state["plugins"]
        print(
            json.dumps(
                [
                    {
                        "name": "marketplaceStatus",
                        "enabled": enabled,
                        "transport": {
                            "type": "stdio",
                            "command": "/private/machine/path/node",
                            "env": {"EXAMPLE_SECRET": "must-not-leak"},
                        },
                        "auth_status": "unsupported",
                    }
                ]
            )
        )
        return 0

    print(f"Unsupported fake Codex command: {' '.join(args)}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
