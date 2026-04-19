"""Freeze mutable DSL state into IR input state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from typist.discovery.module_name import module_basename, module_name_from_path
from typist.dsl.const import Const, ConstExpr
from typist.dsl.scalar import ScalarType
from typist.errors import ValidationError
from typist.ir.nodes import BinaryExprIR, ConstIR, ConstRefExprIR, IntLiteralExprIR, ModuleIR, ModuleRefIR, RepoIR, ScalarAliasIR, SourceSpanIR, UnaryExprIR
from typist.paths import repo_relative_path


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


def freeze_module(*, loaded_module: LoadedModule, definition_map: dict[int, tuple[ModuleRefIR, str]]) -> FrozenModule:
    """Freeze one loaded Python module into constant-only IR."""
    module_source = SourceSpanIR(path=str(loaded_module.module_path), line=1, column=None)
    local_constants: list[ConstIR] = []
    local_types: list[ScalarAliasIR] = []
    seen_local_object_ids: set[int] = set()

    for name, value in loaded_module.module.__dict__.items():
        if name.startswith("__"):
            continue
        if isinstance(value, (Const, ScalarType)):
            if id(value) in seen_local_object_ids:
                raise ValidationError(f"{loaded_module.module_path}: DSL object bound to multiple top-level names")
            seen_local_object_ids.add(id(value))
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
    local_types.sort(key=lambda type_ir: (type_ir.source.line, type_ir.name))
    module_ir = ModuleIR(
        ref=loaded_module.module_ref,
        source=module_source,
        constants=tuple(local_constants),
        types=tuple(local_types),
        dependencies=(),
    )
    return FrozenModule(module_ir=module_ir, has_local_definitions=bool(local_constants or local_types))


def freeze_repo(*, repo_root: Path, frozen_modules: list[FrozenModule], tool_version: str | None) -> RepoIR:
    """Assemble repository IR from frozen modules."""
    modules = tuple(frozen_module.module_ir for frozen_module in frozen_modules)
    return RepoIR(repo_root=str(repo_root), modules=modules, tool_version=tool_version)


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
