"""Read and write the on-disk IR cache.

The cache mirrors the source tree under ``frontend.piketype_root`` —
input ``alpha/piketype/foo.py`` becomes ``alpha/piketype/foo.ir.json``
under the cache root. A top-level ``_index.json`` lists every cached
module and pins the schema version.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from piketype.config import Config
from piketype.ir.nodes import ModuleIR, RepoIR
from piketype.ir_io.codec import decode_module, encode_module
from piketype.ir_io.schema import SCHEMA_VERSION, IRSchemaMismatchError


_INDEX_FILENAME = "_index.json"
_MODULE_SUFFIX = ".ir.json"


def write_cache(*, repo: RepoIR, config: Config) -> Path:
    """Write the IR cache for ``repo`` under ``config.frontend.ir_cache``.

    Returns the cache root path. Existing cache files are overwritten;
    any stale module IR files (modules removed since the last build) are
    left in place. (Pruning is a future enhancement.)
    """
    cache_root = config.frontend.ir_cache
    piketype_root = config.frontend.piketype_root
    project_root = config.project_root

    cache_root.mkdir(parents=True, exist_ok=True)

    module_entries: list[dict[str, Any]] = []
    for module in repo.modules:
        source_path = project_root / module.ref.repo_relative_path
        ir_relpath = _module_ir_relpath(module=module, piketype_root=piketype_root, project_root=project_root)
        ir_path = cache_root / ir_relpath
        ir_path.parent.mkdir(parents=True, exist_ok=True)
        ir_path.write_text(
            json.dumps(encode_module(module), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        module_entries.append(
            {
                "python_module_name": module.ref.python_module_name,
                "repo_relative_path": module.ref.repo_relative_path,
                "ir_relpath": str(ir_relpath),
                "source_hash": _hash_file(source_path) if source_path.is_file() else "",
            }
        )

    index = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": repo.tool_version,
        "project_root": ".",
        "modules": module_entries,
    }
    index_path = cache_root / _INDEX_FILENAME
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return cache_root


def read_cache(*, config: Config) -> RepoIR:
    """Load the IR cache and reconstruct a ``RepoIR``.

    Raises ``IRSchemaMismatchError`` on schema version mismatch.
    Raises ``FileNotFoundError`` if the cache is missing — caller
    should re-run ``piketype build``.
    """
    cache_root = config.frontend.ir_cache
    index_path = cache_root / _INDEX_FILENAME
    if not index_path.is_file():
        raise FileNotFoundError(
            f"IR cache index missing at {index_path}; run `piketype build` first"
        )

    raw_obj: object = json.loads(index_path.read_text(encoding="utf-8"))
    raw = _as_mapping(raw_obj, where=str(index_path))

    schema_version = raw.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise IRSchemaMismatchError(
            f"IR cache schema_version={schema_version!r} does not match this build's "
            f"SCHEMA_VERSION={SCHEMA_VERSION}; re-run `piketype build` to regenerate the cache"
        )

    tool_version_raw = raw.get("tool_version")
    tool_version = tool_version_raw if isinstance(tool_version_raw, str) else None
    modules_index = _as_list(raw.get("modules") or [], where=f"{index_path}: modules")

    modules: list[ModuleIR] = []
    for entry_obj in modules_index:
        entry = _as_mapping(entry_obj, where=f"{index_path}: module entry")
        ir_relpath = entry.get("ir_relpath")
        if not isinstance(ir_relpath, str):
            raise IRSchemaMismatchError(f"{index_path}: missing 'ir_relpath' in module entry")
        ir_path = cache_root / ir_relpath
        ir_data: object = json.loads(ir_path.read_text(encoding="utf-8"))
        modules.append(decode_module(ir_data))

    return RepoIR(
        repo_root=str(config.project_root),
        modules=tuple(modules),
        tool_version=tool_version,
    )


def _as_mapping(value: object, *, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IRSchemaMismatchError(f"{where}: expected mapping, got {type(value).__name__}")
    typed: dict[str, Any] = {}
    for k, v in value.items():  # pyright: ignore[reportUnknownVariableType]
        typed[str(k)] = v  # pyright: ignore[reportUnknownArgumentType]
    return typed


def _as_list(value: object, *, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise IRSchemaMismatchError(f"{where}: expected list, got {type(value).__name__}")
    typed: list[Any] = []
    for item in value:  # pyright: ignore[reportUnknownVariableType]
        typed.append(item)  # pyright: ignore[reportUnknownArgumentType]
    return typed


def _module_ir_relpath(*, module: ModuleIR, piketype_root: Path, project_root: Path) -> Path:
    """Return the IR file's path relative to the cache root.

    Mirrors the source tree under ``piketype_root``, with ``.py``
    replaced by ``.ir.json``. If the module sits above ``piketype_root``
    (legacy/edge case), fall back to a path under ``project_root``.
    """
    abs_source = project_root / module.ref.repo_relative_path
    try:
        relative = abs_source.resolve().relative_to(piketype_root.resolve())
    except ValueError:
        relative = abs_source.resolve().relative_to(project_root.resolve())
    return relative.with_suffix(".ir.json")


def _hash_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
