"""Python module loading helpers.

This module provides a per-run scoped session for loading piketype DSL modules.

Why per-run scoping is required: piketype DSL types (ScalarType, StructType, etc.)
are tracked by Python object identity. When module A imports a type from module B
via ``from B import T``, Python's import machinery must return the *same* T object
that piketype itself tracks for B. The loader achieves this by:

1. Pre-cleaning ``sys.modules`` of all keys piketype "owns" for this run (the
   discovered module names plus their dotted prefixes), so the subsequent loads
   are fresh.
2. Loading each module exactly once per run via ``load_or_get_module``, which
   reuses cached entries from ``sys.modules`` to preserve identity.
3. Restoring originals on exit so consecutive runs in the same Python process
   (e.g., test fixture loads) do not leak state.

This contract is enforced via the ``prepare_run`` context manager. Calling
``load_or_get_module`` outside an active scope raises ``RuntimeError``.
"""

from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import sys
from collections.abc import Generator
from pathlib import Path
from types import ModuleType

from piketype.discovery.module_name import module_name_from_path
from piketype.errors import PikeTypeError


_active_owned_keys: frozenset[str] | None = None


@contextmanager
def repo_import_path(repo_root: Path) -> Generator[None]:
    """Temporarily add the repo root to ``sys.path``."""
    repo_root_str = str(repo_root)
    already_present = repo_root_str in sys.path
    if not already_present:
        sys.path.insert(0, repo_root_str)
    try:
        yield
    finally:
        if not already_present:
            sys.path.remove(repo_root_str)


def _compute_owned_keys(*, module_paths: list[Path], repo_root: Path) -> frozenset[str]:
    """Compute the set of sys.modules keys this run owns.

    For each discovered module name (e.g., ``alpha.piketype.foo``), the owned
    set includes the leaf name and every dotted prefix (``alpha``,
    ``alpha.piketype``). Prefixes cover implicit namespace packages that
    Python's import system creates when loading nested modules.
    """
    keys: set[str] = set()
    for path in module_paths:
        name = module_name_from_path(path=path, repo_root=repo_root)
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            keys.add(".".join(parts[:i]))
    return frozenset(keys)


@contextmanager
def prepare_run(*, repo_root: Path, module_paths: list[Path]) -> Generator[None]:
    """Enter a per-run loader scope.

    Snapshots originals of any owned ``sys.modules`` entries, pre-cleans the
    owned keys, yields control, and on exit restores originals (or removes
    keys that did not pre-exist).

    Within an active scope, ``load_or_get_module`` is callable and returns
    cached entries to preserve cross-module type identity.
    """
    global _active_owned_keys

    if _active_owned_keys is not None:
        raise RuntimeError("prepare_run scopes cannot be nested")

    owned_keys = _compute_owned_keys(module_paths=module_paths, repo_root=repo_root)
    pre_owned: dict[str, ModuleType] = {k: sys.modules[k] for k in owned_keys if k in sys.modules}

    for key in owned_keys:
        sys.modules.pop(key, None)

    _active_owned_keys = owned_keys
    try:
        yield
    finally:
        _active_owned_keys = None
        for key in owned_keys:
            sys.modules.pop(key, None)
        for key, original in pre_owned.items():
            sys.modules[key] = original


def load_or_get_module(path: Path, *, repo_root: Path) -> ModuleType:
    """Load a piketype module within an active ``prepare_run`` scope.

    If the module is already cached in ``sys.modules`` (because a prior
    ``from M import ...`` triggered Python's import machinery to load it),
    return the cached instance. Otherwise execute the module fresh and
    cache it.

    Raises ``RuntimeError`` if called outside an active ``prepare_run``
    scope, since identity stability across modules requires the scope's
    snapshot/restore contract.
    """
    if _active_owned_keys is None:
        raise RuntimeError("load_or_get_module called outside prepare_run scope")

    module_name = module_name_from_path(path=path, repo_root=repo_root)

    if module_name not in _active_owned_keys:
        raise RuntimeError(
            f"module {module_name!r} is not in the active prepare_run owned-key set; "
            "it must be in module_paths passed to prepare_run"
        )

    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PikeTypeError(f"could not create import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        with repo_import_path(repo_root):
            spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise PikeTypeError(f"failed to load module {path}: {exc}") from exc
    return module
