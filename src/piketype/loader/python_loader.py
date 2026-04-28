"""Python module loading helpers."""

from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from piketype.discovery.module_name import module_name_from_path
from piketype.errors import PikeTypeError


@contextmanager
def repo_import_path(repo_root: Path):
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


def load_module_from_path(path: Path, *, repo_root: Path) -> ModuleType:
    """Load a Python module from a file path using repo-root import semantics."""
    module_name = module_name_from_path(path=path, repo_root=repo_root)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PikeTypeError(f"could not create import spec for {path}")

    sys.modules.pop(module_name, None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        with repo_import_path(repo_root):
            spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - exercised via integration path
        sys.modules.pop(module_name, None)
        raise PikeTypeError(f"failed to load module {path}: {exc}") from exc
    return module
