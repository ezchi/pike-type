"""View-model dataclasses and builders for the Python backend.

Implements FR-1, FR-8, FR-9, FR-18 of spec 010-jinja-template-migration.
View models are frozen dataclasses with primitive fields plus nested
view-model dataclasses. Builders are top-level keyword-only functions
that consume frozen IR and produce view models containing every
numeric primitive and pre-rendered fragment the templates need.

The transitional ``body_lines`` / ``has_body_lines`` fields on
``ModuleView`` exist only during the FR-6 sub-step migration commits
(T-08..T-11). They are removed in the cleanup commit (T-12).

This module is dormant at T-07: the production emitter does not yet
import from here. Tests in ``tests/test_view_py.py`` exercise the
builders directly.
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
    ModuleRefIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    StructFieldIR,
    StructIR,
    TypeDefIR,
    TypeRefIR,
    UnaryExprIR,
    VecConstIR,
    byte_count,
)
from piketype.names import py_enum_class_name, py_type_class_name


# ---------------------------------------------------------------------------
# View model dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConstantView:
    """One module-level constant."""

    name: str
    value_expr: str  # pre-rendered Python expression


@dataclass(frozen=True, slots=True)
class ScalarAliasView:
    """One scalar alias type."""

    kind: str  # always "scalar_alias" — discriminator for template dispatch
    class_name: str
    width: int
    byte_count: int
    signed: bool
    is_wide: bool  # width > 64
    min_value: int  # 0 if not signed
    max_value: int
    mask: int  # 0 for wide
    sign_bit: int  # 0 if not signed
    pad_bits: int  # byte_count*8 - width (only meaningful for narrow signed)
    msb_byte_mask: int  # for wide unsigned tail mask


@dataclass(frozen=True, slots=True)
class EnumMemberView:
    name: str
    resolved_value_expr: str


@dataclass(frozen=True, slots=True)
class EnumView:
    kind: str  # always "enum"
    class_name: str
    enum_class_name: str
    width: int
    byte_count: int
    mask: int  # (1 << width) - 1
    first_member_name: str
    members: tuple[EnumMemberView, ...]


@dataclass(frozen=True, slots=True)
class FlagFieldView:
    name: str
    bit_mask: int  # MSB-first: 1 << (total_bits - 1 - i)


@dataclass(frozen=True, slots=True)
class FlagsView:
    kind: str  # always "flags"
    class_name: str
    num_flags: int
    byte_count: int
    total_bits: int  # byte_count * 8
    data_mask: int  # ((1 << num_flags) - 1) << alignment_bits
    alignment_bits: int  # total_bits - num_flags
    flag_mask: int  # (1 << num_flags) - 1 — flat data-only mask used by pack/unpack
    fields: tuple[FlagFieldView, ...]


@dataclass(frozen=True, slots=True)
class StructFieldView:
    name: str
    annotation: str  # pre-rendered "int", "bytes", "addr_ct | None"
    default_expr: str  # pre-rendered "0", 'b"\\x00" * 4', "field(default_factory=foo_ct)"
    byte_count: int
    pack_bits: int  # byte_count * 8
    # Type discriminators (exactly one is True).
    is_struct_ref: bool
    is_flags_ref: bool
    is_enum_ref: bool
    is_scalar_ref: bool  # TypeRef -> ScalarAlias
    is_narrow_scalar: bool  # ScalarTypeSpec, width <= 64
    is_wide_scalar: bool  # ScalarTypeSpec, width > 64
    target_class: str  # _type_class_name of referenced TypeRef target; "" otherwise
    width: int  # data width in bits (0 for non-scalar refs)
    signed: bool
    min_value: int
    max_value: int
    mask: int
    sign_bit_value: int
    pad_bits: int
    msb_byte_mask: int
    # Pre-computed shift / range values used by signed-narrow from_bytes.
    sign_bit_index: int  # width - 1 (signed narrow); 0 otherwise
    full_range: int  # 2 ** width = 1 << width (signed narrow); 0 otherwise
    # Pack/unpack data — data-only width across all field kinds and the
    # LSB-aligned slice position inside the struct's packed int.
    data_width: int  # data width for pack/unpack (full data width for type refs)
    data_mask: int  # (1 << data_width) - 1
    unpack_slice_low: int  # LSB position of this field inside the packed int
    # Number of hex digits needed to represent data_width: (data_width + 3) // 4.
    # Used by the compare() template to format narrow-unsigned and wide fields.
    hex_width: int


@dataclass(frozen=True, slots=True)
class StructView:
    kind: str  # always "struct"
    class_name: str
    width: int  # data width
    byte_count: int  # includes alignment bytes
    alignment_bytes: int
    fields: tuple[StructFieldView, ...]
    has_struct_field: bool  # at least one field.is_struct_ref
    pack_total_width: int  # sum of field data widths — width of the pack() int


type TypeView = ScalarAliasView | StructView | EnumView | FlagsView


@dataclass(frozen=True, slots=True)
class PyCrossModuleImportView:
    """A single cross-module wrapper-class import."""

    target_types_module: str
    wrapper_class_name: str


@dataclass(frozen=True, slots=True)
class ModuleView:
    """Top-level Python module view."""

    header: str
    has_types: bool
    has_structs: bool
    has_enums: bool
    has_flags: bool
    constants: tuple[ConstantView, ...]
    types: tuple[TypeView, ...]
    cross_module_imports: tuple[PyCrossModuleImportView, ...]


# ---------------------------------------------------------------------------
# Helpers (pure)
# ---------------------------------------------------------------------------


def _type_class_name(type_name: str) -> str:
    """Convert a generated type name to its software wrapper class name."""
    return py_type_class_name(type_name)


def _py_types_module_path(*, source_module: ModuleRefIR, target_module: ModuleRefIR) -> str:
    """Return the Python import path for the target module's generated _types.py.

    Convention: the user adds the configured ``backends.py.backend_root``
    directory to PYTHONPATH at runtime, so the leading
    ``<py.backend_root>`` segment does NOT appear in import names. For
    DSL at ``<sub>/piketype/<name>.py`` the file is at
    ``<py.backend_root>/<sub>/<name>_types.py`` (with no
    ``<py.language_id>`` segment in the default config) and imports as
    ``<sub>.<name>_types``. Same-``<sub>`` source/target use a relative
    dotted import.
    """
    tgt_parts = target_module.namespace_parts
    src_parts = source_module.namespace_parts
    if (
        len(src_parts) >= 2
        and len(tgt_parts) >= 2
        and src_parts[-2] == "piketype"
        and tgt_parts[-2] == "piketype"
        and src_parts[:-2] == tgt_parts[:-2]
    ):
        return f".{tgt_parts[-1]}_types"
    if len(tgt_parts) < 2 or tgt_parts[-2] != "piketype":
        return ".".join(tgt_parts) + "_types"
    new_parts = tgt_parts[:-2] + (f"{tgt_parts[-1]}_types",)
    return ".".join(new_parts)


def _render_py_expr(expr: ExprIR) -> str:
    """Render an expression into Python syntax (FR-9-compatible: pure function)."""
    match expr:
        case IntLiteralExprIR(value=value):
            return str(value)
        case ConstRefExprIR(name=name):
            return name
        case UnaryExprIR(op=op, operand=operand):
            return f"({op}{_render_py_expr(operand)})"
        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
            return f"({_render_py_expr(lhs)} {op} {_render_py_expr(rhs)})"


def _resolved_type_width(*, type_ir: TypeDefIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(type_ir, ScalarAliasIR):
        return type_ir.resolved_width
    if isinstance(type_ir, FlagsIR):
        return len(type_ir.fields)
    if isinstance(type_ir, EnumIR):
        return type_ir.resolved_width
    return sum(
        _resolved_field_width(field_type=field.type_ir, repo_type_index=repo_type_index)
        for field in type_ir.fields
    )


def _resolved_field_width(*, field_type: ScalarTypeSpecIR | TypeRefIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(field_type, ScalarTypeSpecIR):
        return field_type.resolved_width
    target = repo_type_index[(field_type.module.python_module_name, field_type.name)]
    return _resolved_type_width(type_ir=target, repo_type_index=repo_type_index)


def _type_byte_count(*, type_ir: TypeDefIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    if isinstance(type_ir, ScalarAliasIR):
        return byte_count(type_ir.resolved_width)
    if isinstance(type_ir, FlagsIR):
        return (len(type_ir.fields) + type_ir.alignment_bits) // 8
    if isinstance(type_ir, EnumIR):
        return byte_count(type_ir.resolved_width)
    field_bytes = sum(
        _field_byte_count(field_ir=f, repo_type_index=repo_type_index) for f in type_ir.fields
    )
    return field_bytes + type_ir.alignment_bits // 8


def _field_byte_count(*, field_ir: StructFieldIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> int:
    match field_ir.type_ir:
        case ScalarTypeSpecIR(resolved_width=resolved_width):
            return byte_count(resolved_width)
        case TypeRefIR(module=mod_ref, name=name):
            target = repo_type_index[(mod_ref.python_module_name, name)]
            return _type_byte_count(type_ir=target, repo_type_index=repo_type_index)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_constant_view(*, const_ir: ConstIR) -> ConstantView:
    return ConstantView(name=const_ir.name, value_expr=_render_py_expr(const_ir.expr))


def _render_py_vec_literal(*, width: int, value: int, base: str) -> str:
    """Render a Python literal honoring the VecConst base."""
    match base:
        case "hex":
            return f"0x{value:0{(width + 3) // 4}X}"
        case "dec":
            return str(value)
        case "bin":
            return f"0b{value:0{width}b}"
        case _:
            raise ValueError(f"unsupported VecConst base: {base!r}")


def build_py_vec_constant_view(*, vec_const_ir: VecConstIR) -> ConstantView:
    return ConstantView(
        name=vec_const_ir.name,
        value_expr=_render_py_vec_literal(
            width=vec_const_ir.width, value=vec_const_ir.value, base=vec_const_ir.base
        ),
    )


def build_scalar_alias_view(*, type_ir: ScalarAliasIR) -> ScalarAliasView:
    width = type_ir.resolved_width
    bc = byte_count(width)
    signed = type_ir.signed
    is_wide = width > 64

    if is_wide:
        max_value = 2**width - 1
        msb_byte_mask = (1 << (width % 8)) - 1 if width % 8 else 0xFF
        return ScalarAliasView(
            kind="scalar_alias",
            class_name=_type_class_name(type_ir.name),
            width=width,
            byte_count=bc,
            signed=signed,
            is_wide=True,
            min_value=0,
            max_value=max_value,
            mask=0,
            sign_bit=0,
            pad_bits=0,
            msb_byte_mask=msb_byte_mask,
        )

    if signed:
        min_value = -(2 ** (width - 1))
        max_value = 2 ** (width - 1) - 1
        mask = (1 << width) - 1
        sign_bit = 1 << (width - 1)
        pad_bits = bc * 8 - width
        return ScalarAliasView(
            kind="scalar_alias",
            class_name=_type_class_name(type_ir.name),
            width=width,
            byte_count=bc,
            signed=True,
            is_wide=False,
            min_value=min_value,
            max_value=max_value,
            mask=mask,
            sign_bit=sign_bit,
            pad_bits=pad_bits,
            msb_byte_mask=0,
        )

    # Narrow unsigned.
    return ScalarAliasView(
        kind="scalar_alias",
        class_name=_type_class_name(type_ir.name),
        width=width,
        byte_count=bc,
        signed=False,
        is_wide=False,
        min_value=0,
        max_value=2**width - 1,
        mask=0,  # narrow unsigned does not use MASK constant
        sign_bit=0,
        pad_bits=0,
        msb_byte_mask=0,
    )


def build_enum_view(*, type_ir: EnumIR) -> EnumView:
    members = tuple(
        EnumMemberView(name=v.name, resolved_value_expr=str(v.resolved_value))
        for v in type_ir.values
    )
    width = type_ir.resolved_width
    return EnumView(
        kind="enum",
        class_name=_type_class_name(type_ir.name),
        enum_class_name=py_enum_class_name(type_ir.name),
        width=width,
        byte_count=byte_count(width),
        mask=(1 << width) - 1,
        first_member_name=type_ir.values[0].name if type_ir.values else "0",
        members=members,
    )


def build_flags_view(*, type_ir: FlagsIR) -> FlagsView:
    num_flags = len(type_ir.fields)
    bc = byte_count(num_flags)
    total_bits = bc * 8
    data_mask = ((1 << num_flags) - 1) << type_ir.alignment_bits
    fields = tuple(
        FlagFieldView(name=flag.name, bit_mask=1 << (total_bits - 1 - i))
        for i, flag in enumerate(type_ir.fields)
    )
    return FlagsView(
        kind="flags",
        class_name=_type_class_name(type_ir.name),
        num_flags=num_flags,
        byte_count=bc,
        total_bits=total_bits,
        data_mask=data_mask,
        alignment_bits=type_ir.alignment_bits,
        flag_mask=(1 << num_flags) - 1,
        fields=fields,
    )


def _build_struct_field_view(
    *,
    field_ir: StructFieldIR,
    repo_type_index: dict[tuple[str, str], TypeDefIR],
    unpack_slice_low: int,
) -> StructFieldView:
    fbc = _field_byte_count(field_ir=field_ir, repo_type_index=repo_type_index)
    pack_bits = fbc * 8
    data_width = _resolved_field_width(field_type=field_ir.type_ir, repo_type_index=repo_type_index)

    # Defaults — overwritten by branches below.
    annotation = ""
    default_expr = ""
    is_struct_ref = is_flags_ref = is_enum_ref = is_scalar_ref = False
    is_narrow_scalar = is_wide_scalar = False
    target_class = ""
    width = 0
    signed = False
    min_value = 0
    max_value = 0
    mask = 0
    sign_bit_value = 0
    pad_bits = 0
    msb_byte_mask = 0
    sign_bit_index = 0
    full_range = 0

    match field_ir.type_ir:
        case TypeRefIR(module=ref_module, name=ref_name):
            target = repo_type_index[(ref_module.python_module_name, ref_name)]
            target_class = _type_class_name(target.name)
            if isinstance(target, StructIR):
                is_struct_ref = True
                annotation = f"{target_class} | None"
                default_expr = f"field(default_factory={target_class})"
            elif isinstance(target, FlagsIR):
                is_flags_ref = True
                annotation = target_class
                default_expr = f"field(default_factory={target_class})"
            elif isinstance(target, EnumIR):
                is_enum_ref = True
                annotation = target_class
                default_expr = f"field(default_factory={target_class})"
            else:
                # ScalarAliasIR
                is_scalar_ref = True
                annotation = target_class
                default_expr = f"field(default_factory={target_class})"
        case ScalarTypeSpecIR(resolved_width=rw, signed=is_signed):
            width = rw
            signed = is_signed
            if rw <= 64:
                is_narrow_scalar = True
                annotation = "int"
                default_expr = "0"
                if is_signed:
                    min_value = -(2 ** (rw - 1))
                    max_value = 2 ** (rw - 1) - 1
                    mask = (1 << rw) - 1
                    sign_bit_value = 1 << (rw - 1)
                    pad_bits = pack_bits - rw
                    sign_bit_index = rw - 1
                    full_range = 1 << rw
                else:
                    max_value = 2**rw - 1
                    mask = (1 << rw) - 1
            else:
                is_wide_scalar = True
                annotation = "bytes"
                default_expr = f'b"\\x00" * {fbc}'
                msb_byte_mask = (1 << (rw % 8)) - 1 if rw % 8 else 0xFF

    return StructFieldView(
        name=field_ir.name,
        annotation=annotation,
        default_expr=default_expr,
        byte_count=fbc,
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
        min_value=min_value,
        max_value=max_value,
        mask=mask,
        sign_bit_value=sign_bit_value,
        pad_bits=pad_bits,
        msb_byte_mask=msb_byte_mask,
        sign_bit_index=sign_bit_index,
        full_range=full_range,
        data_width=data_width,
        data_mask=(1 << data_width) - 1,
        unpack_slice_low=unpack_slice_low,
        hex_width=(data_width + 3) // 4,
    )


def build_struct_view(*, type_ir: StructIR, repo_type_index: dict[tuple[str, str], TypeDefIR]) -> StructView:
    width = _resolved_type_width(type_ir=type_ir, repo_type_index=repo_type_index)

    # First pass: compute each field's data width so we know the LSB
    # position of every slice inside the packed int.
    field_data_widths = [
        _resolved_field_width(field_type=f.type_ir, repo_type_index=repo_type_index)
        for f in type_ir.fields
    ]
    pack_total_width = sum(field_data_widths)

    # Field at index i is at the highest bits not yet consumed by fields 0..i.
    # slice_low(i) = sum of data widths of fields after i.
    cumulative_after: list[int] = []
    running = 0
    for dw in reversed(field_data_widths):
        cumulative_after.append(running)
        running += dw
    cumulative_after.reverse()

    fields = tuple(
        _build_struct_field_view(
            field_ir=f, repo_type_index=repo_type_index, unpack_slice_low=cumulative_after[i],
        )
        for i, f in enumerate(type_ir.fields)
    )
    struct_byte_count = (
        sum(_field_byte_count(field_ir=f, repo_type_index=repo_type_index) for f in type_ir.fields)
        + type_ir.alignment_bits // 8
    )
    return StructView(
        kind="struct",
        class_name=_type_class_name(type_ir.name),
        width=width,
        byte_count=struct_byte_count,
        alignment_bytes=type_ir.alignment_bits // 8,
        fields=fields,
        has_struct_field=any(f.is_struct_ref for f in fields),
        pack_total_width=pack_total_width,
    )


def build_module_view_py(
    *, module: ModuleIR, header: str, repo_type_index: dict[tuple[str, str], TypeDefIR] | None = None,
) -> ModuleView:
    """Build the top-level ``ModuleView`` for one module.

    The ``header`` argument is the pre-rendered comment header
    (already converted to ``#``-prefixed Python comments by the caller
    via ``backends/common/headers.py``). Templates emit it verbatim.
    """
    if repo_type_index is None:
        repo_type_index = {(module.ref.python_module_name, t.name): t for t in module.types}
    has_types = bool(module.types)
    has_structs = any(isinstance(t, StructIR) for t in module.types)
    has_enums = any(isinstance(t, EnumIR) for t in module.types)
    has_flags = any(isinstance(t, FlagsIR) for t in module.types)

    constants = (
        tuple(build_constant_view(const_ir=c) for c in module.constants)
        + tuple(build_py_vec_constant_view(vec_const_ir=v) for v in module.vec_constants)
    )

    types: list[TypeView] = []
    for t in module.types:
        if isinstance(t, ScalarAliasIR):
            types.append(build_scalar_alias_view(type_ir=t))
        elif isinstance(t, StructIR):
            types.append(build_struct_view(type_ir=t, repo_type_index=repo_type_index))
        elif isinstance(t, FlagsIR):
            types.append(build_flags_view(type_ir=t))
        else:
            types.append(build_enum_view(type_ir=t))

    cross_module_imports = _collect_py_cross_module_imports(module=module, repo_type_index=repo_type_index)

    return ModuleView(
        header=header,
        has_types=has_types,
        has_structs=has_structs,
        has_enums=has_enums,
        has_flags=has_flags,
        constants=constants,
        types=tuple(types),
        cross_module_imports=cross_module_imports,
    )


def _collect_py_cross_module_imports(
    *, module: ModuleIR, repo_type_index: dict[tuple[str, str], TypeDefIR],
) -> tuple[PyCrossModuleImportView, ...]:
    """Build PyCrossModuleImportView entries for every direct cross-module type ref.

    Sorted by `(target_types_module, wrapper_class_name)`. Deduplicated.
    """
    seen: set[tuple[str, str]] = set()
    entries: list[PyCrossModuleImportView] = []
    for type_ir in module.types:
        if isinstance(type_ir, StructIR):
            for field in type_ir.fields:
                if isinstance(field.type_ir, TypeRefIR):
                    target_module = field.type_ir.module
                    if target_module.python_module_name == module.ref.python_module_name:
                        continue
                    target = repo_type_index[(target_module.python_module_name, field.type_ir.name)]
                    target_types_module = _py_types_module_path(
                        source_module=module.ref, target_module=target_module
                    )
                    wrapper = _type_class_name(target.name)
                    key = (target_types_module, wrapper)
                    if key in seen:
                        continue
                    seen.add(key)
                    entries.append(
                        PyCrossModuleImportView(
                            target_types_module=target_types_module,
                            wrapper_class_name=wrapper,
                        )
                    )
    entries.sort(key=lambda e: (e.target_types_module, e.wrapper_class_name))
    return tuple(entries)
