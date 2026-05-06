"""Struct DSL nodes."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Self

from piketype.dsl.base import DslNode
from piketype.dsl.enum import EnumType
from piketype.dsl.flags import FlagsType
from piketype.dsl.scalar import ScalarType
from piketype.dsl.source_info import SourceInfo, capture_source_info
from piketype.errors import ValidationError


_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


type StructFieldType = ScalarType | StructType | FlagsType | EnumType


@dataclass(frozen=True, slots=True)
class StructMember:
    """One mutable-DSL struct member."""

    name: str
    type: StructFieldType
    source: SourceInfo
    rand: bool


@dataclass(slots=True)
class StructType(DslNode):
    """Packed struct definition."""

    members: list[StructMember]
    _alignment_multiple_bits: int | None

    def __init__(self, *, source: SourceInfo | None = None) -> None:
        resolved_source = capture_source_info() if source is None else source
        DslNode.__init__(self, source=resolved_source)
        self.members = []
        self._alignment_multiple_bits = None

    @property
    def alignment_multiple_bits(self) -> int | None:
        """Requested total-width alignment multiple in bits, if set."""
        return self._alignment_multiple_bits

    def add_member(
        self,
        name: str,
        type: StructFieldType,
        *,
        rand: bool = True,
        sw: object | None = None,
    ) -> Self:
        """Append one member and return self for chaining."""
        if self._alignment_multiple_bits is not None:
            raise ValidationError("cannot add members after align_to_bits()")
        if sw is not None:
            raise ValidationError("struct member sw= override is not supported in this milestone")
        if not isinstance(name, str) or not _SNAKE_CASE_RE.fullmatch(name):
            raise ValidationError(f"struct member name must be snake_case, got {name!r}")
        if not isinstance(type, (ScalarType, StructType, FlagsType, EnumType)):
            raise ValidationError("struct member type must be a scalar, struct, flags, or enum type in this milestone")
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

    def align_to_bits(self, alignment_bits: int) -> Self:
        """Pad total struct width to a multiple of alignment_bits. Returns self."""
        if type(alignment_bits) is not int:
            raise ValidationError(f"align_to_bits() argument must be int, got {type(alignment_bits).__name__}")
        if alignment_bits <= 0:
            raise ValidationError(f"align_to_bits() argument must be positive, got {alignment_bits}")
        if alignment_bits % 8 != 0:
            raise ValidationError(
                f"align_to_bits() argument must be a multiple of 8, got {alignment_bits}"
            )
        if self._alignment_multiple_bits is not None:
            raise ValidationError("align_to_bits() already set on this struct")
        self._alignment_multiple_bits = alignment_bits
        return self

    def multiple_of(self, n: int) -> Self:
        """Compatibility alias for align_to_bits()."""
        self.align_to_bits(n)
        return self


def Struct() -> StructType:
    """Create a packed struct type."""
    return StructType(source=capture_source_info())
