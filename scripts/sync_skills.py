#!/usr/bin/env python3
"""Copy profile-selected skill folders to a user-chosen destination directory.

Agent hosts (Cursor, Claude Code, Codex, and others) discover skills from their own
paths. This script only packages the portable skill directories; it does not rewrite
host-specific configuration.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "profiles"
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def plugin_paths_for_profile(profile_name: str) -> list[Path]:
    profile = load_json(PROFILES / f"{profile_name}.json")
    marketplace = load_json(MARKETPLACE_PATH)
    by_name = {
        entry["name"]: ROOT / entry["source"]["path"]
        for entry in marketplace["plugins"]
    }
    missing = [name for name in profile["plugins"] if name not in by_name]
    if missing:
        raise KeyError(f"Profile references unknown plugins: {', '.join(missing)}")
    return [by_name[name] for name in profile["plugins"]]


def iter_skill_dirs(plugin_dirs: list[Path]) -> list[Path]:
    skills: list[Path] = []
    seen: dict[str, Path] = {}
    for plugin_dir in plugin_dirs:
        skills_root = plugin_dir / "skills"
        if not skills_root.is_dir():
            continue
        for skill_dir in sorted(skills_root.iterdir()):
            if not (skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file()):
                continue
            previous = seen.get(skill_dir.name)
            if previous is not None:
                raise ValueError(
                    f"Duplicate skill name '{skill_dir.name}' in "
                    f"{previous.relative_to(ROOT)} and {skill_dir.relative_to(ROOT)}"
                )
            seen[skill_dir.name] = skill_dir
            skills.append(skill_dir)
    return skills


def sync_skills(target: Path, skill_dirs: list[Path], *, dry_run: bool) -> int:
    target = target.expanduser().resolve()
    if not dry_run and target.exists() and not target.is_dir():
        raise NotADirectoryError(f"Target exists and is not a directory: {target}")
    if dry_run:
        print(f"[dry-run] mkdir {target}")
    else:
        target.mkdir(parents=True, exist_ok=True)

    for skill_dir in skill_dirs:
        destination = target / skill_dir.name
        if dry_run:
            print(f"[dry-run] copy {skill_dir.relative_to(ROOT)} -> {destination}")
            continue
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(skill_dir, destination)
        print(f"Synced {skill_dir.name}")
    return len(skill_dirs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        default="development",
        choices=["minimal", "development", "full"],
        help="Profile whose marketplace plugins supply skills",
    )
    parser.add_argument(
        "--target",
        required=True,
        type=Path,
        help="Destination directory (for example ~/.cursor/skills or .claude/skills)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned copies without writing files",
    )
    args = parser.parse_args()

    try:
        plugin_dirs = plugin_paths_for_profile(args.profile)
        skill_dirs = iter_skill_dirs(plugin_dirs)
        if not skill_dirs:
            print(f"No skills found for profile '{args.profile}'.", file=sys.stderr)
            return 1
        count = sync_skills(args.target, skill_dirs, dry_run=args.dry_run)
    except (OSError, KeyError, ValueError, json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Skill sync failed: {error}", file=sys.stderr)
        return 1

    action = "Would sync" if args.dry_run else "Synced"
    print(f"{action} {count} skill(s) from profile '{args.profile}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
