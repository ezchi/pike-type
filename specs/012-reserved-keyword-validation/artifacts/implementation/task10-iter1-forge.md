# Task 10: Negative fixture — flags field `try` (AC-6) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_flags_field_try/project/.git/HEAD` — repo-root marker.
- `tests/fixtures/keyword_flags_field_try/project/alpha/piketype/types.py` — `mode_t` flags type with two flags (`try`, `ready`).

## Key Implementation Decisions

- Two-flag flags type to avoid empty-flags structural rule firing.
- `ready` is non-keyword in all three languages (verified) so the keyword rule fires precisely on `try`.

## Deviations from Plan

None.

## Tests Added

`test_flags_field_try_is_rejected` (T-017). Manual run confirms `flag 'try' is a reserved keyword in target language(s): C++, Python`.
