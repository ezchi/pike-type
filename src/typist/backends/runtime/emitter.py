"""Runtime backend."""

from __future__ import annotations

from pathlib import Path

from typist.backends.common.headers import render_header
from typist.ir.nodes import RepoIR
from typist.paths import sv_runtime_output_path


def emit_runtime(repo: RepoIR) -> list[Path]:
    """Emit shared runtime outputs."""
    repo_root = Path(repo.repo_root)
    output_path = sv_runtime_output_path(repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_runtime_sv(), encoding="utf-8")
    return [output_path]


def render_runtime_sv() -> str:
    """Render the milestone-01 runtime placeholder package."""
    header = render_header(source_paths=("<runtime>",))
    return f"{header}\npackage typist_runtime_pkg;\nendpackage\n"
