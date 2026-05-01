"""View-model dataclasses and builders for the SystemVerilog backend.

Implements FR-1, FR-8, FR-9, FR-18 of spec 010-jinja-template-migration.
This module provides per-kind frozen dataclasses for both the synth
package (typedefs + pack/unpack functions) and the test package
(verification helper classes). All numeric primitives, bit-shift
positions, and width-derived values are precomputed in pure Python;
templates render structure and syntax via dedicated Jinja macros.
"""

from __future__ import annotations

from dataclasses import dataclass

from piketype.ir.nodes import (
    BinaryExprIR,
    ConstIR,
    ConstRefExprIR,
    EnumIR,
    EnumValueIR,
    ExprIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    StructFieldIR,
    StructIR,
    TypeDefIR,
    TypeRefIR,
    UnaryExprIR,
    byte_count,
)


# ---------------------------------------------------------------------------
# Module-level views
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SvConstantView:
    sv_type: str
    name: str
    sv_expr: str


# ---------------------------------------------------------------------------
# Synth package — per-kind type views
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SvScalarAliasView:
    kind: str  # "scalar_alias"
    name: str
    base: str  # _type_base_name (strip _t)
    upper_base: str
    base_type: str  # state_kind: "logic" / "bit"
    width: int
    width_expr: str  # _render_sv_expr(width_expr) — used in localparam
    byte_count: int
    signed: bool
    is_one_bit: bool  # width == 1 — affects bracket syntax in typedef


@dataclass(frozen=True, slots=True)
class SvSynthStructFieldView:
    """One field in a packed struct typedef."""
    name: str
    field_type_text: str  # _render_sv_struct_field_type result, e.g. "logic signed [4:0]" or "foo_t"
    has_pre_padding: bool  # field.padding_bits > 0
    pre_padding_bits: int
    is_pre_padding_one_bit: bool


@dataclass(frozen=True, slots=True)
class SvSynthStructView:
    kind: str  # "struct"
    name: str
    base: str
    upper_base: str
    width: int
    byte_count: int
    alignment_bits: int
    has_alignment: bool
    is_alignment_one_bit: bool
    fields: tuple[SvSynthStructFieldView, ...]


@dataclass(frozen=True, slots=True)
class SvSynthFlagsView:
    kind: str  # "flags"
    name: str
    base: str
    upper_base: str
    width: int  # = num_flags
    byte_count: int
    alignment_bits: int
    has_alignment: bool
    is_alignment_one_bit: bool
    field_names: tuple[str, ...]
    # Reverse-iteration assignments for unpack: (flag_name, bit_index)
    unpack_bit_assignments: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class SvSynthEnumMemberView:
    name: str
    value_expr: str  # str(resolved_value)


@dataclass(frozen=True, slots=True)
class SvSynthEnumView:
    kind: str  # "enum"
    name: str
    base: str
    upper_base: str
    width: int
    byte_count: int
    is_one_bit: bool
    members: tuple[SvSynthEnumMemberView, ...]


@dataclass(frozen=True, slots=True)
class SvSynthStructPackPartView:
    """One element of a pack_<base> concat expression for a struct."""
    expr: str  # "pack_<inner>(a.<field>)" or "a.<field>"


@dataclass(frozen=True, slots=True)
class SvSynthStructUnpackFieldView:
    """One field of a struct unpack body (in reversed declaration order)."""
    name: str
    width: int  # data width
    is_type_ref: bool
    inner_base: str  # for type ref
    inner_upper: str
    has_signed_padding: bool  # padding_bits > 0 and signed
    padding_bits: int
    sign_bit_index: int  # width - 1


@dataclass(frozen=True, slots=True)
class SvSynthStructPackUnpackView:
    """Pack/unpack data attached to a struct view (driven by its declaration order)."""
    pack_parts: tuple[SvSynthStructPackPartView, ...]  # declaration order
    unpack_fields: tuple[SvSynthStructUnpackFieldView, ...]  # REVERSED declaration order


type SvSynthTypeView = (
    SvScalarAliasView | SvSynthStructView | SvSynthFlagsView | SvSynthEnumView
)


