"""Generate command."""

from __future__ import annotations

from pathlib import Path

from piketype import __version__
from piketype.backends.cpp.emitter import emit_cpp
from piketype.backends.py.emitter import emit_py
from piketype.backends.runtime.emitter import emit_runtime
from piketype.backends.sv.emitter import emit_sv
from piketype.discovery.scanner import ensure_cli_path_is_valid, find_piketype_modules
from piketype.dsl.freeze import (
    FrozenModule,
    build_const_definition_map,
    build_loaded_module,
    build_type_definition_map,
    freeze_module,
    freeze_repo,
)
from piketype.loader.python_loader import load_or_get_module, prepare_run
from piketype.manifest.write_json import write_manifest
from piketype.repo import find_repo_root
from piketype.validate.engine import validate_repo
from piketype.validate.namespace import check_duplicate_basenames, validate_cpp_namespace


def run_gen(path: str, *, namespace: str | None = None) -> None:
    """Run generation orchestration."""
    if namespace is not None:
        validate_cpp_namespace(namespace)

    cli_path = Path(path).resolve()
    ensure_cli_path_is_valid(cli_path)
    repo_root = find_repo_root(cli_path)
    module_paths = find_piketype_modules(repo_root)

    # FR-9a: basename uniqueness runs unconditionally (cross-module SV imports
    # identify target packages by basename, so duplicates would silently misroute).
    check_duplicate_basenames(module_paths=module_paths)

    with prepare_run(repo_root=repo_root, module_paths=module_paths):
        loaded_modules = [
            build_loaded_module(
                module=load_or_get_module(module_path, repo_root=repo_root),
                module_path=module_path,
                repo_root=repo_root,
            )
            for module_path in module_paths
        ]
        definition_map = build_const_definition_map(loaded_modules=loaded_modules)
        type_definition_map = build_type_definition_map(loaded_modules=loaded_modules)

        frozen_modules: list[FrozenModule] = []
        cli_module_had_local_definitions = False
        for loaded_module in loaded_modules:
            frozen_module = freeze_module(
                loaded_module=loaded_module,
                definition_map=definition_map,
                type_definition_map=type_definition_map,
            )
            if loaded_module.module_path == cli_path and frozen_module.has_local_definitions:
                cli_module_had_local_definitions = True
            frozen_modules.append(frozen_module)

        repo = freeze_repo(repo_root=repo_root, frozen_modules=frozen_modules, tool_version=__version__)
        validate_repo(repo)
        if not cli_module_had_local_definitions:
            from piketype.errors import ValidationError

            raise ValidationError(f"{cli_path}: piketype file defines no DSL objects")

        emit_sv(repo)
        emit_py(repo)
        emit_cpp(repo, namespace=namespace)
        emit_runtime(repo)
        write_manifest(repo)
