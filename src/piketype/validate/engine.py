"""Validation entry points."""

from __future__ import annotations

from piketype.errors import ValidationError
import re

from piketype.ir.nodes import EnumIR, FlagsIR, ModuleIR, RepoIR, ScalarAliasIR, ScalarTypeSpecIR, StructIR, TypeRefIR


_UPPER_CASE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


_FLAGS_RESERVED_API_NAMES = frozenset({"value", "to_bytes", "from_bytes", "clone", "width", "byte_count"})


def validate_repo(repo: RepoIR) -> None:
    """Validate the frozen repository IR."""
    type_index = {
        (module.ref.python_module_name, type_ir.name): type_ir
        for module in repo.modules
        for type_ir in module.types
    }
    for module in repo.modules:
        if not module.constants:
            if not module.types:
                raise ValidationError(f"{module.ref.repo_relative_path}: piketype file defines no DSL objects")

        seen_names: set[str] = set()
        for const in module.constants:
            if const.name in seen_names:
                raise ValidationError(f"{module.ref.repo_relative_path}: duplicate constant name {const.name}")
            seen_names.add(const.name)
            _validate_const_storage(
                value=const.resolved_value,
                signed=const.resolved_signed,
                width=const.resolved_width,
                module_path=module.ref.repo_relative_path,
                const_name=const.name,
            )
        seen_type_names: set[str] = set()
        for type_ir in module.types:
            if type_ir.name in seen_names or type_ir.name in seen_type_names:
                raise ValidationError(f"{module.ref.repo_relative_path}: duplicate type name {type_ir.name}")
            seen_type_names.add(type_ir.name)
            if not type_ir.name.endswith("_t"):
                raise ValidationError(f"{module.ref.repo_relative_path}: type {type_ir.name} must end with _t")
            if isinstance(type_ir, ScalarAliasIR):
                if type_ir.resolved_width <= 0:
                    raise ValidationError(f"{module.ref.repo_relative_path}: type {type_ir.name} width must be positive")
                continue
            if isinstance(type_ir, StructIR):
                if not type_ir.fields:
                    raise ValidationError(f"{module.ref.repo_relative_path}: struct {type_ir.name} must have at least one field")
                seen_field_names: set[str] = set()
                for field in type_ir.fields:
                    if field.name in seen_field_names:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: struct {type_ir.name} has duplicate field {field.name}"
                        )
                    seen_field_names.add(field.name)
                    if isinstance(field.type_ir, ScalarTypeSpecIR):
                        if field.type_ir.resolved_width <= 0:
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} width must be positive"
                            )
                        continue
                    if isinstance(field.type_ir, TypeRefIR):
                        if field.type_ir.module.python_module_name != module.ref.python_module_name:
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} "
                                "cross-module type references are not supported in this milestone"
                            )
                        target = type_index.get((field.type_ir.module.python_module_name, field.type_ir.name))
                        if target is None:
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} "
                                f"references unknown type {field.type_ir.name}"
                            )
                        if not isinstance(target, (ScalarAliasIR, StructIR, FlagsIR)):
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} "
                                "must reference a scalar alias, struct, or flags in this milestone"
                            )
                        continue
                continue
            if isinstance(type_ir, FlagsIR):
                if not type_ir.fields:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: flags {type_ir.name} must have at least one flag"
                    )
                if len(type_ir.fields) > 64:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: flags {type_ir.name} has {len(type_ir.fields)} flags, "
                        "maximum is 64"
                    )
                seen_flag_names: set[str] = set()
                for flag in type_ir.fields:
                    if flag.name in seen_flag_names:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: flags {type_ir.name} has duplicate flag {flag.name}"
                        )
                    seen_flag_names.add(flag.name)
                    if flag.name.endswith("_pad"):
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: flags {type_ir.name} "
                            f"flag '{flag.name}' uses reserved '_pad' suffix"
                        )
                    if flag.name in _FLAGS_RESERVED_API_NAMES:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: flags {type_ir.name} "
                            f"flag '{flag.name}' collides with generated class API name"
                        )
                continue
            if isinstance(type_ir, EnumIR):
                if not type_ir.values:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} must have at least one value"
                    )
                if type_ir.resolved_width <= 0:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} width must be positive"
                    )
                if type_ir.resolved_width > 64:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} width {type_ir.resolved_width} exceeds maximum 64"
                    )
                seen_value_names: set[str] = set()
                seen_resolved_values: set[int] = set()
                for enum_val in type_ir.values:
                    if not _UPPER_CASE_RE.fullmatch(enum_val.name):
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"value name {enum_val.name!r} must be UPPER_CASE"
                        )
                    if enum_val.name in seen_value_names:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"has duplicate value name {enum_val.name!r}"
                        )
                    seen_value_names.add(enum_val.name)
                    if enum_val.resolved_value in seen_resolved_values:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"has duplicate resolved value {enum_val.resolved_value}"
                        )
                    seen_resolved_values.add(enum_val.resolved_value)
                    if enum_val.resolved_value < 0:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"value {enum_val.name} has negative value {enum_val.resolved_value}"
                        )
                    if enum_val.resolved_value >= 2**type_ir.resolved_width:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"value {enum_val.name}={enum_val.resolved_value} does not fit in {type_ir.resolved_width} bits"
                        )
                continue
            raise ValidationError(f"{module.ref.repo_relative_path}: unsupported type node {type(type_ir).__name__}")
        _validate_struct_cycles(module=module, type_index=type_index)
        _validate_pad_suffix_reservation(module=module)
        _validate_signed_width_constraint(module=module, type_index=type_index)
        _validate_generated_identifier_collision(module=module)
        _validate_alignment_bits(module=module)
        _validate_enum_literal_collision(module=module)


