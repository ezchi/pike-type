"""C++ namespace validation for the --namespace CLI argument."""

from __future__ import annotations

import re
from pathlib import Path

from piketype.errors import ValidationError

# Complete C++17 keyword set (including alternative tokens).
CPP17_KEYWORDS: frozenset[str] = frozenset({
    "alignas", "alignof", "and", "and_eq", "asm", "auto",
    "bitand", "bitor", "bool", "break",
    "case", "catch", "char", "char8_t", "char16_t", "char32_t",
    "class", "compl", "concept", "const", "consteval", "constexpr",
    "constinit", "const_cast", "continue", "co_await", "co_return",
    "co_yield",
    "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern",
    "false", "float", "for", "friend",
    "goto",
    "if", "inline", "int",
    "long",
    "mutable",
    "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
    "operator", "or", "or_eq",
    "private", "protected", "public",
    "register", "reinterpret_cast", "requires", "return",
    "short", "signed", "sizeof", "static", "static_assert",
    "static_cast", "struct", "switch",
    "template", "this", "thread_local", "throw", "true", "try",
    "typedef", "typeid", "typename",
    "union", "unsigned", "using",
    "virtual", "void", "volatile",
    "wchar_t", "while",
    "xor", "xor_eq",
})

_IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_cpp_namespace(value: str) -> tuple[str, ...]:
    """Validate a ``::``-separated C++ namespace string.

    Returns the parsed segments on success.
    Raises ``ValidationError`` on any validation failure.
    """
    if not value:
        raise ValidationError("--namespace value must not be empty")

    segments = value.split("::")

    for index, segment in enumerate(segments):
        if not segment:
            raise ValidationError(
                f"--namespace contains an empty segment in '{value}'"
            )
        if not _IDENT_RE.match(segment):
            raise ValidationError(
                f"--namespace segment '{segment}' is not a valid C++ identifier"
            )
        if segment in CPP17_KEYWORDS:
            raise ValidationError(
                f"--namespace segment '{segment}' is a C++ keyword"
            )
        if segment.startswith("_"):
            raise ValidationError(
                f"--namespace segment '{segment}' must not begin with an underscore"
            )
        if "__" in segment:
            raise ValidationError(
                f"--namespace segment '{segment}' must not contain '__'"
            )
        if segment.endswith("_"):
            raise ValidationError(
                f"--namespace segment '{segment}' must not end with an underscore"
            )
        if index == 0 and segment == "std":
            raise ValidationError(
                "--namespace must not use 'std' as the first segment"
            )

    # Composition-level guard-prefix check (belt-and-suspenders).
    guard_prefix = value.replace("::", "_").upper()
    if "__" in guard_prefix:
        raise ValidationError(
            f"--namespace '{value}' would produce a reserved include-guard prefix "
            f"containing '__': {guard_prefix}"
        )
    if guard_prefix.startswith("_"):
        raise ValidationError(
            f"--namespace '{value}' would produce a reserved include-guard prefix "
            f"starting with '_': {guard_prefix}"
        )

    return tuple(segments)


def check_duplicate_basenames(*, module_paths: list[Path]) -> None:
    """Reject duplicate module basenames anywhere in the repo (FR-9a).

    Raises ``ValidationError`` listing the conflicting paths if any two
    discovered modules share the same file stem. Runs unconditionally for
    every ``piketype gen`` invocation (not just under ``--namespace``)
    because cross-module SV imports identify target packages by basename.
    """
    by_stem: dict[str, list[Path]] = {}
    for path in module_paths:
        by_stem.setdefault(path.stem, []).append(path)

    duplicates = {stem: paths for stem, paths in by_stem.items() if len(paths) > 1}
    if not duplicates:
        return

    parts: list[str] = []
    for stem in sorted(duplicates):
        paths_str = ", ".join(str(p) for p in sorted(duplicates[stem]))
        parts.append(f"  '{stem}': {paths_str}")
    raise ValidationError(
        "piketype requires unique module basenames across the repo, but duplicates were found:\n"
        + "\n".join(parts)
    )
