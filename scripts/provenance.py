"""Deterministic provenance helpers shared by update and verification workflows."""

from __future__ import annotations

import hashlib
from pathlib import Path


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
