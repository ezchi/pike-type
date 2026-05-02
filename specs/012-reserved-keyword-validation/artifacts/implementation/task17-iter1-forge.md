# Task 17: Add 8 negative + positive tests in test_validate_keywords.py — Forge Iteration 1

## Files Changed

- `tests/test_validate_keywords.py` — extended. Added 8 new test methods (4 positive, 4 negative) covering T-009..T-016. Total in this file: 9 (1 from T-007 smoke + 8 new). Reorganized into `# -- Positive tests --` and `# -- Negative tests --` sections.

## Test method ↔ AC mapping

| Test method                                       | AC ref | Fixture                                  |
|---------------------------------------------------|--------|------------------------------------------|
| `test_keyword_near_miss_type_id_passes`           | AC-7   | `keyword_near_miss`                      |
| `test_module_name_logic_is_accepted`              | AC-4b  | `keyword_module_name_logic_passes`       |
| `test_type_name_class_t_is_accepted`              | AC-2   | `keyword_type_name_class_t_passes`       |
| `test_enum_value_while_is_accepted`               | AC-3   | `keyword_enum_value_while_passes`        |
| `test_struct_field_type_is_rejected`              | AC-1   | `keyword_struct_field_type`              |
| `test_flags_field_try_is_rejected`                | AC-6   | `keyword_flags_field_try`                |
| `test_constant_for_is_rejected`                   | AC-5   | `keyword_constant_for`                   |
| `test_module_name_class_is_rejected`              | AC-4   | `keyword_module_name_class`              |
| `test_uppercase_check_fires_before_keyword_check` | AC-11  | `keyword_enum_ordering_for`              |

## Key Implementation Decisions

- **Negative-test substring assertions target the structural part of the FR-3 format.** Each `assertIn` matches the most diagnostic chunk (identifier name + role + language list) so the test is robust to non-semantic wording changes elsewhere in the message but fails loudly on language-list drift (which is the actual regression risk).
- **Positive tests use `assert_trees_equal`** for byte-for-byte golden comparison (existing convention).
- **AC-11 negative test asserts both `"UPPER_CASE" in stderr` and `"reserved keyword" NOT in stderr`** to pin the precedence direction (structural check wins).
- **Docstrings cite the AC ref** in each test method so future readers can trace test → spec without leaving the file.

## Deviations from Plan

None.

## Tests Added

9 total in `test_validate_keywords.py`. Verification:

- `.venv/bin/python -m unittest tests.test_validate_keywords -v` → 9 tests, OK.
- Full suite: 303 tests, OK (3 skipped — 2 from snapshot canary on Python 3.13, 1 unrelated pre-existing skip).
