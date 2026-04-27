# Validation Report — Spec 002: `--namespace` CLI Argument

## Test Results

**86 tests, 0 failures, 0 errors.**

- 33 unit tests (`test_namespace_validation.py`)
- 10 new integration tests (`test_gen_const_sv.py`)
- 43 existing tests (all pass unchanged)

## Acceptance Criteria Verification

| AC | Description | Test | Status |
|----|-------------|------|--------|
| 1 | Namespace is `foo::bar::<basename>` | `test_namespace_override_multi_module` | PASS |
| 2 | Guard is `FOO_BAR_<BASENAME>_TYPES_HPP` | `test_namespace_override_multi_module` | PASS |
| 3 | No `--namespace` = identical output | All existing golden tests | PASS |
| 4 | `foo::::bar` rejected (empty segment) | `test_namespace_rejects_empty_segment` | PASS |
| 5 | `123bad` rejected (non-identifier) | `test_namespace_rejects_non_identifier` | PASS |
| 6 | `class` rejected (keyword) | `test_namespace_rejects_cpp_keyword` | PASS |
| 7 | `foo__bar` rejected (double underscore) | `test_namespace_rejects_double_underscore` | PASS |
| 8 | `_foo` rejected (leading underscore) | `test_namespace_rejects_leading_underscore` | PASS |
| 9 | `std::types` rejected (std first) | `test_namespace_rejects_std_first_segment` | PASS |
| 10 | `foo_` rejected (trailing underscore) | `test_namespace_rejects_trailing_underscore` | PASS |
| 11 | `foo::_bar` rejected (underscore non-first) | `test_namespace_rejects_leading_underscore_non_first` | PASS |
| 12 | SV/Python/manifest/runtime unchanged | `test_namespace_override_multi_module` (full tree) | PASS |
| 13 | Duplicate basenames rejected | `test_namespace_rejects_duplicate_basenames` | PASS |
| 14 | Multi-module golden test | `test_namespace_override_multi_module` (2 modules) | PASS |
| 15 | Negative tests per category (9) | 9 individual negative tests | PASS |
| 16 | Existing golden tests unchanged | All 15 existing golden/negative tests | PASS |

## Files Changed

| File | Change |
|------|--------|
| `src/typist/validate/namespace.py` | New: validation logic |
| `src/typist/cli.py` | Modified: `--namespace` arg on `gen` |
| `src/typist/commands/gen.py` | Modified: plumbing + duplicate check |
| `src/typist/backends/cpp/emitter.py` | Modified: namespace override |
| `tests/test_namespace_validation.py` | New: 33 unit tests |
| `tests/test_gen_const_sv.py` | Modified: helper + 10 integration tests |
| `tests/fixtures/namespace_override/` | New: multi-module fixture |
| `tests/goldens/gen/namespace_override/` | New: golden output |
