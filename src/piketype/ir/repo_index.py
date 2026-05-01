"""Repo-wide indexes over frozen IR.

Backends consume `RepoIR` and resolve `TypeRefIR` lookups via the index
returned by `build_repo_type_index`. The index is keyed by
``(module_python_name, type_name)`` so cross-module references resolve to
the correct defining module's type, even when multiple modules declare a
type with the same local name.
"""

from __future__ import annotations

from piketype.ir.nodes import RepoIR, TypeDefIR


def build_repo_type_index(repo: RepoIR) -> dict[tuple[str, str], TypeDefIR]:
    """Build a repo-wide type index keyed by (module_python_name, type_name)."""
    index: dict[tuple[str, str], TypeDefIR] = {}
    for module in repo.modules:
        for type_def in module.types:
            index[(module.ref.python_module_name, type_def.name)] = type_def
    return index
