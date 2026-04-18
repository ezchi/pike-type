"""Backend registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from typist.ir.nodes import RepoIR


class Backend(Protocol):
    """Protocol for backend emitters."""

    def emit(self, repo: RepoIR) -> None:
        """Emit files from frozen IR."""


@dataclass(frozen=True, slots=True)
class BackendRegistry:
    """Container for backend instances."""

    backends: tuple[Backend, ...] = ()
