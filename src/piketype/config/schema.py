"""Frozen schema for the parsed piketype.yaml config.

All paths are absolute after resolution. Relative paths in the YAML are
anchored at the config file's directory (the project root). Frontend and
backend sections are split into separate dataclasses so per-stage tools
can take only the section they need.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BackendConfig:
    """Per-backend output configuration.

    A backend's outputs land at::

        <backend_root>/<sub>/<language_id>/<file>

    where ``<sub>`` is the module's path relative to
    ``frontend.piketype_root`` (with the trailing ``piketype/`` stripped).
    Empty ``backend_root`` resolves to the project root; an empty
    ``language_id`` collapses that segment.
    """

    name: str
    backend_root: Path
    language_id: str = ""


@dataclass(frozen=True, slots=True)
class FrontendConfig:
    """Frontend (IR builder) stage configuration."""

    piketype_root: Path
    ir_cache: Path
    exclude_globs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Config:
    """Resolved piketype.yaml configuration."""

    project_root: Path
    config_path: Path
    frontend: FrontendConfig
    backends: tuple[BackendConfig, ...]

    def get_backend(self, name: str) -> BackendConfig | None:
        """Return the backend config for ``name`` or ``None`` if absent."""
        for backend in self.backends:
            if backend.name == name:
                return backend
        return None
