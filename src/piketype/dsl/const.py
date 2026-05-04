"""Constant DSL nodes and expression support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from piketype.dsl.base import DslNode
from piketype.dsl.source_info import SourceInfo, capture_source_info
from piketype.errors import ValidationError


def _literal_to_expr(value: int, *, source: SourceInfo) -> ConstExpr:
    """Wrap an integer literal as a constant expression."""
    return ConstExpr(kind="int_literal", source=source, value=value)


def _coerce_operand(value: ConstOperand, *, source: SourceInfo) -> ConstExpr:
    """Convert a supported operand to an expression node."""
    if isinstance(value, Const):
        return ConstExpr(kind="const_ref", source=source, target=value)
    if isinstance(value, VecConst):
        return ConstExpr(kind="const_ref", source=source, target=value)
    if isinstance(value, ConstExpr):
        return value
    if isinstance(value, int):
        return _literal_to_expr(value, source=source)
    raise ValidationError(f"unsupported Const operand type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class ConstExpr:
    """Runtime constant-expression node."""

    SUPPORTED_UNARY_OPS: ClassVar[set[str]] = {"+", "-", "~"}
    SUPPORTED_BINARY_OPS: ClassVar[set[str]] = {"+", "-", "*", "//", "%", "&", "|", "^", "<<", ">>"}

    kind: str
    source: SourceInfo
    value: int | None = None
    op: str | None = None
    lhs: ConstExpr | None = None
    rhs: ConstExpr | None = None
    operand: ConstExpr | None = None
    target: Const | None = None

    def __add__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("+", self, other)

    def __radd__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("+", other, self)

    def __sub__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("-", self, other)

    def __rsub__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("-", other, self)

    def __mul__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("*", self, other)

    def __rmul__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("*", other, self)

    def __floordiv__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("//", self, other)

    def __rfloordiv__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("//", other, self)

    def __truediv__(self, _other: ConstOperand) -> ConstExpr:
        raise ValidationError("Const() expressions support // only, not /")

    def __rtruediv__(self, _other: ConstOperand) -> ConstExpr:
        raise ValidationError("Const() expressions support // only, not /")

    def __mod__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("%", self, other)

    def __rmod__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("%", other, self)

    def __and__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("&", self, other)

    def __rand__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("&", other, self)

    def __or__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("|", self, other)

    def __ror__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("|", other, self)

    def __xor__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("^", self, other)

    def __rxor__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("^", other, self)

    def __lshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("<<", self, other)

    def __rlshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("<<", other, self)

    def __rshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr(">>", self, other)

    def __rrshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr(">>", other, self)

    def __neg__(self) -> ConstExpr:
        return _unary_expr("-", self)

    def __pos__(self) -> ConstExpr:
        return _unary_expr("+", self)

    def __invert__(self) -> ConstExpr:
        return _unary_expr("~", self)


@dataclass(slots=True)
class Const(DslNode):
    """Top-level integer constant."""

    value: int
    signed: bool | None
    width: int | None
    expr: ConstExpr

    def __init__(self, value: int | ConstExpr, *, signed: bool | None = None, width: int | None = None) -> None:
        if signed is not None and not isinstance(signed, bool):
            raise ValidationError(f"Const() signed= must be bool or None, got {type(signed).__name__}")
        if width is not None and width not in (32, 64):
            raise ValidationError(f"Const() width= must be 32, 64, or None, got {width}")
        source = capture_source_info()
        expr = _coerce_operand(value, source=source)
        resolved_value = _eval_expr(expr)
        DslNode.__init__(self, source=source)
        self.value = resolved_value
        self.signed = signed
        self.width = width
        self.expr = expr

    def __add__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("+", self, other)

    def __radd__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("+", other, self)

    def __sub__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("-", self, other)

    def __rsub__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("-", other, self)

    def __mul__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("*", self, other)

    def __rmul__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("*", other, self)

    def __floordiv__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("//", self, other)

    def __rfloordiv__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("//", other, self)

    def __truediv__(self, _other: ConstOperand) -> ConstExpr:
        raise ValidationError("Const() expressions support // only, not /")

    def __rtruediv__(self, _other: ConstOperand) -> ConstExpr:
        raise ValidationError("Const() expressions support // only, not /")

    def __mod__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("%", self, other)

    def __rmod__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("%", other, self)

    def __and__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("&", self, other)

    def __rand__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("&", other, self)

    def __or__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("|", self, other)

    def __ror__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("|", other, self)

    def __xor__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("^", self, other)

    def __rxor__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("^", other, self)

    def __lshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("<<", self, other)

    def __rlshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("<<", other, self)

    def __rshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr(">>", self, other)

    def __rrshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr(">>", other, self)

    def __neg__(self) -> ConstExpr:
        return _unary_expr("-", self)

    def __pos__(self) -> ConstExpr:
        return _unary_expr("+", self)

    def __invert__(self) -> ConstExpr:
        return _unary_expr("~", self)


type ConstOperand = Const | VecConst | ConstExpr | int


@dataclass(slots=True)
class VecConst(DslNode):
    """Fixed-width logic vector constant.

    Eagerly resolves `width` and `value` at construction time (mirroring
    `Const`), validates against width range (1..64) and overflow
    (0 <= value <= 2**width - 1), and exposes `.value` so the instance
    can serve as a `ConstOperand` in other constant expressions.
    """

    SUPPORTED_BASES: ClassVar[set[str]] = {"hex", "dec", "bin"}

    width: int        # resolved eagerly
    value: int        # resolved eagerly (overflow-checked)
    base: str
    width_expr: ConstExpr
    value_expr: ConstExpr

    def __init__(
        self,
        width: ConstOperand,
        value: ConstOperand,
        *,
        base: str = "dec",
    ) -> None:
        if base not in VecConst.SUPPORTED_BASES:
            raise ValidationError(
                f"VecConst() base= must be one of {sorted(VecConst.SUPPORTED_BASES)}, got {base!r}"
            )
        source = capture_source_info()
        DslNode.__init__(self, source=source)
        width_expr = _coerce_operand(width, source=source)
        value_expr = _coerce_operand(value, source=source)
        resolved_width = _eval_expr(width_expr)
        resolved_value = _eval_expr(value_expr)
        if resolved_width < 1 or resolved_width > 64:
            raise ValidationError(
                f"VecConst() width {resolved_width} out of supported range 1..64"
            )
        if resolved_value < 0:
            raise ValidationError(
                f"VecConst(width={resolved_width}, value={resolved_value}) negative value rejected; "
                f"value must satisfy 0 <= value <= 2**{resolved_width} - 1 (= {2**resolved_width - 1})"
            )
        if resolved_value > 2**resolved_width - 1:
            raise ValidationError(
                f"VecConst(width={resolved_width}, value={resolved_value}) overflows; "
                f"value must satisfy 0 <= value <= 2**{resolved_width} - 1 (= {2**resolved_width - 1})"
            )
        self.width = resolved_width
        self.value = resolved_value
        self.base = base
        self.width_expr = width_expr
        self.value_expr = value_expr

    def __add__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("+", self, other)

    def __radd__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("+", other, self)

    def __sub__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("-", self, other)

    def __rsub__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("-", other, self)

    def __mul__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("*", self, other)

    def __rmul__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("*", other, self)

    def __floordiv__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("//", self, other)

    def __rfloordiv__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("//", other, self)

    def __mod__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("%", self, other)

    def __rmod__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("%", other, self)

    def __and__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("&", self, other)

    def __rand__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("&", other, self)

    def __or__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("|", self, other)

    def __ror__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("|", other, self)

    def __xor__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("^", self, other)

    def __rxor__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("^", other, self)

    def __lshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("<<", self, other)

    def __rlshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr("<<", other, self)

    def __rshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr(">>", self, other)

    def __rrshift__(self, other: ConstOperand) -> ConstExpr:
        return _binary_expr(">>", other, self)

    def __neg__(self) -> ConstExpr:
        return _unary_expr("-", self)

    def __pos__(self) -> ConstExpr:
        return _unary_expr("+", self)

    def __invert__(self) -> ConstExpr:
        return _unary_expr("~", self)


def _binary_expr(op: str, lhs: ConstOperand, rhs: ConstOperand) -> ConstExpr:
    """Create a binary constant-expression node."""
    if op not in ConstExpr.SUPPORTED_BINARY_OPS:
        raise ValidationError(f"unsupported Const binary operator {op}")
    source = capture_source_info()
    return ConstExpr(
        kind="binary_op",
        source=source,
        op=op,
        lhs=_coerce_operand(lhs, source=source),
        rhs=_coerce_operand(rhs, source=source),
    )


def _unary_expr(op: str, operand: ConstOperand) -> ConstExpr:
    """Create a unary constant-expression node."""
    if op not in ConstExpr.SUPPORTED_UNARY_OPS:
        raise ValidationError(f"unsupported Const unary operator {op}")
    source = capture_source_info()
    return ConstExpr(
        kind="unary_op",
        source=source,
        op=op,
        operand=_coerce_operand(operand, source=source),
    )


def _eval_expr(expr: ConstExpr) -> int:
    """Evaluate a runtime constant expression."""
    match expr.kind:
        case "int_literal":
            if expr.value is None:
                raise ValidationError("malformed literal expression")
            return expr.value
        case "const_ref":
            if expr.target is None:
                raise ValidationError("malformed const reference expression")
            return expr.target.value
        case "unary_op":
            if expr.op is None or expr.operand is None:
                raise ValidationError("malformed unary expression")
            value = _eval_expr(expr.operand)
            match expr.op:
                case "+":
                    return +value
                case "-":
                    return -value
                case "~":
                    return ~value
                case _:
                    raise ValidationError(f"unsupported unary operator {expr.op}")
        case "binary_op":
            if expr.op is None or expr.lhs is None or expr.rhs is None:
                raise ValidationError("malformed binary expression")
            lhs = _eval_expr(expr.lhs)
            rhs = _eval_expr(expr.rhs)
            match expr.op:
                case "+":
                    return lhs + rhs
                case "-":
                    return lhs - rhs
                case "*":
                    return lhs * rhs
                case "//":
                    return lhs // rhs
                case "%":
                    return lhs % rhs
                case "&":
                    return lhs & rhs
                case "|":
                    return lhs | rhs
                case "^":
                    return lhs ^ rhs
                case "<<":
                    return lhs << rhs
                case ">>":
                    return lhs >> rhs
                case _:
                    raise ValidationError(f"unsupported binary operator {expr.op}")
        case _:
            raise ValidationError(f"unsupported Const expression kind {expr.kind}")
