# Commit C — Forge Artifact (Tasks T12-T17)

Freeze produces cross-module IR; validator accepts; manifest serializes dependencies.

## Files Changed

- `src/piketype/dsl/freeze.py` — added `_collect_module_dependencies` and updated `freeze_module` to populate `ModuleIR.dependencies`. Added R8 invariant docstring on the new helper.
- `src/piketype/validate/engine.py` — removed cross-module rejection (lines 69-73 in develop); updated unknown-target error message to include both module and type name per FR-5.
- `src/piketype/manifest/write_json.py` — populate `dependencies` from `module.dependencies`; sort by `(target_module, kind)`.
- `tests/test_struct_enum_member.py` — converted `test_cross_module_enum_rejected` to `test_cross_module_enum_accepted` (the spec 009 constraint is relaxed by spec 011).
- `tests/test_freeze.py` — created. 5 tests: cross-module TypeRefIR production, dependency collection, deterministic sort, no same-module dependency, cross-module ConstRefExprIR.
- `tests/test_validate_engine.py` — created. 2 tests: unknown-type rejection, cross-module accepted.

## Key Implementation Decisions

- **Dependency collection traverses every ExprIR site.** `_collect_module_dependencies` walks `const.expr`, `scalar_alias.width_expr`, `struct.field.type_spec.width_expr`, `enum.width_expr`, and `enum.value.expr`. It uses a small recursive `visit_expr` for `UnaryExprIR`/`BinaryExprIR` traversal.
- **Frozen-dataclass workaround.** `ModuleIR` is `@dataclass(frozen=True)`. Since `_collect_module_dependencies` requires the constructed `ModuleIR` to walk, `freeze_module` constructs the module twice — first with `dependencies=()`, then with the result of `_collect_module_dependencies`. Cleaner than mutating after-the-fact.
- **Spec 009 test conversion.** The negative test for cross-module enum rejection is now obsolete. Rather than delete it, I converted it to a positive test that asserts `validate_repo` does not raise — preserves the test's RepoIR construction structure as documentation of cross-module validation behavior.

## Deviations from Plan

- None.

## Tests Added

- `tests/test_freeze.py` (5 tests).
- `tests/test_validate_engine.py` (2 tests).

## Integration Check (T17)

- `uv run python -m unittest discover tests/` — **266 tests, 0 failures, 1 skipped** (perf gate). All pre-existing fixtures byte-identical (manifest goldens still emit `"dependencies": []` for all current fixtures since none have cross-module refs).
