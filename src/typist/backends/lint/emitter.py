"""Lint backend placeholders."""

from __future__ import annotations

from typist.ir.nodes import RepoIR


def emit_lint(_repo: RepoIR) -> None:
    """Emit lint scaffolding."""
