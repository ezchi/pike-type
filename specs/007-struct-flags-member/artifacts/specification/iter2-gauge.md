# Gauge Review — Iteration 2

**Provider:** codex (gpt-5.5)

## Prior Issue Resolution

All prior BLOCKING issues resolved:
- Freeze alignment (`_serialized_width_from_dsl`) — covered in FR-3.
- Python/C++ width/byte-count — covered in FR-8.
- C++ `BYTE_COUNT` naming — corrected in FR-9.
- Round-trip test scope — clarified in FR-10.
- Brittle test count — fixed (AC-21 says "existing test suite").

## New Issues

- **BLOCKING** — FR-6 gives the wrong SV helper `to_slv()` / `from_slv()` behavior. The spec says to call `pack_<flags>(field.to_slv())`, but that is NOT the nested-composite helper pattern. Existing struct helpers assign typedef values directly: `packed_value.<field> = <field>.to_slv();` and `<field>.from_slv(value_in.<field>);`. `pack_<flags>()` returns data-width only (no alignment padding), so using it in `to_slv()` would shift flag bits into padding. FR-6 should require direct typedef field assignment.

- **WARNING** — Dependency ordering claim not fully resolved. Spec still claims source-line ordering matches Python execution order. Freeze sorts types by `(source.line, name)`, which works for common DSL patterns but could fail for same-line definitions or helper-function-constructed objects. The spec should acknowledge this as a reliance on conventional DSL usage rather than a guarantee.

- **WARNING** — FR-6 uses `bytes[offset +: BYTE_COUNT]` for `from_bytes()` but the existing SV backend copies dynamic-array bytes into a temporary `field_bytes` array before delegation. The spec should describe the actual pattern.

VERDICT: REVISE
