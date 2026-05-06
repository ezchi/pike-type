"""SystemVerilog backend.

Renders synth and test packages via Jinja2 templates. The SV emitter
holds no semantic logic; all numeric primitives, MSB-first bit
positions, signed-padding decisions, and pack/unpack step structures
are computed by ``build_synth_module_view_sv`` and
``build_test_module_view_sv`` in ``view.py``, and the templates in
``templates/`` render structure and syntax (per-kind macros for
scalar_alias, struct, flags, enum — both synth typedef-pack-unpack
triplets and test verification helper classes).

The synth package is emitted under the ``sv`` backend; the test
verification package under the ``sim`` backend. Each is independent: a
config that omits one but declares the other will skip the omitted
output.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from piketype.backends.common.headers import render_header
from piketype.backends.common.render import make_environment, render
from piketype.backends.sv.view import build_synth_module_view_sv, build_test_module_view_sv
from piketype.config import Config
from piketype.ir.nodes import RepoIR
from piketype.ir.repo_index import build_repo_type_index
from piketype.paths import backend_output_path


def emit_sv(repo: RepoIR, *, config: Config) -> list[Path]:
    """Emit SystemVerilog synth and test package files for all modules."""
    written_paths: list[Path] = []
    sv_backend = config.get_backend("sv")
    sim_backend = config.get_backend("sim")
    if sv_backend is None and sim_backend is None:
        return written_paths

    project_root = config.project_root
    piketype_root = config.frontend.piketype_root
    repo_root = Path(repo.repo_root)
    env = make_environment(package="piketype.backends.sv")
    repo_type_index = build_repo_type_index(repo)
    for module in repo.modules:
        header = render_header(source_paths=(module.ref.repo_relative_path,))
        module_path = repo_root / module.ref.repo_relative_path
        if sv_backend is not None:
            synth_output_path = backend_output_path(
                backend=sv_backend,
                project_root=project_root,
                piketype_root=piketype_root,
                module_path=module_path,
                basename_suffix="_pkg",
                ext=".sv",
            )
            synth_output_path.parent.mkdir(parents=True, exist_ok=True)
            synth_view = replace(
                build_synth_module_view_sv(module=module, repo_type_index=repo_type_index),
                header=header,
            )
            synth_output_path.write_text(
                render(env=env, template_name="module_synth.j2", context=synth_view),
                encoding="utf-8",
            )
            written_paths.append(synth_output_path)
        if sim_backend is not None and module.types:
            test_output_path = backend_output_path(
                backend=sim_backend,
                project_root=project_root,
                piketype_root=piketype_root,
                module_path=module_path,
                basename_suffix="_test_pkg",
                ext=".sv",
            )
            test_output_path.parent.mkdir(parents=True, exist_ok=True)
            test_view = replace(
                build_test_module_view_sv(module=module, repo_type_index=repo_type_index),
                header=header,
            )
            test_output_path.write_text(
                render(env=env, template_name="module_test.j2", context=test_view),
                encoding="utf-8",
            )
            written_paths.append(test_output_path)
    return written_paths
