"""Struct DSL nodes."""

from __future__ import annotations

from dataclasses import dataclass
import re

from typist.dsl.base import DslNode
from typist.dsl.scalar import ScalarType
from typist.dsl.source_info import SourceInfo, capture_source_info
from typist.errors import ValidationError


_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class StructMember:
    """One mutable-DSL struct member."""

    name: str
    type: ScalarType
    source: SourceInfo
    rand: bool


@dataclass(slots=True)
class StructType(DslNode):
    """Packed struct definition."""

    members: list[StructMember]

    def __init__(self, *, source: SourceInfo | None = None) -> None:
        resolved_source = capture_source_info() if source is None else source
        DslNode.__init__(self, source=resolved_source)
        self.members = []

    def add_member(
        self,
        name: str,
        type: ScalarType,
        *,
        rand: bool = True,
        sw: object | None = None,
    ) -> StructType:
        """Append one member and return self for chaining."""
        if sw is not None:
            raise ValidationError("struct member sw= override is not supported in this milestone")
        if not isinstance(name, str) or not _SNAKE_CASE_RE.fullmatch(name):
            raise ValidationError(f"struct member name must be snake_case, got {name!r}")
        if not isinstance(type, ScalarType):
            raise ValidationError("struct member type must be a scalar type in this milestone")
        if not isinstance(rand, bool):
            raise ValidationError(f"struct member rand= must be bool, got {rand.__class__.__name__}")
        self.members.append(
            StructMember(
                name=name,
                type=type,
                source=capture_source_info(),
                rand=rand,
            )
        )
        return self


def Struct() -> StructType:
    """Create a packed struct type."""
    return StructType(source=capture_source_info())
