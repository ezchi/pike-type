"""Flags DSL nodes."""

from __future__ import annotations

from dataclasses import dataclass
import re

from piketype.dsl.base import DslNode
from piketype.dsl.source_info import SourceInfo, capture_source_info
from piketype.errors import ValidationError


_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class FlagMember:
    """One mutable-DSL flag member."""

    name: str
    source: SourceInfo


@dataclass(slots=True)
class FlagsType(DslNode):
    """Packed flags definition."""

    flags: list[FlagMember]

    def __init__(self, *, source: SourceInfo | None = None) -> None:
        resolved_source = capture_source_info() if source is None else source
        DslNode.__init__(self, source=resolved_source)
        self.flags = []

    def add_flag(self, name: str) -> FlagsType:
        """Append one flag and return self for chaining."""
        if not _SNAKE_CASE_RE.fullmatch(name):
            raise ValidationError(f"flag name must be snake_case, got {name!r}")
        if any(f.name == name for f in self.flags):
            raise ValidationError(f"duplicate flag name {name!r}")
        self.flags.append(
            FlagMember(
                name=name,
                source=capture_source_info(),
            )
        )
        return self

    @property
    def width(self) -> int:
        """Number of flags (data bits)."""
        return len(self.flags)


def Flags() -> FlagsType:
    """Create a packed flags type."""
    return FlagsType(source=capture_source_info())
