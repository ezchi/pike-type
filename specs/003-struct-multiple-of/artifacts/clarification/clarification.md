# Clarification — Spec 003: Struct `multiple_of(N)` Alignment

## Status: No clarifications needed

The specification is self-contained with no open questions. All functional requirements map directly to existing code locations with clear modification points.

| FR | Code Location | Modification |
|----|--------------|--------------|
| FR-1/FR-2 | `src/typist/dsl/struct.py:27-63` | Add `_alignment` field to `StructType`, add `multiple_of()` method, guard `add_member` |
| FR-3 | `src/typist/ir/nodes.py:122-128` | Add `alignment_bits: int = 0` to `StructIR` |
| FR-7 | `src/typist/dsl/freeze.py:143-164` | Compute `alignment_bits` during struct freeze, pass to `StructIR` |
| FR-8 | `src/typist/validate/engine.py:44-77` | Add alignment_bits-multiple-of-8 assertion |
| FR-4 | `src/typist/backends/sv/emitter.py:137-149,351+` | Add `_align_pad` to struct typedef, update BYTE_COUNT, update helper to_bytes/from_bytes |
| FR-5 | `src/typist/backends/cpp/emitter.py:340-417` | Append zero bytes in to_bytes, consume in from_bytes, update BYTE_COUNT |
| FR-6 | `src/typist/backends/py/emitter.py:301-460` | Append zero bytes in to_bytes, consume in from_bytes, update BYTE_COUNT |

## Resolved Ambiguities (from spec iterations)

These were resolved during the Forge-Gauge specification loop:

1. **Power-of-two not required** — FR-2 allows any multiple of 8 (e.g., `multiple_of(24)` is valid).
2. **Bool rejection** — FR-2 uses `type(N) is int` to reject `bool` subclass.
3. **Pack/unpack unchanged** — SV pack/unpack operate on data-only width, unaffected by alignment.
4. **Helper class WIDTH vs BYTE_COUNT** — `WIDTH` stays data-only, `BYTE_COUNT` includes alignment.
5. **Nested struct width is recursive** — Inner struct alignment_bits included in outer struct natural_width.
6. **from_bytes requires exact BYTE_COUNT** — Consistent with existing behavior across all backends.
7. **Alignment pad is unsigned** — Always zero-filled, unlike signed per-field padding which is sign-extended.
