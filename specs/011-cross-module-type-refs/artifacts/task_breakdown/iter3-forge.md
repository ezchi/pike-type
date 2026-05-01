# Tasks — Spec 011 Cross-Module Type References

Tasks are grouped by the 6-commit staging plan. Each task names its files, dependencies, and verification criteria. Tasks within the same commit can be partially parallelized but the order shown is the safest sequential path.

The "byte-parity at every commit" rule (project memory) is verified at the end of each commit's last task by running the full existing test suite.

---

## Commit A — Loader Isolation

### T1: Implement `prepare_run` and `load_or_get_module` in `python_loader.py`

**Description.** Refactor `src/piketype/loader/python_loader.py` to add per-run scoped `sys.modules` snapshot/restore. Remove `load_module_from_path` entirely; replace with `prepare_run` (context manager) and `load_or_get_module` (cached module loader). `load_or_get_module` raises `RuntimeError` if called outside an active `prepare_run` scope.

**Files:**
- `src/piketype/loader/python_loader.py` — modify (rewrite)

**Dependencies:** none.

**Verification:**
- `basedpyright src/piketype` passes.
- Module loads still work end-to-end (verified in T2 + T3).

---

### T2: Migrate `run_gen` to use `prepare_run`

**Description.** Update `src/piketype/commands/gen.py` to wrap the module-loading loop in `prepare_run(repo_root, module_paths)` and call `load_or_get_module(path, repo_root=repo_root)` instead of `load_module_from_path`.

**Files:**
- `src/piketype/commands/gen.py` — modify

**Dependencies:** T1.

**Verification:**
- All existing integration tests in `tests/test_gen_*.py` pass byte-identical to current goldens.

---

### T3: Migrate test helpers to use `prepare_run`

**Description.** Update `tests/test_view_py.py`, `tests/test_view_cpp.py`, `tests/test_view_sv.py` (and any other test that calls `load_module_from_path` — verify with `grep -RIn "load_module_from_path" tests/`) to use `prepare_run` + `load_or_get_module`.

**Files:**
- `tests/test_view_py.py` — modify
- `tests/test_view_cpp.py` — modify
- `tests/test_view_sv.py` — modify
- (any other callers) — modify

**Dependencies:** T1.

**Verification:**
- `python -m unittest discover tests/` passes with all existing tests green.

---

### T4: Add `tests/test_loader.py` for snapshot/restore + identity

**Description.** Create unit tests for the new loader contract:
- Test 1: `prepare_run` snapshots existing entries and pops owned keys; on exit, restores originals.
- Test 2: Loading two different fixture repos sequentially leaves no piketype modules in `sys.modules` after the second run.
- Test 3: Within a single run, accessing `byte_t` via `bar.module.__dict__["byte_t"]` returns the same object as `foo.module.__dict__["byte_t"]` (identity stability).
- Test 4: `load_or_get_module` raises `RuntimeError` when called outside `prepare_run`.

**Files:**
- `tests/test_loader.py` — create

**Dependencies:** T1, T2, T3.

**Verification:** `python -m unittest tests.test_loader` passes.

---

### T5: Capture perf baseline + add `tests/test_perf_gen.py`

**Description.** Capture pre-Commit-A perf baseline by checking out `develop` (or the immediate-pre-Commit-A SHA), running the perf harness on every fixture, and recording medians to `tests/perf_baseline.json`. Then implement `tests/test_perf_gen.py` per the plan (env-gated `PIKETYPE_PERF_TEST=1`, fails on >5% total or >10% per-fixture regression).

**Files:**
- `tests/perf_baseline.json` — create
- `tests/test_perf_gen.py` — create

**Dependencies:** T1, T2, T3 (loader must work end-to-end before measuring).

**Verification:** `PIKETYPE_PERF_TEST=1 python -m unittest tests.test_perf_gen` passes (Commit A should not regress vs. pre-Commit-A baseline).

---

### T6 — Commit-A integration check

**Description.** Run the full existing test suite, verify byte-identical existing goldens. Confirm `basedpyright src/piketype tests/` is clean. Commit as Commit A.

**Files:** none.

**Dependencies:** T1, T2, T3, T4, T5.

**Verification:** `python -m unittest discover tests/` all green; `basedpyright src/piketype tests/` zero errors. Tag candidate: `commit-a-loader-isolation`.

