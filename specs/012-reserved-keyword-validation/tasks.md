# Tasks — 012-reserved-keyword-validation

**Spec:** `specs/012-reserved-keyword-validation/spec.md`
**Plan:** `specs/012-reserved-keyword-validation/plan.md`
**Status:** draft (task_breakdown iteration 1)

## Plan corrections required

The plan referenced two paths/conventions that do not exactly match repo state. Tasks below follow the actual repo state; the implementation retrospect should propose plan amendments.

1. **`CHANGELOG.md` does not exist at the repo root.** The plan (§Implementation Strategy / Commit D) suggested updating it "if the repo maintains one." Verified: there is no `CHANGELOG.md` in the repo. The "update changelog" subtask is dropped.
2. **Integration-test home should be a new file, not `tests/test_validate_engine.py`.** The plan (§Components C-2 / C-5) proposed adding CLI-driven keyword integration tests in `tests/test_validate_engine.py`. That file is currently dedicated to **direct RepoIR unit tests** (no subprocess; constructs IR in-memory and calls `validate_repo` directly — see file docstring "Direct RepoIR unit tests for validation extensions"). Mixing CLI subprocess tests in would break the file's purpose. Existing CLI-driven negative tests live in `tests/test_gen_const_sv.py` (e.g. `test_rejects_pad_suffix_field`). For review hygiene, this feature gets a dedicated file `tests/test_validate_keywords.py` that imports the shared helpers (`copy_tree`, `assert_trees_equal`, `FIXTURES_DIR`, `PROJECT_ROOT`) from `tests.test_gen_const_sv` and defines its own `KeywordValidationTest(unittest.TestCase)` with a local `run_piketype` method (one-time duplication; deliberate per Constitution simplicity preference over premature refactoring).

Both deviations are mechanical, not semantic; the spec and plan's intent is preserved.

---

## Conventions

- Each task is independently buildable. After every task `basedpyright --strict` and `python -m unittest` MUST pass.
- Tasks are grouped by the four plan commits (A–D). Within each commit, tasks are ordered by dependency.
- File paths are relative to repo root unless absolute. Verified existence noted with ✓ at the path's first appearance.
- A task's "Verify" steps describe what the implementer must check before marking the task complete.

---

## Commit A — `keywords.py` and snapshot unit test

### T-001. Create `src/piketype/validate/keywords.py` skeleton with frozen sets

**Description.** Create a new module containing four frozen sets (SV, C++, Python hard, Python soft) and the `keyword_languages(identifier)` helper function. No wiring to the engine yet.

**Files to create.**
- `src/piketype/validate/keywords.py`

**Files to modify.** None.

