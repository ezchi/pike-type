# Delta Revision — Iteration 6 (Delta 4)

## Gauge Feedback (from iter5 delta gauge)
1. MAJOR: NFR-4 still lists FR-13 as validation-only, but FR-13 now enables positive code generation.
2. MAJOR: Missing acceptance coverage for wide scalar round-trip serialization.
3. MAJOR: FR-7 wide scalar wrapper `std::vector<std::uint8_t>` normalization invariant underspecified.

## Changes Made

### spec.md — NFR-4
- **Before:** "Validation-only behaviors (FR-11, FR-13, FR-14)"
- **After:** "Validation-only behaviors (FR-11, FR-14)". FR-13 now noted as having both validation and code-gen components.

### spec.md — FR-7 Wide scalar storage
- **Before:** "to_bytes() returns this vector directly (padding zeros in MSB byte)"
- **After:** Added normalized invariant: vector always has exactly `kByteCount` elements, upper `padding_bits` bits of MSB byte always zero. Constructors/setters enforce by clearing padding bits. `to_bytes()` returns directly (no copy needed). `from_bytes()` masks padding to enforce invariant.

### spec.md — AC-24 (new)
- 65-bit unsigned scalar `to_bytes()`/`from_bytes()` round-trip, padding masking, cross-language identity.

### spec.md — AC-25 (new)
- Struct containing 65-bit unsigned member + 1-bit flag, 10 bytes total, same across all backends.

### spec.md — Changelog
- 4 entries for delta 4.

## Sections NOT Modified
- All FR-* except FR-7 (narrow edit to wide scalar paragraph only)
- All other NFR-* except NFR-4
- All AC-1 through AC-23
- All clarifications C-1 through C-15
- Definitions, User Stories, Out of Scope
