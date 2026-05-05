# Task 15: Positive fixture — enum value `WHILE` (AC-3) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_enum_value_while_passes/project/.git/HEAD` — marker.
- `tests/fixtures/keyword_enum_value_while_passes/project/alpha/piketype/types.py` — `state_t` enum with `IDLE` and `WHILE`.
- `tests/goldens/gen/keyword_enum_value_while_passes/...` — 13 generated files.

## Key Implementation Decisions

- `WHILE` (UPPER_CASE) is a valid identifier in C++/SV/Python. Lowercase `while` IS a keyword in all three. Per FR-4 the keyword check is exact-case, so `WHILE` passes. The UPPER_CASE structural rule is also satisfied.
- Sibling value `IDLE` keeps the enum non-trivially populated.

## Deviations from Plan

None.

## Tests Added

`test_enum_value_while_is_accepted` (T-017). Verified by `assert_trees_equal`.
