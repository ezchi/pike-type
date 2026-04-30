"""View-model dataclasses and builders for the SystemVerilog backend.

Implements FR-1, FR-8, FR-9, FR-18 of spec 010-jinja-template-migration.

**Compromise note:** matches the C++ backend's pragmatic compromise.
SV rendering is the largest and most complex of the three backends
(949 line legacy emitter, with ~10 helpers across synth-package and
test-package outputs). To avoid an over-long single-iteration
migration, this phase keeps the legacy ``_render_sv_*`` helpers in
``backends.sv.emitter`` and calls them from the view-model builders
to produce a precomputed ``body_text: str`` per type. The two
primary templates (``module_synth.j2`` and ``module_test.j2``) own
package-level structure (header, package open/close, constants,
type loop, optional import). Per-type kind macros are left as a
follow-up.
"""

from __future__ import annotations

from dataclasses import dataclass

from piketype.ir.nodes import (
    BinaryExprIR,
    ConstIR,
    ConstRefExprIR,
    ExprIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    ScalarAliasIR,
    StructIR,
    TypeDefIR,
    UnaryExprIR,
)


@dataclass(frozen=True, slots=True)
class SvConstantView:
    sv_type: str  # e.g. "int signed", "logic [31:0]", "longint unsigned"
    name: str
    sv_expr: str  # pre-rendered SV literal or expression


@dataclass(frozen=True, slots=True)
class SvSynthTypeView:
    """One synth-package type block (localparams + typedef + pack/unpack)."""

    name: str
    body_text: str  # already indented (2 spaces) per legacy emitter contract


@dataclass(frozen=True, slots=True)
class SvTestTypeView:
    """One test-package helper class block."""

    name: str
    body_text: str  # already indented (2 spaces) per legacy emitter contract


@dataclass(frozen=True, slots=True)
class SvSynthModuleView:
    header: str
    package_name: str  # f"{basename}_pkg"
    has_constants: bool
    has_types: bool
    constants: tuple[SvConstantView, ...]
    types: tuple[SvSynthTypeView, ...]


@dataclass(frozen=True, slots=True)
class SvTestModuleView:
    header: str
    package_name: str  # f"{basename}_test_pkg"
    synth_package_import: str  # f"  import {basename}_pkg::*;"
    types: tuple[SvTestTypeView, ...]


def _render_sv_expr(expr: ExprIR) -> str:
    match expr:
        case IntLiteralExprIR(value=value):
            return str(value)
        case ConstRefExprIR(name=name):
            return name
        case UnaryExprIR(op=op, operand=operand):
            return f"({op}{_render_sv_expr(operand)})"
        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
            return f"({_render_sv_expr(lhs)} {op} {_render_sv_expr(rhs)})"


def _build_constant_view(*, const_ir: ConstIR) -> SvConstantView:
    from piketype.backends.sv import emitter as _legacy

    sv_type, sv_literal = _legacy._render_sv_const(  # pyright: ignore[reportPrivateUsage]
        value=const_ir.resolved_value,
        signed=const_ir.resolved_signed,
        width=const_ir.resolved_width,
    )
    sv_expr = sv_literal if isinstance(const_ir.expr, IntLiteralExprIR) else _render_sv_expr(const_ir.expr)
    return SvConstantView(sv_type=sv_type, name=const_ir.name, sv_expr=sv_expr)


def _build_synth_type_view(
    *, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]
) -> SvSynthTypeView:
    from piketype.backends.sv import emitter as _legacy

    lines = _legacy._render_sv_type_block(type_ir=type_ir, type_index=type_index)  # pyright: ignore[reportPrivateUsage]
    return SvSynthTypeView(name=type_ir.name, body_text="\n".join(lines))


def _build_test_type_view(
    *, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]
) -> SvTestTypeView:
    from piketype.backends.sv import emitter as _legacy

    if isinstance(type_ir, ScalarAliasIR):
        lines = _legacy._render_sv_scalar_helper_class(type_ir=type_ir)  # pyright: ignore[reportPrivateUsage]
    elif isinstance(type_ir, StructIR):
        lines = _legacy._render_sv_struct_helper_class(type_ir=type_ir, type_index=type_index)  # pyright: ignore[reportPrivateUsage]
    elif isinstance(type_ir, FlagsIR):
        lines = _legacy._render_sv_flags_helper_class(type_ir=type_ir)  # pyright: ignore[reportPrivateUsage]
    else:
        lines = _legacy._render_sv_enum_helper_class(type_ir=type_ir)  # pyright: ignore[reportPrivateUsage]
    indented = [f"  {line}" for line in lines]
    return SvTestTypeView(name=type_ir.name, body_text="\n".join(indented))


def build_synth_module_view_sv(*, module: ModuleIR) -> SvSynthModuleView:
    type_index = {t.name: t for t in module.types}
    constants = tuple(_build_constant_view(const_ir=c) for c in module.constants)
    types = tuple(_build_synth_type_view(type_ir=t, type_index=type_index) for t in module.types)
    return SvSynthModuleView(
        header="",  # caller supplies header
        package_name=f"{module.ref.basename}_pkg",
        has_constants=bool(constants),
        has_types=bool(types),
        constants=constants,
        types=types,
    )


def build_test_module_view_sv(*, module: ModuleIR) -> SvTestModuleView:
    type_index = {t.name: t for t in module.types}
    types = tuple(_build_test_type_view(type_ir=t, type_index=type_index) for t in module.types)
    return SvTestModuleView(
        header="",
        package_name=f"{module.ref.basename}_test_pkg",
        synth_package_import=f"  import {module.ref.basename}_pkg::*;",
        types=types,
    )
