"""SystemVerilog backend.

Renders synth and test packages via Jinja2 templates. The SV emitter
holds no semantic logic; all numeric primitives, MSB-first bit
positions, signed-padding decisions, and pack/unpack step structures
are computed by ``build_synth_module_view_sv`` and
``build_test_module_view_sv`` in ``view.py``, and the templates in
``templates/`` render structure and syntax (per-kind macros for
scalar_alias, struct, flags, enum — both synth typedef-pack-unpack
triplets and test verification helper classes).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from piketype.backends.common.headers import render_header
from piketype.backends.common.render import make_environment, render
from piketype.backends.sv.view import build_synth_module_view_sv, build_test_module_view_sv
from piketype.ir.nodes import RepoIR
from piketype.paths import sv_module_output_path, sv_test_module_output_path


def emit_sv(repo: RepoIR) -> list[Path]:
    """Emit SystemVerilog synth and test package files for all modules."""
    written_paths: list[Path] = []
    repo_root = Path(repo.repo_root)
    env = make_environment(package="piketype.backends.sv")
    for module in repo.modules:
        header = render_header(source_paths=(module.ref.repo_relative_path,))
        synth_output_path = sv_module_output_path(
            repo_root=repo_root,
            module_path=repo_root / module.ref.repo_relative_path,
        )
        synth_output_path.parent.mkdir(parents=True, exist_ok=True)
        synth_view = replace(build_synth_module_view_sv(module=module), header=header)
        synth_output_path.write_text(
            render(env=env, template_name="module_synth.j2", context=synth_view),
            encoding="utf-8",
        )
        written_paths.append(synth_output_path)
        if module.types:
            test_output_path = sv_test_module_output_path(
                repo_root=repo_root,
                module_path=repo_root / module.ref.repo_relative_path,
            )
            test_output_path.parent.mkdir(parents=True, exist_ok=True)
            test_view = replace(build_test_module_view_sv(module=module), header=header)
            test_output_path.write_text(
                render(env=env, template_name="module_test.j2", context=test_view),
                encoding="utf-8",
            )
            written_paths.append(test_output_path)
    return written_paths