**Implementation notes.**
- Follow Constitution coding standards: `from __future__ import annotations`, frozenset literals, keyword-only function args.
- Top-of-file comment per spec NFR-5: list IEEE 1800-2017 + 1800-2023 standard refs (call out the 2023-only additions explicitly: `nettype`, `interconnect`, plus any other 2023 reserved-word additions discovered while sourcing the standard); ISO C++20 ref (N4861) with the explicit decisions on contextual identifiers (`import`, `module` IN; `final`, `override` OUT; coroutine keywords `co_await`/`co_yield`/`co_return` are reserved keywords, not contextual); CPython patch version of the snapshot (capture the running interpreter's `platform.python_version()` at the time of authoring, e.g. `3.12.7`).
- The SV keyword set is sourced from IEEE 1800-2017 Annex B + IEEE 1800-2023 reserved-keyword additions. List all SV keywords as literal strings. (Reference set: ~248 entries for 1800-2017; the 2023 additions are a small handful.)
- The C++ set is sourced from C++20 reserved keywords + alternative tokens + `import` + `module`. Excludes `final` and `override`. Includes `co_await`, `co_yield`, `co_return`.
- The Python hard set is the literal list from `keyword.kwlist` under the running CPython 3.12.x interpreter. The Python soft set is the literal list from `keyword.softkwlist`. Both captured at authoring time as `frozenset` literals; do NOT compute at runtime.
- `keyword_languages(identifier)` returns `tuple[str, ...]`, alphabetically sorted, labels in `{"C++", "Python", "Python (soft)", "SystemVerilog"}`. Hard Python wins over soft Python (defensive).

**Dependencies.** None (first task).

**Verify.**
- `basedpyright --strict src/piketype/validate/keywords.py` returns 0 errors.
- `python -c "from piketype.validate.keywords import SV_KEYWORDS, CPP_KEYWORDS, PY_HARD_KEYWORDS, PY_SOFT_KEYWORDS, keyword_languages; print(len(SV_KEYWORDS), len(CPP_KEYWORDS), len(PY_HARD_KEYWORDS), len(PY_SOFT_KEYWORDS))"` prints four positive integers.
- `python -c "from piketype.validate.keywords import keyword_languages; print(keyword_languages('type'))"` prints `('Python (soft)', 'SystemVerilog')` under Python 3.12.
- `python -c "from piketype.validate.keywords import keyword_languages; print(keyword_languages('type_id'))"` prints `()`.
- `python -c "from piketype.validate.keywords import keyword_languages; print(keyword_languages('class'))"` prints `('C++', 'Python')`.
- Existing test suite still passes: `python -m unittest discover tests`.

---

### T-002. Add Python snapshot unit test

**Description.** Create `tests/test_keyword_set_snapshot.py` with a single test class. Asserts that `PY_HARD_KEYWORDS == frozenset(keyword.kwlist)` and `PY_SOFT_KEYWORDS == frozenset(keyword.softkwlist)` when the running interpreter is Python 3.12.x. Skips with an explanatory message under any other Python minor version.

**Files to create.**
- `tests/test_keyword_set_snapshot.py`

**Files to modify.** None.

**Implementation notes.**
- Use `unittest.TestCase` and `@unittest.skipUnless(sys.version_info[:2] == (3, 12), "...")`.
- Import the snapshot frozensets from `piketype.validate.keywords` and the live sets from the stdlib `keyword` module.
- Two test methods: `test_hard_keyword_snapshot_matches_keyword_kwlist`, `test_soft_keyword_snapshot_matches_keyword_softkwlist`.

**Dependencies.** T-001.

**Verify.**
- `python -m unittest tests.test_keyword_set_snapshot -v` passes (or skips with reason on non-3.12).
- `basedpyright --strict tests/test_keyword_set_snapshot.py` returns 0 errors.

---

### T-003. Commit A — verify byte parity

**Description.** Run the full test suite and `basedpyright --strict` over the entire `src/` to confirm commit A is clean and byte-stable.

**Files to create.** None.
**Files to modify.** None.

**Dependencies.** T-001, T-002.

**Verify.**
- `basedpyright --strict src/piketype/` returns 0 errors.
- `python -m unittest discover tests` passes.
- `git status` shows only `src/piketype/validate/keywords.py` and `tests/test_keyword_set_snapshot.py` as new files; no other changes.
- Stage and commit: `feat(validate): add reserved-keyword sets and snapshot unit test`. Use a real conventional-commit type and scope from the constitution (`feat`/`fix`/`refactor`/`docs`/`test`/`steel`; scope ∈ {`sv`, `cpp`, `py`, `dsl`, `emitter`, `codegen`, `init`, ...}). For this commit `feat(validate)` is appropriate.

---

## Commit B — Wire validator into `engine.py` + positive smoke fixture

### T-004. Add `_validate_reserved_keywords` and format helpers in `engine.py`

**Description.** Implement the validator helper and two private message formatters. Do NOT yet call the helper from `validate_repo`.

**Files to modify.**
- `src/piketype/validate/engine.py` ✓

**Implementation notes.**
- Add at the bottom of `engine.py` (after the existing helpers):
  - `def _validate_reserved_keywords(*, repo: RepoIR) -> None`
  - `def _format_field_msg(*, module_path: str, kind: str, type_name: str, role: str, identifier: str, langs: tuple[str, ...]) -> str`
  - `def _format_top_level_msg(*, module_path: str, kind: str, identifier: str, langs: tuple[str, ...]) -> str`
- Iteration order from plan §Components C-2:
  ```
  for module in repo.modules:
      check module-name (FR-1.6)
      for const in module.constants:    check const.name
      for type_ir in module.types:
          check type_ir.name (full name)
          if struct: for field in fields: check field.name
          if flags:  for flag in fields: check flag.name
          if enum:   for value in values: check value.name
  ```
- Module-name check: per-language emitted form (per plan §C-2 module-name block). Uses `module.ref.basename`, NOT `python_module_name`. Verified against `src/piketype/backends/sv/view.py:699`.
- Per-identifier check (non-module) uses `keyword_languages(identifier)` from `keywords.py`.
- Error message shape strictly matches FR-3 normative format. Sorted alphabetical language list, comma-joined, "(soft)" annotation inline only when soft-only.
- First-fail: raise `ValidationError` on first hit; do not collect.
- Imports added at the top of the file: `from piketype.validate.keywords import (CPP_KEYWORDS, PY_HARD_KEYWORDS, PY_SOFT_KEYWORDS, SV_KEYWORDS, keyword_languages)`.

**Dependencies.** T-001 (keywords.py exists).

**Verify.**
- `basedpyright --strict src/piketype/validate/engine.py` returns 0 errors.
- `python -m unittest discover tests` still passes — no behavior change yet because the helper is not called.
- Quick manual check: import `_validate_reserved_keywords` and call on an empty `RepoIR` — no exception.

---

### T-005. Wire `_validate_reserved_keywords` into `validate_repo`

**Description.** Add a single call site at the end of `validate_repo` (after `_validate_cross_module_name_conflicts`). Also pre-flight: run the entire existing test suite to surface any incidental fixture breakage.

**Files to modify.**
- `src/piketype/validate/engine.py` ✓

**Implementation notes.**
- Add `_validate_reserved_keywords(repo=repo)` as the last line of `validate_repo`.
- Run existing tests; if any fail with a keyword-collision error, that fixture has an incidental name collision (R-1 in plan). Capture the affected fixture(s) and address in T-008.

**Dependencies.** T-004.

**Verify.**
- `basedpyright --strict src/piketype/` returns 0 errors.
- `python -m unittest discover tests` either passes cleanly OR fails ONLY on incidental keyword collisions in existing fixtures. Document the failures (if any) for T-008.

---

### T-006. Add positive smoke fixture (`type_id` near-miss, AC-7)

**Description.** Create a fixture demonstrating that `type_id` (substring of `type`, not itself a keyword) passes validation and produces the expected golden output.

**Files to create.**
- `tests/fixtures/keyword_near_miss/project/alpha/piketype/types.py`
- `tests/fixtures/keyword_near_miss/project/.gitignore` (if other fixtures follow this convention)
- `tests/goldens/gen/keyword_near_miss/<expected tree>`

**Files to modify.** None.

**Implementation notes.**
- Fixture DSL: a single struct `near_miss_t` with a field named `type_id` (the near-miss). The struct should include a second field to satisfy any existing minimum-field rules (existing `_validate_repo` rejects empty structs).
- Generate the golden by running `piketype gen` against the fixture from a clean working tree (after T-005 is wired) and copying the resulting `gen/` tree to `tests/goldens/gen/keyword_near_miss/`.
- Conform to the existing fixture/golden conventions (mirror `tests/fixtures/struct_sv_basic/` and `tests/goldens/gen/struct_sv_basic/` for shape).

**Dependencies.** T-005.

**Verify.**
- `python -m piketype.cli gen tests/fixtures/keyword_near_miss/project/alpha/piketype/types.py` (run from the fixture project dir) succeeds with exit 0.
- The generated `gen/` tree matches `tests/goldens/gen/keyword_near_miss/` byte-for-byte.

---

### T-007. Create `tests/test_validate_keywords.py` and add smoke-fixture test

**Description.** Create the dedicated test file for keyword validation. Add the first test: positive smoke covering the `keyword_near_miss` fixture (AC-7). Pattern: import shared helpers from `tests.test_gen_const_sv`; define a class `KeywordValidationTest(unittest.TestCase)` with a local `run_piketype` method (mirror the existing one in `test_gen_const_sv.py`).

**Files to create.**
- `tests/test_validate_keywords.py`

**Files to modify.** None.

**Implementation notes.**
- Header: `"""Integration tests for reserved-keyword validation (FR-1..FR-9)."""`
- Imports: `from __future__ import annotations`; `subprocess`, `tempfile`, `os`, `sys`, `unittest`, `pathlib.Path`. From `tests.test_gen_const_sv` import `FIXTURES_DIR`, `GOLDENS_DIR`, `PROJECT_ROOT`, `copy_tree`, `assert_trees_equal`. (Verify those names are top-level in that module; if any aren't, copy them locally with a one-line comment citing the source.)
- Define `class KeywordValidationTest(unittest.TestCase)` with a local `run_piketype(self, repo_dir, cli_arg, *extra_args)` method identical in shape to `test_gen_const_sv.py:45`. Local duplication is intentional per the plan-corrections note.
- First test: `test_keyword_near_miss_type_id_passes` — runs gen against the fixture, asserts `returncode == 0`, calls `assert_trees_equal` against the golden.

**Dependencies.** T-006.

**Verify.**
- `python -m unittest tests.test_validate_keywords -v` passes (or shows just one positive test passing).
- `basedpyright --strict tests/test_validate_keywords.py` returns 0 errors.

---

### T-008. Address incidental fixture breakage (if any from T-005)

**Description.** If T-005 surfaced any existing fixture with an incidental keyword collision (R-1 in plan), repair it: rename the offending DSL identifier and regenerate the affected golden. If no breakage was surfaced, this task is a no-op (mark complete with an explanatory note in the commit message).

**Files to create.** None.
**Files to modify.** Per fixture: `tests/fixtures/<case>/project/...` and `tests/goldens/gen/<case>/...`.

**Implementation notes.**
- For each affected fixture: rename the offending DSL identifier (e.g. `type` → `type_id` if a field; choose a non-colliding rename), regenerate the golden, verify the corresponding integration test still passes.
- Document each rename in the commit message with the rationale: which identifier, which language(s) it collided with, what the rename was.

**Dependencies.** T-005.

**Verify.**
- `python -m unittest discover tests` passes cleanly across all existing test files (post-fix).
- The affected goldens' diffs are limited to the renamed identifier (no unrelated changes).

---

### T-009. Commit B — verify byte parity

**Description.** Run full suite and pyright. Squash T-004..T-008 into a single commit if the implementer prefers, OR keep them as separate commits within commit B's scope.

**Files to create.** None. **Files to modify.** None.

**Dependencies.** T-004, T-005, T-006, T-007, T-008.

**Verify.**
- `basedpyright --strict src/piketype/` returns 0 errors.
- `python -m unittest discover tests` passes (with either no incidental breakage or post-fix passes).
- `git diff --stat <commit-A-sha>..HEAD` shows: new fixture+golden under `keyword_near_miss/`, modifications to `engine.py`, new file `test_validate_keywords.py`. No other unintended files.
- Conventional commit: `feat(validate): wire reserved-keyword check into validate_repo`.

---

## Commit C — Negative test fixtures and tests

### T-010. Negative fixture: struct field `type` (FR-1.2 / AC-1)

**Description.** Create a fixture with a struct containing a field named `type`. Expected behavior: `piketype gen` exits non-zero with stderr containing the FR-3-format substring identifying `field 'type'` as a reserved keyword in `Python (soft), SystemVerilog`.

**Files to create.**
- `tests/fixtures/keyword_struct_field_type/project/alpha/piketype/types.py`

**Files to modify.** None.

**Implementation notes.**
- Fixture DSL: `foo_t = Struct().add_member("type", Logic(2)).add_member("payload", Logic(8))`. (Second field added to avoid tripping any min-field structural rules first.)
- No golden under `tests/goldens/gen/keyword_struct_field_type/` because validation fails before emission.

**Dependencies.** T-009.

**Verify.**
- Manual: `python -m piketype.cli gen <fixture>/...types.py` exits non-zero with the expected stderr substring.

---

### T-011. Negative fixture: flags field `try` (FR-1.3 / AC-6)

**Description.** Create a fixture with a flags type containing a field named `try`. Expected substring: `flag 'try' is a reserved keyword in target language(s): C++, Python`.

**Files to create.**
- `tests/fixtures/keyword_flags_field_try/project/alpha/piketype/types.py`

**Dependencies.** T-009.

**Verify.** Manual `piketype gen` smoke check as in T-010.

---

### T-012. Negative fixture: constant `for` (FR-1.5 / AC-5)

**Description.** Create a fixture with a top-level constant named `for`. Expected substring: `constant 'for' is a reserved keyword in target language(s): C++, Python, SystemVerilog`.

**Files to create.**
- `tests/fixtures/keyword_constant_for/project/alpha/piketype/types.py`

**Dependencies.** T-009.

**Verify.** Manual smoke check.

---

### T-013. Negative fixture: module file `class.py` (FR-1.6 / AC-4)

**Description.** Create a fixture whose DSL file is named `class.py`. Expected substring: `module name 'class' is a reserved keyword in target language(s): C++, Python`.

**Files to create.**
- `tests/fixtures/keyword_module_name_class/project/alpha/piketype/class.py`

**Implementation notes.**
- Module file name `class.py`. The contents define one valid struct so the module isn't empty.
- The CLI invocation in the test passes the path to `class.py` as the cli arg.

**Dependencies.** T-009.

**Verify.** Manual smoke check.

---

### T-014. Positive fixture: module file `logic.py` (FR-1.6 / AC-4b)

**Description.** Create a fixture whose DSL file is named `logic.py`. The SV emitted package is `logic_pkg` (not a keyword), and `logic` is not a keyword in C++ or Python. Expected: validation passes; generated output committed as a golden.

**Files to create.**
- `tests/fixtures/keyword_module_name_logic_passes/project/alpha/piketype/logic.py`
- `tests/goldens/gen/keyword_module_name_logic_passes/<expected tree>`

**Dependencies.** T-009.

**Verify.**
- `piketype gen` succeeds (exit 0).
- Generated tree matches the new golden byte-for-byte.

---

### T-015. Positive fixture: type `class_t` (FR-1.1 / AC-2)

**Description.** Create a fixture with a struct named `class_t` (full name) and a field with a non-keyword name. Expected: validation passes; the type-name `class_t` is not itself a keyword and the base form `class` is not checked. Generated output committed as a golden.

**Files to create.**
- `tests/fixtures/keyword_type_name_class_t_passes/project/alpha/piketype/types.py`
- `tests/goldens/gen/keyword_type_name_class_t_passes/<expected tree>`

**Dependencies.** T-009.

**Verify.**
- `piketype gen` succeeds.
- Tree matches golden.

---

### T-016. Ordering fixture: lowercase enum value `for` (AC-11)

**Description.** Create a fixture with an enum value named `for` (lowercase). The UPPER_CASE structural check should fire BEFORE the keyword check. Expected: stderr contains `value 'for' must be UPPER_CASE` (or the existing exact wording from `engine.py:128`), NOT the keyword-check error wording.

**Files to create.**
- `tests/fixtures/keyword_enum_ordering_for/project/alpha/piketype/types.py`

**Implementation notes.**
- Confirm the existing UPPER_CASE error wording by reading `engine.py` (lines around 126–130). Use that exact substring in the test assertion.

**Dependencies.** T-009.

**Verify.** Manual smoke check.

---

### T-017. Add negative tests in `test_validate_keywords.py`

**Description.** Add seven test methods to `KeywordValidationTest` covering the fixtures from T-010 through T-016.

**Files to modify.**
- `tests/test_validate_keywords.py`

**Implementation notes.**
- Test method names (snake_case, descriptive):
  - `test_struct_field_type_is_rejected` (T-010, AC-1)
  - `test_flags_field_try_is_rejected` (T-011, AC-6)
  - `test_constant_for_is_rejected` (T-012, AC-5)
  - `test_module_name_class_is_rejected` (T-013, AC-4)
  - `test_module_name_logic_is_accepted` (T-014, AC-4b)
  - `test_type_name_class_t_is_accepted` (T-015, AC-2)
  - `test_uppercase_check_fires_before_keyword_check` (T-016, AC-11)
- Each negative test follows the existing pattern: `assertNotEqual(result.returncode, 0)` + `assertIn(<substring>, result.stderr)`.
- Each positive test follows: `assertEqual(result.returncode, 0)` + `assert_trees_equal(self, expected_root, repo_dir / "gen")`.
- The substring used in each negative test is the **structural part** of the FR-3 format (e.g. `field 'type' is a reserved keyword in target language(s): Python (soft), SystemVerilog`), not a full line. This is byte-stable per Constitution principle 3 but still robust against unrelated changes.

**Dependencies.** T-010, T-011, T-012, T-013, T-014, T-015, T-016.

**Verify.**
- `python -m unittest tests.test_validate_keywords -v` passes all seven new tests (plus the smoke from T-007 = 8 total).
- `basedpyright --strict tests/test_validate_keywords.py` returns 0 errors.

---

### T-018. Commit C — verify byte parity

**Description.** Full pyright + suite. Confirm no existing golden under `tests/goldens/gen/<old case>/` has changed (i.e. AC-8 holds).

**Files to create.** None. **Files to modify.** None.

**Dependencies.** T-010..T-017.

**Verify.**
- `basedpyright --strict src/ tests/` returns 0 errors.
- `python -m unittest discover tests` passes.
- `git diff --stat <commit-B-sha>..HEAD -- tests/goldens/gen/` shows ONLY the two new golden trees added in T-014 and T-015 (and the `keyword_near_miss` from T-006 if not yet committed).
- Conventional commit: `test(validate): add keyword-validation fixtures and integration tests`.

---

## Commit D — Documentation

### T-019. Update `docs/architecture.md` with the new validation pass

**Description.** Add one paragraph (or short subsection) to `docs/architecture.md` describing the reserved-keyword validation pass: where it runs in the validation pipeline, what identifiers it checks, what languages it targets, and where the keyword sets are sourced.

**Files to modify.**
- `docs/architecture.md` ✓

**Implementation notes.**
- Read `docs/architecture.md` first to determine the right anchor (likely a section about validation passes or pipeline stages).
- Keep the addition minimal and link to `src/piketype/validate/keywords.py` for the source-of-truth keyword sets.

**Dependencies.** T-018.

**Verify.**
- `git diff docs/architecture.md` shows only an addition (no rewrites of unrelated sections).
- Conventional commit: `docs(validate): document reserved-keyword validation pass`.

---

## Task → AC traceability

| AC    | Task(s)              |
|-------|----------------------|
| AC-1  | T-010, T-017         |
| AC-2  | T-015, T-017         |
| AC-3  | (positive, satisfied implicitly by T-007 smoke + UPPER_CASE-passing enum values; no separate fixture required because exact-case behavior is encoded in `keyword_languages()` and tested via T-001 smoke checks) |
| AC-4  | T-013, T-017         |
| AC-4b | T-014, T-017         |
| AC-5  | T-012, T-017         |
| AC-6  | T-011, T-017         |
| AC-7  | T-006, T-007         |
| AC-8  | T-008 (incidental repair if needed) + T-018 (verification) |
| AC-9  | T-001 (single-file keyword module by construction) |
| AC-10 | (deterministic-by-construction; no separate test required per plan §Testing Strategy) |
| AC-11 | T-016, T-017         |

## Task → FR traceability

| FR    | Task(s)              |
|-------|----------------------|
| FR-1.1 | T-004, T-015         |
| FR-1.2 | T-004, T-010         |
| FR-1.3 | T-004, T-011         |
| FR-1.4 | T-004 (covered by code path; no negative test directly possible — see AC-11/T-016) |
| FR-1.5 | T-004, T-012         |
| FR-1.6 | T-004, T-013, T-014  |
| FR-2  | T-001 (data sources, in-source comment) |
| FR-3  | T-004 (format helpers); T-010..T-013 (fixtures exercise the format) |
| FR-4  | T-001 (exact-case via `frozenset` membership); positive coverage via T-007 (`type_id` near-miss) |
| FR-5  | T-005 (entry point at end of `validate_repo`) |
| FR-6  | T-004 (raises existing `ValidationError`) |
| FR-7  | T-004 (first-fail loop ordering); T-016 (precedence with structural validation) |
| FR-8  | T-001 + T-004 (all three keyword sets always consulted) |
| FR-9  | T-005 (placement after existing checks); T-016 (ordering verification) |
| NFR-1 | (algorithmic; no test) |
| NFR-2 | (deterministic-by-construction) |
| NFR-3 | T-002 (Python snapshot canary); T-006/T-007/T-010..T-017 (per-kind fixtures) |
| NFR-4 | T-001 (literal frozensets, no runtime `keyword` import in `keywords.py`) |
| NFR-5 | T-001 (in-source comment); T-019 (`docs/architecture.md`) |
