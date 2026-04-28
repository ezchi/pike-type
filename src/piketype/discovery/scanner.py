"""Filesystem scanning for piketype modules."""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError
from piketype.paths import GEN_DIRNAME


def is_under_piketype_dir(path: Path) -> bool:
    """Return whether the path lives under a directory named ``piketype``."""
    return "piketype" in path.parts


def ensure_cli_path_is_valid(path: Path) -> None:
    """Validate that the CLI path is a concrete DSL module path."""
    if path.suffix != ".py":
        raise PikeTypeError(f"expected a Python file path, got {path}")
    if path.name == "__init__.py":
        raise PikeTypeError(f"{path} is not a valid piketype module")
    if not is_under_piketype_dir(path):
        raise PikeTypeError(f"{path} is not under a piketype/ directory")


def find_piketype_modules(repo_root: Path) -> list[Path]:
    """Return all DSL module files under piketype/ directories."""
    return sorted(
        path
        for path in repo_root.rglob("*.py")
        if path.name != "__init__.py"
        and GEN_DIRNAME not in path.relative_to(repo_root).parts
        and is_under_piketype_dir(path.relative_to(repo_root))
    )
