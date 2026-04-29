# Gauge Review — Plan Iteration 1

## BLOCKING

1. Golden output paths are wrong. Actual structure is `sv/alpha/piketype/types_pkg.sv`, `py/alpha/piketype/types_types.py`, `cpp/alpha/piketype/types_types.hpp`, `piketype_manifest.json` — not `alpha/gen/sv/alpha_types_pkg.sv`.

2. AC-11 test incomplete. Need to also test that assigning a raw `IntEnum` value (e.g., `cmd_enum_t.WRITE`) directly to the struct field raises `TypeError`, not just `None`.

3. AC-15 (C++ clone) not mapped. Need explicit assertion or golden-content check for `.clone()` on enum fields.

4. Cross-module negative test (AC-22/AC-24) is too vague. Must specify concrete approach (inline IR construction or separate fixture).

## WARNING

- AC-3: Only 2-bit enum tested. Add 8-bit enum freeze assertion for padding_bits=0.
- Fixture needs `.git/` repo marker (existing fixtures have `.git/HEAD` or `.git/` directory).
- Regression step should include `basedpyright` check per constitution.

## NOTE

- EnumType/EnumIR imports already exist in freeze.py, engine.py, and backends — no new imports needed in most files.

VERDICT: REVISE