@dataclass(frozen=True, slots=True)
class SvSynthModuleView:
    header: str
    package_name: str
    has_constants: bool
    has_types: bool
    constants: tuple[SvConstantView, ...]
    types: tuple[SvSynthTypeView, ...]
    # Pack/unpack data parallel to types[]; only populated for struct kind.
    pack_unpack: tuple[SvSynthStructPackUnpackView | None, ...]
    # Explicit per-symbol cross-module imports. Each entry is (pkg_name, symbol_name);
    # template renders `import {pkg}::{sym};`. Sorted by (pkg, sym).
    synth_cross_module_imports: tuple[tuple[str, str], ...]


# ---------------------------------------------------------------------------
# Test package — per-kind helper class views
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SvTestScalarHelperView:
    kind: str  # "scalar_alias"
    helper_class_name: str  # _helper_class_name (e.g. "addr_helper")
    underlying_typedef: str  # type_ir.name (e.g. "addr_t")
    upper_base: str
    width: int
    byte_count: int
    total_bits: int  # bc * 8
    pad_bits: int  # (-width) % 8
    signed: bool
    has_signed_padding: bool  # pad_bits > 0 and signed


@dataclass(frozen=True, slots=True)
class SvTestStructFieldDeclView:
    """One struct helper-class field declaration."""
    name: str
    decl: str  # pre-rendered field decl line, e.g. "rand logic [4:0] foo;" or "alpha_helper foo;"
    is_composite_ref: bool
    target_helper_class: str  # for composite refs


@dataclass(frozen=True, slots=True)
class SvTestStructFieldStepView:
    """One struct helper-class to_bytes / from_bytes / sprint per-field datum."""
    name: str
    is_composite_ref: bool
    byte_count: int
    width: int
    total_bits: int  # byte_count * 8
    signed: bool
    pad_bits: int
    has_signed_padding: bool  # pad_bits > 0 and signed


@dataclass(frozen=True, slots=True)
class SvTestStructHelperView:
    kind: str  # "struct"
    helper_class_name: str
    underlying_typedef: str
    upper_base: str
    has_alignment: bool
    alignment_bits: int
    alignment_bytes: int
    field_decls: tuple[SvTestStructFieldDeclView, ...]
    field_steps: tuple[SvTestStructFieldStepView, ...]
    sprint_format: str  # comma-joined "name=%s" / "name=0x%0h" parts
    sprint_args: str  # comma-joined sprint() / name parts


@dataclass(frozen=True, slots=True)
class SvTestFlagsHelperView:
    kind: str  # "flags"
    helper_class_name: str
    underlying_typedef: str
    upper_base: str
    num_flags: int
    byte_count: int
    total_bits: int
    has_alignment: bool
    field_names: tuple[str, ...]
    # Per-flag MSB-first (name, bit_pos)
    flag_bit_positions: tuple[tuple[str, int], ...]
    sprint_format: str
    sprint_args: str


@dataclass(frozen=True, slots=True)
class SvTestEnumHelperView:
    kind: str  # "enum"
    helper_class_name: str
    underlying_typedef: str
    upper_base: str
    width: int
    byte_count: int
    total_bits: int
    first_value_name: str


type SvTestHelperView = (
    SvTestScalarHelperView | SvTestStructHelperView | SvTestFlagsHelperView | SvTestEnumHelperView
)


@dataclass(frozen=True, slots=True)
class SvTestModuleView:
    header: str
    package_name: str
    same_module_synth_basename: str
    # Explicit per-symbol imports from foreign synth packages
    # (typedef of scalar-alias cross-module refs).
    cross_module_synth_imports: tuple[tuple[str, str], ...]
    # Explicit per-symbol imports from foreign test packages
    # (helper class `T_ct` for composite cross-module refs).
    cross_module_test_imports: tuple[tuple[str, str], ...]
    helpers: tuple[SvTestHelperView, ...]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _type_base_name(name: str) -> str:
    return name[:-2] if name.endswith("_t") else name


def _helper_class_name(type_name: str) -> str:
    if type_name.endswith("_t"):
        return f"{type_name[:-2]}_ct"
    return f"{type_name}_ct"


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


