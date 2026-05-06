"""Path and naming helpers.

For a DSL file at ``<piketype_root>/<sub>/piketype/<base>.py``, generated
outputs land at::

    <backend.out>/<sub>/[<backend.name>/]<base><suffix><ext>

The ``<backend.name>`` segment is inserted only when ``backend.language_id``
is true. The basename suffix and extension are backend-defined constants
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

    The shape depends on ``backend.out_layout``:

    * ``prefix`` →  ``<backend.out>/<sub>/[<backend.name>/]<file>``.
      ``backend.out`` is treated as an absolute path; ``<sub>`` is the
      module's parent path (with the ``piketype/`` segment stripped).
    * ``suffix`` →  ``<project_root>/<sub>/<rel_out>/[<backend.name>/]<file>``.
      ``rel_out`` is ``backend.out`` made relative to ``project_root``;
      this is the HDL role-directory convention (e.g. ``alpha/rtl/...``).

    ``language_id: true`` inserts a ``<backend.name>/`` segment before
    the file in either layout.
    """
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

    if backend.out_layout == "prefix":
        components: list[str] = list(sub)
        if backend.language_id:
            components.append(backend.name)
        components.append(file_name)
        return backend.out / Path(*components)

    # suffix layout
    try:
        rel_out = backend.out.resolve().relative_to(project_root.resolve())
    except ValueError as exc:
        raise PikeTypeError(
            f"backend {backend.name!r}: out={backend.out} is outside project_root={project_root} "
            f"and cannot be used with out_layout=suffix"
        ) from exc
    components_suffix: list[str] = [*sub, *rel_out.parts]
    if backend.language_id:
        components_suffix.append(backend.name)
    components_suffix.append(file_name)
    return project_root / Path(*components_suffix)


def manifest_output_path(*, project_root: Path) -> Path:
    """Return the generated manifest file path under project root."""
    return project_root / "piketype_manifest.json"
