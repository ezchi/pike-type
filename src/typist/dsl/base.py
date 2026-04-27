"""Base classes for DSL runtime objects."""

from __future__ import annotations

from dataclasses import dataclass

from typist.dsl.source_info import SourceInfo


@dataclass(slots=True)
class DslNode:
    """Base runtime node with source information."""

    source: SourceInfo
