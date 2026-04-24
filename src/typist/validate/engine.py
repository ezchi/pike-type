"""Validation entry points."""

from __future__ import annotations

from typist.errors import ValidationError
from typist.ir.nodes import RepoIR, ScalarAliasIR, ScalarTypeSpecIR, StructIR, TypeRefIR


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
                raise ValidationError(f"{module.ref.repo_relative_path}: typist file defines no DSL objects")

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
                        if not isinstance(target, (ScalarAliasIR, StructIR)):
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} "
                                "must reference a scalar alias or struct in this milestone"
                            )
                        continue
                continue
            raise ValidationError(f"{module.ref.repo_relative_path}: unsupported type node {type(type_ir).__name__}")
        _validate_struct_cycles(module=module, type_index=type_index)


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
