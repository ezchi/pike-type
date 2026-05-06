"""Filesystem scanning for piketype modules."""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError


EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}
)


def is_under_piketype_dir(path: Path) -> bool:
    """Return whether the path's PARENT directory is exactly ``piketype``.

    Strict layout: DSL files must be at ``<prefix>/piketype/<name>.py`` —
    no nesting under ``piketype/``.
    """
    parts = path.parts
    return len(parts) >= 2 and parts[-2] == "piketype"


def ensure_cli_path_is_valid(path: Path) -> None:
    """Validate that the CLI path is a concrete DSL module path."""
    if path.suffix != ".py":
        raise PikeTypeError(f"expected a Python file path, got {path}")
    if path.name == "__init__.py":
        raise PikeTypeError(f"{path} is not a valid piketype module")
    if not is_under_piketype_dir(path):
        raise PikeTypeError(
            f"{path} must be at <prefix>/piketype/<name>.py "
            f"(parent directory must be exactly 'piketype/')"
        )


def find_piketype_modules(repo_root: Path) -> list[Path]:
    """Return all DSL module files at ``<prefix>/piketype/<name>.py``.

    Files whose basename starts with ``_`` (e.g. ``_helper.py``) are
    skipped: they are still importable from sibling DSL modules via
    Python's import machinery, but the build stage does not generate
    output for them. ``__init__.py`` is always skipped.
    """
    def _included(path: Path) -> bool:
        if path.name == "__init__.py":
            return False
        if path.stem.startswith("_"):
            return False
        rel = path.relative_to(repo_root)
        rel_parts = set(rel.parts)
        if rel_parts & EXCLUDED_DIRS:
            return False
        return is_under_piketype_dir(rel)

    return sorted(path for path in repo_root.rglob("*.py") if _included(path))


def find_skipped_underscore_modules(repo_root: Path) -> list[Path]:
    """Return DSL module candidates whose basename starts with ``_``.

    Used by the build stage to surface skipped modules in
    ``diagnostics.json`` so the user knows the convention applied.
    """
    def _is_underscore_skip(path: Path) -> bool:
        if path.name == "__init__.py" or not path.stem.startswith("_"):
            return False
        rel = path.relative_to(repo_root)
        rel_parts = set(rel.parts)
        if rel_parts & EXCLUDED_DIRS:
            return False
        return is_under_piketype_dir(rel)

    return sorted(path for path in repo_root.rglob("*.py") if _is_underscore_skip(path))
