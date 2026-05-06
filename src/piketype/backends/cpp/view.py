"""View-model dataclasses and builders for the C++ backend.

Implements FR-1, FR-8, FR-9, FR-18 of spec 010-jinja-template-migration.
This module provides per-kind frozen dataclasses (CppScalarAliasView,
CppEnumView, CppFlagsView, CppStructView) with all numeric primitives
and pre-rendered C++ literals precomputed. Templates in
``backends/cpp/templates/`` consume these primitives directly via
dedicated Jinja macros (one per type kind) — there is no body_text
passthrough in the final state.
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
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    ModuleRefIR,
    ScalarAliasIR,
    StructFieldIR,
    StructIR,
    TypeDefIR,
    TypeRefIR,
    UnaryExprIR,
    VecConstIR,
    byte_count,
)


# ---------------------------------------------------------------------------
# Module-level views
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CppGuardView:
    macro: str  # exact include-guard symbol


@dataclass(frozen=True, slots=True)
class CppNamespaceView:
    qualified: str  # "" if no namespace
    has_namespace: bool
    open_line: str
    close_line: str


@dataclass(frozen=True, slots=True)
class CppConstantView:
    cpp_type: str
    name: str
    value_expr: str  # pre-rendered C++ literal or expression


# ---------------------------------------------------------------------------
# Per-kind type views
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CppScalarAliasView:
    kind: str  # "scalar_alias"
    class_name: str
    width: int
    byte_count: int
    signed: bool
    storage_type: str  # _cpp_scalar_value_type result
    # Mutually-exclusive discriminators
    is_narrow_signed: bool
    is_narrow_unsigned: bool
    is_wide: bool
    # Branch-control booleans for the signed narrow path.
    has_signed_padding: bool  # is_narrow_signed and (byte_count*8 - width) > 0
    has_signed_short_width: bool  # is_narrow_signed and width < 64
    needs_validate: bool  # narrow only; True iff width not in {8, 16, 32, 64}
    is_single_byte: bool  # narrow only; True iff byte_count == 1
    bswap_intrinsic: str  # "" if no bswap path; else "__builtin_bswapN"
    bswap_uint_type: str  # "" if no bswap path; else "uintN_t"
    # Literals (empty string when the active branch does not consume them).
    min_value_literal: str
    max_value_literal: str
    mask_literal: str  # narrow only; "" for wide
    sign_bit_literal: str  # signed-narrow only
    full_range_literal: str  # signed-short-width only
    byte_total_mask_literal: str  # signed-padding only
    msb_byte_mask_literal: str  # wide only


@dataclass(frozen=True, slots=True)
class CppEnumMemberView:
    name: str
    value_literal: str  # _cpp_unsigned_literal(resolved_value)


@dataclass(frozen=True, slots=True)
class CppEnumView:
    kind: str  # "enum"
    class_name: str  # wrapper class (e.g. "color_ct")
    enum_class_name: str  # underlying enum class (e.g. "color_enum_t")
    width: int
    byte_count: int
    underlying_uint_type: str  # _cpp_scalar_value_type(width=W, signed=False)
    first_member_name: str
    mask_literal: str
    members: tuple[CppEnumMemberView, ...]


@dataclass(frozen=True, slots=True)
class CppFlagFieldView:
    name: str
    name_upper: str  # name.upper()
    bit_mask_literal: str  # 0x..U or 0x..ULL


@dataclass(frozen=True, slots=True)
class CppFlagsView:
    kind: str  # "flags"
    class_name: str
    num_flags: int
    byte_count: int
    storage_bits: int
    storage_type: str
    data_mask_literal: str
    fields: tuple[CppFlagFieldView, ...]


@dataclass(frozen=True, slots=True)
class CppStructFieldView:
    name: str
    field_type_str: str  # bare type, e.g. "uint32_t"
    byte_count: int
    byte_offset: int  # byte offset of this field within the struct
    pack_bits: int  # byte_count * 8
    # Type discriminators (exactly one is True).
    is_struct_ref: bool
    is_flags_ref: bool
    is_enum_ref: bool
    is_scalar_ref: bool
    is_narrow_scalar: bool
    is_wide_scalar: bool
    target_class: str  # "" if scalar spec
    width: int
    signed: bool
    has_signed_padding: bool  # is_narrow_scalar and signed and pad_bits > 0
    has_signed_short_width: bool  # is_narrow_scalar and signed and width < 64
    needs_validate: bool  # narrow only; True iff width not in {8, 16, 32, 64}
    is_single_byte: bool  # narrow only; True iff byte_count == 1
    bswap_intrinsic: str  # "" if not power-of-2 multibyte; else "__builtin_bswapN"
    bswap_uint_type: str  # "" if no bswap; else "uintN_t" matching the intrinsic
    min_value_literal: str
    max_value_literal: str
    mask_literal: str
    sign_bit_literal: str
    full_range_literal: str
    byte_total_mask_literal: str  # narrow signed: mask of all BYTE_COUNT bytes
    msb_byte_mask_literal: str


@dataclass(frozen=True, slots=True)
class CppStructView:
    kind: str  # "struct"
    class_name: str
    width: int
    byte_count: int
    alignment_bytes: int
    alignment_offset: int  # byte offset where alignment padding begins (= byte_count - alignment_bytes)
    has_inline_helpers: bool  # at least one field is a narrow or wide inline scalar
    fields: tuple[CppStructFieldView, ...]


type CppTypeView = CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView


@dataclass(frozen=True, slots=True)
class CppModuleView:
    header: str
    guard: CppGuardView
    namespace: CppNamespaceView
    has_types: bool
    standard_includes: tuple[str, ...]
    constants: tuple[CppConstantView, ...]
    types: tuple[CppTypeView, ...]
    # Cross-module include paths (e.g., "alpha/piketype/foo_types.hpp"); template
    # renders `#include "{p}"`. Sorted ascending, deduplicated.
    cross_module_include_paths: tuple[str, ...]


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


def _type_class_name(type_name: str) -> str:
    """Convert snake_case type name to PascalCase C++ class name.

    Strips trailing ``_t`` if present, then capitalizes each
    underscore-separated segment.

    Examples: ``addr_t`` → ``Addr``, ``ll_table_update_t`` →
    ``LlTableUpdate``, ``foo`` → ``Foo``.
    """
    base = type_name[:-2] if type_name.endswith("_t") else type_name
    return "".join(seg[:1].upper() + seg[1:] for seg in base.split("_") if seg)


def _cpp_scalar_value_type(*, width: int, signed: bool) -> str:
    if width <= 8:
        return "int8_t" if signed else "uint8_t"
    if width <= 16:
        return "int16_t" if signed else "uint16_t"
    if width <= 32:
        return "int32_t" if signed else "uint32_t"
    return "int64_t" if signed else "uint64_t"


def _cpp_unsigned_literal(value: int) -> str:
    """Render an unsigned integer literal for C++ (decimal form)."""
    if value <= 0xFFFFFFFF:
        return f"{value}U"
    return f"{value}ULL"


def _cpp_signed_min_literal(*, width: int) -> str:
    """Render a signed minimum literal that compiles cleanly under -Wpedantic.

    For width=64, ``-9223372036854775808`` is parsed as ``-(9223372036854775808)``
    where the unary operand exceeds INT64_MAX and is thus unsigned. Use
    ``INT64_MIN`` from ``<cstdint>`` instead.
    """
    minimum = -(2 ** (width - 1))
    if width == 64:
        return "INT64_MIN"
    return str(minimum)


def _cpp_signed_max_literal(*, width: int) -> str:
    """Render a signed maximum literal. Mirrors ``_cpp_signed_min_literal``."""
    maximum = 2 ** (width - 1) - 1
    if width == 64:
        return "INT64_MAX"
    return str(maximum)


def _bswap_intrinsic(byte_count: int) -> tuple[str, str]:
    """Return (intrinsic, uint_type) for a power-of-2 multibyte byte_count.

    Returns ``("", "")`` for byte_count == 1 (no swap needed) or
    non-power-of-2 widths {3, 5, 6, 7} (no native intrinsic; caller falls
    back to a byte loop).
    """
    if byte_count == 2:
        return ("__builtin_bswap16", "uint16_t")
    if byte_count == 4:
        return ("__builtin_bswap32", "uint32_t")
    if byte_count == 8:
        return ("__builtin_bswap64", "uint64_t")
    return ("", "")


def _shortened_qualifier(*, current_ns: str, target_ns: str) -> str:
    """Return the shortest unambiguous namespace qualifier from current_ns to target_ns.

    Relies on C++ sibling-namespace lookup: from inside ``a::b``, an
    unqualified ``c::Foo`` resolves to ``a::c::Foo`` if it exists.

    - Same namespace → ``""`` (caller emits unqualified).
    - Common-prefix sibling → relative path (e.g., ``"table"``).
    - No common prefix → absolute path (e.g., ``"::other::lib"``).
    """
    if current_ns == target_ns:
        return ""
    current_parts = current_ns.split("::") if current_ns else []
    target_parts = target_ns.split("::") if target_ns else []
    common = 0
    while (
        common < len(current_parts)
        and common < len(target_parts)
        and current_parts[common] == target_parts[common]
    ):
        common += 1
    if common == 0:
        return f"::{target_ns}"
    return "::".join(target_parts[common:])


def _cpp_hex_literal(value: int, *, is_64: bool) -> str:
    """Render an unsigned integer literal for C++ (hex form, used by flags masks)."""
    if is_64:
        return f"0x{value:02X}ULL"
    return f"0x{value:02X}U"


# ---------------------------------------------------------------------------
# Module-level builders
# ---------------------------------------------------------------------------


def _build_guard_view(*, module: ModuleIR, namespace: str | None) -> CppGuardView:
    if namespace is not None:
        macro = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
    else:
        macro = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
    return CppGuardView(macro=macro)


def _module_ref_namespace(*, module_ref: ModuleRefIR, namespace: str | None) -> str:
    """Compute the C++ namespace string for a module given by ModuleRefIR.

    Same rule as ``_build_namespace_view``: under ``--namespace=N``, returns
    ``N::{basename}``; otherwise filters out the literal ``"piketype"`` segment
    from ``module_ref.namespace_parts``.
    """
    if namespace is not None:
        return f"{namespace}::{module_ref.basename}"
    return "::".join(p for p in module_ref.namespace_parts if p != "piketype")


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
    base = ("<cstdint>",)
    if has_types:
        return base + ("<array>", "<cstddef>", "<cstring>", "<span>", "<stdexcept>")
    return base


def _build_constant_view(*, const_ir: ConstIR) -> CppConstantView:
    # Local copy of _render_cpp_const to avoid emitter dependency.
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


def _render_cpp_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
    """Choose a safe C++ constant type and literal spelling."""
    if width == 32 and signed:
        return ("int32_t", str(value))
    if width == 32 and not signed:
        return ("uint32_t", f"{value}U")
    if width == 64 and signed:
        return ("int64_t", f"{value}LL")
    if width == 64 and not signed:
        return ("uint64_t", f"{value}ULL")
    raise ValueError(f"unsupported C++ constant storage: signed={signed}, width={width}")


def _cpp_uint_type(width: int) -> str:
    """Round up to the smallest uintN_t that fits a VecConst width."""
    if width <= 8:
        return "uint8_t"
    if width <= 16:
        return "uint16_t"
    if width <= 32:
        return "uint32_t"
    return "uint64_t"


def _cpp_literal_suffix(width: int) -> str:
    if width <= 16:
        return ""
    if width <= 32:
        return "U"
    return "ULL"


def _render_cpp_vec_literal(*, width: int, value: int, base: str) -> str:
    """Render a C++ literal honoring the VecConst base."""
    suffix = _cpp_literal_suffix(width)
    match base:
        case "hex":
            return f"0x{value:0{(width + 3) // 4}X}{suffix}"
        case "dec":
            return f"{value}{suffix}"
        case "bin":
            return f"0b{value:0{width}b}{suffix}"
        case _:
            raise ValueError(f"unsupported VecConst base: {base!r}")


def _build_cpp_vec_constant_view(*, vec_const_ir: VecConstIR) -> CppConstantView:
    return CppConstantView(
        cpp_type=_cpp_uint_type(vec_const_ir.width),
        name=vec_const_ir.name,
        value_expr=_render_cpp_vec_literal(
            width=vec_const_ir.width, value=vec_const_ir.value, base=vec_const_ir.base
        ),
    )


# ---------------------------------------------------------------------------
# Per-kind builders
# ---------------------------------------------------------------------------


def _build_scalar_alias_view(*, type_ir: ScalarAliasIR) -> CppScalarAliasView:
    width = type_ir.resolved_width
    bc = byte_count(width)
    signed = type_ir.signed
    is_wide = width > 64
    storage_type = _cpp_scalar_value_type(width=width, signed=signed)

    if is_wide:
        # Wide unsigned only (per current emitter contract).
        pad = bc * 8 - width
        msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
        return CppScalarAliasView(
            kind="scalar_alias",
            class_name=_type_class_name(type_ir.name),
            width=width,
            byte_count=bc,
            signed=signed,
            storage_type="std::array<uint8_t, BYTE_COUNT>",
            is_narrow_signed=False,
            is_narrow_unsigned=False,
            is_wide=True,
            has_signed_padding=False,
            has_signed_short_width=False,
            needs_validate=False,
            is_single_byte=False,
            bswap_intrinsic="",
            bswap_uint_type="",
            min_value_literal="",
            max_value_literal="",
            mask_literal="",
            sign_bit_literal="",
            full_range_literal="",
            byte_total_mask_literal="",
            msb_byte_mask_literal=msb_mask,
        )

    # Narrow path — width <= 64.
    mask = (1 << width) - 1 if width < 64 else 2**64 - 1
    mask_literal = _cpp_unsigned_literal(mask)
    pad_bits = bc * 8 - width
    needs_validate = width not in (8, 16, 32, 64)
    is_single_byte = bc == 1

    bswap_intrinsic, bswap_uint_type = _bswap_intrinsic(bc)
    if signed:
        has_signed_padding = pad_bits > 0
        has_signed_short_width = width < 64
        bt = (1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1
        return CppScalarAliasView(
            kind="scalar_alias",
            class_name=_type_class_name(type_ir.name),
            width=width,
            byte_count=bc,
            signed=True,
            storage_type=storage_type,
            is_narrow_signed=True,
            is_narrow_unsigned=False,
            is_wide=False,
            has_signed_padding=has_signed_padding,
            has_signed_short_width=has_signed_short_width,
            needs_validate=needs_validate,
            is_single_byte=is_single_byte,
            bswap_intrinsic=bswap_intrinsic,
            bswap_uint_type=bswap_uint_type,
            min_value_literal=_cpp_signed_min_literal(width=width) if needs_validate else "",
            max_value_literal=_cpp_signed_max_literal(width=width) if needs_validate else "",
            mask_literal=mask_literal,
            sign_bit_literal=_cpp_unsigned_literal(1 << (width - 1)) if has_signed_short_width else "",
            full_range_literal=_cpp_unsigned_literal(1 << width) if has_signed_short_width else "",
            byte_total_mask_literal=_cpp_unsigned_literal(bt),
            msb_byte_mask_literal="",
        )

    # Narrow unsigned.
    maximum = 2**width - 1 if width < 64 else 2**64 - 1
    return CppScalarAliasView(
        kind="scalar_alias",
        class_name=_type_class_name(type_ir.name),
        width=width,
        byte_count=bc,
        signed=False,
        storage_type=storage_type,
        is_narrow_signed=False,
        is_narrow_unsigned=True,
        is_wide=False,
        has_signed_padding=False,
        has_signed_short_width=False,
        needs_validate=needs_validate,
        is_single_byte=is_single_byte,
        bswap_intrinsic=bswap_intrinsic,
        bswap_uint_type=bswap_uint_type,
        min_value_literal="",
        max_value_literal=_cpp_unsigned_literal(maximum) if needs_validate else "",
        mask_literal=mask_literal,
        sign_bit_literal="",
        full_range_literal="",
        byte_total_mask_literal="",
        msb_byte_mask_literal="",
    )


def _build_enum_view(*, type_ir: EnumIR) -> CppEnumView:
    base = type_ir.name[:-2] if type_ir.name.endswith("_t") else type_ir.name
    width = type_ir.resolved_width
    members = tuple(
        CppEnumMemberView(name=v.name, value_literal=_cpp_unsigned_literal(v.resolved_value))
        for v in type_ir.values
    )
    return CppEnumView(
        kind="enum",
        class_name=_type_class_name(type_ir.name),
        enum_class_name=f"{base}_enum_t",
        width=width,
        byte_count=byte_count(width),
        underlying_uint_type=_cpp_scalar_value_type(width=width, signed=False),
        first_member_name=type_ir.values[0].name if type_ir.values else "0",
        mask_literal=_cpp_unsigned_literal((1 << width) - 1 if width < 64 else 2**64 - 1),
        members=members,
    )


def _build_flags_view(*, type_ir: FlagsIR) -> CppFlagsView:
    num_flags = len(type_ir.fields)
    total_width = num_flags + type_ir.alignment_bits
    bc = byte_count(total_width)
    storage_bits = bc * 8
    storage_type = _cpp_scalar_value_type(width=storage_bits, signed=False)
    data_mask_val = ((1 << num_flags) - 1) << (storage_bits - num_flags)
    is_64 = storage_bits > 32
    fields = tuple(
        CppFlagFieldView(
            name=field.name,
            name_upper=field.name.upper(),
            bit_mask_literal=_cpp_hex_literal(1 << (storage_bits - 1 - i), is_64=is_64),
        )
        for i, field in enumerate(type_ir.fields)
    )
    return CppFlagsView(
        kind="flags",
        class_name=_type_class_name(type_ir.name),
        num_flags=num_flags,
        byte_count=bc,
        storage_bits=storage_bits,
        storage_type=storage_type,
        data_mask_literal=_cpp_hex_literal(data_mask_val, is_64=is_64),
        fields=fields,
    )


def _resolved_type_width(*, type_ir: TypeDefIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    """Resolve the data-width-only (no alignment padding) for use in struct field aggregation."""
    if isinstance(type_ir, ScalarAliasIR):
        return type_ir.resolved_width
    if isinstance(type_ir, FlagsIR):
        return len(type_ir.fields)  # data width only — alignment_bits NOT included
    if isinstance(type_ir, EnumIR):
        return type_ir.resolved_width
    total = 0
    for f in type_ir.fields:
        if isinstance(f.type_ir, TypeRefIR):
            target = repo_type_index[(f.type_ir.module.python_module_name, f.type_ir.name)]
            total += _resolved_type_width(type_ir=target, repo_type_index=repo_type_index)
        else:
            total += f.type_ir.resolved_width
    return total


def _type_byte_count(*, type_ir: TypeDefIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(type_ir, ScalarAliasIR):
        return byte_count(type_ir.resolved_width)
    if isinstance(type_ir, FlagsIR):
        return (len(type_ir.fields) + type_ir.alignment_bits) // 8
    if isinstance(type_ir, EnumIR):
        return byte_count(type_ir.resolved_width)
    field_bytes = sum(_field_byte_count(field_ir=f, repo_type_index=repo_type_index) for f in type_ir.fields)
    return field_bytes + type_ir.alignment_bits // 8


def _field_byte_count(*, field_ir: StructFieldIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(field_ir.type_ir, TypeRefIR):
        target = repo_type_index[(field_ir.type_ir.module.python_module_name, field_ir.type_ir.name)]
        return _type_byte_count(type_ir=target, repo_type_index=repo_type_index)
    return byte_count(field_ir.type_ir.resolved_width)


def _build_struct_field_view(
    *, field_ir: StructFieldIR, byte_offset: int,
    repo_type_index: dict[tuple[str, str], TypeDefIR],
    current_module: ModuleIR, emit_namespace: str | None,
) -> CppStructFieldView:
    """Build a struct-field view from frozen IR. All primitives precomputed
    in pure Python; templates consume them via macros, no legacy helper calls."""
    fbc = _field_byte_count(field_ir=field_ir, repo_type_index=repo_type_index)
    pack_bits = fbc * 8

    # Field type string — derived from the IR directly.
    if isinstance(field_ir.type_ir, TypeRefIR):
        target_for_name = repo_type_index[(field_ir.type_ir.module.python_module_name, field_ir.type_ir.name)]
        is_cross_module = field_ir.type_ir.module.python_module_name != current_module.ref.python_module_name
        if is_cross_module:
            current_ns = _build_namespace_view(module=current_module, namespace=emit_namespace).qualified
            target_ns = _module_ref_namespace(module_ref=field_ir.type_ir.module, namespace=emit_namespace)
            qualifier = _shortened_qualifier(current_ns=current_ns, target_ns=target_ns)
            class_name = _type_class_name(target_for_name.name)
            field_type_str = f"{qualifier}::{class_name}" if qualifier else class_name
        else:
            field_type_str = _type_class_name(target_for_name.name)
    else:
        spec_w = field_ir.type_ir.resolved_width
        if spec_w <= 64:
            field_type_str = _cpp_scalar_value_type(width=spec_w, signed=field_ir.type_ir.signed)
        else:
            field_type_str = f"std::array<uint8_t, {fbc}>"

    # Defaults
    is_struct_ref = is_flags_ref = is_enum_ref = is_scalar_ref = False
    is_narrow_scalar = is_wide_scalar = False
    target_class = ""
    width = 0
    signed = False
    has_signed_padding = has_signed_short_width = False
    min_value_literal = ""
    max_value_literal = ""
    mask_literal = ""
    sign_bit_literal = ""
    full_range_literal = ""
    byte_total_mask_literal = ""
    msb_byte_mask_literal = ""

    needs_validate = False
    is_single_byte = fbc == 1
    bswap_intrinsic = ""
    bswap_uint_type = ""
    if isinstance(field_ir.type_ir, TypeRefIR):
        target = repo_type_index[(field_ir.type_ir.module.python_module_name, field_ir.type_ir.name)]
        target_class = _type_class_name(target.name)
        if isinstance(target, StructIR):
            is_struct_ref = True
        elif isinstance(target, FlagsIR):
            is_flags_ref = True
        elif isinstance(target, EnumIR):
            is_enum_ref = True
        else:
            is_scalar_ref = True
    else:
        # ScalarTypeSpecIR
        spec = field_ir.type_ir
        width = spec.resolved_width
        signed = spec.signed
        if width <= 64:
            is_narrow_scalar = True
            needs_validate = width not in (8, 16, 32, 64)
            bswap_intrinsic, bswap_uint_type = _bswap_intrinsic(fbc)
            mask = (1 << width) - 1 if width < 64 else 2**64 - 1
            mask_literal = _cpp_unsigned_literal(mask)
            pad_bits = pack_bits - width
            if signed:
                has_signed_padding = pad_bits > 0
                has_signed_short_width = width < 64
                if needs_validate:
                    min_value_literal = _cpp_signed_min_literal(width=width)
                    max_value_literal = _cpp_signed_max_literal(width=width)
                if has_signed_short_width:
                    sign_bit_literal = _cpp_unsigned_literal(1 << (width - 1))
                    full_range_literal = _cpp_unsigned_literal(1 << width)
                bt = (1 << pack_bits) - 1 if pack_bits < 64 else 2**64 - 1
                byte_total_mask_literal = _cpp_unsigned_literal(bt)
            else:
                if needs_validate:
                    maximum = 2**width - 1 if width < 64 else 2**64 - 1
                    max_value_literal = _cpp_unsigned_literal(maximum)
        else:
            is_wide_scalar = True
            pad = pack_bits - width
            msb_byte_mask_literal = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"

    return CppStructFieldView(
        name=field_ir.name,
        field_type_str=field_type_str,
        byte_count=fbc,
        byte_offset=byte_offset,
        pack_bits=pack_bits,
        is_struct_ref=is_struct_ref,
        is_flags_ref=is_flags_ref,
        is_enum_ref=is_enum_ref,
        is_scalar_ref=is_scalar_ref,
        is_narrow_scalar=is_narrow_scalar,
        is_wide_scalar=is_wide_scalar,
        target_class=target_class,
        width=width,
        signed=signed,
        has_signed_padding=has_signed_padding,
        has_signed_short_width=has_signed_short_width,
        needs_validate=needs_validate,
        is_single_byte=is_single_byte,
        bswap_intrinsic=bswap_intrinsic,
        bswap_uint_type=bswap_uint_type,
        min_value_literal=min_value_literal,
        max_value_literal=max_value_literal,
        mask_literal=mask_literal,
        sign_bit_literal=sign_bit_literal,
        full_range_literal=full_range_literal,
        byte_total_mask_literal=byte_total_mask_literal,
        msb_byte_mask_literal=msb_byte_mask_literal,
    )


def _build_struct_view(
    *, type_ir: StructIR, repo_type_index: dict[tuple[str, str], TypeDefIR],
    current_module: ModuleIR, emit_namespace: str | None,
) -> CppStructView:
    # Compute data width matching legacy: sum of field data widths, ignoring per-field padding.
    data_width = 0
    for f in type_ir.fields:
        if isinstance(f.type_ir, TypeRefIR):
            target = repo_type_index[(f.type_ir.module.python_module_name, f.type_ir.name)]
            data_width += _resolved_type_width(type_ir=target, repo_type_index=repo_type_index)
        else:
            data_width += f.type_ir.resolved_width
    width = data_width
    field_byte_counts = [
        _field_byte_count(field_ir=f, repo_type_index=repo_type_index) for f in type_ir.fields
    ]
    alignment_bytes = type_ir.alignment_bits // 8
    bc_total = sum(field_byte_counts) + alignment_bytes
    offsets: list[int] = []
    cursor = 0
    for fbc in field_byte_counts:
        offsets.append(cursor)
        cursor += fbc
    field_views = tuple(
        _build_struct_field_view(
            field_ir=f, byte_offset=off, repo_type_index=repo_type_index,
            current_module=current_module, emit_namespace=emit_namespace,
        )
        for f, off in zip(type_ir.fields, offsets, strict=True)
    )
    has_inline_helpers = any(f.is_narrow_scalar or f.is_wide_scalar for f in field_views)
    return CppStructView(
        kind="struct",
        class_name=_type_class_name(type_ir.name),
        width=width,
        byte_count=bc_total,
        alignment_bytes=alignment_bytes,
        alignment_offset=bc_total - alignment_bytes,
        has_inline_helpers=has_inline_helpers,
        fields=field_views,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_module_view_cpp(
    *, module: ModuleIR, namespace: str | None = None,
    repo_type_index: dict[tuple[str, str], TypeDefIR] | None = None,
) -> CppModuleView:
    if repo_type_index is None:
        repo_type_index = {(module.ref.python_module_name, t.name): t for t in module.types}
    has_types = bool(module.types)

    types_list: list[CppTypeView] = []
    for t in module.types:
        if isinstance(t, ScalarAliasIR):
            types_list.append(_build_scalar_alias_view(type_ir=t))
        elif isinstance(t, EnumIR):
            types_list.append(_build_enum_view(type_ir=t))
        elif isinstance(t, FlagsIR):
            types_list.append(_build_flags_view(type_ir=t))
        else:
            types_list.append(
                _build_struct_view(
                    type_ir=t, repo_type_index=repo_type_index,
                    current_module=module, emit_namespace=namespace,
                )
            )

    return CppModuleView(
        header="",  # caller supplies via dataclasses.replace
        guard=_build_guard_view(module=module, namespace=namespace),
        namespace=_build_namespace_view(module=module, namespace=namespace),
        has_types=has_types,
        standard_includes=_standard_includes(has_types=has_types),
        constants=(
            tuple(_build_constant_view(const_ir=c) for c in module.constants)
            + tuple(_build_cpp_vec_constant_view(vec_const_ir=v) for v in module.vec_constants)
        ),
        types=tuple(types_list),
        cross_module_include_paths=_collect_cpp_cross_module_includes(module=module),
    )


def _collect_cpp_cross_module_includes(*, module: ModuleIR) -> tuple[str, ...]:
    """Collect include paths for direct cross-module type refs.

    Path format: `{namespace_parts joined by /}/{basename}_types.hpp` where
    `namespace_parts` is from the target's `ModuleRefIR`.

    Sorted ascending and deduplicated.
    """
    seen: set[str] = set()
    for type_ir in module.types:
        if isinstance(type_ir, StructIR):
            for field in type_ir.fields:
                if isinstance(field.type_ir, TypeRefIR):
                    target_module = field.type_ir.module
                    if target_module.python_module_name == module.ref.python_module_name:
                        continue
                    # Path under gen/cpp/: {namespace_parts joined}/<basename>_types.hpp.
                    # namespace_parts ends with the basename, so drop the last and append `_types.hpp`.
                    parts = target_module.namespace_parts
                    path = "/".join(parts[:-1]) + f"/{target_module.basename}_types.hpp"
                    seen.add(path)
    return tuple(sorted(seen))
