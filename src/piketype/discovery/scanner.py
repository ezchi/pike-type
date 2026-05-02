"""Filesystem scanning for piketype modules."""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError
from piketype.paths import GEN_DIRNAME


EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}
)


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
    def _included(path: Path) -> bool:
        if path.name == "__init__.py":
            return False
        rel = path.relative_to(repo_root)
        rel_parts = set(rel.parts)
        if rel_parts & EXCLUDED_DIRS:
            return False
        if GEN_DIRNAME in rel_parts:
            return False
        return is_under_piketype_dir(rel)

    return sorted(path for path in repo_root.rglob("*.py") if _included(path))
