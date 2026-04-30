"""View-model dataclasses and builders for the C++ backend.

Implements FR-1, FR-8, FR-9, FR-18 of spec 010-jinja-template-migration.

**Compromise note (T-14..T-19):** the per-type body rendering for
C++ is substantially larger than Python's (1067 line legacy emitter
vs. 792). To avoid an over-long single-iteration migration, this
phase keeps the legacy ``_render_cpp_*`` helpers in
``backends.cpp.emitter`` and calls them from the view-model
builders to produce a precomputed ``body_text: str`` per type. The
primary template (``module.j2``) owns module-level structure
(header, include guard, includes, namespace, type loop) and emits
each type's body via ``{{ t.body_text }}``. A follow-up may convert
each type kind to a dedicated Jinja macro (matching the Python
backend's pattern). Until then this view-model is FR-8/FR-9
compliant (primitives + primitive tuples + nested view-model
dataclasses) and the template is the single audit site for module
structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from piketype.ir.nodes import (
    BinaryExprIR,
    ConstIR,
    ConstRefExprIR,
    EnumIR,
    ExprIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    ScalarAliasIR,
    StructIR,
    UnaryExprIR,
)


@dataclass(frozen=True, slots=True)
class CppGuardView:
    macro: str  # exact include-guard symbol


@dataclass(frozen=True, slots=True)
class CppNamespaceView:
    qualified: str  # "" if no namespace
    has_namespace: bool
    open_line: str  # "" if no namespace
    close_line: str  # "" if no namespace


@dataclass(frozen=True, slots=True)
class CppConstantView:
    cpp_type: str
    name: str
    value_expr: str  # pre-rendered C++ literal or expression


@dataclass(frozen=True, slots=True)
class CppTypeView:
    """One generated type. ``body_text`` is the legacy-rendered body
    (FR-19 compromise; see module docstring)."""

    kind: str  # "scalar_alias" | "struct" | "enum" | "flags"
    name: str
    body_text: str


@dataclass(frozen=True, slots=True)
class CppModuleView:
    header: str
    guard: CppGuardView
    namespace: CppNamespaceView
    has_types: bool
    standard_includes: tuple[str, ...]  # declaration order — NOT alphabetized
    constants: tuple[CppConstantView, ...]
    types: tuple[CppTypeView, ...]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_cpp_expr(expr: ExprIR) -> str:
    match expr:
        case IntLiteralExprIR(value=value):
            return str(value)
        case ConstRefExprIR(name=name):
            return name
        case UnaryExprIR(op=op, operand=operand):
            return f"({op}{_render_cpp_expr(operand)})"
        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
            return f"({_render_cpp_expr(lhs)} {op} {_render_cpp_expr(rhs)})"
        case _:
            raise ValueError(f"unsupported C++ expression node {type(expr).__name__}")


def _build_guard_view(*, module: ModuleIR, namespace: str | None) -> CppGuardView:
    if namespace is not None:
        macro = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
    else:
        macro = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
    return CppGuardView(macro=macro)


def _build_namespace_view(*, module: ModuleIR, namespace: str | None) -> CppNamespaceView:
    if namespace is not None:
        qualified = f"{namespace}::{module.ref.basename}"
    else:
        qualified = "::".join(p for p in module.ref.namespace_parts if p != "piketype")
    if not qualified:
        return CppNamespaceView(qualified="", has_namespace=False, open_line="", close_line="")
    return CppNamespaceView(
        qualified=qualified,
        has_namespace=True,
        open_line=f"namespace {qualified} {{",
        close_line=f"}}  // namespace {qualified}",
    )


def _standard_includes(*, has_types: bool) -> tuple[str, ...]:
    """Declaration-order include list — NOT alphabetized (matches legacy emitter)."""
    base = ("<cstdint>",)
    if has_types:
        return base + ("<cstddef>", "<stdexcept>", "<vector>")
    return base


def _build_constant_view(*, const_ir: ConstIR) -> CppConstantView:
    # Lazy import to avoid circular dep with emitter.
    from piketype.backends.cpp.emitter import _render_cpp_const

    cpp_type, cpp_literal = _render_cpp_const(
        value=const_ir.resolved_value,
        signed=const_ir.resolved_signed,
        width=const_ir.resolved_width,
    )
    if isinstance(const_ir.expr, IntLiteralExprIR):
        value_expr = cpp_literal
    else:
        value_expr = _render_cpp_expr(const_ir.expr)
    return CppConstantView(cpp_type=cpp_type, name=const_ir.name, value_expr=value_expr)


def _build_type_view(*, type_ir, type_index) -> CppTypeView:  # type: ignore[no-untyped-def]
    """Render the type's body via legacy helpers and wrap as a CppTypeView."""
    from piketype.backends.cpp.emitter import (
        _render_cpp_enum,
        _render_cpp_flags,
        _render_cpp_scalar_alias,
        _render_cpp_struct,
    )

    if isinstance(type_ir, ScalarAliasIR):
        return CppTypeView(
            kind="scalar_alias",
            name=type_ir.name,
            body_text="\n".join(_render_cpp_scalar_alias(type_ir=type_ir)),
        )
    if isinstance(type_ir, StructIR):
        return CppTypeView(
            kind="struct",
            name=type_ir.name,
            body_text="\n".join(_render_cpp_struct(type_ir=type_ir, type_index=type_index)),
        )
    if isinstance(type_ir, FlagsIR):
        return CppTypeView(
            kind="flags",
            name=type_ir.name,
            body_text="\n".join(_render_cpp_flags(type_ir=type_ir)),
        )
    if isinstance(type_ir, EnumIR):
        return CppTypeView(
            kind="enum",
            name=type_ir.name,
            body_text="\n".join(_render_cpp_enum(type_ir=type_ir)),
        )
    raise ValueError(f"unsupported C++ type IR {type(type_ir).__name__}")


def build_module_view_cpp(*, module: ModuleIR, namespace: str | None = None) -> CppModuleView:
    """Build the C++ module view model."""
    type_index = {t.name: t for t in module.types}
    has_types = bool(module.types)
    return CppModuleView(
        header="",  # caller supplies header via emit_cpp
        guard=_build_guard_view(module=module, namespace=namespace),
        namespace=_build_namespace_view(module=module, namespace=namespace),
        has_types=has_types,
        standard_includes=_standard_includes(has_types=has_types),
        constants=tuple(build_constant_view_for_emit(c) for c in module.constants),
        types=tuple(_build_type_view(type_ir=t, type_index=type_index) for t in module.types),
    )


def build_constant_view_for_emit(const_ir: ConstIR) -> CppConstantView:
    """Public alias used both by build_module_view_cpp and tests."""
    return _build_constant_view(const_ir=const_ir)
