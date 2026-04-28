"""Path and naming helpers."""

from __future__ import annotations

from pathlib import Path


GEN_DIRNAME = "gen"


def repo_relative_path(path: Path, *, repo_root: Path) -> Path:
    """Return a path relative to the repository root."""
    return path.resolve().relative_to(repo_root.resolve())


def gen_root(*, repo_root: Path) -> Path:
    """Return the generated-output root path."""
    return repo_root / GEN_DIRNAME


def sv_module_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated SV file path for a module package."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    return gen_root(repo_root=repo_root) / "sv" / relative.parent / f"{relative.stem}_pkg.sv"


def sv_test_module_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated SV verification package path for a module."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    return gen_root(repo_root=repo_root) / "sv" / relative.parent / f"{relative.stem}_test_pkg.sv"


def sv_runtime_output_path(*, repo_root: Path) -> Path:
    """Return the generated SV runtime package path."""
    return gen_root(repo_root=repo_root) / "sv" / "runtime" / "piketype_runtime_pkg.sv"


def py_module_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated Python file path for a module."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    return gen_root(repo_root=repo_root) / "py" / relative.parent / f"{relative.stem}_types.py"


def py_runtime_output_path(*, repo_root: Path) -> Path:
    """Return the generated Python runtime module path."""
    return gen_root(repo_root=repo_root) / "py" / "runtime" / "piketype_runtime.py"


def cpp_header_output_path(*, repo_root: Path, module_path: Path) -> Path:
    """Return the generated C++ header path for a module."""
    relative = repo_relative_path(module_path, repo_root=repo_root)
    return gen_root(repo_root=repo_root) / "cpp" / relative.parent / f"{relative.stem}_types.hpp"


def cpp_runtime_header_output_path(*, repo_root: Path) -> Path:
    """Return the generated C++ runtime header path."""
    return gen_root(repo_root=repo_root) / "cpp" / "runtime" / "piketype_runtime.hpp"


def cpp_runtime_source_output_path(*, repo_root: Path) -> Path:
    """Return the generated C++ runtime source path."""
    return gen_root(repo_root=repo_root) / "cpp" / "runtime" / "piketype_runtime.cpp"


def manifest_output_path(*, repo_root: Path) -> Path:
    """Return the generated manifest file path."""
    return gen_root(repo_root=repo_root) / "piketype_manifest.json"
