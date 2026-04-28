# Validation Results — Spec 005: Flags() DSL Type

## Test Results

- **Full test suite:** 139 passed (101 existing + 38 new), 0 failed
- **basedpyright:** 0 errors on new files (src/typist/dsl/flags.py)

## Acceptance Criteria Verification

### AC-1: FlagsType width property
**PASS** — `test_width_property`: `Flags().add_flag("a").add_flag("b").add_flag("c").width == 3`

### AC-2: SV typedef struct packed with logic fields and _align_pad
**PASS** — Golden file `types_pkg.sv` contains correct typedef for triple_t with 3 logic fields + `logic [4:0] _align_pad`

### AC-3: C++ class with uint8_t storage and correct masks
**PASS** — Golden file `types_types.hpp` contains `A_MASK = 0x80U`, `B_MASK = 0x40U`, `C_MASK = 0x20U` with getter/setter methods

### AC-4: Python runtime round-trips with explicit byte vectors
**PASS** — 18 runtime tests verify to_bytes/from_bytes for all 5 fixture types with explicit byte vectors

### AC-5: 8-flag type with no _align_pad and uint8_t
**PASS** — Golden files show byte_t has no _align_pad in SV, uses std::uint8_t in C++

### AC-6: 9-flag type with uint16_t and 7 padding bits
**PASS** — Golden files show wide_t uses std::uint16_t with correct 16-bit masks

### AC-7: Validation rejects invalid inputs
**PASS** — 10 negative validation tests:
- FlagsDSLTest: duplicate, non-snake_case, empty name (3 tests)
- FlagsValidationTest: 0 flags, >64 flags, duplicates, _pad suffix, reserved names (value, to_bytes, from_bytes), missing _t suffix (7 tests)

### AC-8: Golden-file integration tests pass
**PASS** — `test_generates_flags_golden` compares all generated files byte-for-byte against golden files

### AC-9: Idempotency
**PASS** — `test_idempotent` verifies second gen run produces identical output

### AC-10: basedpyright strict mode
**PASS** — 0 errors on new file `src/typist/dsl/flags.py`. Pre-existing errors in other files are unchanged.

### AC-11: 1-flag serialization
**PASS** — `test_single_flag_true`: `{flag=True}` → `b'\x80'`; `test_single_flag_false`: `{flag=False}` → `b'\x00'`

### AC-12: 33-flag type with uint64_t and ULL suffixes
**PASS** — Golden file `types_types.hpp` shows very_wide_ct uses `std::uint64_t` with `ULL` mask suffixes

### AC-13: Python from_bytes wrong size raises ValueError
**PASS** — `test_from_bytes_wrong_size` verifies ValueError on wrong byte count

### AC-14: Nonzero padding bits masked on from_bytes
**PASS** — `test_nonzero_padding_masked`: `from_bytes(b'\xa3')` equals `from_bytes(b'\xa0')` and `to_bytes()` returns `b'\xa0'`

### AC-15: Manifest includes flags kind
**PASS** — Golden file `typist_manifest.json` includes `"kind": "flags"`, `"flag_count"`, and `"flag_names"` entries

## Summary

**All 15 acceptance criteria verified. 139 tests pass. 0 regressions.**
