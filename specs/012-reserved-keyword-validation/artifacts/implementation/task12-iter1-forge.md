# Task 12: Negative fixture — module file `class.py` (AC-4) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_module_name_class/project/.git/HEAD` — repo-root marker.
- `tests/fixtures/keyword_module_name_class/project/alpha/piketype/class.py` — DSL module file named `class.py` (Python keyword as filename). Loader uses `importlib.util.spec_from_file_location` (verified at `src/piketype/loader/python_loader.py:129`), which loads keyword-named files unproblematically.

## Key Implementation Decisions

- File contents are a minimal valid struct so the module isn't empty (existing rule).
- Confirms gauge-audit point G in the iter-2 task-breakdown review: the loader does NOT use the `import` statement, so files named after Python keywords load fine and the validator gets to fire.

## Deviations from Plan

None.

## Tests Added

`test_module_name_class_is_rejected` (T-017). Manual run confirms `module name 'class' is a reserved keyword in target language(s): C++, Python` (note: NOT SystemVerilog because the SV emitted form is `class_pkg`, not a keyword).
