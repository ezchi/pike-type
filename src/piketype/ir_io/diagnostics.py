"""Build-stage diagnostics file.

Written alongside the IR cache as ``diagnostics.json``. Each entry
carries a ``severity`` (``error`` | ``warning`` | ``info``), a stable
``code`` for grepping, and a human-readable ``message``. ``error``
entries cause the build to exit non-zero and any subsequent ``gen``
to refuse to run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


_DIAGNOSTICS_FILENAME = "diagnostics.json"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    severity: str  # "error" | "warning" | "info"
    code: str
    message: str


def write_diagnostics(*, cache_root: Path, diagnostics: list[Diagnostic]) -> Path:
    """Write the diagnostics JSON file, return its path."""
    cache_root.mkdir(parents=True, exist_ok=True)
    path = cache_root / _DIAGNOSTICS_FILENAME
    payload = {
        "diagnostics": [
            {"severity": d.severity, "code": d.code, "message": d.message}
            for d in diagnostics
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def has_errors(diagnostics: list[Diagnostic]) -> bool:
    """Return True if any diagnostic has severity ``error``."""
    return any(d.severity == "error" for d in diagnostics)
