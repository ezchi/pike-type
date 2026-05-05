"""Path and naming helpers.

Generated outputs are co-located with the DSL source's containing prefix.
For a DSL file at ``<prefix>/piketype/<name>.py``, outputs land at:

  <prefix>/rtl/<name>_pkg.sv             (SV synthesis package)
  <prefix>/sim/<name>_test_pkg.sv        (SV verification package)
  <prefix>/py/<name>_types.py            (Python types)
  <prefix>/cpp/<name>_types.hpp          (C++ header)

The manifest is a single repo-root file: ``./piketype_manifest.json``.
"""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError


def repo_relative_path(path: Path, *, repo_root: Path) -> Path:
    """Return a path relative to the repository root."""
    return path.resolve().relative_to(repo_root.resolve())


def module_prefix(*, repo_root: Path, module_path: Path) -> Path:
    """Return the DSL module's prefix path (everything before ``piketype/``).

    Strict layout: DSL file MUST be at ``<prefix>/piketype/<name>.py`` with
    no nesting under ``piketype/``. Raises ``PikeTypeError`` if the layout
    is invalid.
    """
    relative = repo_relative_path(module_path, repo_root=repo_root)
    parts = relative.parts
    if len(parts) < 2 or parts[-2] != "piketype":
        raise PikeTypeError(
            f"DSL module {relative} must be at <prefix>/piketype/<name>.py "
            f"(parent directory must be exactly 'piketype/')"
        )
    return Path(*parts[:-2]) if len(parts) > 2 else Path()


def sv_module_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated SV synth-package path for a module."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    prefix = module_prefix(repo_root=repo_root, module_path=module_path)
    return repo_root / prefix / "rtl" / f"{relative.stem}_pkg.sv"


def sv_test_module_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated SV verification-package path for a module."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    prefix = module_prefix(repo_root=repo_root, module_path=module_path)
    return repo_root / prefix / "sim" / f"{relative.stem}_test_pkg.sv"


def py_module_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated Python types path for a module."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    prefix = module_prefix(repo_root=repo_root, module_path=module_path)
    return repo_root / prefix / "py" / f"{relative.stem}_types.py"


def cpp_header_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated C++ header path for a module."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    prefix = module_prefix(repo_root=repo_root, module_path=module_path)
    return repo_root / prefix / "cpp" / f"{relative.stem}_types.hpp"


def manifest_output_path(*, repo_root: Path) -> Path:
    """Return the generated manifest file path (repo-root)."""
    return repo_root / "piketype_manifest.json"
