"""Generate command."""

from __future__ import annotations

from pathlib import Path

from typist import __version__
from typist.backends.runtime.emitter import emit_runtime
from typist.backends.sv.emitter import emit_sv
from typist.discovery.scanner import ensure_cli_path_is_valid, find_typist_modules
from typist.dsl.freeze import freeze_module, freeze_repo
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

    frozen_modules = []
    cli_module_had_local_definitions = False
    for module_path in module_paths:
        loaded_module = load_module_from_path(module_path, repo_root=repo_root)
        frozen_module = freeze_module(module=loaded_module, module_path=module_path, repo_root=repo_root)
        if module_path == cli_path and frozen_module.has_local_definitions:
            cli_module_had_local_definitions = True
        frozen_modules.append(frozen_module)

    repo = freeze_repo(repo_root=repo_root, frozen_modules=frozen_modules, tool_version=__version__)
    validate_repo(repo)
    if not cli_module_had_local_definitions:
        from typist.errors import ValidationError

        raise ValidationError(f"{cli_path}: typist file defines no DSL objects")

    emit_sv(repo)
    emit_runtime(repo)
    write_manifest(repo)
