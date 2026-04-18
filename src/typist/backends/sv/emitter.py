"""SystemVerilog backend."""

from __future__ import annotations

from pathlib import Path

from typist.backends.common.headers import render_header
from typist.ir.nodes import ModuleIR, RepoIR
from typist.paths import sv_module_output_path


def emit_sv(repo: RepoIR) -> list[Path]:
    """Emit SystemVerilog package files for all modules."""
    written_paths: list[Path] = []
    repo_root = Path(repo.repo_root)
    for module in repo.modules:
        output_path = sv_module_output_path(
            repo_root=repo_root,
            module_path=repo_root / module.ref.repo_relative_path,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_module_sv(module), encoding="utf-8")
        written_paths.append(output_path)
    return written_paths


def render_module_sv(module: ModuleIR) -> str:
    """Render a constant-only SystemVerilog package."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    body_lines = [f"package {module.ref.basename}_pkg;"]
    for const in module.constants:
        body_lines.append(f"  localparam int {const.name} = {const.resolved_value};")
    body_lines.append("endpackage")
    return f"{header}\n" + "\n".join(body_lines) + "\n"
