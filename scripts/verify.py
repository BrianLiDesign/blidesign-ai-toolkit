#!/usr/bin/env python3
"""Validate the portable marketplace through its public repository contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from sync_catalog import build_catalog


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SHA = re.compile(r"^[0-9a-f]{40}$")
SECRET_PATTERNS = {
    "OpenAI key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"gh[oprsu]_[A-Za-z0-9]{20,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


class VerificationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VerificationError(f"Cannot read valid JSON from {path.relative_to(ROOT)}: {error}") from error


def validate_marketplace() -> tuple[str, set[str]]:
    marketplace = load_json(MARKETPLACE_PATH)
    name = marketplace.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise VerificationError("Marketplace name is missing or invalid")

    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or not entries:
        raise VerificationError("Marketplace must contain at least one plugin")

    names: set[str] = set()
    for entry in entries:
        plugin_name = entry.get("name")
        if not isinstance(plugin_name, str) or plugin_name in names:
            raise VerificationError(f"Invalid or duplicate plugin name: {plugin_name!r}")
        names.add(plugin_name)
        expected_path = f"./plugins/{plugin_name}"
        if entry.get("source") != {"source": "local", "path": expected_path}:
            raise VerificationError(f"{plugin_name}: source must be {expected_path}")
        policy = entry.get("policy", {})
        if policy.get("installation") not in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}:
            raise VerificationError(f"{plugin_name}: invalid installation policy")
        if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
            raise VerificationError(f"{plugin_name}: invalid authentication policy")
        if not entry.get("category"):
            raise VerificationError(f"{plugin_name}: category is required")

        validate_plugin(ROOT / "plugins" / plugin_name, plugin_name)
    return name, names


def validate_plugin(plugin_dir: Path, expected_name: str) -> None:
    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    manifest = load_json(manifest_path)
    if plugin_dir.name != expected_name or manifest.get("name") != expected_name:
        raise VerificationError(f"{expected_name}: folder and manifest names must match")
    if not SEMVER.fullmatch(str(manifest.get("version", ""))):
        raise VerificationError(f"{expected_name}: version must be strict semver")
    for field in ("description", "author", "interface"):
        if not manifest.get(field):
            raise VerificationError(f"{expected_name}: {field} is required")

    skills_path = manifest.get("skills")
    if skills_path:
        skills_dir = plugin_dir / str(skills_path).removeprefix("./")
        if not any(skills_dir.glob("*/SKILL.md")):
            raise VerificationError(f"{expected_name}: declared skills path has no skills")

    mcp_path = manifest.get("mcpServers")
    if mcp_path:
        resolved = plugin_dir / str(mcp_path).removeprefix("./")
        mcp = load_json(resolved)
        if not mcp.get("mcpServers"):
            raise VerificationError(f"{expected_name}: declared MCP configuration is empty")


def validate_profiles(marketplace_name: str, plugin_names: set[str]) -> None:
    profiles = sorted((ROOT / "profiles").glob("*.json"))
    if {path.stem for path in profiles} != {"minimal", "development", "full"}:
        raise VerificationError("Profiles must be exactly minimal, development, and full")
    for path in profiles:
        profile = load_json(path)
        if profile.get("marketplace") != marketplace_name:
            raise VerificationError(f"{path.name}: wrong marketplace name")
        selected = profile.get("plugins")
        if not isinstance(selected, list) or not set(selected).issubset(plugin_names):
            raise VerificationError(f"{path.name}: references an unknown marketplace plugin")
        external = profile.get("externalPlugins")
        if not isinstance(external, list):
            raise VerificationError(f"{path.name}: externalPlugins must be a list")
        for item in external:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise VerificationError(f"{path.name}: invalid external plugin entry")


def validate_packaged_catalog(marketplace_name: str, plugin_names: set[str]) -> None:
    catalog = load_json(ROOT / "plugins" / "developer-mcps" / "assets" / "catalog.json")
    expected = build_catalog()
    if catalog.get("marketplace") != marketplace_name:
        raise VerificationError("Packaged MCP catalog has the wrong marketplace name")
    catalog_plugins = catalog.get("plugins", [])
    if len(catalog_plugins) != len(plugin_names) or set(catalog_plugins) != plugin_names:
        raise VerificationError("Packaged MCP catalog does not match marketplace plugins")
    if catalog != expected:
        raise VerificationError("Packaged MCP catalog is stale; run scripts/sync_catalog.py")


def validate_provenance() -> None:
    lock = load_json(ROOT / "upstream" / "sources.lock.json")
    sources = lock.get("sources", {})
    if not sources:
        raise VerificationError("At least one upstream source must be recorded")
    for name, source in sources.items():
        if not SHA.fullmatch(str(source.get("commit", ""))):
            raise VerificationError(f"{name}: upstream commit must be a full SHA")
        destination = ROOT / str(source.get("destination", ""))
        if not destination.is_dir():
            raise VerificationError(f"{name}: destination does not exist")
        if not source.get("license"):
            raise VerificationError(f"{name}: license is required")


def scan_for_secrets() -> None:
    ignored = {".git", "__pycache__"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or ignored.intersection(path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                raise VerificationError(f"Potential {label} found in {path.relative_to(ROOT)}")


def main() -> int:
    try:
        marketplace_name, plugins = validate_marketplace()
        validate_profiles(marketplace_name, plugins)
        validate_provenance()
        validate_packaged_catalog(marketplace_name, plugins)
        scan_for_secrets()
    except VerificationError as error:
        print(f"Marketplace verification failed: {error}", file=sys.stderr)
        return 1

    skill_count = len(list((ROOT / "plugins" / "engineering-skills" / "skills").glob("*/SKILL.md")))
    print(
        f"Marketplace verification passed: {len(plugins)} plugins, "
        f"{skill_count} vendored engineering skills, 3 profiles."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
