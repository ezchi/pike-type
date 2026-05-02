# Task 14: Positive fixture — type `class_t` (AC-2) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_type_name_class_t_passes/project/.git/HEAD` — marker.
- `tests/fixtures/keyword_type_name_class_t_passes/project/alpha/piketype/types.py` — defines `class_t = Struct().add_member("addr", Logic(8)).add_member("payload", Logic(16))`.
- `tests/goldens/gen/keyword_type_name_class_t_passes/...` — 13 generated files.

## Key Implementation Decisions

- `class_t` is the full type name. The keyword check inspects `class_t` against the keyword sets — `class_t` is not a keyword in any language (only the bare `class` is). Per FR-1.1 the base form `class` is NOT checked. The fixture proves this.
- Two non-keyword fields (`addr`, `payload`).

## Deviations from Plan

None.

## Tests Added

`test_type_name_class_t_is_accepted` (T-017). Verified by `assert_trees_equal` against the golden.
