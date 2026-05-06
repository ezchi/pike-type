"""Frontend build stage: discover, execute, freeze, write IR cache.

This is the only stage that runs user Python. Its outputs are:

  * the IR cache under ``config.frontend.ir_cache``
  * ``diagnostics.json`` listing skipped modules, cycles, and errors

If any diagnostic has severity ``error`` (e.g. an import cycle), the
build raises ``PikeTypeError`` after persisting the diagnostics file
so the user can inspect what went wrong.
"""

from __future__ import annotations

from pathlib import Path

from piketype import __version__
from piketype.config import Config, find_config, load_config
from piketype.discovery.dep_graph import detect_module_cycles
from piketype.discovery.scanner import find_piketype_modules, find_skipped_underscore_modules
from piketype.dsl.freeze import (
    FrozenModule,
    build_const_definition_map,
    build_loaded_module,
    build_type_definition_map,
    build_vec_const_definition_map,
    freeze_module,
    freeze_repo,
)
from piketype.errors import PikeTypeError
from piketype.ir.nodes import RepoIR
from piketype.ir_io import Diagnostic, has_errors, write_cache, write_diagnostics
from piketype.loader.python_loader import load_or_get_module, prepare_run
from piketype.validate.engine import validate_repo
from piketype.validate.namespace import check_duplicate_basenames


def run_build(*, config_path: Path | None = None, start: Path | None = None) -> RepoIR:
    """Resolve config, build, write IR cache + diagnostics, return ``RepoIR``."""
    config = load_config(find_config(explicit=config_path, start=start))
    return _build_and_cache(config=config)


def build_repo_in_process(*, config: Config) -> RepoIR:
    """Run the build using a pre-loaded ``Config``."""
    return _build_and_cache(config=config)


def _build_and_cache(*, config: Config) -> RepoIR:
    project_root = config.project_root
    piketype_root = config.frontend.piketype_root
    diagnostics: list[Diagnostic] = []

    skipped_underscore = find_skipped_underscore_modules(piketype_root)
    for path in skipped_underscore:
        diagnostics.append(
            Diagnostic(
                severity="info",
                code="underscore-skip",
                message=f"skipped {path.relative_to(project_root)} (leading underscore)",
            )
        )

    module_paths = find_piketype_modules(piketype_root)
    check_duplicate_basenames(module_paths=module_paths)

    with prepare_run(repo_root=project_root, module_paths=module_paths):
        loaded_modules = [
            build_loaded_module(
                module=load_or_get_module(module_path, repo_root=project_root),
                module_path=module_path,
                repo_root=project_root,
            )
            for module_path in module_paths
        ]
        definition_map = build_const_definition_map(loaded_modules=loaded_modules)
        type_definition_map = build_type_definition_map(loaded_modules=loaded_modules)
        vec_const_definition_map = build_vec_const_definition_map(loaded_modules=loaded_modules)

        frozen_modules: list[FrozenModule] = []
        for loaded_module in loaded_modules:
            frozen_modules.append(
                freeze_module(
                    loaded_module=loaded_module,
                    definition_map=definition_map,
                    type_definition_map=type_definition_map,
                    vec_const_definition_map=vec_const_definition_map,
                )
            )

        repo = freeze_repo(repo_root=project_root, frozen_modules=frozen_modules, tool_version=__version__)
        validate_repo(repo)

    for cycle in detect_module_cycles(repo):
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="module-cycle",
                message=f"module dependency cycle: {' -> '.join(cycle)}",
            )
        )

    write_cache(repo=repo, config=config)
    write_diagnostics(cache_root=config.frontend.ir_cache, diagnostics=diagnostics)

    if has_errors(diagnostics):
        raise PikeTypeError(
            f"build failed with errors; see {config.frontend.ir_cache / 'diagnostics.json'}"
        )

    return repo
