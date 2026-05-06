"""Initialize a piketype project by writing a default ``piketype.yaml``."""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError


_DEFAULT_CONFIG_YAML = """\
# piketype project configuration.
# Reference: docs/piketype-yaml.md
#
# Every key below is shown with its default value. Remove any key you
# don't override to keep the file short. Unknown keys cause a hard
# error so typos surface immediately.
#
# Output path formula: <backend_root>/<sub>/<language_id>/<file>
# where <sub> is the module path between piketype_root and piketype/.
# Empty backend_root defaults to the project root; empty language_id
# collapses that segment.

frontend:
  # Where DSL files live. Walked recursively for <sub>/piketype/<base>.py.
  # Default: this directory (project root).
  piketype_root: .

  # Where the build writes IR cache, _index.json, and diagnostics.json.
  # Default: <project_root>/.piketype-cache
  ir_cache: .piketype-cache

  # Glob patterns to skip during discovery (reserved; currently unused).
  exclude: []

backends:
  # SystemVerilog synthesis package. Role directory sits next to source:
  # <sub>/rtl/<base>_pkg.sv.
  sv:
    backend_root: ""    # empty -> project root
    language_id: rtl

  # SystemVerilog test/verification package: <sub>/sim/<base>_test_pkg.sv
  sim:
    backend_root: ""
    language_id: sim

  # Python wrapper module. The package root sits above the source tree:
  # py/<sub>/<base>_types.py. Add <backend_root> to PYTHONPATH at
  # runtime to import as <sub>.<base>_types.
  py:
    backend_root: py
    language_id: ""     # no per-language subdir

  # C++ header: cpp/<sub>/<base>_types.hpp
  cpp:
    backend_root: cpp
    language_id: ""
"""

_FILENAME = "piketype.yaml"


def run_init(*, path: Path | None = None, force: bool = False) -> Path:
    """Write ``piketype.yaml`` with default backends to ``path`` (or cwd).

    Returns the absolute path of the written file. Raises
    ``PikeTypeError`` if a config already exists at the target and
    ``force`` is False.
    """
    target_dir = (path or Path.cwd()).expanduser().resolve()
    if not target_dir.is_dir():
        raise PikeTypeError(f"target is not a directory: {target_dir}")

    target = target_dir / _FILENAME
    if target.exists() and not force:
        raise PikeTypeError(f"{target} already exists; pass --force to overwrite")

    target.write_text(_DEFAULT_CONFIG_YAML, encoding="utf-8")
    return target
