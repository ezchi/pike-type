"""Helpers for deriving module identities from paths."""

from __future__ import annotations

from pathlib import Path

from typist.paths import repo_relative_path


def module_basename(path: Path) -> str:
    """Return the module basename without its suffix."""
    return path.stem


def module_name_from_path(*, path: Path, repo_root: Path) -> str:
    """Return the Python import-style module name for a file path."""
    relative = repo_relative_path(path, repo_root=repo_root)
    return ".".join(relative.with_suffix("").parts)