def _sv_signed_literal(*, width: int, value: int) -> str:
    if value < 0:
        return f"-{width}'sd{abs(value)}"
    return f"{width}'sd{value}"


def _render_sv_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
    if width == 32 and signed:
        return ("int", _sv_signed_literal(width=32, value=value))
    if width == 32 and not signed:
        return ("int unsigned", f"32'd{value}")
    if width == 64 and signed:
        return ("longint", _sv_signed_literal(width=64, value=value))
    if width == 64 and not signed:
        return ("longint unsigned", f"64'd{value}")
    raise ValueError(f"unsupported SV constant storage: signed={signed}, width={width}")


def _data_width(*, type_ir: TypeDefIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(type_ir, ScalarAliasIR):
        return type_ir.resolved_width
    if isinstance(type_ir, FlagsIR):
        return len(type_ir.fields)
    if isinstance(type_ir, EnumIR):
        return type_ir.resolved_width
    return sum(_field_data_width(field=f, repo_type_index=repo_type_index) for f in type_ir.fields)


def _field_data_width(*, field: StructFieldIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(field.type_ir, ScalarTypeSpecIR):
        return field.type_ir.resolved_width
    target = repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]
    return _data_width(type_ir=target, repo_type_index=repo_type_index)


def _type_byte_count(*, type_ir: TypeDefIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(type_ir, ScalarAliasIR):
        return byte_count(type_ir.resolved_width)
    if isinstance(type_ir, FlagsIR):
        return byte_count(len(type_ir.fields))
    if isinstance(type_ir, EnumIR):
        return byte_count(type_ir.resolved_width)
    field_bytes = sum(_field_byte_count(field=f, repo_type_index=repo_type_index) for f in type_ir.fields)
    return field_bytes + type_ir.alignment_bits // 8


def _field_byte_count(*, field: StructFieldIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(field.type_ir, ScalarTypeSpecIR):
        return byte_count(field.type_ir.resolved_width)
    target = repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]
    return _type_byte_count(type_ir=target, repo_type_index=repo_type_index)


def _is_field_signed(*, field: StructFieldIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> bool:
    if isinstance(field.type_ir, ScalarTypeSpecIR):
        return field.type_ir.signed
    target = repo_type_index.get((field.type_ir.module.python_module_name, field.type_ir.name))
    if isinstance(target, ScalarAliasIR):
        return target.signed
    return False


def _is_sv_composite_ref(*, field_type, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> bool:  # type: ignore[no-untyped-def]
    return isinstance(field_type, TypeRefIR) and isinstance(
        repo_type_index[(field_type.module.python_module_name, field_type.name)], (StructIR, FlagsIR, EnumIR)
    )


def _render_sv_struct_field_type(field_type) -> str:  # type: ignore[no-untyped-def]
    if isinstance(field_type, TypeRefIR):
        return field_type.name
    base_type = field_type.state_kind
    signed_kw = " signed" if field_type.signed else ""
    if field_type.resolved_width == 1:
        return f"{base_type}{signed_kw}"
    return f"{base_type}{signed_kw} [{field_type.resolved_width - 1}:0]"


def _render_sv_helper_field_decl(*, field: StructFieldIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> str:
    if isinstance(field.type_ir, TypeRefIR):
        target = repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]
        if isinstance(target, (StructIR, FlagsIR, EnumIR)):
            return f"{_helper_class_name(target.name)} {field.name};"
        rand_kw = "rand " if field.rand else ""
        return f"{rand_kw}{target.name} {field.name};"
    rand_kw = "rand " if field.rand else ""
    return f"{rand_kw}{_render_sv_struct_field_type(field.type_ir)} {field.name};"


# ---------------------------------------------------------------------------
# Module-level builders
# ---------------------------------------------------------------------------


def _build_constant_view(*, const_ir: ConstIR) -> SvConstantView:
    sv_type, sv_literal = _render_sv_const(
        value=const_ir.resolved_value,
        signed=const_ir.resolved_signed,
        width=const_ir.resolved_width,
    )
    sv_expr = sv_literal if isinstance(const_ir.expr, IntLiteralExprIR) else _render_sv_expr(const_ir.expr)
    return SvConstantView(sv_type=sv_type, name=const_ir.name, sv_expr=sv_expr)


# ---------------------------------------------------------------------------
# Synth per-kind builders
# ---------------------------------------------------------------------------


def _build_synth_scalar_alias(*, type_ir: ScalarAliasIR) -> SvScalarAliasView:
    base = _type_base_name(type_ir.name)
    return SvScalarAliasView(
        kind="scalar_alias",
        name=type_ir.name,
        base=base,
        upper_base=base.upper(),
        base_type=type_ir.state_kind,
        width=type_ir.resolved_width,
        width_expr=_render_sv_expr(type_ir.width_expr),
        byte_count=byte_count(type_ir.resolved_width),
        signed=type_ir.signed,
        is_one_bit=type_ir.resolved_width == 1,
    )


def _build_synth_struct(*, type_ir: StructIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> SvSynthStructView:
    base = _type_base_name(type_ir.name)
    fields = tuple(
        SvSynthStructFieldView(
            name=f.name,
            field_type_text=_render_sv_struct_field_type(f.type_ir),
            has_pre_padding=f.padding_bits > 0,
            pre_padding_bits=f.padding_bits,
            is_pre_padding_one_bit=f.padding_bits == 1,
        )
        for f in type_ir.fields
    )
    return SvSynthStructView(
        kind="struct",
        name=type_ir.name,
        base=base,
        upper_base=base.upper(),
        width=_data_width(type_ir=type_ir, repo_type_index=repo_type_index),
        byte_count=_type_byte_count(type_ir=type_ir, repo_type_index=repo_type_index),
        alignment_bits=type_ir.alignment_bits,
        has_alignment=type_ir.alignment_bits > 0,
        is_alignment_one_bit=type_ir.alignment_bits == 1,
        fields=fields,
    )


def _build_synth_flags(*, type_ir: FlagsIR) -> SvSynthFlagsView:
    base = _type_base_name(type_ir.name)
    field_names = tuple(f.name for f in type_ir.fields)
    # Unpack assigns each flag from a[bit_idx] in REVERSED declaration order.
    unpack_bits = tuple(
        (flag.name, bit_idx) for bit_idx, flag in enumerate(reversed(type_ir.fields))
    )
    return SvSynthFlagsView(
        kind="flags",
        name=type_ir.name,
        base=base,
        upper_base=base.upper(),
        width=len(type_ir.fields),
        byte_count=byte_count(len(type_ir.fields)),
        alignment_bits=type_ir.alignment_bits,
        has_alignment=type_ir.alignment_bits > 0,
        is_alignment_one_bit=type_ir.alignment_bits == 1,
        field_names=field_names,
        unpack_bit_assignments=unpack_bits,
    )


def _build_synth_enum(*, type_ir: EnumIR) -> SvSynthEnumView:
    base = _type_base_name(type_ir.name)
    return SvSynthEnumView(
        kind="enum",
        name=type_ir.name,
        base=base,
        upper_base=base.upper(),
        width=type_ir.resolved_width,
        byte_count=byte_count(type_ir.resolved_width),
        is_one_bit=type_ir.resolved_width == 1,
        members=tuple(
            SvSynthEnumMemberView(name=v.name, value_expr=str(v.resolved_value))
            for v in type_ir.values
        ),
    )


def _build_struct_pack_unpack(
    *, type_ir: StructIR, repo_type_index: dict[tuple[str, str], TypeDefIR]
) -> SvSynthStructPackUnpackView:
    pack_parts: list[SvSynthStructPackPartView] = []
    for field in type_ir.fields:
        if isinstance(field.type_ir, TypeRefIR):
            inner_target = repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]
            inner_base = _type_base_name(inner_target.name)
            pack_parts.append(SvSynthStructPackPartView(expr=f"pack_{inner_base}(a.{field.name})"))
        else:
            pack_parts.append(SvSynthStructPackPartView(expr=f"a.{field.name}"))

    unpack_fields: list[SvSynthStructUnpackFieldView] = []
    for field in reversed(type_ir.fields):
        fw = _field_data_width(field=field, repo_type_index=repo_type_index)
        is_signed = _is_field_signed(field=field, repo_type_index=repo_type_index)
        has_signed_padding = field.padding_bits > 0 and is_signed
        if isinstance(field.type_ir, TypeRefIR):
            inner_target = repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]
            inner_base = _type_base_name(inner_target.name)
            unpack_fields.append(
                SvSynthStructUnpackFieldView(
                    name=field.name,
                    width=fw,
                    is_type_ref=True,
                    inner_base=inner_base,
                    inner_upper=inner_base.upper(),
                    has_signed_padding=has_signed_padding,
                    padding_bits=field.padding_bits,
                    sign_bit_index=fw - 1 if has_signed_padding else 0,
                )
            )
        else:
            unpack_fields.append(
                SvSynthStructUnpackFieldView(
                    name=field.name,
                    width=fw,
                    is_type_ref=False,
                    inner_base="",
                    inner_upper="",
                    has_signed_padding=has_signed_padding,
                    padding_bits=field.padding_bits,
                    sign_bit_index=fw - 1 if has_signed_padding else 0,
                )
            )
    return SvSynthStructPackUnpackView(
        pack_parts=tuple(pack_parts),
        unpack_fields=tuple(unpack_fields),
    )


# ---------------------------------------------------------------------------
# Test helper builders
# ---------------------------------------------------------------------------


def _build_test_scalar_helper(*, type_ir: ScalarAliasIR) -> SvTestScalarHelperView:
    base = _type_base_name(type_ir.name)
    bc = byte_count(type_ir.resolved_width)
    pad = (-type_ir.resolved_width) % 8
    return SvTestScalarHelperView(
        kind="scalar_alias",
        helper_class_name=_helper_class_name(type_ir.name),
        underlying_typedef=type_ir.name,
        upper_base=base.upper(),
        width=type_ir.resolved_width,
        byte_count=bc,
        total_bits=bc * 8,
        pad_bits=pad,
        signed=type_ir.signed,
        has_signed_padding=(pad > 0 and type_ir.signed),
    )


def _build_test_struct_helper(
    *, type_ir: StructIR, repo_type_index: dict[tuple[str, str], TypeDefIR]
) -> SvTestStructHelperView:
    base = _type_base_name(type_ir.name)
    helper_name = _helper_class_name(type_ir.name)

    decls: list[SvTestStructFieldDeclView] = []
    steps: list[SvTestStructFieldStepView] = []
    fmt_parts: list[str] = []
    arg_parts: list[str] = []

    for field in type_ir.fields:
        is_composite = _is_sv_composite_ref(field_type=field.type_ir, repo_type_index=repo_type_index)
        target_helper = ""
        if is_composite and isinstance(field.type_ir, TypeRefIR):
            inner_target = repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]
            target_helper = _helper_class_name(inner_target.name)
        decls.append(
            SvTestStructFieldDeclView(
                name=field.name,
                decl=_render_sv_helper_field_decl(field=field, repo_type_index=repo_type_index),
                is_composite_ref=is_composite,
                target_helper_class=target_helper,
            )
        )
        fbc = _field_byte_count(field=field, repo_type_index=repo_type_index)
        fw = _field_data_width(field=field, repo_type_index=repo_type_index)
        is_signed = _is_field_signed(field=field, repo_type_index=repo_type_index)
        steps.append(
            SvTestStructFieldStepView(
                name=field.name,
                is_composite_ref=is_composite,
                byte_count=fbc,
                width=fw,
                total_bits=fbc * 8,
                signed=is_signed,
                pad_bits=field.padding_bits,
                has_signed_padding=(field.padding_bits > 0 and is_signed),
            )
        )
        if is_composite:
            fmt_parts.append(f"{field.name}=%s")
            arg_parts.append(f"{field.name}.sprint()")
        else:
            fmt_parts.append(f"{field.name}=0x%0h")
            arg_parts.append(field.name)

    return SvTestStructHelperView(
        kind="struct",
        helper_class_name=helper_name,
        underlying_typedef=type_ir.name,
        upper_base=base.upper(),
        has_alignment=type_ir.alignment_bits > 0,
        alignment_bits=type_ir.alignment_bits,
        alignment_bytes=type_ir.alignment_bits // 8,
        field_decls=tuple(decls),
        field_steps=tuple(steps),
        sprint_format=", ".join(fmt_parts),
        sprint_args=", ".join(arg_parts),
    )


def _build_test_flags_helper(*, type_ir: FlagsIR) -> SvTestFlagsHelperView:
    base = _type_base_name(type_ir.name)
    num_flags = len(type_ir.fields)
    bc = byte_count(num_flags)
    total_bits = bc * 8
    flag_bits = tuple(
        (flag.name, total_bits - 1 - i) for i, flag in enumerate(type_ir.fields)
    )
    fmt_parts = [f"{flag.name}=%0b" for flag in type_ir.fields]
    arg_parts = [flag.name for flag in type_ir.fields]
    return SvTestFlagsHelperView(
        kind="flags",
        helper_class_name=_helper_class_name(type_ir.name),
        underlying_typedef=type_ir.name,
        upper_base=base.upper(),
        num_flags=num_flags,
        byte_count=bc,
        total_bits=total_bits,
        has_alignment=type_ir.alignment_bits > 0,
        field_names=tuple(f.name for f in type_ir.fields),
        flag_bit_positions=flag_bits,
        sprint_format=", ".join(fmt_parts),
        sprint_args=", ".join(arg_parts),
    )


def _build_test_enum_helper(*, type_ir: EnumIR) -> SvTestEnumHelperView:
    base = _type_base_name(type_ir.name)
    bc = byte_count(type_ir.resolved_width)
    return SvTestEnumHelperView(
        kind="enum",
        helper_class_name=_helper_class_name(type_ir.name),
        underlying_typedef=type_ir.name,
        upper_base=base.upper(),
        width=type_ir.resolved_width,
        byte_count=bc,
        total_bits=bc * 8,
        first_value_name=type_ir.values[0].name if type_ir.values else "0",
    )


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def build_synth_module_view_sv(
    *, module: ModuleIR, repo_type_index: dict[tuple[str, str], TypeDefIR] | None = None,
) -> SvSynthModuleView:
    if repo_type_index is None:
        # Same-module-only fallback for callers (e.g., legacy tests) that haven't been
        # migrated yet. Builds a single-module index from the input module's types.
        repo_type_index = {(module.ref.python_module_name, t.name): t for t in module.types}
    types_list: list[SvSynthTypeView] = []
    pack_unpack_list: list[SvSynthStructPackUnpackView | None] = []
    for t in module.types:
        if isinstance(t, ScalarAliasIR):
            types_list.append(_build_synth_scalar_alias(type_ir=t))
            pack_unpack_list.append(None)
        elif isinstance(t, StructIR):
            types_list.append(_build_synth_struct(type_ir=t, repo_type_index=repo_type_index))
            pack_unpack_list.append(_build_struct_pack_unpack(type_ir=t, repo_type_index=repo_type_index))
        elif isinstance(t, FlagsIR):
            types_list.append(_build_synth_flags(type_ir=t))
            pack_unpack_list.append(None)
        else:
            types_list.append(_build_synth_enum(type_ir=t))
            pack_unpack_list.append(None)
    return SvSynthModuleView(
        header="",
        package_name=f"{module.ref.basename}_pkg",
        has_constants=bool(module.constants),
        has_types=bool(module.types),
        constants=tuple(_build_constant_view(const_ir=c) for c in module.constants),
        types=tuple(types_list),
        pack_unpack=tuple(pack_unpack_list),
        synth_cross_module_imports=_collect_cross_module_synth_imports(
            module=module, repo_type_index=repo_type_index
        ),
    )


def build_test_module_view_sv(
    *, module: ModuleIR, repo_type_index: dict[tuple[str, str], TypeDefIR] | None = None,
) -> SvTestModuleView:
    if repo_type_index is None:
        repo_type_index = {(module.ref.python_module_name, t.name): t for t in module.types}
    helpers: list[SvTestHelperView] = []
    for t in module.types:
        if isinstance(t, ScalarAliasIR):
            helpers.append(_build_test_scalar_helper(type_ir=t))
        elif isinstance(t, StructIR):
            helpers.append(_build_test_struct_helper(type_ir=t, repo_type_index=repo_type_index))
        elif isinstance(t, FlagsIR):
            helpers.append(_build_test_flags_helper(type_ir=t))
        else:
            helpers.append(_build_test_enum_helper(type_ir=t))
    return SvTestModuleView(
        header="",
        package_name=f"{module.ref.basename}_test_pkg",
        same_module_synth_basename=module.ref.basename,
        cross_module_synth_imports=_collect_cross_module_test_synth_imports(
            module=module, repo_type_index=repo_type_index
        ),
        cross_module_test_imports=_collect_cross_module_test_helper_imports(
            module=module, repo_type_index=repo_type_index
        ),
        helpers=tuple(helpers),
    )


def _iter_cross_module_typerefs(
    *, module: ModuleIR
) -> list[TypeRefIR]:
    """Return all cross-module TypeRefIRs in this module's struct fields.

    Deduplicated by (target_python_module_name, target_type_name); ordered
    deterministically by that key.
    """
    seen: dict[tuple[str, str], TypeRefIR] = {}
    for type_ir in module.types:
        if isinstance(type_ir, StructIR):
            for field in type_ir.fields:
                ref = field.type_ir
                if isinstance(ref, TypeRefIR) and ref.module.python_module_name != module.ref.python_module_name:
                    seen.setdefault((ref.module.python_module_name, ref.name), ref)
    return [seen[k] for k in sorted(seen.keys())]


def _collect_cross_module_synth_imports(
    *, module: ModuleIR, repo_type_index: dict[tuple[str, str], TypeDefIR]
) -> tuple[tuple[str, str], ...]:
    """Per-symbol imports for the synth package.

    For each cross-module type `T_t` referenced by this module's struct fields,
    import the bundle `{T_t, LP_<UPPER>_WIDTH, pack_<base>, unpack_<base>}` from
    `<target>_pkg`. Sorted by (pkg, symbol).
    """
    pairs: set[tuple[str, str]] = set()
    for ref in _iter_cross_module_typerefs(module=module):
        pkg = f"{ref.module.basename}_pkg"
        base = _type_base_name(ref.name)
        upper = base.upper()
        pairs.add((pkg, ref.name))
        pairs.add((pkg, f"LP_{upper}_WIDTH"))
        pairs.add((pkg, f"pack_{base}"))
        pairs.add((pkg, f"unpack_{base}"))
    return tuple(sorted(pairs))


def _collect_cross_module_test_synth_imports(
    *, module: ModuleIR, repo_type_index: dict[tuple[str, str], TypeDefIR]
) -> tuple[tuple[str, str], ...]:
    """Per-symbol imports for the test package, drawn from foreign synth packages.

    For each scalar-alias cross-module ref, import the typedef name from
    `<target>_pkg` (used as a raw helper-class field type, e.g. `rand byte_t f;`).
    Composite cross-module refs do not need a synth-package import in the test
    package — they reference the helper class instead. Sorted by (pkg, symbol).
    """
    pairs: set[tuple[str, str]] = set()
    for ref in _iter_cross_module_typerefs(module=module):
        target = repo_type_index.get((ref.module.python_module_name, ref.name))
        if isinstance(target, ScalarAliasIR):
            pairs.add((f"{ref.module.basename}_pkg", ref.name))
    return tuple(sorted(pairs))


def _collect_cross_module_test_helper_imports(
    *, module: ModuleIR, repo_type_index: dict[tuple[str, str], TypeDefIR]
) -> tuple[tuple[str, str], ...]:
    """Per-symbol imports for the test package, drawn from foreign test packages.

    For each composite (struct/flags/enum) cross-module ref, import the helper
    class name `<base>_ct` from `<target>_test_pkg`. Scalar-alias refs do not
    need a helper-class import. Sorted by (pkg, symbol).
    """
    pairs: set[tuple[str, str]] = set()
    for ref in _iter_cross_module_typerefs(module=module):
        target = repo_type_index.get((ref.module.python_module_name, ref.name))
        if isinstance(target, (StructIR, FlagsIR, EnumIR)):
            pairs.add((f"{ref.module.basename}_test_pkg", _helper_class_name(target.name)))
    return tuple(sorted(pairs))
