"""Scalar DSL nodes."""

from __future__ import annotations

from dataclasses import dataclass

from typist.dsl.base import DslNode
from typist.dsl.const import Const, ConstExpr, _coerce_operand, _eval_expr
from typist.dsl.source_info import SourceInfo, capture_source_info
from typist.errors import ValidationError


@dataclass(slots=True)
class ScalarType(DslNode):
    """Named or inline scalar type definition."""

    state_kind: str
    width_value: int
    width_expr: ConstExpr
    signed: bool

    def __init__(
        self,
        state_kind: str,
        width: int | Const | ConstExpr,
        *,
        signed: bool = False,
        source: SourceInfo | None = None,
    ) -> None:
        if state_kind not in {"bit", "logic"}:
            raise ValidationError(f"unsupported scalar state kind {state_kind}")
        if not isinstance(signed, bool):
            raise ValidationError(f"scalar signed= must be bool, got {type(signed).__name__}")
        resolved_source = capture_source_info() if source is None else source
        width_expr = _coerce_operand(width, source=resolved_source)
        width_value = _eval_expr(width_expr)
        if width_value <= 0:
            raise ValidationError(f"scalar width must be positive, got {width_value}")
        DslNode.__init__(self, source=resolved_source)
        self.state_kind = state_kind
        self.width_value = width_value
        self.width_expr = width_expr
        self.signed = signed


def Bit(width: int | Const | ConstExpr, *, signed: bool = False) -> ScalarType:
    """Create a 2-state scalar type."""
    return ScalarType("bit", width, signed=signed, source=capture_source_info())


def Logic(width: int | Const | ConstExpr, *, signed: bool = False) -> ScalarType:
    """Create a 4-state scalar type."""
    return ScalarType("logic", width, signed=signed, source=capture_source_info())
