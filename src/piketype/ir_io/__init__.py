"""IR persistence layer.

Serializes the in-memory ``RepoIR`` tree to JSON files on disk and back.
The frontend stage (`piketype build`) writes IR; backend stages
(`piketype gen <lang>`) read IR. This boundary means no backend ever
executes user Python.

Cache layout::

    <ir_cache>/
      index.json                      schema_version + module index
      <sub>/<base>.ir.json            per-module IR mirroring source tree
      diagnostics.json                build-stage diagnostics

A schema_version mismatch on read raises ``IRSchemaMismatchError`` with
a clear "regenerate IR cache" message.
"""

from __future__ import annotations

from piketype.ir_io.cache import read_cache, write_cache
from piketype.ir_io.codec import decode_repo, encode_repo
from piketype.ir_io.diagnostics import Diagnostic, has_errors, write_diagnostics
from piketype.ir_io.schema import SCHEMA_VERSION, IRSchemaMismatchError

__all__ = [
    "Diagnostic",
    "IRSchemaMismatchError",
    "SCHEMA_VERSION",
    "decode_repo",
    "encode_repo",
    "has_errors",
    "read_cache",
    "write_cache",
    "write_diagnostics",
]
