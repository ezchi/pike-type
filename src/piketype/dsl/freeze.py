"""Freeze mutable DSL state into IR input state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from piketype.discovery.module_name import module_basename, module_name_from_path
from piketype.dsl.const import Const, ConstExpr, VecConst
from piketype.dsl.enum import EnumType
from piketype.dsl.flags import FlagsType
from piketype.dsl.scalar import ScalarType
from piketype.dsl.struct import StructType
from piketype.errors import ValidationError
from piketype.ir.nodes import (
    BinaryExprIR,
    ConstIR,
    ConstRefExprIR,
    EnumIR,
    EnumValueIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleDependencyIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    SourceSpanIR,
    StructFieldIR,
    StructIR,
    TypeDefIR,
    TypeRefIR,
    UnaryExprIR,
    VecConstIR,
    VecConstImportIR,
    padding_bits as compute_padding_bits,
)
from piketype.paths import repo_relative_path


@dataclass(frozen=True, slots=True)
class LoadedModule:
    """Loaded Python module with derived identity."""

    module: ModuleType
    module_path: Path
    module_ref: ModuleRefIR


@dataclass(frozen=True, slots=True)
class FrozenModule:
    """Intermediate frozen module data before repo assembly."""

    module_ir: ModuleIR
    has_local_definitions: bool


def build_loaded_module(*, module: ModuleType, module_path: Path, repo_root: Path) -> LoadedModule:
    """Build stable module identity for a loaded Python module."""
    relative_path = repo_relative_path(module_path, repo_root=repo_root)
    return LoadedModule(
        module=module,
        module_path=module_path,
        module_ref=ModuleRefIR(
            repo_relative_path=str(relative_path),
            python_module_name=module_name_from_path(path=module_path, repo_root=repo_root),
            namespace_parts=tuple(relative_path.with_suffix("").parts),
            basename=module_basename(module_path),
        ),
    )


def build_const_definition_map(*, loaded_modules: list[LoadedModule]) -> dict[int, tuple[ModuleRefIR, str]]:
    """Build a stable mapping from Const object id to its defining module/name."""
    definition_map: dict[int, tuple[ModuleRefIR, str]] = {}
    for loaded in loaded_modules:
        seen_object_ids: set[int] = set()
        for name, value in loaded.module.__dict__.items():
            if name.startswith("__"):
                continue
            if not isinstance(value, Const):
                continue
            if id(value) in seen_object_ids:
                raise ValidationError(f"{loaded.module_path}: DSL object bound to multiple top-level names")
            seen_object_ids.add(id(value))
            if Path(value.source.path).resolve() != loaded.module_path.resolve():
                continue
            definition_map[id(value)] = (loaded.module_ref, name)
    return definition_map


def build_vec_const_definition_map(*, loaded_modules: list[LoadedModule]) -> dict[int, tuple[ModuleRefIR, str]]:
    """Build a stable mapping from VecConst object id to its defining module/name."""
    definition_map: dict[int, tuple[ModuleRefIR, str]] = {}
    for loaded in loaded_modules:
        seen_object_ids: set[int] = set()
        for name, value in loaded.module.__dict__.items():
            if name.startswith("__"):
                continue
            if not isinstance(value, VecConst):
                continue
            if id(value) in seen_object_ids:
                raise ValidationError(f"{loaded.module_path}: DSL object bound to multiple top-level names")
            seen_object_ids.add(id(value))
            if Path(value.source.path).resolve() != loaded.module_path.resolve():
                continue
            definition_map[id(value)] = (loaded.module_ref, name)
    return definition_map


def build_type_definition_map(*, loaded_modules: list[LoadedModule]) -> dict[int, tuple[ModuleRefIR, str]]:
    """Build a stable mapping from top-level type object id to defining module/name."""
    definition_map: dict[int, tuple[ModuleRefIR, str]] = {}
    for loaded in loaded_modules:
        seen_object_ids: set[int] = set()
        for name, value in loaded.module.__dict__.items():
            if name.startswith("__"):
                continue
            if not isinstance(value, (ScalarType, StructType, FlagsType, EnumType)):
                continue
            if id(value) in seen_object_ids:
                raise ValidationError(f"{loaded.module_path}: DSL object bound to multiple top-level names")
            seen_object_ids.add(id(value))
            if Path(value.source.path).resolve() != loaded.module_path.resolve():
                continue
            definition_map[id(value)] = (loaded.module_ref, name)
    return definition_map


def freeze_module(
    *,
    loaded_module: LoadedModule,
    definition_map: dict[int, tuple[ModuleRefIR, str]],
    type_definition_map: dict[int, tuple[ModuleRefIR, str]],
    vec_const_definition_map: dict[int, tuple[ModuleRefIR, str]] | None = None,
) -> FrozenModule:
    """Freeze one loaded Python module into constant-only IR."""
    if vec_const_definition_map is None:
        vec_const_definition_map = {}
    module_source = SourceSpanIR(path=str(loaded_module.module_path), line=1, column=None)
    local_constants: list[ConstIR] = []
    local_vec_constants: list[VecConstIR] = []
    local_vec_const_imports: list[VecConstImportIR] = []
    local_types: list[TypeDefIR] = []
    seen_local_object_ids: set[int] = set()

    for name, value in loaded_module.module.__dict__.items():
        if name.startswith("__"):
            continue
        if isinstance(value, (Const, VecConst, ScalarType, StructType, FlagsType, EnumType)):
            if id(value) in seen_local_object_ids:
                raise ValidationError(f"{loaded_module.module_path}: DSL object bound to multiple top-level names")
            seen_local_object_ids.add(id(value))
        if isinstance(value, VecConst):
            mapped = vec_const_definition_map.get(id(value))
            if mapped is None or mapped[0].python_module_name == loaded_module.module_ref.python_module_name:
                # First-sighting (this module defines it).
                local_vec_constants.append(
                    _freeze_vec_const(
                        name=name,
                        vec_const=value,
                        const_definition_map=definition_map,
                    )
                )
            else:
                # Cross-module sighting: this module imports the VecConst from another.
                local_vec_const_imports.append(
                    VecConstImportIR(
                        target_module_ref=mapped[0],
                        symbol_name=mapped[1],
                    )
                )
            continue
        if not isinstance(value, Const):
            if isinstance(value, ScalarType):
                if Path(value.source.path).resolve() != loaded_module.module_path.resolve():
                    continue
                type_source = SourceSpanIR(
                    path=value.source.path,
                    line=value.source.line,
                    column=value.source.column,
                )
                local_types.append(
                    ScalarAliasIR(
                        name=name,
                        source=type_source,
                        state_kind=value.state_kind,
                        signed=value.signed,
                        width_expr=_freeze_expr(expr=value.width_expr, definition_map=definition_map),
                        resolved_width=value.width_value,
                    )
                )
            elif isinstance(value, StructType):
                if Path(value.source.path).resolve() != loaded_module.module_path.resolve():
                    continue
                struct_source = SourceSpanIR(
                    path=value.source.path,
                    line=value.source.line,
                    column=value.source.column,
                )
                local_types.append(
                    StructIR(
                        name=name,
                        source=struct_source,
                        fields=tuple(
                            _freeze_struct_field(
                                member=member,
                                definition_map=definition_map,
                                type_definition_map=type_definition_map,
                            )
                            for member in value.members
                        ),
                        alignment_bits=_compute_alignment_bits(value),
                    )
                )
            elif isinstance(value, FlagsType):
                if Path(value.source.path).resolve() != loaded_module.module_path.resolve():
                    continue
                flags_source = SourceSpanIR(
                    path=value.source.path,
                    line=value.source.line,
                    column=value.source.column,
                )
                local_types.append(
                    FlagsIR(
                        name=name,
                        source=flags_source,
                        fields=tuple(
                            FlagFieldIR(
                                name=flag.name,
                                source=SourceSpanIR(
                                    path=flag.source.path,
                                    line=flag.source.line,
                                    column=flag.source.column,
                                ),
                            )
                            for flag in value.flags
                        ),
                        alignment_bits=(-len(value.flags)) % 8,
                    )
                )
            elif isinstance(value, EnumType):
                if Path(value.source.path).resolve() != loaded_module.module_path.resolve():
                    continue
                enum_source = SourceSpanIR(
                    path=value.source.path,
                    line=value.source.line,
                    column=value.source.column,
                )
                resolved_values = _resolve_enum_values(value)
                if value._explicit_width is not None:
                    resolved_width = value._explicit_width
                elif not resolved_values:
                    resolved_width = 0
                else:
                    max_val = max(v for _, v in resolved_values)
                    resolved_width = max(1, max_val.bit_length())
                local_types.append(
                    EnumIR(
                        name=name,
                        source=enum_source,
                        width_expr=IntLiteralExprIR(
                            value=resolved_width,
                            source=enum_source,
                        ),
                        resolved_width=resolved_width,
                        values=tuple(
                            EnumValueIR(
                                name=member_name,
                                source=SourceSpanIR(
                                    path=value.members[idx].source.path,
                                    line=value.members[idx].source.line,
                                    column=value.members[idx].source.column,
                                ),
                                expr=IntLiteralExprIR(
                                    value=resolved_val,
                                    source=SourceSpanIR(
                                        path=value.members[idx].source.path,
                                        line=value.members[idx].source.line,
                                        column=value.members[idx].source.column,
                                    ),
                                ),
                                resolved_value=resolved_val,
                            )
                            for idx, (member_name, resolved_val) in enumerate(resolved_values)
                        ),
                    )
                )
            continue
        if Path(value.source.path).resolve() != loaded_module.module_path.resolve():
            continue
        const_source = SourceSpanIR(
            path=value.source.path,
            line=value.source.line,
            column=value.source.column,
        )
        resolved_signed, resolved_width = _resolve_const_storage(
            value=value.value,
            signed=value.signed,
            width=value.width,
        )
        local_constants.append(
            ConstIR(
                name=name,
                source=const_source,
                expr=_freeze_expr(expr=value.expr, definition_map=definition_map),
                resolved_value=value.value,
                resolved_signed=resolved_signed,
                resolved_width=resolved_width,
            )
        )

    local_constants.sort(key=lambda const: (const.source.line, const.name))
    local_vec_constants.sort(key=lambda v: (v.source.line, v.name))
    local_vec_const_imports.sort(key=lambda v: (v.target_module_ref.python_module_name, v.symbol_name))
    local_types.sort(key=lambda type_ir: (type_ir.source.line, type_ir.name))
    module_ir = ModuleIR(
        ref=loaded_module.module_ref,
        source=module_source,
        constants=tuple(local_constants),
        types=tuple(local_types),
        dependencies=(),
        vec_constants=tuple(local_vec_constants),
        vec_const_imports=tuple(local_vec_const_imports),
    )
    # Re-create with populated dependencies (frozen dataclasses cannot be mutated).
    module_ir = ModuleIR(
        ref=module_ir.ref,
        source=module_ir.source,
        constants=module_ir.constants,
        types=module_ir.types,
        dependencies=_collect_module_dependencies(module_ir),
        vec_constants=module_ir.vec_constants,
        vec_const_imports=module_ir.vec_const_imports,
    )
    return FrozenModule(
        module_ir=module_ir,
        has_local_definitions=bool(local_constants or local_types or local_vec_constants),
    )


def freeze_repo(*, repo_root: Path, frozen_modules: list[FrozenModule], tool_version: str | None) -> RepoIR:
    """Assemble repository IR from frozen modules."""
    modules = tuple(frozen_module.module_ir for frozen_module in frozen_modules)
    return RepoIR(repo_root=str(repo_root), modules=modules, tool_version=tool_version)


def _collect_module_dependencies(module_ir: ModuleIR) -> tuple[ModuleDependencyIR, ...]:
    """Walk module IR and collect cross-module type/const reference dependencies.

    Returns a deterministically-ordered tuple of `ModuleDependencyIR` entries,
    one per distinct (target_python_module_name, kind) pair.

    Sources of cross-module references:
    - Every `TypeRefIR` reachable from struct fields, scalar alias `width_expr`,
      struct field `width_expr`, enum value `expr`, constant `expr`. Cross-module
      means `type_ref.module.python_module_name != module_ir.ref.python_module_name`.
    - Every `ConstRefExprIR` reachable from any `ExprIR` traversal.

    Note (R8 invariant): cross-module `TypeRefIR` always points to a top-level
    named DSL type, never `ScalarTypeSpecIR`. Only named bindings are importable
    across modules, and `_freeze_field_type` only emits `TypeRefIR` for objects
    in `type_definition_map`.
    """
    self_module = module_ir.ref.python_module_name
    targets: set[tuple[str, str]] = set()  # (target_python_module_name, kind)
    target_refs: dict[tuple[str, str], ModuleRefIR] = {}

    def visit_expr(expr: object) -> None:
        if isinstance(expr, ConstRefExprIR):
            if expr.module.python_module_name != self_module:
                key = (expr.module.python_module_name, "const_ref")
                targets.add(key)
                target_refs[key] = expr.module
        elif isinstance(expr, UnaryExprIR):
            visit_expr(expr.operand)
        elif isinstance(expr, BinaryExprIR):
            visit_expr(expr.lhs)
            visit_expr(expr.rhs)
        # IntLiteralExprIR has no children.

    def add_type_ref(ref: TypeRefIR) -> None:
        if ref.module.python_module_name != self_module:
            key = (ref.module.python_module_name, "type_ref")
            targets.add(key)
            target_refs[key] = ref.module

    # Constants.
    for const in module_ir.constants:
        visit_expr(const.expr)

    # VecConst imports (cross-module sightings → vec_const_import dep edge).
    for vci in module_ir.vec_const_imports:
        if vci.target_module_ref.python_module_name != self_module:
            key = (vci.target_module_ref.python_module_name, "vec_const_import")
            targets.add(key)
            target_refs[key] = vci.target_module_ref

    # Types.
    for type_ir in module_ir.types:
        if isinstance(type_ir, ScalarAliasIR):
            visit_expr(type_ir.width_expr)
        elif isinstance(type_ir, StructIR):
            for field in type_ir.fields:
                if isinstance(field.type_ir, TypeRefIR):
                    add_type_ref(field.type_ir)
                elif isinstance(field.type_ir, ScalarTypeSpecIR):
                    visit_expr(field.type_ir.width_expr)
        elif isinstance(type_ir, EnumIR):
            visit_expr(type_ir.width_expr)
            for value in type_ir.values:
                visit_expr(value.expr)
        # FlagsIR has no expressions or type refs.

    return tuple(
        ModuleDependencyIR(target=target_refs[key], kind=key[1])
        for key in sorted(targets)
    )


def _serialized_width_from_dsl(struct_type: StructType) -> int:
    """Compute serialized bit width of a struct from mutable DSL objects (recursive)."""
    from piketype.ir.nodes import byte_count

    total = 0
    for member in struct_type.members:
        if isinstance(member.type, ScalarType):
            total += byte_count(member.type.width_value) * 8
        elif isinstance(member.type, StructType):
            inner_natural = _serialized_width_from_dsl(member.type)
            inner_align = _compute_alignment_bits(member.type)
            total += inner_natural + inner_align
        elif isinstance(member.type, FlagsType):
            total += byte_count(len(member.type.flags)) * 8
        elif isinstance(member.type, EnumType):
            total += byte_count(member.type.width) * 8
    return total


def _compute_alignment_bits(struct_type: StructType) -> int:
    """Compute trailing alignment padding bits for a struct from DSL objects."""
    if struct_type._alignment is None:
        return 0
    natural_width = _serialized_width_from_dsl(struct_type)
    return (-natural_width) % struct_type._alignment


def _freeze_struct_field(
    *,
    member,
    definition_map: dict[int, tuple[ModuleRefIR, str]],
    type_definition_map: dict[int, tuple[ModuleRefIR, str]],
) -> StructFieldIR:
    """Freeze one struct field."""
    field_source = SourceSpanIR(path=member.source.path, line=member.source.line, column=member.source.column)
    type_ir = _freeze_field_type(
        type_obj=member.type,
        definition_map=definition_map,
        type_definition_map=type_definition_map,
    )
    if isinstance(type_ir, ScalarTypeSpecIR):
        pad = compute_padding_bits(type_ir.resolved_width)
    elif isinstance(type_ir, TypeRefIR):
        if isinstance(member.type, ScalarType):
            pad = compute_padding_bits(member.type.width_value)
        elif isinstance(member.type, EnumType):
            pad = compute_padding_bits(member.type.width)
        else:
            pad = 0
    else:
        pad = 0
    return StructFieldIR(
        name=member.name,
        source=field_source,
        type_ir=type_ir,
        rand=member.rand,
        padding_bits=pad,
    )


def _freeze_field_type(
    *,
    type_obj: ScalarType | StructType | FlagsType | EnumType,
    definition_map: dict[int, tuple[ModuleRefIR, str]],
    type_definition_map: dict[int, tuple[ModuleRefIR, str]],
):
    """Freeze a struct field type."""
    source = SourceSpanIR(path=type_obj.source.path, line=type_obj.source.line, column=type_obj.source.column)
    resolved = type_definition_map.get(id(type_obj))
    if resolved is not None:
        module_ref, type_name = resolved
        return TypeRefIR(module=module_ref, name=type_name, source=source)
    if isinstance(type_obj, StructType):
        raise ValidationError("inline anonymous struct member types are not supported in this milestone")
    if isinstance(type_obj, FlagsType):
        raise ValidationError("inline anonymous flags member types are not supported in this milestone")
    if isinstance(type_obj, EnumType):
        raise ValidationError("inline anonymous enum member types are not supported in this milestone")
    return ScalarTypeSpecIR(
        source=source,
        state_kind=type_obj.state_kind,
        signed=type_obj.signed,
        width_expr=_freeze_expr(expr=type_obj.width_expr, definition_map=definition_map),
        resolved_width=type_obj.width_value,
    )


def _freeze_expr(*, expr: ConstExpr, definition_map: dict[int, tuple[ModuleRefIR, str]]):
    """Freeze a runtime constant expression into IR."""
    source = SourceSpanIR(path=expr.source.path, line=expr.source.line, column=expr.source.column)
    match expr.kind:
        case "int_literal":
            if expr.value is None:
                raise ValidationError("malformed literal expression")
            return IntLiteralExprIR(value=expr.value, source=source)
        case "const_ref":
            if expr.target is None:
                raise ValidationError("malformed const reference expression")
            try:
                module_ref, const_name = definition_map[id(expr.target)]
            except KeyError as exc:
                raise ValidationError("unresolved Const reference in expression") from exc
            return ConstRefExprIR(module=module_ref, name=const_name, source=source)
        case "unary_op":
            if expr.op is None or expr.operand is None:
                raise ValidationError("malformed unary expression")
            return UnaryExprIR(
                op=expr.op,
                operand=_freeze_expr(expr=expr.operand, definition_map=definition_map),
                source=source,
            )
        case "binary_op":
            if expr.op is None or expr.lhs is None or expr.rhs is None:
                raise ValidationError("malformed binary expression")
            return BinaryExprIR(
                op=expr.op,
                lhs=_freeze_expr(expr=expr.lhs, definition_map=definition_map),
                rhs=_freeze_expr(expr=expr.rhs, definition_map=definition_map),
                source=source,
            )
        case _:
            raise ValidationError(f"unsupported Const expression kind {expr.kind}")


def _resolve_const_storage(*, value: int, signed: bool | None, width: int | None) -> tuple[bool, int]:
    """Resolve effective signedness and width for a constant."""
    int32_min = -(2**31)
    int32_max = 2**31 - 1
    uint32_max = 2**32 - 1
    int64_min = -(2**63)
    int64_max = 2**63 - 1
    uint64_max = 2**64 - 1

    if signed is None:
        if value < 0:
            inferred_signed = True
            inferred_width = 32 if int32_min <= value <= int32_max else 64
        elif value <= int32_max:
            inferred_signed = True
            inferred_width = 32
        elif value <= uint32_max:
            inferred_signed = False
            inferred_width = 32
        elif value <= int64_max:
            inferred_signed = True
            inferred_width = 64
        elif value <= uint64_max:
            inferred_signed = False
            inferred_width = 64
        else:
            raise ValidationError(f"constant value out of supported range [{int64_min}, {uint64_max}]")
    elif signed:
        inferred_signed = True
        if width is None:
            if int32_min <= value <= int32_max:
                inferred_width = 32
            elif int64_min <= value <= int64_max:
                inferred_width = 64
            else:
                raise ValidationError(f"signed constant value out of supported range [{int64_min}, {int64_max}]")
        else:
            inferred_width = width
    else:
        inferred_signed = False
        if width is None:
            if 0 <= value <= uint32_max:
                inferred_width = 32
            elif 0 <= value <= uint64_max:
                inferred_width = 64
            else:
                raise ValidationError(f"unsigned constant value out of supported range [0, {uint64_max}]")
        else:
            inferred_width = width

    effective_width = inferred_width if width is None else width
    _validate_const_storage(value=value, signed=inferred_signed, width=effective_width)
    return (inferred_signed, effective_width)


def _freeze_vec_const(
    *,
    name: str,
    vec_const: VecConst,
    const_definition_map: dict[int, tuple[ModuleRefIR, str]],
) -> VecConstIR:
    """Freeze a `VecConst` DSL object into a `VecConstIR`.

    Resolves `width_expr` and `value_expr` to ints using the const-expression
    evaluator (with the cross-module map so a VecConst whose value references
    a `Const` in another module resolves correctly), then validates width
    range (1..64) and overflow (0 <= value <= 2**width - 1).
    """
    width = _eval_expr_int(expr=vec_const.width_expr, definition_map=const_definition_map)
    value = _eval_expr_int(expr=vec_const.value_expr, definition_map=const_definition_map)
    source = SourceSpanIR(
        path=vec_const.source.path,
        line=vec_const.source.line,
        column=vec_const.source.column,
    )
    return _freeze_vec_const_storage(
        width=width,
        value=value,
        base=vec_const.base,
        source=source,
        name=name,
    )


def _freeze_vec_const_storage(
    *,
    width: int,
    value: int,
    base: str,
    source: SourceSpanIR,
    name: str,
) -> VecConstIR:
    """Validate and construct a frozen VecConstIR.

    Errors carry the offending value, the declared width, and the formula
    `2**N - 1` per spec FR-7's three-substring contract.
    """
    if width < 1 or width > 64:
        raise ValidationError(
            f"VecConst({name!r}) width {width} out of supported range 1..64"
        )
    if value < 0:
        raise ValidationError(
            f"VecConst({name!r}, width={width}) negative value {value} rejected; "
            f"value must satisfy 0 <= value <= 2**{width} - 1 (= {2**width - 1})"
        )
    if value > 2**width - 1:
        raise ValidationError(
            f"VecConst({name!r}, width={width}) value {value} overflows; "
            f"value must satisfy 0 <= value <= 2**{width} - 1 (= {2**width - 1})"
        )
    return VecConstIR(name=name, source=source, width=width, value=value, base=base)


def _eval_expr_int(*, expr: ConstExpr, definition_map: dict[int, tuple[ModuleRefIR, str]]) -> int:
    """Evaluate a runtime ConstExpr to an int.

    Uses the same recursive evaluator as Const's freeze pipeline. The
    `definition_map` is only needed if the expression contains `const_ref`
    nodes that must resolve to defining-module constants — in that case we
    walk through the target Const's value (already resolved at DSL-construction
    time per `Const.__init__`).
    """
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
            inner = _eval_expr_int(expr=expr.operand, definition_map=definition_map)
            match expr.op:
                case "+":
                    return +inner
                case "-":
                    return -inner
                case "~":
                    return ~inner
                case _:
                    raise ValidationError(f"unsupported unary operator {expr.op}")
        case "binary_op":
            if expr.op is None or expr.lhs is None or expr.rhs is None:
                raise ValidationError("malformed binary expression")
            lhs = _eval_expr_int(expr=expr.lhs, definition_map=definition_map)
            rhs = _eval_expr_int(expr=expr.rhs, definition_map=definition_map)
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
            raise ValidationError(f"unsupported VecConst expression kind {expr.kind}")


def _resolve_enum_values(enum_type: EnumType) -> list[tuple[str, int]]:
    """Resolve auto-fill values for an enum, returning (name, resolved_value) pairs."""
    resolved: list[tuple[str, int]] = []
    prev_val = -1
    for member in enum_type.members:
        if member.value is not None:
            val = member.value
        else:
            val = prev_val + 1
        resolved.append((member.name, val))
        prev_val = val
    return resolved


def _validate_const_storage(*, value: int, signed: bool, width: int) -> None:
    """Validate that a constant value fits its resolved signedness and width."""
    if width not in (32, 64):
        raise ValidationError(f"constant width must be 32 or 64, got {width}")
    if signed:
        minimum = -(2 ** (width - 1))
        maximum = 2 ** (width - 1) - 1
    else:
        minimum = 0
        maximum = 2**width - 1
    if value < minimum or value > maximum:
        kind = "signed" if signed else "unsigned"
        raise ValidationError(f"{kind} {width}-bit constant value {value} is out of range [{minimum}, {maximum}]")
