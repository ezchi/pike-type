"""Encode/decode RepoIR ↔ JSON-safe dict.

The IR is a tree of frozen dataclasses with three tagged unions
(``ExprIR``, ``TypeDefIR``, ``FieldTypeIR``). Encoding tags every
dataclass instance with ``__kind__`` so the decoder can pick the right
class for union slots. Tuples encode as lists; primitives pass
through.

This codec is generic over the IR module: any frozen dataclass listed
in ``CLASS_REGISTRY`` round-trips. Adding a new IR node type means
appending it to the registry — no per-class encode/decode helpers.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from piketype.ir.nodes import (
    BinaryExprIR,
    ConstIR,
    ConstRefExprIR,
    EnumIR,
    EnumValueIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleDependencyIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    SourceSpanIR,
    StructFieldIR,
    StructIR,
    TypeRefIR,
    UnaryExprIR,
    VecConstIR,
    VecConstImportIR,
)


_REGISTRY_CLASSES: tuple[type[Any], ...] = (
    BinaryExprIR,
    ConstIR,
    ConstRefExprIR,
    EnumIR,
    EnumValueIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleDependencyIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    SourceSpanIR,
    StructFieldIR,
    StructIR,
    TypeRefIR,
    UnaryExprIR,
    VecConstIR,
    VecConstImportIR,
)

CLASS_REGISTRY: dict[str, type[Any]] = {cls.__name__: cls for cls in _REGISTRY_CLASSES}


def encode_repo(repo: RepoIR) -> dict[str, Any]:
    """Encode a ``RepoIR`` into a JSON-safe dict."""
    return _encode(repo)


def decode_repo(data: object) -> RepoIR:
    """Decode a previously encoded ``RepoIR`` dict back into a frozen tree."""
    decoded = _decode(data)
    if not isinstance(decoded, RepoIR):
        raise ValueError(f"expected encoded RepoIR, got {type(decoded).__name__}")
    return decoded


def encode_module(module: ModuleIR) -> dict[str, Any]:
    """Encode one ``ModuleIR`` (used for per-module IR cache files)."""
    return _encode(module)


def decode_module(data: object) -> ModuleIR:
    """Decode one ``ModuleIR``."""
    decoded = _decode(data)
    if not isinstance(decoded, ModuleIR):
        raise ValueError(f"expected encoded ModuleIR, got {type(decoded).__name__}")
    return decoded


def _encode(obj: object) -> Any:
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, tuple):
        items: tuple[Any, ...] = obj  # pyright: ignore[reportUnknownVariableType]
        return [_encode(x) for x in items]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result: dict[str, Any] = {"__kind__": type(obj).__name__}
        for field in dataclasses.fields(obj):
            result[field.name] = _encode(getattr(obj, field.name))
        return result
    raise TypeError(f"cannot encode value of type {type(obj).__name__}")


def _decode(data: object) -> Any:
    if data is None or isinstance(data, (bool, int, str)):
        return data
    if isinstance(data, list):
        items: list[Any] = list(data)  # pyright: ignore[reportUnknownArgumentType]
        return tuple(_decode(x) for x in items)
    if isinstance(data, dict):
        body: dict[str, Any] = {str(k): v for k, v in data.items()}  # pyright: ignore[reportUnknownVariableType,reportUnknownArgumentType]
        kind = body.get("__kind__")
        if not isinstance(kind, str):
            raise ValueError(f"missing or invalid __kind__: {kind!r}")
        cls = CLASS_REGISTRY.get(kind)
        if cls is None:
            raise ValueError(f"unknown IR kind: {kind!r}")
        kwargs: dict[str, Any] = {}
        for field in dataclasses.fields(cls):
            if field.name in body:
                kwargs[field.name] = _decode(body[field.name])
        return cls(**kwargs)
    raise TypeError(f"cannot decode value of type {type(data).__name__}")
