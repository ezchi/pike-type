"""Enum DSL nodes."""

from __future__ import annotations

from dataclasses import dataclass
import re

from piketype.dsl.base import DslNode
from piketype.dsl.source_info import SourceInfo, capture_source_info
from piketype.errors import ValidationError


_UPPER_CASE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True, slots=True)
class EnumMember:
    """One mutable-DSL enum member."""

    name: str
    source: SourceInfo
    value: int | None


@dataclass(slots=True)
class EnumType(DslNode):
    """Enum type definition."""

    members: list[EnumMember]
    _explicit_width: int | None

    def __init__(self, *, width: int | None = None, source: SourceInfo | None = None) -> None:
        resolved_source = capture_source_info() if source is None else source
        DslNode.__init__(self, source=resolved_source)
        if width is not None:
            if not isinstance(width, int):
                raise ValidationError(f"enum width must be an integer, got {type(width).__name__}")
            if width < 1 or width > 64:
                raise ValidationError(f"enum width must be in [1, 64], got {width}")
        self.members = []
        self._explicit_width = width

    def add_value(self, name: str, value: int | None = None) -> EnumType:
        """Append one enumerator and return self for chaining."""
        if not _UPPER_CASE_RE.fullmatch(name):
            raise ValidationError(f"enum value name must be UPPER_CASE, got {name!r}")
        if any(m.name == name for m in self.members):
            raise ValidationError(f"duplicate enum value name {name!r}")
        if value is not None and not isinstance(value, int):
            raise ValidationError(f"enum value must be an integer, got {type(value).__name__}")
        if value is not None and value < 0:
            raise ValidationError(f"enum value must be non-negative, got {value}")
        self.members.append(
            EnumMember(
                name=name,
                source=capture_source_info(),
                value=value,
            )
        )
        return self

    @property
    def width(self) -> int:
        """Explicit width if set, otherwise inferred minimum."""
        if self._explicit_width is not None:
            return self._explicit_width
        if not self.members:
            return 0
        max_value = self._resolve_max_value()
        return max(1, max_value.bit_length())

    def _resolve_max_value(self) -> int:
        """Resolve the maximum value across all members (including auto-fill)."""
        max_val = 0
        prev_val = -1
        for member in self.members:
            if member.value is not None:
                resolved = member.value
            else:
                resolved = prev_val + 1
            prev_val = resolved
            if resolved > max_val:
                max_val = resolved
        return max_val


def Enum(width: int | None = None) -> EnumType:
    """Create an enum type, optionally with explicit bit-width."""
    return EnumType(width=width, source=capture_source_info())
