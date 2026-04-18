"""C++ backend placeholders."""

from __future__ import annotations

from typist.ir.nodes import RepoIR


def emit_cpp(_repo: RepoIR) -> None:
    """Emit C++ outputs."""
