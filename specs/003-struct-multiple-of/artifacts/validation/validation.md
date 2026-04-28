# Validation Report — Spec 003: Struct `multiple_of(N)` Alignment

## Test Results

**101 tests passed, 0 failed** (86 pre-existing + 15 new).

## Acceptance Criteria Verification

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 | PASS | `aligned_t`: SV golden shows `LP_ALIGNED_WIDTH=17`, `LP_ALIGNED_BYTE_COUNT=4`, `_align_pad` field. Helper class `WIDTH=LP_ALIGNED_WIDTH`, `BYTE_COUNT=LP_ALIGNED_BYTE_COUNT`. Python `BYTE_COUNT=4`, `WIDTH=17`. |
| AC-2 | PASS | `no_extra_pad_t`: SV golden shows `LP_NO_EXTRA_PAD_BYTE_COUNT=3`, no `_align_pad`. Python `BYTE_COUNT=3`. |
| AC-3 | PASS | `test_multiple_of_zero`, `test_multiple_of_negative`, `test_multiple_of_not_multiple_of_8_val_5`, `test_multiple_of_not_multiple_of_8_val_3` all raise `ValidationError` with correct messages. |
| AC-4 | PASS | `test_multiple_of_bool` raises `ValidationError("must be int")`. |
| AC-5 | PASS | `test_multiple_of_twice` raises `ValidationError("already set")`. |
| AC-6 | PASS | `test_add_member_after_multiple_of` raises `ValidationError("cannot add")`. |
| AC-7 | PASS | All 86 pre-existing golden-file tests pass unchanged. |
| AC-8 | PASS | `test_generates_struct_multiple_of` golden-file comparison passes for all 3 backends. |
| AC-9 | PASS | SV golden: `pack_aligned` and `unpack_aligned` use `LP_ALIGNED_WIDTH` (17, data-only). No `_align_pad` in pack/unpack. |
| AC-10 | PASS | `test_aligned_struct_round_trip`, `test_no_extra_pad_round_trip`, `test_outer_nested_round_trip` all pass. |
| AC-11 | PASS | `basedpyright` reports 67 errors (same count as pre-existing baseline). No new errors introduced. |
| AC-12 | PASS | 7 negative `unittest.TestCase` methods cover all specified values with message substring assertions. |
| AC-13 | PASS | `inner_t` with `multiple_of(16)` used as field in `outer_t`. Golden shows `LP_OUTER_BYTE_COUNT=3` (inner 2 bytes + y 1 byte). Runtime `test_outer_nested_round_trip` passes. |

## basedpyright

67 errors (pre-existing baseline, no new errors added). 2 new `reportPrivateUsage` warnings for `_alignment` access in `freeze.py`, offset by 2 pre-existing errors resolved.