---

## Commit B — Repo-Wide Type Index Plumbing (Full Switchover)

### T7: Add `build_repo_type_index`

**Description.** Add `src/piketype/ir/repo_index.py` containing `build_repo_type_index(repo: RepoIR) -> dict[tuple[str, str], TypeDefIR]`. Iterate every `module.types` and key by `(module.ref.python_module_name, type_def.name)`. Add a unit test verifying empty repo, single-module repo, and multi-module repo with same-named types in different modules.

**Files:**
- `src/piketype/ir/repo_index.py` — create
- `tests/test_repo_index.py` — create

**Dependencies:** T6 (Commit A complete).

**Verification:** `python -m unittest tests.test_repo_index` passes.

---

### T8: Plumb repo-wide index through SV emitter and view

**Description.** Update `src/piketype/backends/sv/emitter.py` to call `build_repo_type_index(repo)` once and pass to every `build_synth_module_view_sv` and `build_test_module_view_sv` call as a new keyword argument `repo_type_index`. Update `src/piketype/backends/sv/view.py` so that every `TypeRefIR` resolution reads `repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]` instead of `type_index[field.type_ir.name]`. Remove the local `{t.name: t for t in module.types}` shortcut wherever a `TypeRefIR` is dereferenced.

**Files:**
- `src/piketype/backends/sv/emitter.py` — modify
- `src/piketype/backends/sv/view.py` — modify

**Dependencies:** T7.

**Verification:** All existing SV goldens byte-identical (run `python -m unittest tests.test_view_sv tests.test_gen_const_sv tests.test_gen_struct_sv` etc.).

---

### T9: Plumb repo-wide index through Python emitter and view

**Description.** Mirror T8 for the Python backend.

**Files:**
- `src/piketype/backends/py/emitter.py` — modify
- `src/piketype/backends/py/view.py` — modify

**Dependencies:** T7.

**Verification:** All existing Python goldens byte-identical.

---

### T10: Plumb repo-wide index through C++ emitter and view

**Description.** Mirror T8 for the C++ backend.

**Files:**
- `src/piketype/backends/cpp/emitter.py` — modify
- `src/piketype/backends/cpp/view.py` — modify

**Dependencies:** T7.

**Verification:** All existing C++ goldens byte-identical.

---

### T11 — Commit-B integration check

**Description.** Run full test suite. Confirm all goldens byte-identical. Run `basedpyright src/piketype tests/` and confirm zero errors. Commit as Commit B.

**Files:** none.

**Dependencies:** T7, T8, T9, T10.

**Verification:** Full suite green; `basedpyright src/piketype tests/` zero errors; perf gate passes.

---

## Commit C — Freeze Cross-Module IR + Validation Acceptance + Manifest

### T12: Implement `_collect_module_dependencies`

**Description.** Add `_collect_module_dependencies(module_ir: ModuleIR) -> tuple[ModuleDependencyIR, ...]` to `src/piketype/dsl/freeze.py`. Walks every `TypeRefIR` and `ConstRefExprIR` in the module's types and constants (struct fields, scalar alias `width_expr`, struct field `width_expr`, enum value `expr`, constant `expr`); filters cross-module entries; deduplicates and sorts by `(target_python_module_name, kind)`. Update `freeze_module` to call this and pass the result as `dependencies=...` to `ModuleIR(...)`. Also add a docstring on `_freeze_field_type` documenting the R8 invariant: a cross-module `TypeRefIR` always points to a top-level named DSL type (never `ScalarTypeSpecIR`), because only named bindings are importable across modules and `_freeze_field_type` only emits `TypeRefIR` for objects in `type_definition_map`.

**Files:**
- `src/piketype/dsl/freeze.py` — modify

**Dependencies:** T11.

**Verification:** Existing fixtures still byte-identical (no existing fixture has cross-module refs, so dependencies remain empty).

---

### T13: Remove cross-module rejection in validate/engine.py

**Description.** Remove `engine.py:69-73` cross-module rejection. Update unknown-target lookup at lines 74-76 to consult the repo-level `type_index` (already keyed by `(module, name)` at line 19-23). Update unknown-target error message to FR-5 wording: `"struct {struct_name} field {field_name} references unknown type {module}::{type_name}"`.

**Files:**
- `src/piketype/validate/engine.py` — modify

