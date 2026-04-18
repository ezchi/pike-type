"""Constant DSL node."""

from __future__ import annotations

from dataclasses import dataclass

from typist.dsl.base import DslNode
from typist.dsl.source_info import capture_source_info
from typist.errors import ValidationError


@dataclass(slots=True)
class Const(DslNode):
    """Top-level integer constant."""

    value: int

    def __init__(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValidationError(f"Const() requires an integer literal, got {type(value).__name__}")
        DslNode.__init__(self, source=capture_source_info())
        self.value = value
