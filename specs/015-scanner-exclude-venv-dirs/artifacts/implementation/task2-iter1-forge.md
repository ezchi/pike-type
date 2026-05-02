# Task 2: Create focused unit test file `tests/test_scanner.py` — Forge Iteration 1

## Files Changed
- `tests/test_scanner.py` — new. Four `unittest.TestCase` methods covering AC-1, AC-3, AC-4, AC-5, FR-7/NFR-2.

## Key Implementation Decisions
- **Module-level `_touch(path: Path) -> None` helper** that creates parent dirs and writes an empty file. The plan said "inline if cleaner"; with four tests each touching multiple files, a one-line helper is cleaner than repeating `path.parent.mkdir(parents=True, exist_ok=True)` and `path.write_text("")` inline. Underscore prefix marks it as private to the test module.
- **`tempfile.TemporaryDirectory()` per test** (no class-level fixture, no `setUp`). Each test owns its own root, so tests are independent and parallelizable in any future test runner. This is also the pattern the Constitution §Testing prescribes for golden-file integration tests; reusing it for unit tests keeps style consistent.
- **`test_excludes_venv_duplicate`** uses the exact path shape from the original bug report: `.venv/lib/python3.13/site-packages/piketype/example/foo.py`. Asserts `==` on full `list[Path]`, not just length, so any future reordering or extra inclusion is caught.
- **`test_all_six_excluded_names_rejected`** iterates the six excluded names from the spec's FR-3 explicitly (not imported from `scanner.EXCLUDED_DIRS`) — this is intentional: the test enforces the spec's enumeration as the source of truth, so a regression that drops or renames one of the six entries fails the test even if `EXCLUDED_DIRS` is updated. Each name gets a `<name>/piketype/foo.py` file (under a `piketype/` ancestor, satisfying `is_under_piketype_dir`); confirms AC-4 (excluded-dir filter beats `is_under_piketype_dir`) and AC-5 (all six names rejected).
- **`test_clean_repo_unchanged`** is the regression sentinel for AC-3: a clean repo with one real module returns just that module.
- **`test_sorted_output`** asserts both that the result equals its own `sorted(...)` AND the explicit ascending order `[aaa, zzz]`. Two assertions because the first catches accidental sort removal; the second catches accidental reverse-sort.
- **No use of `unittest.subTest`, `pytest.parametrize`, or `unittest.TestLoader.loadTestsFromName`**. Per Constitution §Testing: "Tests use `unittest.TestCase`, not pytest fixtures or parametrize" — and Clarification C-4 reaffirms it.
- **`if __name__ == "__main__": unittest.main()`** trailer matches the convention used in `tests/test_loader.py` and several others (verified by sampling).

## Deviations from Plan
- None on requirements.
- One textual deviation: I named the helper `_touch` (per the plan's suggestion of `_touch(path: Path) -> None`), and inlined its body into two function statements rather than splitting into more helper functions. The plan said "inline if cleaner" — this is the cleaner shape.

## Tests Added
- `tests/test_scanner.py::FindPiketypeModulesTests::test_excludes_venv_duplicate` — AC-1
- `tests/test_scanner.py::FindPiketypeModulesTests::test_all_six_excluded_names_rejected` — AC-4 + AC-5
- `tests/test_scanner.py::FindPiketypeModulesTests::test_clean_repo_unchanged` — AC-3
- `tests/test_scanner.py::FindPiketypeModulesTests::test_sorted_output` — FR-7 / NFR-2
