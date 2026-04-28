"""Source-location capture helpers."""

from __future__ import annotations

from dataclasses import dataclass
import inspect
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceInfo:
    """Captured source location for DSL objects."""

    path: str
    line: int
    column: int | None


def capture_source_info() -> SourceInfo:
    """Capture caller file and line information."""
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None or frame.f_back.f_back is None:
        return SourceInfo(path="<unknown>", line=0, column=None)
    caller = frame.f_back.f_back
    return SourceInfo(
        path=str(Path(caller.f_code.co_filename)),
        line=caller.f_lineno,
        column=None,
    )
