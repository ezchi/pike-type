"""Repository discovery helpers."""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError


def find_repo_root(start: Path) -> Path:
    """Walk upward until a repository marker is found."""
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    raise PikeTypeError(f"could not find repo root from {start}")