**Dependencies:** T11.

**Verification:** Existing fixtures still pass validation.

---

### T14: Update manifest serializer for `dependencies`

**Description.** Update `src/piketype/manifest/write_json.py` to serialize each `ModuleIR.dependencies` entry as `{"target_module": <python_module_name>, "kind": <type_ref|const_ref>}`. Sort by `(target_module, kind)`. Empty lists serialize as `[]` (preserving existing manifest goldens).

**Files:**
- `src/piketype/manifest/write_json.py` — modify

**Dependencies:** T12.

**Verification:** All existing manifest goldens byte-identical (still empty `[]`).

---

### T15: Add freeze unit tests

**Description.** Add `tests/test_freeze.py` cases for:
- Cross-module `TypeRefIR` is produced when a struct member references a type from another module.
- Cross-module `ConstRefExprIR` is produced when a scalar alias width references a Const from another module.
- `_collect_module_dependencies` returns deduplicated, sorted entries.

**Files:**
- `tests/test_freeze.py` — create or extend

**Dependencies:** T12.

**Verification:** `python -m unittest tests.test_freeze` passes.

---

### T16: Add validation unit tests for unknown-type rejection

**Description.** Add cases to `tests/test_validate_engine.py` constructing a `RepoIR` directly with a struct field whose `TypeRefIR.module` and `TypeRefIR.name` do not exist in any loaded module's types. Assert the FR-5 error message.

**Files:**
- `tests/test_validate_engine.py` — extend

**Dependencies:** T13.

**Verification:** `python -m unittest tests.test_validate_engine` passes.

---

### T17 — Commit-C integration check

**Description.** Run full suite. All existing goldens byte-identical. Run `basedpyright src/piketype tests/` and confirm zero errors. Commit as Commit C.

**Files:** none.

**Dependencies:** T12, T13, T14, T15, T16.

**Verification:** Full suite green; `basedpyright src/piketype tests/` zero errors; perf gate passes.

---

## Commit D — Template-First Emission + Cross-Module Fixture/Goldens

### T18: Refactor SV `view.py:704` into template

**Description.** Remove the `f"  import {module.ref.basename}_pkg::*;"` construction at `src/piketype/backends/sv/view.py:704`. Update `src/piketype/backends/sv/templates/module_test.j2` to render the same-module synth import using the existing `module.ref.basename` view-model field directly (`{% raw %}  import {{ module.ref.basename }}_pkg::*;{% endraw %}`).

**Files:**
- `src/piketype/backends/sv/view.py` — modify
- `src/piketype/backends/sv/templates/module_test.j2` — modify

**Dependencies:** T17.

**Verification:** All existing SV `_test_pkg.sv` goldens byte-identical.

---

### T19: Add SV cross-module import view-model fields and template rendering

**Description.** Add `synth_cross_module_target_basenames`, `cross_module_synth_target_basenames`, `cross_module_test_target_basenames` to `SvSynthModuleView` and `SvTestModuleView` (semantic parts only — basenames). Populate them in `build_synth_module_view_sv` and `build_test_module_view_sv` by walking the module's types' fields and collecting unique cross-module target basenames sorted by `target.python_module_name`. Update `module_synth.j2` and `module_test.j2` to render the imports per FR-9 and FR-10 layout (CL-1, CL-3 whitespace).

**Files:**
- `src/piketype/backends/sv/view.py` — modify
- `src/piketype/backends/sv/templates/module_synth.j2` — modify
- `src/piketype/backends/sv/templates/module_test.j2` — modify

**Dependencies:** T18.

**Verification:** Existing SV goldens still byte-identical (no existing fixture has cross-module refs, so the new blocks are empty).

---

### T20: Add Python cross-module import view-model field and template rendering

**Description.** Add `cross_module_imports: tuple[PyCrossModuleImportView, ...]` to `PyModuleView`, where `PyCrossModuleImportView` is a frozen dataclass with `target_types_module: str` and `wrapper_class_name: str`. Populate from cross-module `TypeRefIR`s. Update `module.j2` to render `from {{ imp.target_types_module }} import {{ imp.wrapper_class_name }}` per FR-11 / CL-2 layout.

**Files:**
- `src/piketype/backends/py/view.py` — modify
- `src/piketype/backends/py/templates/module.j2` — modify

**Dependencies:** T17.

