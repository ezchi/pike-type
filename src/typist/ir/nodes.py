"""Frozen IR node definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpanIR:
    """Source location in frozen IR."""

    path: str
    line: int
    column: int | None


@dataclass(frozen=True, slots=True)
class ModuleRefIR:
    """Stable identity for a DSL module."""

    repo_relative_path: str
    python_module_name: str
    namespace_parts: tuple[str, ...]
    basename: str


@dataclass(frozen=True, slots=True)
class IntLiteralExprIR:
    """Literal integer expression."""

    value: int
    source: SourceSpanIR


@dataclass(frozen=True, slots=True)
class ConstIR:
    """Frozen constant definition."""

    name: str
    source: SourceSpanIR
    expr: IntLiteralExprIR
    resolved_value: int


@dataclass(frozen=True, slots=True)
class ModuleDependencyIR:
    """Module dependency entry."""

    target: ModuleRefIR
    kind: str


@dataclass(frozen=True, slots=True)
class ModuleIR:
    """Frozen module node."""

    ref: ModuleRefIR
    source: SourceSpanIR
    constants: tuple[ConstIR, ...]
    types: tuple[object, ...]
    dependencies: tuple[ModuleDependencyIR, ...]


@dataclass(frozen=True, slots=True)
class RepoIR:
    """Frozen repository IR root."""

    repo_root: str
    modules: tuple[ModuleIR, ...]
    tool_version: str | None
