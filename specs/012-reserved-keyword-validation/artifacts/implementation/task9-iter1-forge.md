# Task 9: Negative fixture — struct field `type` (AC-1) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_struct_field_type/project/.git/HEAD` — fake repo-root marker.
- `tests/fixtures/keyword_struct_field_type/project/alpha/piketype/types.py` — defines `foo_t` with field `type`.

## Key Implementation Decisions

- Two-field struct (avoid min-field structural rule firing first).
- The DSL accepts string field names verbatim; no Python syntax restriction (unlike module-level bindings).

## Deviations from Plan

None.

## Tests Added

`test_struct_field_type_is_rejected` (added in T-017). Verified manually: `piketype gen` emits the FR-3 message with `Python (soft), SystemVerilog`.
