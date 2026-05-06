"""Name conversion helpers for DSL and generated identifiers."""

from __future__ import annotations

import re


_CAP_WORDS_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_LEGACY_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]*_t$")
_WORD_BOUNDARY_RE = re.compile(r"(.)([A-Z][a-z]+)")
_LOWER_TO_UPPER_RE = re.compile(r"([a-z0-9])([A-Z])")


def is_valid_type_name(name: str) -> bool:
    """Return true for supported DSL type declaration styles."""
    return bool(_CAP_WORDS_RE.fullmatch(name) or _LEGACY_TYPE_RE.fullmatch(name))


def to_snake_case(name: str) -> str:
    """Convert a CapWords identifier to snake_case."""
    partially_split = _WORD_BOUNDARY_RE.sub(r"\1_\2", name)
    return _LOWER_TO_UPPER_RE.sub(r"\1_\2", partially_split).lower()


def sv_type_base_name(type_name: str) -> str:
    """Return the SystemVerilog base name without the trailing _t."""
    if type_name.endswith("_t"):
        return type_name[:-2]
    return to_snake_case(type_name)


def sv_type_name(type_name: str) -> str:
    """Return the SystemVerilog typedef name for a DSL type name."""
    if type_name.endswith("_t"):
        return type_name
    return f"{sv_type_base_name(type_name)}_t"


def sv_helper_class_name(type_name: str) -> str:
    """Return the SystemVerilog test helper class name for a DSL type name."""
    return f"{sv_type_base_name(type_name)}_ct"


def py_type_class_name(type_name: str) -> str:
    """Return the generated Python runtime class name for a DSL type name."""
    if type_name.endswith("_t"):
        return f"{type_name[:-2]}_ct"
    return type_name


def py_enum_class_name(type_name: str) -> str:
    """Return the generated Python enum class name for a DSL enum type name."""
    if type_name.endswith("_t"):
        return f"{type_name[:-2]}_enum_t"
    return f"{type_name}Enum"
