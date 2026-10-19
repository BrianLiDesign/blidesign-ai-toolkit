"""Deterministic provenance helpers shared by update and verification workflows."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


OVERLAY_START = "<!-- blidesign-toolkit-overlay:start -->"
OVERLAY_END = "<!-- blidesign-toolkit-overlay:end -->"


def load_skill_overlays(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schemaVersion") != 1 or not isinstance(data.get("skills"), dict):
        raise ValueError("Skill overlays require schemaVersion 1 and a skills object")
    for name, text in data["skills"].items():
        if not re.fullmatch(r"[a-z0-9-]+", name) or not isinstance(text, str) or not text.strip():
            raise ValueError("Skill overlays require safe skill names and nonempty text")
        if OVERLAY_START in text or OVERLAY_END in text:
            raise ValueError("Overlay text cannot contain overlay markers")
    return data["skills"]


def overlay_suffix(text: str) -> str:
    return f"\n\n{OVERLAY_START}\n{text.strip()}\n{OVERLAY_END}\n"


def apply_skill_overlays(directory: Path, path: Path) -> None:
    """Append owned guidance without changing upstream content or provenance."""
    pending = {}
    for name, text in load_skill_overlays(path).items():
        target = directory / name / "SKILL.md"
        if not target.is_file() or not target.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f"Overlay target missing or outside skill tree: {name}")
        original = target.read_text(encoding="utf-8")
        if OVERLAY_START in original:
            if original.count(OVERLAY_START) != 1 or original.count(OVERLAY_END) != 1 or not original.rstrip().endswith(OVERLAY_END):
                raise ValueError(f"Malformed existing toolkit overlay: {name}")
            original = original.split(OVERLAY_START)[0]
        pending[target] = original.rstrip() + overlay_suffix(text)
    for target, text in pending.items():
        target.write_bytes(text.encode("utf-8"))


def digest_directory(directory: Path) -> str:
    """Hash every sorted relative path and its exact stored file bytes."""
    hasher = hashlib.sha256()
    files = sorted(
        (path for path in directory.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(directory).as_posix(),
    )
    for path in files:
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        content = path.read_bytes()
        hasher.update(len(relative).to_bytes(8, "big"))
        hasher.update(relative)
        hasher.update(len(content).to_bytes(8, "big"))
        hasher.update(content)
    return hasher.hexdigest()
