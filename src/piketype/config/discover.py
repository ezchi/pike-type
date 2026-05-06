"""Locate the piketype.yaml file.

Two modes:

1. Explicit ``--config <path>``: caller passes a concrete path to a YAML file.
2. Implicit upward walk: caller passes a starting directory; this walks
   upward looking for ``piketype.yaml``.

In both cases, the returned path is absolute. Generated outputs are
anchored at the YAML's directory, never at the caller's CWD.
"""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError


CONFIG_FILENAME = "piketype.yaml"


def find_config(*, explicit: Path | None = None, start: Path | None = None) -> Path:
    """Resolve the project's piketype.yaml.

    ``explicit`` wins if provided. Otherwise walk upward from ``start``
    (default: CWD) looking for ``piketype.yaml``. Raises if not found.
    """
    if explicit is not None:
        resolved = explicit.expanduser().resolve()
        if not resolved.is_file():
            raise PikeTypeError(f"config not found: {resolved}")
        return resolved

    origin = (start or Path.cwd()).expanduser().resolve()
    for candidate in (origin, *origin.parents):
        config_path = candidate / CONFIG_FILENAME
        if config_path.is_file():
            return config_path
    raise PikeTypeError(
        f"could not find {CONFIG_FILENAME} from {origin} (pass --config explicitly)"
    )
