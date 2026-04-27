"""Filesystem scanning for typist modules."""

from __future__ import annotations

from pathlib import Path

from typist.errors import TypistError
from typist.paths import GEN_DIRNAME


def is_under_typist_dir(path: Path) -> bool:
    """Return whether the path lives under a directory named ``typist``."""
    return "typist" in path.parts


def ensure_cli_path_is_valid(path: Path) -> None:
    """Validate that the CLI path is a concrete DSL module path."""
    if path.suffix != ".py":
        raise TypistError(f"expected a Python file path, got {path}")
    if path.name == "__init__.py":
        raise TypistError(f"{path} is not a valid typist module")
    if not is_under_typist_dir(path):
        raise TypistError(f"{path} is not under a typist/ directory")


def find_typist_modules(repo_root: Path) -> list[Path]:
    """Return all DSL module files under typist/ directories."""
    return sorted(
        path
        for path in repo_root.rglob("*.py")
        if path.name != "__init__.py"
        and GEN_DIRNAME not in path.relative_to(repo_root).parts
        and is_under_typist_dir(path.relative_to(repo_root))
    )
