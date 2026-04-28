"""Frozen IR node definitions."""

from __future__ import annotations

from dataclasses import dataclass


def byte_count(width: int) -> int:
    """Number of bytes needed to hold ``width`` data bits."""
    return (width + 7) // 8


def padding_bits(width: int) -> int:
    """Number of MSB padding bits to reach the next byte boundary."""
    return (-width) % 8


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
class ConstRefExprIR:
    """Reference to a named constant."""

    module: ModuleRefIR
    name: str
    source: SourceSpanIR


@dataclass(frozen=True, slots=True)
class UnaryExprIR:
    """Unary expression."""

    op: str
    operand: ExprIR
    source: SourceSpanIR


@dataclass(frozen=True, slots=True)
class BinaryExprIR:
    """Binary expression."""

    op: str
    lhs: ExprIR
    rhs: ExprIR
    source: SourceSpanIR


type ExprIR = IntLiteralExprIR | ConstRefExprIR | UnaryExprIR | BinaryExprIR


@dataclass(frozen=True, slots=True)
class ScalarAliasIR:
    """Frozen named scalar alias definition."""

    name: str
    source: SourceSpanIR
    state_kind: str
    signed: bool
    width_expr: ExprIR
    resolved_width: int


@dataclass(frozen=True, slots=True)
class ScalarTypeSpecIR:
    """Inline scalar type specification."""

    source: SourceSpanIR
    state_kind: str
    signed: bool
    width_expr: ExprIR
    resolved_width: int


@dataclass(frozen=True, slots=True)
class TypeRefIR:
    """Reference to another named type."""

    module: ModuleRefIR
    name: str
    source: SourceSpanIR


type FieldTypeIR = ScalarTypeSpecIR | TypeRefIR


@dataclass(frozen=True, slots=True)
class StructFieldIR:
    """Frozen packed struct field."""

    name: str
    source: SourceSpanIR
    type_ir: FieldTypeIR
    rand: bool
    padding_bits: int = 0


@dataclass(frozen=True, slots=True)
class StructIR:
    """Frozen packed struct definition."""

    name: str
    source: SourceSpanIR
    fields: tuple[StructFieldIR, ...]
    alignment_bits: int = 0


@dataclass(frozen=True, slots=True)
class FlagFieldIR:
    """Frozen single-bit flag field."""

    name: str
    source: SourceSpanIR


@dataclass(frozen=True, slots=True)
class FlagsIR:
    """Frozen packed flags definition."""

    name: str
    source: SourceSpanIR
    fields: tuple[FlagFieldIR, ...]
    alignment_bits: int = 0


type TypeDefIR = ScalarAliasIR | StructIR | FlagsIR


@dataclass(frozen=True, slots=True)
class ConstIR:
    """Frozen constant definition."""

    name: str
    source: SourceSpanIR
    expr: ExprIR
    resolved_value: int
    resolved_signed: bool
    resolved_width: int


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
    types: tuple[TypeDefIR, ...]
    dependencies: tuple[ModuleDependencyIR, ...]


@dataclass(frozen=True, slots=True)
class RepoIR:
    """Frozen repository IR root."""

    repo_root: str
    modules: tuple[ModuleIR, ...]
    tool_version: str | None