**Verification:** Existing Python goldens still byte-identical.

---

### T21: Add C++ cross-module include + qualified field type

**Description.** Add `cross_module_include_paths: tuple[str, ...]` to `CppModuleView`. Update `_build_struct_field_view` (and `_render_cpp_struct_pack_step`, `_render_cpp_struct_unpack_step`, `_is_*_ref` helpers, default-construct, clone) to detect cross-module `TypeRefIR` and emit fully-qualified field type via `_build_namespace_view(module=field_ir.type_ir.module, namespace=<emit_namespace>)` prefixed with `::`. Update `module.j2` to render `#include "{{ p }}"`.

**Files:**
- `src/piketype/backends/cpp/view.py` — modify
- `src/piketype/backends/cpp/templates/module.j2` — modify

**Dependencies:** T17.

**Verification:** Existing C++ goldens still byte-identical.

---

### T22: Create cross-module primary fixture

**Description.** Create `tests/fixtures/cross_module_type_refs/project/` containing `pyproject.toml` (or marker), `alpha/piketype/__init__.py`, `alpha/piketype/foo.py` (defining `byte_t`, `addr_t`, `cmd_t`, `perms_t`), and `alpha/piketype/bar.py` (defining `bar_t` with all four cross-module members).

**Files:**
- `tests/fixtures/cross_module_type_refs/project/pyproject.toml` — create
- `tests/fixtures/cross_module_type_refs/project/alpha/piketype/__init__.py` — create
- `tests/fixtures/cross_module_type_refs/project/alpha/piketype/foo.py` — create
- `tests/fixtures/cross_module_type_refs/project/alpha/piketype/bar.py` — create

**Dependencies:** T19, T20, T21.

**Verification:** Manually run `cd tests/fixtures/cross_module_type_refs/project && piketype gen alpha/piketype/bar.py` succeeds.

---

### T23: Generate primary fixture goldens

**Description.** Run `piketype gen` on the new fixture, copy generated `gen/` tree to `tests/goldens/gen/cross_module_type_refs/`, and inspect manually against the spec's expected output (specifically the `bar_pkg.sv` snippet and the `import foo_pkg::*;` line). Commit the goldens.

**Files:**
- `tests/goldens/gen/cross_module_type_refs/` — create entire tree

**Dependencies:** T22.

**Verification:** Generated output matches spec example for `bar_pkg.sv`. Each generated file passes manual review.

---

### T24: Add `tests/test_no_inline_imports.py` (AC-23 AST static check)

**Description.** Implement the AST static check per AC-23 covering `Constant`, `JoinedStr`, `BinOp(Add)`, `Call(func=Attribute(attr="format"|"join"|"format_map"))`, and `BinOp(Mod)`. Include named positive cases (legitimate `.join`/`.format`/`%` patterns that are NOT flagged) and negative cases (synthetic bad patterns that ARE flagged). Run the check over `src/piketype/backends/{sv,py,cpp}/{view,emitter}.py` and assert empty result.

**Files:**
- `tests/test_no_inline_imports.py` — create

**Dependencies:** T18 (after `view.py:704` move, the live source must be clean).

**Verification:** `python -m unittest tests.test_no_inline_imports` passes.

---

### T25: Add cross-module integration test

**Description.** Add `tests/test_gen_cross_module.py` that: (1) copies the `cross_module_type_refs` fixture to a temp dir, (2) runs `piketype gen alpha/piketype/bar.py`, (3) byte-compares the entire `gen/` tree against `tests/goldens/gen/cross_module_type_refs/`. Use `unittest.TestCase` per repo convention. Also add an idempotency case (run twice, compare).

**Files:**
- `tests/test_gen_cross_module.py` — create

**Dependencies:** T22, T23.

**Verification:** Test passes.

---

### T26: Generate `--namespace=proj::lib` goldens + namespace integration test

**Description.** Run `piketype gen --namespace=proj::lib alpha/piketype/bar.py` on the cross_module fixture; commit goldens at `tests/goldens/gen/cross_module_type_refs_namespace_proj/`. Add a test case in `tests/test_gen_cross_module.py` that runs `piketype gen --namespace=proj::lib` and compares against this golden tree. Specifically assert that `bar_types.hpp` contains `::proj::lib::foo::byte_t_ct` for the field type.

