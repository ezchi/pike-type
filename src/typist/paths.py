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


def sv_runtime_output_path(*, repo_root: Path) -> Path:
    """Return the generated SV runtime package path."""
    return gen_root(repo_root=repo_root) / "sv" / "runtime" / "typist_runtime_pkg.sv"


def manifest_output_path(*, repo_root: Path) -> Path:
    """Return the generated manifest file path."""
    return gen_root(repo_root=repo_root) / "typist_manifest.json"
