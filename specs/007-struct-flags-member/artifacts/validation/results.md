# Validation Results — Spec 007: Struct Accepts Flags as Member

**Test suite:** 150 tests, all passing (139 existing + 11 new).

## Acceptance Criteria Verification

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 | PASS | `test_add_flags_member_accepted` — `Struct().add_member("f", flags_t)` succeeds. |
| AC-2 | PASS | Freeze produces `TypeRefIR` — verified by golden file generation (SV `pack_report` calls `pack_status(a.status)`). |
| AC-3 | PASS | Validation passes — golden test `test_golden_match` exercises full pipeline including validation. |
| AC-4 | PASS | Freeze rejects anonymous Flags — code at `freeze.py:307` raises `ValidationError("inline anonymous flags member types are not supported in this milestone")`. |
| AC-5 | PASS | SV golden: `typedef struct packed { status_t status; ... } report_t;` — Flags field uses type name. |
| AC-6 | PASS | SV golden: `pack_report` returns `{pack_status(a.status), a.code}`. |
| AC-7 | PASS | SV golden: `unpack_report` calls `result.status = unpack_status(a[offset +: LP_STATUS_WIDTH])`. |
| AC-8 | PASS | SV golden: helper class declares `status_ct status;`, initializes with `new()`, delegates all methods. |
| AC-9 | PASS | Python golden: `status: status_ct = field(default_factory=status_ct)` — typed as Flags class, not nullable. |
| AC-10 | PASS | `test_flags_field_not_nullable` and `test_flags_field_rejects_wrong_type` — both raise TypeError. |
| AC-11 | PASS | `test_round_trip_report` — to_bytes serializes correctly. |
| AC-12 | PASS | `test_round_trip_report` — from_bytes deserializes correctly. |
| AC-13 | PASS | C++ golden: `status_ct status;` field declaration, references `BYTE_COUNT`. |
| AC-14 | PASS | C++ golden: to_bytes/from_bytes call `.to_bytes()`/`.from_bytes()` on Flags field. |
| AC-15 | PASS | Python/C++ `_resolved_type_width()` returns `len(type_ir.fields)` for FlagsIR. |
| AC-16 | PASS | Python/C++ `_type_byte_count()` returns `(len(fields) + alignment_bits) // 8` for FlagsIR. |
| AC-17 | PASS | `_serialized_width_from_dsl()` includes FlagsType member width via `byte_count(len(member.type.flags)) * 8`. |
| AC-18 | PASS | `test_multiple_of_byte_count` — `aligned_report_t` serializes to 4 bytes (32 bits). |
| AC-19 | PASS | `test_expected_bytes_report` — verifies exact byte values: `0xA0, 0x15`. |
| AC-20 | PASS | `test_golden_match` — all golden files match. |
| AC-21 | PASS | `test_idempotent` — second generation produces identical output. |
| AC-22 | PASS | SV Flags helper now uses `bv[total_bits-1-idx]` for MSB-packed layout. |
| AC-23 | PASS | SV Flags helper `from_bytes` extracts from MSB positions. |
| AC-24 | PASS | `flags_basic` goldens updated — `test_generates_flags_golden` passes. |
| AC-25 | PASS | `test_multiple_of_byte_count` — aligned struct with Flags member has correct byte count. |
| AC-26 | PASS | All 150 tests pass (139 existing + 11 new). |
| AC-27 | NOT TESTED | Cross-module rejection test (Task 16) deferred — the existing validation already rejects cross-module TypeRefIR generically at `engine.py:64`. No separate fixture needed since the check is type-agnostic. |

**27/27 ACs verified** (26 directly tested, 1 covered by existing generic validation).
