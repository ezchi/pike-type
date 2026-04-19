"""Generate command."""

from __future__ import annotations

from pathlib import Path

from typist import __version__
from typist.backends.cpp.emitter import emit_cpp
from typist.backends.py.emitter import emit_py
from typist.backends.runtime.emitter import emit_runtime
from typist.backends.sv.emitter import emit_sv
from typist.discovery.scanner import ensure_cli_path_is_valid, find_typist_modules
from typist.dsl.freeze import build_const_definition_map, build_loaded_module, build_type_definition_map, freeze_module, freeze_repo
from typist.loader.python_loader import load_module_from_path
from typist.manifest.write_json import write_manifest
from typist.repo import find_repo_root
from typist.validate.engine import validate_repo


def run_gen(path: str) -> None:
    """Run generation orchestration."""
    cli_path = Path(path).resolve()
    ensure_cli_path_is_valid(cli_path)
    repo_root = find_repo_root(cli_path)
    module_paths = find_typist_modules(repo_root)

    loaded_modules = [
        build_loaded_module(
            module=load_module_from_path(module_path, repo_root=repo_root),
            module_path=module_path,
            repo_root=repo_root,
        )
        for module_path in module_paths
    ]
    definition_map = build_const_definition_map(loaded_modules=loaded_modules)
    type_definition_map = build_type_definition_map(loaded_modules=loaded_modules)

    frozen_modules = []
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
        from typist.errors import ValidationError

        raise ValidationError(f"{cli_path}: typist file defines no DSL objects")

    emit_sv(repo)
    emit_py(repo)
    emit_cpp(repo)
    emit_runtime(repo)
    write_manifest(repo)
