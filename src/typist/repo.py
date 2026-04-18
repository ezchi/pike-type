"""Repository discovery helpers."""

from __future__ import annotations

from pathlib import Path

from typist.errors import TypistError


def find_repo_root(start: Path) -> Path:
    """Walk upward until a repository marker is found."""
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    raise TypistError(f"could not find repo root from {start}")
