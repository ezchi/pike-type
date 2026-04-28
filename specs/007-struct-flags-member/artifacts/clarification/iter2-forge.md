# Clarification — Iteration 2

## Clarifications

### CL-1: WIDTH vs BYTE_COUNT for Struct with Flags Member [NO SPEC CHANGE]

**Ambiguity:** The spec does not explicitly state how a Flags member contributes to the struct's `WIDTH` (data-only) vs `BYTE_COUNT` (byte-aligned).

**Resolution:** This follows the existing convention established in spec 001:

- **Struct `WIDTH` / `LP_*_WIDTH`** = sum of data widths of all fields. For a Flags member, the data width is the number of flags (e.g., 3 flags → 3 bits). This is used by `pack_<struct>()` / `unpack_<struct>()`.
- **Struct `BYTE_COUNT` / `LP_*_BYTE_COUNT`** = sum of byte-aligned field sizes. For a Flags member, the byte-aligned size is the Flags type's `BYTE_COUNT` (e.g., 3 flags → 1 byte = 8 bits). This is used by `to_bytes()` / `from_bytes()`.

No spec change needed — this is consistent with FR-5 (pack/unpack use data-width `pack_<flags>()`) and FR-8 (`_resolved_type_width()` returns flag count, `_type_byte_count()` returns byte-aligned count).

### CL-2: Dependency Ordering Clarification [SPEC UPDATE]

**Ambiguity:** FR-5 says Flags definitions "must appear before" Struct definitions, then says there's no topological sort and edge cases are unaddressed. This reads as contradictory.

**Resolution:** Reword to remove the "must" requirement. The actual behavior is: the current `(source.line, name)` sort produces correct ordering for conventional DSL definitions. This spec does not add topological sorting — it relies on the same mechanism that already works for nested structs.

**Spec change:** FR-5 dependency ordering bullet reworded.

### CL-3: Cross-Module Flags Member Rejection [SPEC UPDATE]

**Ambiguity:** FR-4/NFR-4 mention the cross-module restriction, but no AC explicitly tests cross-module Flags member rejection.

**Resolution:** The existing validation in `validate/engine.py` line 67 already rejects cross-module `TypeRefIR` targets generically. A Flags member referencing a type from another module would hit this check. However, adding an explicit negative test AC improves coverage.

**Spec change:** Add AC-27.

### CL-4: Manifest Output [NO SPEC CHANGE]

**Ambiguity:** The manifest handling claim in the clarification was not backed by spec text.

**Resolution:** The manifest (`piketype_manifest.json`) serializes types at the module level, not at the struct-field level. A struct's manifest entry has `field_count` but does not enumerate field types. A Flags type used as a struct member is already listed as a separate top-level type entry with `kind: "flags"`. The struct-level manifest entry is unchanged — `field_count` increases by 1 for the Flags member, which happens automatically. No manifest code changes are needed; the golden file for the new fixture will include the correct manifest.
