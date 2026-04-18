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
