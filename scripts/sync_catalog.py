#!/usr/bin/env python3
"""Generate the self-contained MCP catalog from canonical repository sources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "plugins" / "developer-mcps" / "assets" / "catalog.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_catalog() -> dict[str, Any]:
    marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    profiles = sorted(path.stem for path in (ROOT / "profiles").glob("*.json"))
    skills = list(
        (ROOT / "plugins" / "engineering-skills" / "skills").glob("*/SKILL.md")
    )
    sources = load_json(ROOT / "upstream" / "sources.lock.json")["sources"]
    return {
        "schemaVersion": 1,
        "marketplace": marketplace["name"],
        "plugins": [entry["name"] for entry in marketplace["plugins"]],
        "profiles": profiles,
        "vendoredSkillCount": len(skills),
        "upstreamSources": sorted(sources),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the packaged catalog differs from generated content",
    )
    args = parser.parse_args()
    try:
        expected = build_catalog()
        if args.check:
            actual = load_json(CATALOG_PATH)
            if actual != expected:
                print("Packaged MCP catalog is stale; run scripts/sync_catalog.py", file=sys.stderr)
                return 1
            print("Packaged MCP catalog is current.")
            return 0
        CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CATALOG_PATH.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    except (OSError, KeyError, json.JSONDecodeError) as error:
        print(f"Catalog synchronization failed: {error}", file=sys.stderr)
        return 1
    print(f"Updated {CATALOG_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
