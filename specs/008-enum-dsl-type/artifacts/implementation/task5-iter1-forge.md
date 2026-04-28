# Task 5: Validation — Forge Iteration 1

## Files Changed
- `src/piketype/validate/engine.py` — modified. Added EnumIR validation block, enum literal collision check, enum value vs generated identifier check.

## Key Implementation Decisions
- EnumIR block checks: non-empty, UPPER_CASE names, no duplicate names, no duplicate resolved values, non-negative, width in [1,64], values fit width.
- `_validate_enum_literal_collision()` checks enum value names vs constants and vs other enums in same module.
- `_validate_generated_identifier_collision()` extended to also check enum value names vs reserved generated identifiers.

## Deviations from Plan
- None.
