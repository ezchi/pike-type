# Task 13: Positive fixture — module file `logic.py` (AC-4b) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_module_name_logic_passes/project/.git/HEAD` — marker.
- `tests/fixtures/keyword_module_name_logic_passes/project/alpha/piketype/logic.py` — single struct `handler_t`.
- `tests/goldens/gen/keyword_module_name_logic_passes/...` — 13 generated files captured.

## Key Implementation Decisions

- `logic` is a SystemVerilog keyword; SV emitted form is `logic_pkg` which is NOT a keyword. C++ namespace and Python module both emit bare `logic` which is not a C++/Python keyword. Hence the module-name check accepts.
- Single-struct module produces a complete codegen tree (SV pkg + test_pkg, C++ header, Python module, runtime files, manifest) — golden captures all 13 files.

## Deviations from Plan

None.

## Tests Added

`test_module_name_logic_is_accepted` (T-017). Verified by `assert_trees_equal` against the golden.
