"""Validation entry points."""

from __future__ import annotations

from typist.errors import ValidationError
from typist.ir.nodes import RepoIR

def validate_repo(repo: RepoIR) -> None:
    """Validate the frozen repository IR."""
    for module in repo.modules:
        if not module.constants:
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
