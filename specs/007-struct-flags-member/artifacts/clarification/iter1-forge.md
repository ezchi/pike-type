# Clarification — Iteration 1

## Forge Assessment

The specification is clear and complete. No ambiguities or open questions were identified during the 5-iteration specification review. The gauge approved with zero blocking or warning issues.

### Potential Clarification Points Reviewed

1. **Flags field padding within struct:** A Flags member in a struct has `padding_bits == 0` in its `StructFieldIR` because the Flags type is already byte-aligned internally (via `_align_pad`). The struct does not add additional per-field byte padding on top of the Flags member. This is implicit in the spec (FR-5 says the Flags typedef is used directly) but worth confirming — it's consistent with how nested struct members work (struct-typed fields also have `padding_bits == 0`).

2. **Flags field `_pad` naming collision:** The struct's `_pad` suffix reservation (from spec 001) applies to struct member names. A Flags field named `status` would generate `status` in the typedef, not `status_pad`. No collision risk. The Flags type's internal `_align_pad` lives inside the Flags typedef, not at the struct level.

3. **Manifest output:** The JSON manifest (`piketype_manifest.json`) already lists types with their kinds. A Flags member in a struct would appear as a `TypeRefIR` in the struct's field list, referencing the Flags type by name. The manifest serialization handles `TypeRefIR` generically. No manifest changes are needed.

### Conclusion

No clarifications needed. The spec is ready for planning.
