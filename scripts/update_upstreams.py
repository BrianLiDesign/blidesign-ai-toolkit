#!/usr/bin/env python3
"""Check or safely update pinned, vendored upstream skill collections."""

from __future__ import annotations

import argparse
import codecs
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from provenance import digest_directory
from sync_catalog import build_catalog


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "upstream" / "sources.lock.json"


def run_git(*arguments: str, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def ensure_repo_path(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise RuntimeError(f"Refusing to modify a path outside the repository: {resolved}")
    return resolved


def remote_head(repository: str) -> str:
    output = run_git("ls-remote", repository, "HEAD")
    commit = output.split()[0] if output else ""
    if len(commit) != 40:
        raise RuntimeError("Upstream HEAD did not resolve to a full commit SHA")
    return commit


def flatten_skills(source_root: Path, stage: Path) -> int:
    skill_directories = [path.parent for path in source_root.rglob("SKILL.md")]
    names = [path.name for path in skill_directories]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise RuntimeError(f"Duplicate skill names cannot be flattened: {', '.join(duplicates)}")
    if not skill_directories:
        raise RuntimeError("Upstream contains no SKILL.md files")

    stage.mkdir(parents=True)
    for skill_directory in skill_directories:
        copied = stage / skill_directory.name
        shutil.copytree(skill_directory, copied)
        skill_path = copied / "SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8")
        if "disable-model-invocation: true" in skill_text:
            skill_path.write_text(
                skill_text.replace(
                    "disable-model-invocation: true",
                    "disable-model-invocation: false",
                ),
                encoding="utf-8",
            )
            policy_path = copied / "agents" / "openai.yaml"
            if policy_path.exists():
                raise RuntimeError(
                    f"{skill_directory.name}: upstream now supplies agents/openai.yaml; "
                    "review the explicit-only policy translation manually"
                )
            policy_path.parent.mkdir(parents=True)
            display_name = skill_directory.name.replace("-", " ").title()
            policy_path.write_text(
                "interface:\n"
                f'  display_name: "{display_name}"\n'
                f'  short_description: "Explicitly invoke the {display_name} workflow"\n'
                f'  default_prompt: "Use ${skill_directory.name} to guide this task."\n'
                "policy:\n"
                "  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
    normalize_text_line_endings(stage)
    return len(skill_directories)


def normalize_text_line_endings(directory: Path) -> None:
    """Materialize UTF-8 vendored text with LF bytes on every host."""
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_bytes()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            continue
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        path.write_bytes(codecs.encode(normalized, "utf-8"))


def set_plugin_version(plugin_root: Path, version: str) -> None:
    """Update both manifest versions, restoring both if replacement fails."""
    manifest_paths = (
        plugin_root / "plugin.json",
        plugin_root / ".codex-plugin" / "plugin.json",
    )
    originals: dict[Path, bytes] = {}
    staged: dict[Path, Path] = {}
    for manifest_path in manifest_paths:
        originals[manifest_path] = manifest_path.read_bytes()
        manifest = json.loads(originals[manifest_path].decode("utf-8"))
        manifest["version"] = version
        stage = manifest_path.with_name(f".{manifest_path.name}.{uuid.uuid4().hex}.tmp")
        stage.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        staged[manifest_path] = stage

    replaced: list[Path] = []
    try:
        for manifest_path in manifest_paths:
            os.replace(staged[manifest_path], manifest_path)
            replaced.append(manifest_path)
    except BaseException:
        for manifest_path in replaced:
            rollback = manifest_path.with_name(
                f".{manifest_path.name}.{uuid.uuid4().hex}.rollback"
            )
            rollback.write_bytes(originals[manifest_path])
            os.replace(rollback, manifest_path)
        raise
    finally:
        for stage in staged.values():
            stage.unlink(missing_ok=True)


def update_source_lock(
    lock_path: Path, source_name: str, commit: str, destination: Path
) -> None:
    """Record the upstream commit and digest generated from installed content."""
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["sources"][source_name]["commit"] = commit
    lock["sources"][source_name]["contentSha256"] = digest_directory(destination)
    stage = lock_path.with_name(f".{lock_path.name}.{uuid.uuid4().hex}.tmp")
    try:
        stage.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        os.replace(stage, lock_path)
    finally:
        stage.unlink(missing_ok=True)


def apply_update(source_name: str, source: dict[str, str], commit: str) -> int:
    destination = ensure_repo_path(ROOT / source["destination"])
    license_destination = ensure_repo_path(ROOT / source["licensePath"])
    with tempfile.TemporaryDirectory(prefix="marketplace-upstream-") as directory:
        checkout = Path(directory) / "checkout"
        run_git("clone", "--depth", "1", source["repository"], str(checkout))
        checked_out_commit = run_git("rev-parse", "HEAD", cwd=checkout)
        if checked_out_commit != commit:
            raise RuntimeError("Upstream moved while the update was being prepared; retry")
        if not (checkout / "LICENSE").is_file():
            raise RuntimeError("Upstream license file is missing")

        stage = destination.parent / f".skills-stage-{uuid.uuid4().hex}"
        backup = destination.parent / f".skills-backup-{uuid.uuid4().hex}"
        try:
            count = flatten_skills(checkout / "skills", stage)
            destination.rename(backup)
            stage.rename(destination)
            shutil.copy2(checkout / "LICENSE", license_destination)
            shutil.rmtree(backup)
        except Exception:
            if destination.exists() and backup.exists():
                shutil.rmtree(destination)
            if backup.exists() and not destination.exists():
                backup.rename(destination)
            if stage.exists():
                shutil.rmtree(stage)
            raise

    update_source_lock(LOCK_PATH, source_name, commit, destination)
    catalog_path = ROOT / "plugins" / "developer-mcps" / "assets" / "catalog.json"
    catalog = build_catalog()
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    cachebuster = f"codex.upstream-{commit[:12]}"
    for plugin_name in ("engineering-skills", "developer-mcps"):
        plugin_root = ROOT / "plugins" / plugin_name
        portable = json.loads((plugin_root / "plugin.json").read_text(encoding="utf-8"))
        base_version = str(portable["version"]).split("+", 1)[0]
        set_plugin_version(plugin_root, f"{base_version}+{cachebuster}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply available updates")
    args = parser.parse_args()

    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        for name, source in lock["sources"].items():
            latest = remote_head(source["repository"])
            current = source["commit"]
            if latest == current:
                print(f"{name}: current at {current[:12]}")
                continue
            if not args.apply:
                print(f"{name}: update available {current[:12]} -> {latest[:12]}")
                continue
            count = apply_update(name, source, latest)
            print(f"{name}: updated to {latest[:12]} ({count} skills)")
    except (OSError, KeyError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Upstream update failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
