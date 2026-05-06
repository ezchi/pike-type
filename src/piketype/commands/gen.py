"""Generate command.

Backend-only stage. Reads IR from the cache (written by ``piketype build``)
and runs the configured language backends. This stage NEVER executes
user Python — its only inputs are JSON files plus the ``Config``.

A bare ``piketype gen`` runs the frontend build first (in-process) to
refresh the cache, then reads it and runs all enabled backends. The
``--lang`` flag restricts to a single backend. The legacy positional
path is accepted for back-compat: when given, it anchors the upward
config search and is checked for "must define DSL objects".
"""

from __future__ import annotations

from pathlib import Path

from piketype.backends.cpp.emitter import emit_cpp
from piketype.backends.py.emitter import emit_py
from piketype.backends.sv.emitter import emit_sv
from piketype.commands.build import build_repo_in_process
from piketype.config import Config, find_config, load_config
from piketype.discovery.scanner import ensure_cli_path_is_valid
from piketype.errors import ValidationError
from piketype.ir.nodes import RepoIR
from piketype.ir_io import read_cache
from piketype.manifest.write_json import write_manifest
from piketype.validate.namespace import validate_cpp_namespace


def run_gen(
    *,
    path: str | None = None,
    config_path: Path | None = None,
    namespace: str | None = None,
    lang: str | None = None,
) -> None:
    """Run generation orchestration.

    Either ``path`` (legacy) or ``config_path`` (preferred) anchors the
    config lookup. Both omitted → upward walk from CWD.
    """
    if namespace is not None:
        validate_cpp_namespace(namespace)

    cli_path: Path | None = None
    start: Path | None = None
    if path is not None:
        cli_path = Path(path).resolve()
        ensure_cli_path_is_valid(cli_path)
        start = cli_path.parent

    config = load_config(find_config(explicit=config_path, start=start))

    in_process_repo = build_repo_in_process(config=config)
    if cli_path is not None and not _cli_module_has_local_definitions(in_process_repo, cli_path=cli_path):
        raise ValidationError(f"{cli_path}: piketype file defines no DSL objects")

    repo = read_cache(config=config)
    _run_backends(repo, config=config, namespace=namespace, lang=lang)
    write_manifest(repo, config=config)


def _run_backends(repo: RepoIR, *, config: Config, namespace: str | None, lang: str | None) -> None:
    if lang is None or lang in {"sv", "sim"}:
        emit_sv(repo, config=config)
    if lang is None or lang == "py":
        emit_py(repo, config=config)
    if lang is None or lang == "cpp":
        emit_cpp(repo, config=config, namespace=namespace)


def _cli_module_has_local_definitions(repo: RepoIR, *, cli_path: Path) -> bool:
    """Return True if the module that matches ``cli_path`` defines any DSL objects."""
    cli_resolved = cli_path.resolve()
    for module in repo.modules:
        candidate = (Path(repo.repo_root) / module.ref.repo_relative_path).resolve()
        if candidate == cli_resolved:
            return bool(module.constants or module.types or module.vec_constants)
    return False
