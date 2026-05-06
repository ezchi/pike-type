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

    ``out_layout`` controls where the configured ``out`` directory sits
    relative to the per-module ``<sub>`` segment:

      * ``prefix`` (default for language packages such as ``py``/``cpp``):
        output = ``<out>/<sub>/[<backend_id>/]<file>``.
      * ``suffix`` (default for HDL roles such as ``sv``/``sim``):
        output = ``<project_root>/<sub>/<out>/[<backend_id>/]<file>``.
    """

    name: str
    out: Path
    out_layout: str = "prefix"
    language_id: bool = False


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
