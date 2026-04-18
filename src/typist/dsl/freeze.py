"""Freeze mutable DSL state into IR input state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from typist.discovery.module_name import module_basename, module_name_from_path
from typist.dsl.const import Const
from typist.errors import ValidationError
from typist.ir.nodes import ConstIR, IntLiteralExprIR, ModuleIR, ModuleRefIR, RepoIR, SourceSpanIR
from typist.paths import repo_relative_path


@dataclass(frozen=True, slots=True)
class FrozenModule:
    """Intermediate frozen module data before repo assembly."""

    module_ir: ModuleIR
    has_local_definitions: bool


def freeze_module(*, module: ModuleType, module_path: Path, repo_root: Path) -> FrozenModule:
    """Freeze one loaded Python module into constant-only IR."""
    relative_path = repo_relative_path(module_path, repo_root=repo_root)
    module_ref = ModuleRefIR(
        repo_relative_path=str(relative_path),
        python_module_name=module_name_from_path(path=module_path, repo_root=repo_root),
        namespace_parts=tuple(relative_path.with_suffix("").parts),
        basename=module_basename(module_path),
    )
    module_source = SourceSpanIR(path=str(module_path), line=1, column=None)

    local_constants: list[ConstIR] = []
    seen_object_ids: set[int] = set()

    for name, value in module.__dict__.items():
        if name.startswith("__"):
            continue
        if not isinstance(value, Const):
            continue
        if id(value) in seen_object_ids:
            raise ValidationError(f"{module_path}: DSL object bound to multiple top-level names")
        seen_object_ids.add(id(value))
        if Path(value.source.path).resolve() != module_path.resolve():
            continue
        const_source = SourceSpanIR(
            path=value.source.path,
            line=value.source.line,
            column=value.source.column,
        )
        local_constants.append(
            ConstIR(
                name=name,
                source=const_source,
                expr=IntLiteralExprIR(value=value.value, source=const_source),
                resolved_value=value.value,
            )
        )

    local_constants.sort(key=lambda const: (const.source.line, const.name))
    module_ir = ModuleIR(
        ref=module_ref,
        source=module_source,
        constants=tuple(local_constants),
        types=(),
        dependencies=(),
    )
    return FrozenModule(module_ir=module_ir, has_local_definitions=bool(local_constants))


def freeze_repo(*, repo_root: Path, frozen_modules: list[FrozenModule], tool_version: str | None) -> RepoIR:
    """Assemble repository IR from frozen modules."""
    modules = tuple(frozen_module.module_ir for frozen_module in frozen_modules)
    return RepoIR(repo_root=str(repo_root), modules=modules, tool_version=tool_version)
