#!/usr/bin/env python3
"""Validate the portable marketplace through its public repository contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from sync_catalog import build_catalog
from provenance import digest_directory


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SHA = re.compile(r"^[0-9a-f]{40}$")
SECRET_PATTERNS = {
    "OpenAI key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"gh[oprsu]_[A-Za-z0-9]{20,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
PORTABLE_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PORTABLE_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PORTABLE_IDENTITY_FIELDS = ("name", "version", "description", "license")


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


def resolve_plugin_path(plugin_dir: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.startswith("./"):
        raise VerificationError(f"{plugin_dir.name}: {field} must be a ./-relative path")
    resolved = (plugin_dir / value[2:]).resolve()
    if not resolved.is_relative_to(plugin_dir.resolve()):
        raise VerificationError(f"{plugin_dir.name}: {field} escapes the plugin root")
    return resolved


def validate_portable_mcp(plugin_dir: Path, path: Path) -> set[str]:
    configuration = load_json(path)
    if configuration.get("$schema") != PORTABLE_MCP_SCHEMA:
        raise VerificationError(f"{plugin_dir.name}: mcp.json uses an unsupported schema")
    if set(configuration) != {"$schema", "mcpServers"}:
        raise VerificationError(f"{plugin_dir.name}: mcp.json has unsupported fields")
    servers = configuration.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        raise VerificationError(f"{plugin_dir.name}: mcp.json must declare at least one server")

    for server_name, server in servers.items():
        if not isinstance(server_name, str) or not server_name or not isinstance(server, dict):
            raise VerificationError(f"{plugin_dir.name}: mcp.json contains an invalid server")
        server_type = server.get("type")
        if server_type == "stdio":
            allowed = {"type", "command", "args", "env", "cwd"}
            if set(server) - allowed:
                raise VerificationError(
                    f"{plugin_dir.name}: {server_name} has unsupported stdio fields"
                )
            if not isinstance(server.get("command"), str) or not server["command"]:
                raise VerificationError(
                    f"{plugin_dir.name}: {server_name} requires a command"
                )
            args = server.get("args", [])
            if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
                raise VerificationError(
                    f"{plugin_dir.name}: {server_name} args must be strings"
                )
            cwd = server.get("cwd")
            if cwd is not None:
                if isinstance(cwd, str) and cwd.startswith("./"):
                    resolve_plugin_path(plugin_dir, cwd, f"mcpServers.{server_name}.cwd")
                elif not isinstance(cwd, str) or not cwd.startswith(
                    ("${PLUGIN_ROOT}/", "${PLUGIN_DATA}/")
                ):
                    raise VerificationError(
                        f"{plugin_dir.name}: {server_name} has an invalid cwd"
                    )
            environment = server.get("env", {})
            if not isinstance(environment, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in environment.items()
            ):
                raise VerificationError(
                    f"{plugin_dir.name}: {server_name} env must contain strings"
                )
            if {"PLUGIN_ROOT", "PLUGIN_DATA"}.intersection(environment):
                raise VerificationError(
                    f"{plugin_dir.name}: {server_name} cannot override plugin path variables"
                )
        else:
            raise VerificationError(
                f"{plugin_dir.name}: {server_name} uses an unsupported transport"
            )
    return set(servers)


def validate_plugin(plugin_dir: Path, expected_name: str) -> None:
    portable_path = plugin_dir / "plugin.json"
    portable = load_json(portable_path)
    if portable.get("$schema") != PORTABLE_PLUGIN_SCHEMA:
        raise VerificationError(f"{expected_name}: root plugin.json uses an unsupported schema")
    if plugin_dir.name != expected_name or portable.get("name") != expected_name:
        raise VerificationError(f"{expected_name}: folder and manifest names must match")
    if not SEMVER.fullmatch(str(portable.get("version", ""))):
        raise VerificationError(f"{expected_name}: version must be strict semver")
    for field in ("description", "author", "license"):
        if not portable.get(field):
            raise VerificationError(f"{expected_name}: {field} is required")

    compatibility_path = plugin_dir / ".codex-plugin" / "plugin.json"
    compatibility = load_json(compatibility_path)
    for field in PORTABLE_IDENTITY_FIELDS:
        if compatibility.get(field) != portable.get(field):
            raise VerificationError(
                f"{expected_name}: compatibility manifest {field} differs from portable identity"
            )
    if not compatibility.get("author") or not compatibility.get("interface"):
        raise VerificationError(f"{expected_name}: compatibility presentation is incomplete")

    skills_path = compatibility.get("skills")
    if skills_path:
        skills_dir = resolve_plugin_path(plugin_dir, skills_path, "skills")
        if not any(skills_dir.glob("*/SKILL.md")):
            raise VerificationError(f"{expected_name}: declared skills path has no skills")

    compatibility_mcp = compatibility.get("mcpServers")
    portable_mcp_path = plugin_dir / "mcp.json"
    portable_server_names: set[str] = set()
    if portable_mcp_path.exists():
        portable_server_names = validate_portable_mcp(plugin_dir, portable_mcp_path)
    if compatibility_mcp:
        resolved = resolve_plugin_path(plugin_dir, compatibility_mcp, "mcpServers")
        legacy_mcp = load_json(resolved)
        legacy_servers = legacy_mcp.get("mcpServers")
        if not isinstance(legacy_servers, dict) or not legacy_servers:
            raise VerificationError(f"{expected_name}: declared MCP configuration is empty")
        if not portable_mcp_path.exists():
            raise VerificationError(
                f"{expected_name}: portable plugin with MCP requires root mcp.json"
            )
        if set(legacy_servers) != portable_server_names:
            raise VerificationError(
                f"{expected_name}: portable and compatibility MCP server names differ"
            )
        portable_servers = load_json(portable_mcp_path)["mcpServers"]
        for server_name, legacy_server in legacy_servers.items():
            portable_server = portable_servers[server_name]
            for field in ("command", "args"):
                if legacy_server.get(field) != portable_server.get(field):
                    raise VerificationError(
                        f"{expected_name}: {server_name} {field} differs between MCP configs"
                    )


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


def validate_source_provenance(root: Path, name: str, source: dict[str, Any]) -> None:
    if not SHA.fullmatch(str(source.get("commit", ""))):
        raise VerificationError(f"{name}: upstream commit must be a full SHA")
    destination = (root / str(source.get("destination", ""))).resolve()
    if not destination.is_relative_to(root.resolve()):
        raise VerificationError(f"{name}: destination escapes the repository")
    if not destination.is_dir():
        raise VerificationError(f"{name}: destination does not exist")
    if not source.get("license"):
        raise VerificationError(f"{name}: license is required")
    license_path = (root / str(source.get("licensePath", ""))).resolve()
    if not license_path.is_relative_to(root.resolve()) or not license_path.is_file():
        raise VerificationError(f"{name}: vendored license file is missing")
    expected_digest = source.get("contentSha256")
    if not isinstance(expected_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_digest
    ):
        raise VerificationError(f"{name}: contentSha256 must be a SHA-256 digest")
    if digest_directory(destination) != expected_digest:
        raise VerificationError(f"{name}: vendored content digest does not match")


def validate_provenance() -> None:
    lock = load_json(ROOT / "upstream" / "sources.lock.json")
    sources = lock.get("sources", {})
    if not sources:
        raise VerificationError("At least one upstream source must be recorded")
    for name, source in sources.items():
        validate_source_provenance(ROOT, name, source)


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