**Files:**
- `tests/goldens/gen/cross_module_type_refs_namespace_proj/` — create
- `tests/test_gen_cross_module.py` — extend

**Dependencies:** T25.

**Verification:** Test passes.

---

### T26b: Same-process IR identity test (AC-7 part 2)

**Description.** Add a test in `tests/test_loader.py` (or `tests/test_freeze.py`) that loads the `cross_module_type_refs` fixture twice in the same Python process via `prepare_run` + `freeze_repo` and asserts the two `RepoIR` instances are deeply equal. This exercises the AC-7 invariant "Loading the cross-module fixture twice in the same Python process produces identical IR" — distinct from the file-level idempotency test in T25.

**Files:**
- `tests/test_loader.py` or `tests/test_freeze.py` — extend

**Dependencies:** T22, T23 (fixture exists).

**Verification:** Test passes.

---

### T27: Python runtime byte-value test (AC-19)

**Description.** Add `tests/test_runtime_py_cross_module.py` (or extend existing runtime test) that imports `bar_t` and `byte_t_ct` from the generated Python output of the `cross_module_type_refs` fixture and asserts:
- `bar_t(field1=byte_t_ct(0xAB), field2=byte_t_ct(0xCD)).to_bytes() == b"\xab\xcd"` (after constructing the cross-module Enum/Flags/struct members appropriately).
- `bar_t.from_bytes(b"...")` round-trips.

**Files:**
- `tests/test_runtime_py_cross_module.py` — create

**Dependencies:** T23.

**Verification:** Test passes.

---

### T28 — Commit-D integration check

**Description.** Run full suite. Confirm all existing goldens byte-identical. Confirm `tests/test_no_inline_imports` is green. Confirm new cross-module goldens match. Run `basedpyright src/piketype tests/` and confirm zero errors. Commit as Commit D.

**Files:** none.

**Dependencies:** T18-T27.

**Verification:** Full suite green; `basedpyright src/piketype tests/` zero errors; perf gate passes.

---

## Commit E — Validation Extensions

### T29: Replace `_validate_struct_cycles` with repo-level pass

**Description.** Update `src/piketype/validate/engine.py` `_validate_struct_cycles` to build a repo-level graph keyed by `(module_python_name, struct_name)` with edges from any struct field's cross-module-or-same-module struct `TypeRefIR`. Implement N-node cycle detection with deterministic rotation (lex-smallest first). Same-module cycles preserve existing wording (`"recursive struct dependency detected at {name}"`); cross-module cycles use the new format from FR-6.

**Files:**
- `src/piketype/validate/engine.py` — modify

**Dependencies:** T28.

**Verification:** Existing same-module cycle test passes with original wording; new tests in T31 pass.

---

### T30: Implement `_validate_cross_module_name_conflicts` (FR-8)

**Description.** Add `_validate_cross_module_name_conflicts(repo: RepoIR) -> None` to `src/piketype/validate/engine.py`. Implement four sub-rules:
- Local-vs-imported type-name.
- Imported-vs-imported type-name.
- Imported-vs-imported enum literal.
- Local-vs-imported enum literal.

Wire into `validate_repo` after existing per-module validation.

**Files:**
- `src/piketype/validate/engine.py` — modify

**Dependencies:** T28.

**Verification:** Tests in T31 pass.

---

### T31: Add validation tests for FR-6 + FR-8

**Description.** Add `tests/test_validate_engine.py` cases for:
- Cross-module struct cycle 2-node, 3-node, mixed (cycle includes both same-module and cross-module edges).
- FR-8 four sub-cases (each constructed via direct `RepoIR` assembly).

**Files:**
- `tests/test_validate_engine.py` — extend

**Dependencies:** T29, T30.

**Verification:** All cases pass.

---

### T32: Make `check_duplicate_basenames` unconditional + update message (FR-9a)

**Description.** Update `src/piketype/commands/gen.py` to call `check_duplicate_basenames(module_paths=module_paths)` outside the `if namespace is not None:` block. Update the error message in `src/piketype/validate/namespace.py:113-119` from `"--namespace requires unique module basenames..."` to `"piketype requires unique module basenames across the repo..."` (drop the `--namespace` precondition).

**Files:**
- `src/piketype/commands/gen.py` — modify
- `src/piketype/validate/namespace.py` — modify
- `tests/test_namespace_validation.py` — extend (add new test case for duplicate basenames without `--namespace`)

