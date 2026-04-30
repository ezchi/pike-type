"""C++ backend.

Renders C++ headers via Jinja2 templates. The C++ emitter holds no
semantic logic; all numeric primitives, literal forms, and type-kind
discriminators are computed by ``build_module_view_cpp`` in
``view.py``, and the templates in ``templates/`` render structure
and syntax (per-type macros for scalar_alias, enum, flags, struct).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from piketype.backends.common.headers import render_header
from piketype.backends.common.render import make_environment, render
from piketype.backends.cpp.view import build_module_view_cpp
from piketype.ir.nodes import RepoIR
from piketype.paths import cpp_header_output_path


def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
    """Emit C++ outputs."""
    written_paths: list[Path] = []
    repo_root = Path(repo.repo_root)
    env = make_environment(package="piketype.backends.cpp")
    for module in repo.modules:
        output_path = cpp_header_output_path(
            repo_root=repo_root,
            module_path=repo_root / module.ref.repo_relative_path,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        header = render_header(source_paths=(module.ref.repo_relative_path,))
        view = build_module_view_cpp(module=module, namespace=namespace)
        view = replace(view, header=header)
        output_path.write_text(
            render(env=env, template_name="module.j2", context=view),
            encoding="utf-8",
        )
        written_paths.append(output_path)
    return written_paths