def _validate_const_storage(*, value: int, signed: bool, width: int, module_path: str, const_name: str) -> None:
    """Validate that constant IR storage is internally consistent."""
    if width not in (32, 64):
        raise ValidationError(f"{module_path}: constant {const_name} has unsupported width {width}")
    if signed:
        minimum = -(2 ** (width - 1))
        maximum = 2 ** (width - 1) - 1
    else:
        minimum = 0
        maximum = 2**width - 1
    if value < minimum or value > maximum:
        raise ValidationError(
            f"{module_path}: constant {const_name} out of supported range for "
            f"{'signed' if signed else 'unsigned'} {width}-bit storage [{minimum}, {maximum}]"
        )


def _validate_struct_cycles(*, module, type_index: dict[tuple[str, str], object]) -> None:
    """Reject direct or indirect same-module struct cycles."""
    struct_graph: dict[str, set[str]] = {}
    for type_ir in module.types:
        if not isinstance(type_ir, StructIR):
            continue
        deps: set[str] = set()
        for field in type_ir.fields:
            if not isinstance(field.type_ir, TypeRefIR):
                continue
            target = type_index.get((field.type_ir.module.python_module_name, field.type_ir.name))
            if isinstance(target, StructIR):
                deps.add(target.name)
        struct_graph[type_ir.name] = deps

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            raise ValidationError(f"{module.ref.repo_relative_path}: recursive struct dependency detected at {name}")
        visiting.add(name)
        for dep in struct_graph.get(name, set()):
            visit(dep)
        visiting.remove(name)
        visited.add(name)

    for name in struct_graph:
        visit(name)


def _validate_pad_suffix_reservation(*, module: ModuleIR) -> None:
    """FR-11: Reject struct fields whose name ends with _pad."""
    for type_ir in module.types:
        if not isinstance(type_ir, StructIR):
            continue
        for field in type_ir.fields:
            if field.name.endswith("_pad"):
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: struct {type_ir.name} "
                    f"field '{field.name}' uses reserved '_pad' suffix"
                )


def _validate_signed_width_constraint(
    *,
    module: ModuleIR,
    type_index: dict[tuple[str, str], object],
) -> None:
    """FR-13: Reject signed scalars with width > 64."""
    for type_ir in module.types:
        if isinstance(type_ir, ScalarAliasIR):
            if type_ir.signed and type_ir.resolved_width > 64:
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: signed scalar {type_ir.name} "
                    f"width {type_ir.resolved_width} exceeds maximum 64-bit signed width"
                )
        elif isinstance(type_ir, StructIR):
            for field in type_ir.fields:
                if isinstance(field.type_ir, ScalarTypeSpecIR):
                    if field.type_ir.signed and field.type_ir.resolved_width > 64:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: struct {type_ir.name} "
                            f"signed field '{field.name}' width {field.type_ir.resolved_width} "
                            "exceeds maximum 64-bit signed width"
                        )


def _validate_generated_identifier_collision(*, module: ModuleIR) -> None:
    """FR-14: Reject modules where constant names collide with generated identifiers."""
    reserved: dict[str, str] = {}
    for type_ir in module.types:
        base = type_ir.name[:-2] if type_ir.name.endswith("_t") else type_ir.name
        upper_base = base.upper()
        for ident in (
            f"LP_{upper_base}_WIDTH",
            f"LP_{upper_base}_BYTE_COUNT",
            f"pack_{base}",
            f"unpack_{base}",
        ):
            reserved[ident] = type_ir.name
    const_names = {const.name for const in module.constants}
    for const_name in const_names:
        if const_name in reserved:
            raise ValidationError(
                f"{module.ref.repo_relative_path}: constant '{const_name}' "
                f"collides with generated identifier for type '{reserved[const_name]}'"
            )
    for type_ir in module.types:
        if isinstance(type_ir, EnumIR):
            for enum_val in type_ir.values:
                if enum_val.name in reserved:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                        f"value '{enum_val.name}' collides with generated identifier for type '{reserved[enum_val.name]}'"
                    )


def _validate_alignment_bits(*, module: ModuleIR) -> None:
    """Validate that struct alignment_bits is a multiple of 8."""
    for type_ir in module.types:
        if not isinstance(type_ir, StructIR):
            continue
        if type_ir.alignment_bits > 0 and type_ir.alignment_bits % 8 != 0:
            raise ValidationError(
                f"{module.ref.repo_relative_path}: struct {type_ir.name} "
                f"alignment_bits {type_ir.alignment_bits} is not a multiple of 8"
            )


def _validate_enum_literal_collision(*, module: ModuleIR) -> None:
    """FR-17: Reject enum value names that collide across enums or with constants."""
    const_names = {const.name for const in module.constants}
    all_enum_value_names: dict[str, str] = {}
    for type_ir in module.types:
        if not isinstance(type_ir, EnumIR):
            continue
        for enum_val in type_ir.values:
            if enum_val.name in const_names:
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                    f"value '{enum_val.name}' collides with constant name in same module"
                )
            if enum_val.name in all_enum_value_names:
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                    f"value '{enum_val.name}' collides with value in enum {all_enum_value_names[enum_val.name]}"
                )
            all_enum_value_names[enum_val.name] = type_ir.name
