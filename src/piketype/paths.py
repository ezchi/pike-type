"""Path and naming helpers.

For a DSL file at ``<piketype_root>/<sub>/piketype/<base>.py``, generated
outputs land at::

    <backend.backend_root>/<sub>/<backend.language_id>/<base><suffix><ext>

Empty ``backend_root`` resolves to the project root (the segment is
absent in the joined path); empty ``language_id`` collapses that
segment. The basename suffix and extension are backend-defined constants
(e.g. ``_pkg.sv``, ``_test_pkg.sv``, ``_types.py``, ``_types.hpp``) and
are not user-configurable.

The manifest is written at ``<project_root>/piketype_manifest.json``.
"""

from __future__ import annotations

from pathlib import Path

from piketype.config import BackendConfig
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


def backend_output_path(
    *,
    backend: BackendConfig,
    project_root: Path,
    piketype_root: Path,
    module_path: Path,
    basename_suffix: str,
    ext: str,
) -> Path:
    """Compute the output path for a module under a given backend.

    Single formula: ``<backend_root>/<sub>/<language_id>/<file>``, where
    ``<sub>`` is ``module_path`` made relative to ``piketype_root`` with
    the trailing ``piketype/<base>.py`` stripped. An empty
    ``language_id`` collapses that segment.

    ``project_root`` is unused in the new schema but retained in the
    signature for caller compatibility.
    """
    del project_root  # backend_root is already absolute after resolution
    relative = repo_relative_path(module_path, repo_root=piketype_root)
    parts = relative.parts
    if len(parts) < 2 or parts[-2] != "piketype":
        raise PikeTypeError(
            f"DSL module {relative} must be at <prefix>/piketype/<name>.py "
            f"(parent directory must be exactly 'piketype/')"
        )
    sub = parts[:-2]
    base = relative.stem
    file_name = f"{base}{basename_suffix}{ext}"

    components: list[str] = list(sub)
    if backend.language_id:
        components.append(backend.language_id)
    components.append(file_name)
    return backend.backend_root / Path(*components)


def manifest_output_path(*, project_root: Path) -> Path:
    """Return the generated manifest file path under project root."""
    return project_root / "piketype_manifest.json"