**Dependencies:** T28.

**Verification:** Existing fragment-based assertions in `tests/test_namespace_validation.py:176-182` pass without modification (per CL-8). New test case verifies duplicate basenames are rejected without `--namespace`.

---

### T33: Add `cross_module_struct_multiple_of` fixture + goldens + test

**Description.** Create `tests/fixtures/cross_module_struct_multiple_of/` with foo.py (`byte_t = Logic(8)`) and bar.py (`bar_t = Struct().add_member("b", byte_t).multiple_of(32)`). Generate goldens. Add integration test asserting the golden tree byte-matches.

**Files:**
- `tests/fixtures/cross_module_struct_multiple_of/` — create entire tree
- `tests/goldens/gen/cross_module_struct_multiple_of/` — create entire tree
- `tests/test_gen_cross_module.py` — extend

**Dependencies:** T28.

**Verification:** Test passes.

---

### T34: Add cycle fixture or RepoIR-only test

**Description.** Attempt to construct a Python-loadable cross-module struct cycle in `tests/fixtures/cross_module_cycle/`. If infeasible (Python's import system rejects it), fall back to a `RepoIR`-only unit test in `tests/test_validate_engine.py` that constructs `StructIR` instances with cycling `TypeRefIR`s and asserts the FR-6 cross-module cycle error.

**Files:**
- `tests/fixtures/cross_module_cycle/` — create (if feasible) OR
- `tests/test_validate_engine.py` — extend

**Dependencies:** T29.

**Verification:** Test passes.

---

### T35 — Commit-E integration check

**Description.** Run full suite. All existing goldens byte-identical. New tests pass. Run `basedpyright src/piketype tests/` and confirm zero errors. Commit as Commit E.

**Files:** none.

**Dependencies:** T29-T34.

**Verification:** Full suite green; `basedpyright src/piketype tests/` zero errors; perf gate passes.

---

## Commit F — Constitution Amendment

### T36: Replace constitution constraint #4

**Description.** Update `.steel/constitution.md` line 110 to replace the existing constraint #4 ("No cross-module type references") with the exact replacement text from FR-15 (a 4-bullet block describing cross-module references, cycle detection, name collisions, import emission, and basename uniqueness).

**Files:**
- `.steel/constitution.md` — modify

**Dependencies:** T35.

**Verification:** Manual review against FR-15 text.

---

### T37 — Commit-F integration check + final verification

**Description.** Run full suite one final time. Verify:
- All existing goldens byte-identical.
- All new cross-module fixtures produce expected output.
- `tests/test_no_inline_imports` AC-23 check returns empty.
- `basedpyright src/piketype tests/` zero errors.
- Perf gate within budget (NFR-4).
- Constitution amendment applied.
- **NFR-3 dependency check:** `git diff develop -- pyproject.toml` shows no additions to `[project].dependencies` (no new runtime deps). The only allowed runtime dep is the existing `jinja2`. Dev-only additions (e.g., perf-test infrastructure) are acceptable but should be reviewed.

Commit as Commit F.

**Files:** none.

**Dependencies:** T36.

**Verification:** Full suite green. Tag candidate: `commit-f-constitution`.

---

## Summary

| Commit | Tasks | Goal |
|--------|-------|------|
| A — Loader Isolation | T1-T6 | Per-run sys.modules snapshot/restore + tests |
| B — Repo-Wide Index | T7-T11 | Plumb `(module, name)` lookup through all backends |
| C — IR + Validation Acceptance | T12-T17 | Freeze produces cross-module IR; validator accepts; manifest populates |
| D — Template-First Emission | T18-T28 | Move `view.py:704` into template; emit cross-module imports/includes/from-imports; primary fixture + goldens; AC-23 static check |
| E — Validation Extensions | T29-T35 | Cross-module cycles, name collisions, basename uniqueness, multiple_of fixture, cycle test |
| F — Constitution | T36-T37 | Constraint #4 replacement |

**Total tasks: 38** (T1-T37 plus T26b — added in iter2 to cover AC-7 part 2). Estimated effort: ~3-5 days for an engineer familiar with the codebase, longer for a first-time contributor.

The "byte-parity at every commit" rule is enforced by the integration-check task at the end of each commit (T6, T11, T17, T28, T35, T37).
