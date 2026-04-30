# Implementation Plan — Spec 011 Cross-Module Type References

## Architecture Overview

The pipeline is **Discovery → Loader → DSL → Freeze → IR → Validate → Emit**. This feature touches every stage except Discovery:

- **Loader** gets a per-run scoped session that snapshots `sys.modules` and restores it on exit (FR-1). This is the foundational change; without it, cross-module type identity is unstable.
- **DSL** is unchanged in structure. The fix at this layer is downstream of FR-1: with stable identity, existing `_freeze_field_type` and `_freeze_expr` already produce correct `TypeRefIR` and `ConstRefExprIR` for cross-module references.
- **Freeze** gains a dependency-accumulation pass that walks the frozen IR and populates `ModuleIR.dependencies` (FR-4). No changes to `_freeze_field_type` itself — the existing code already produces cross-module `TypeRefIR` once identity is stable.
- **IR** uses existing types (`TypeRefIR`, `ModuleDependencyIR`, `ModuleRefIR`). No new IR node types.
- **Validate** is extended with: (a) cross-module struct cycles (FR-6), (b) cross-module name collisions (FR-8), (c) repo-wide unknown-type detection (FR-5), (d) unconditional duplicate-basename (FR-9a). The existing `engine.py:69-73` rejection is removed.
- **Emit** receives a new repo-wide `RepoTypeIndex` once per `piketype gen` invocation (FR-7) and threads it through every backend's view-builder. SV/Python/C++ templates and view models gain new view-model fields for cross-module imports/includes/from-imports (FR-9/10/11/12). The existing same-module SV synth-import construction at `view.py:704` is moved into Jinja templates as part of the refactor (FR-13).

The "byte-parity at every commit" constraint is met by sequencing the changes in 6 commits where existing-fixture goldens remain unchanged throughout (the cross-module fixture is added in Commit D when emission is wired).

## Components

### Loader — `src/piketype/loader/`

- **`python_loader.py`** — Refactored from a single `load_module_from_path(...)` function into:
  - `prepare_run(repo_root: Path, module_paths: list[Path]) -> ContextManager[None]`: enters a per-run scope. Computes the owned-key set (every discovered module name plus every dotted prefix), snapshots originals, pops owned keys, yields. On `__exit__`, pops run instances and restores originals via `try/finally`.
  - `load_or_get_module(path: Path, *, repo_root: Path) -> ModuleType`: looks up `module_name_from_path(path, repo_root)` in `sys.modules`; if cached, returns it; otherwise runs `spec_from_file_location` + `exec_module` and caches.
  - The original `load_module_from_path` is retained as a thin shim that calls `load_or_get_module` (so test helpers that haven't been updated still work for the duration of Commit A) and emits a `DeprecationWarning` in test scope. After Commit A, `tests/test_view_*.py` helpers are migrated to use `prepare_run`.

### Discovery — `src/piketype/discovery/scanner.py`

- No changes. Existing sorted ordering is preserved.

### DSL — `src/piketype/dsl/freeze.py`

- **`build_const_definition_map`** and **`build_type_definition_map`** — Unchanged. After FR-1, object identity is stable, so the existing `id()`-keyed maps work correctly for cross-module references.
- **`_freeze_field_type`** — Unchanged. Already produces `TypeRefIR(module=module_ref, name=type_name)` for any object found in `type_definition_map`. Cross-module references are resolved via the same code path once identity is stable.
- **`_freeze_expr`** — Unchanged. Already produces `ConstRefExprIR(module=module_ref, name=const_name)` for any `Const` found in `definition_map`.
- **New helper `_collect_module_dependencies(module_ir: ModuleIR) -> tuple[ModuleDependencyIR, ...]`** — Walks every `TypeRefIR` and `ConstRefExprIR` reachable from the module's types (struct fields, scalar alias `width_expr`, struct field `width_expr`, enum value `expr`) and constants (`expr`). Filters to cross-module entries (`target.python_module_name != current_module.python_module_name`). Returns deduplicated, sorted entries by `(target_python_module_name, kind)`.
- **`freeze_module`** — Updated to call `_collect_module_dependencies` and pass the result as `dependencies=...` to `ModuleIR(...)` (replacing the current `dependencies=()`).

### IR — `src/piketype/ir/nodes.py` and `src/piketype/ir/builders.py`

- **`nodes.py`** — Unchanged. Existing `TypeRefIR`, `ModuleDependencyIR`, `ModuleRefIR`, `ModuleIR` shapes are sufficient.
- **`builders.py` (or new `repo_index.py`)** — New helper `build_repo_type_index(repo: RepoIR) -> dict[tuple[str, str], TypeDefIR]` returns a dict keyed by `(module.ref.python_module_name, type_def.name)`. Built once per `piketype gen` invocation by each backend emitter.

### Validate — `src/piketype/validate/engine.py` and `src/piketype/validate/namespace.py`

- **`engine.py`** —
  - Remove the cross-module rejection at lines 69-73.
  - Update the `target = type_index.get(...)` lookup at lines 74 to use `(field.type_ir.module.python_module_name, field.type_ir.name)` (already keyed correctly at lines 19-23 — no change needed there).
  - Update unknown-target error message wording per FR-5.
  - Replace `_validate_struct_cycles` (currently per-module) with a repo-level pass that builds a `(module, struct_name)` graph from all modules' struct fields. Cross-module cycles use the new N-node phrasing per FR-6; same-module cycles preserve the existing wording for the existing negative-test golden.
  - Add `_validate_cross_module_name_conflicts(repo: RepoIR) -> None` implementing FR-8 (local-vs-imported, imported-vs-imported, enum literal collisions).
- **`namespace.py`** —
  - Update `check_duplicate_basenames` error message wording per FR-9a (drop `--namespace` precondition phrase).
- **`commands/gen.py`** —
  - Move the `check_duplicate_basenames(module_paths=module_paths)` call out of the `if namespace is not None:` block so it runs unconditionally (FR-9a).

### Backends — `src/piketype/backends/{sv,py,cpp}/`

#### Common pattern (all three backends)

- **`emitter.py`** — Top-level entry (`emit_sv`, `emit_py`, `emit_cpp`) calls `build_repo_type_index(repo)` once and passes the result to every `build_*_module_view(...)` invocation.
- **`view.py`** — Every helper that resolves a `TypeRefIR.name` is updated to take `repo_type_index: dict[tuple[str, str], TypeDefIR]` and look up `repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]`. The module-local `{t.name: t for t in module.types}` shortcut is removed at every `TypeRefIR` lookup site. (The shortcut may still be used for purely module-local enumeration loops.)

#### SV — `src/piketype/backends/sv/`

- **`view.py`** —
  - The existing `f"  import {module.ref.basename}_pkg::*;"` at `view.py:704` is removed; the synth-package import is added as a view-model field consumed by templates (CL-7 / FR-13).
  - New view-model field `synth_cross_module_imports: tuple[str, ...]` on `SvSynthModuleView` — sorted ascending by `target.python_module_name`, one entry per distinct cross-module target referenced by any struct field in the module's types.
  - New view-model fields on `SvTestModuleView`:
    - `same_module_synth_import: str` (replaces the inline f-string).
    - `cross_module_synth_imports: tuple[str, ...]`.
    - `cross_module_test_imports: tuple[str, ...]`.
- **`templates/module_synth.j2`** — Render a header block with the `package` line, then the cross-module synth imports (no blank between `package` and first import; one blank between import block and first declaration). Use a Jinja `{% for %}` over the new view-model field.
- **`templates/module_test.j2`** — Render the import section as: same-module synth → cross-module synth block → cross-module test block (contiguous, one blank before the first class).

#### Python — `src/piketype/backends/py/`

- **`view.py`** — New view-model field `cross_module_imports: tuple[str, ...]` on `PyModuleView` — each entry is the rendered `from {target.python_module_name}_types import {WrapperClassName}` line. Sort by `(target_module_name, wrapper_class_name)`.
- **`templates/module.j2`** — After the existing `from __future__ import annotations` and stdlib imports, insert the cross-module imports block (one blank above and one blank below).

#### C++ — `src/piketype/backends/cpp/`

- **`view.py`** — New view-model field `cross_module_includes: tuple[str, ...]` on `CppModuleView` — sorted ascending by include path. The `_build_struct_field_view` helper is updated to detect cross-module `TypeRefIR` and emit fully-qualified field type via `_build_namespace_view(module=<target_module>, namespace=<emit_namespace>)`. Same change applies to `_render_cpp_struct_pack_step`, `_render_cpp_struct_unpack_step`, and the `_is_*_ref` helpers used by clone/default-construct.
- **`templates/module.j2`** — Insert the cross-module includes after standard includes, before the `namespace` open.

### Manifest — `src/piketype/manifest/write_json.py`

- Update the per-module record serializer to render `ModuleIR.dependencies` as a list of `{"target_module": "<python_module_name>", "kind": "<type_ref|const_ref>"}` entries. Sort identically to FR-4 (ascending by `(target_module, kind)`).

### Tests

- **`tests/test_loader.py`** (new) — Unit tests for `prepare_run`/`load_or_get_module` snapshot/restore semantics and within-run object identity.
- **`tests/test_freeze.py`** (extended) — Cross-module `TypeRefIR` and `ConstRefExprIR` production after `prepare_run`. `ModuleIR.dependencies` correctly populated and sorted.
- **`tests/test_validate_engine.py`** (extended) — Direct `RepoIR` unit tests for: unknown-type rejection (FR-5), cross-module struct cycle detection (FR-6), name collisions (FR-8 — three sub-cases). All three FR-8 cases use direct `RepoIR` construction.
- **`tests/test_namespace_validation.py`** (extended) — One new case: duplicate basenames are rejected without `--namespace`.
- **`tests/test_no_inline_imports.py`** (new) — AC-23 AST static check.
- **`tests/test_gen_const_sv.py`** or new `tests/test_gen_cross_module.py`** — Integration tests for the new fixtures (`cross_module_type_refs/`, `cross_module_struct_multiple_of/`, `cross_module_cycle/` if Python-loadable).
- **`tests/test_view_*.py`** — Migrate test helpers to use `prepare_run` per CL-4.

### Fixtures

- **`tests/fixtures/cross_module_type_refs/project/alpha/piketype/foo.py`** — `byte_t`, `addr_t` (struct), `cmd_t` (enum), `perms_t` (flags).
- **`tests/fixtures/cross_module_type_refs/project/alpha/piketype/bar.py`** — `bar_t` with all four cross-module types as members.
- **`tests/fixtures/cross_module_struct_multiple_of/project/alpha/piketype/foo.py`** — `byte_t = Logic(8)`.
- **`tests/fixtures/cross_module_struct_multiple_of/project/alpha/piketype/bar.py`** — Struct with `byte_t` member and `.multiple_of(32)`.
- **`tests/fixtures/cross_module_cycle/project/alpha/piketype/foo.py`** + **`bar.py`** — Mutually-referencing structs (if Python-loadable; else use `RepoIR` unit test only).

### Goldens

For each new fixture, generate goldens at `tests/goldens/gen/<fixture>/`:
- `sv/alpha/piketype/{foo,bar}_pkg.sv` and `{foo,bar}_test_pkg.sv`
- `py/alpha/piketype/{foo,bar}_types.py` and `__init__.py`
- `cpp/alpha/piketype/{foo,bar}_types.hpp`
- `piketype_manifest.json`
- Runtime files (unchanged across fixtures, regenerated symlinked)

Goldens are generated by running `piketype gen` on the fixture and committing the output. Verified manually against the spec's expected output before commit.

## Data Model

No changes to existing IR node shapes. New uses of existing fields:

| IR field | Before | After |
|----------|--------|-------|
| `ModuleIR.dependencies` | always `()` | populated with `ModuleDependencyIR` entries |
| `TypeRefIR.module` | always equals current module's `ModuleRefIR` | may equal a different module's `ModuleRefIR` |
| `ConstRefExprIR.module` | always equals current module's `ModuleRefIR` | may equal a different module's `ModuleRefIR` |

Manifest schema gains `dependencies[].target_module` and `dependencies[].kind` keys per module record.

## API Design

No public Python API changes — `piketype gen` CLI is unchanged. Internal API additions:

- `piketype.loader.python_loader.prepare_run(repo_root, module_paths) -> ContextManager`
- `piketype.loader.python_loader.load_or_get_module(path, *, repo_root) -> ModuleType`
- `piketype.ir.repo_index.build_repo_type_index(repo) -> dict[tuple[str, str], TypeDefIR]`
- `piketype.dsl.freeze._collect_module_dependencies(module_ir) -> tuple[ModuleDependencyIR, ...]` (private)
- `piketype.validate.engine._validate_cross_module_name_conflicts(repo) -> None` (private)

Backend `build_*_module_view` functions gain a new keyword argument `repo_type_index`.

Generated SystemVerilog, C++, and Python public APIs are unchanged for existing fixtures (byte-parity).

## Dependencies

No new external dependencies. Implementation uses:
- Python stdlib (`importlib`, `sys`, `pathlib`, `ast`, `dataclasses`).
- Existing Jinja2 (already a runtime dep).
- Existing `unittest` (test runner).

## Implementation Strategy (Commits A-F)

The 6-commit staging is mandated by the spec's byte-parity-per-commit rule. Each commit is independently testable; existing-fixture goldens remain identical throughout.

### Commit A — Loader Isolation

**Files:** `src/piketype/loader/python_loader.py`, `src/piketype/commands/gen.py`, `tests/test_loader.py` (new), `tests/test_view_*.py` (helper migration).

- Add `prepare_run` and `load_or_get_module` to `python_loader.py`.
- Refactor `run_gen` in `gen.py` to wrap its module-loading loop in `prepare_run`.
- Migrate `_load_fixture_module` helpers in `tests/test_view_py.py`, `test_view_cpp.py`, `test_view_sv.py` to use `prepare_run`.
- Add `tests/test_loader.py` with cases for: snapshot/restore correctness, sequential fixture loads not leaking state, within-run object identity stability.

**Acceptance:** All existing tests pass byte-identical.

### Commit B — Repo-Wide Type Index Plumbing

**Files:** `src/piketype/ir/repo_index.py` (new), `src/piketype/backends/{sv,py,cpp}/{emitter,view}.py`.

- Add `build_repo_type_index` in `src/piketype/ir/repo_index.py`.
- Update `emit_sv`, `emit_py`, `emit_cpp` to call `build_repo_type_index(repo)` once and pass through.
- Update every `build_*_module_view` to accept `repo_type_index` keyword argument.
- Update every helper that resolves a `TypeRefIR.name` to use the repo-wide index keyed by `(field.type_ir.module.python_module_name, field.type_ir.name)`. For same-module refs, this is identical to the current behavior since `field.type_ir.module` matches the current module's `ModuleRefIR`.
- Remove module-local `{t.name: t for t in module.types}` shortcuts at every `TypeRefIR` lookup site.

**Acceptance:** All existing fixtures pass byte-identical.

### Commit C — Freeze Cross-Module IR + Validation Acceptance + Manifest Population

**Files:** `src/piketype/dsl/freeze.py`, `src/piketype/validate/engine.py`, `src/piketype/manifest/write_json.py`, `tests/test_freeze.py`, `tests/test_validate_engine.py`.

- Add `_collect_module_dependencies` in `freeze.py` and call from `freeze_module`.
- Remove the cross-module rejection in `engine.py:69-73`.
- Update unknown-target error message in `engine.py` to include both module and type name.
- Update `write_json.py` to serialize `ModuleIR.dependencies`.
- Add `tests/test_freeze.py` cases for cross-module `TypeRefIR` and `ConstRefExprIR` and dependency collection.
- Add `tests/test_validate_engine.py` cases for unknown-type rejection.

**Acceptance:** Existing fixtures byte-identical (no existing fixture has cross-module refs; manifest dependencies still serialize as `[]`).

### Commit D — Template-First Refactor + Cross-Module Emission + New Fixture/Goldens

**Files:** `src/piketype/backends/{sv,py,cpp}/view.py`, `src/piketype/backends/{sv,py,cpp}/templates/*.j2`, `tests/fixtures/cross_module_type_refs/`, `tests/goldens/gen/cross_module_type_refs/`, `tests/test_no_inline_imports.py` (new), `tests/test_gen_cross_module.py` (new).

- Move the existing `f"  import {module.ref.basename}_pkg::*;"` at SV `view.py:704` into a view-model field consumed by `module_test.j2`.
- Add view-model fields for cross-module imports on each backend.
- Update Jinja templates to render the new fields.
- Update C++ `_build_struct_field_view` and pack/unpack/clone helpers for fully-qualified cross-module field types.
- Add the primary fixture and goldens (manually generated by running `piketype gen` and verified against spec).
- Add `tests/test_no_inline_imports.py` (AC-23) — initial implementation focusing on `Constant`, `JoinedStr`, `BinOp(op=Add)`, `Call(func=Attribute(attr="format"|"join"|"format_map"))`, and `BinOp(op=Mod)` cases.
- Add the integration test `tests/test_gen_cross_module.py` running `piketype gen` on the new fixture and comparing against goldens.

**Acceptance:** Existing fixtures byte-identical; new fixture goldens produce expected output.

### Commit E — Validation Extensions + Remaining Negative Fixtures

**Files:** `src/piketype/validate/engine.py`, `src/piketype/validate/namespace.py`, `src/piketype/commands/gen.py`, `tests/test_validate_engine.py`, `tests/test_namespace_validation.py`, `tests/fixtures/cross_module_struct_multiple_of/`, `tests/fixtures/cross_module_cycle/` (or `RepoIR`-only test).

- Replace `_validate_struct_cycles` with the repo-level version (FR-6).
- Add `_validate_cross_module_name_conflicts` (FR-8).
- Move `check_duplicate_basenames` out of the `if namespace is not None:` gate (FR-9a).
- Update duplicate-basename error message per FR-9a.
- Add `tests/test_validate_engine.py` cases for cross-module cycles and FR-8 collisions.
- Add the `multiple_of` fixture and goldens.
- Add the cycle fixture (Python-loadable if feasible; otherwise `RepoIR`-only unit test).

**Acceptance:** Existing tests pass; new tests pass.

### Commit F — Constitution Amendment

**Files:** `.steel/constitution.md`.

- Replace constraint #4 with the exact text in FR-15.

**Acceptance:** No code changes; constitution change reviewed manually.

## Risks and Mitigations

### R1: Sys.modules restore leaks owned keys on test discovery

**Risk.** `pytest`/`unittest` discovery imports test files which trigger piketype module imports outside of `prepare_run`. Subsequent `prepare_run` snapshots may include those discovery-time imports as "originals" and restore them after the run, leading to stale references.

**Mitigation.** `prepare_run` only snapshots originals for keys in the **owned-key set** (computed from the run's `module_paths`). Discovery-time imports of unrelated test fixtures don't intersect. Verify with a targeted `tests/test_loader.py` case that loads two different fixture repos sequentially and asserts module objects from the first run do not survive into the second.

### R2: Repo-wide type index doesn't include cross-module-only references

**Risk.** A struct in module M references a type T in module N. If N has no other types, the repo-wide index might miss T.

**Mitigation.** `build_repo_type_index` iterates `repo.modules` and indexes every `module.types` entry, regardless of whether any other module references it. The index is built from definitions, not references.

### R3: Helper class field decl uses raw type name for cross-module scalar TypeRef

**Risk.** `_render_sv_helper_field_decl` (`view.py:370-378`) emits raw `byte_t field1;` for a scalar `TypeRefIR`. After cross-module references work, the helper class in `bar_test_pkg` references `byte_t` unqualified, which requires `import foo_pkg::*;` (FR-10's cross-module synth import in test packages). If the test package only imports `foo_test_pkg::*`, this breaks.

**Mitigation.** FR-10 emits BOTH `import foo_pkg::*;` AND `import foo_test_pkg::*;` per cross-module target. AC-4 verifies this exact ordering. The fixture's `bar_test_pkg.sv` golden exercises both imports.

### R4: AC-23 false positives on legitimate code

**Risk.** The AST static check might flag legitimate string literals or expressions that happen to start with `import `, `#include `, or `from `.

**Mitigation.** A spot check during planning (already verified by codex iter4 gauge note) found no false positives in the current backend `view.py`/`emitter.py` files. The check is scoped to those six files only and excludes top-level `ast.Import` and `ast.ImportFrom` statements. New legitimate patterns can be added to the allowlist file-by-file if needed.

### R5: Performance regression beyond NFR-4 budget

**Risk.** The repo-wide index build + dependency-accumulation visitor + name-collision validation add per-module work. NFR-4 caps regression at 5%.

**Mitigation.** All new work is O(n) over types/refs in the repo, with constant-factor overhead. Index build is one pass; dependency accumulation is one pass per module. Collision validation is O(types × wildcard imports) which is small in practice. Benchmark before/after Commit E using the existing fixture suite; if regression exceeds 5%, profile and optimize the dependency visitor.

### R6: SV template inline-import refactor changes byte output

**Risk.** Moving `f"  import {module.ref.basename}_pkg::*;"` from `view.py:704` into the test-package template might change leading whitespace or trailing newlines.

**Mitigation.** Match the exact rendered byte sequence of the current template + view-model output. Verify by running existing fixture suite after Commit D and comparing against pre-Commit-D goldens — if any differ, fix the template.

### R7: Cycle fixture infeasible at Python load level

**Risk.** A true Python-level mutual import (`from foo import x` in bar.py and `from bar import y` in foo.py) raises `ImportError`. Constructing a piketype-level cycle at the DSL layer requires both modules to import from each other.

**Mitigation.** FR-16 explicitly permits a `RepoIR`-only unit test as a fallback. Implementer constructs `StructIR` instances with cycling `TypeRefIR`s directly and asserts `ValidationError`.

## Testing Strategy

### Unit tests (fast, isolated)

- **Loader isolation** (`tests/test_loader.py`): snapshot/restore, identity stability, sequential fixture isolation.
- **Freeze** (`tests/test_freeze.py`): cross-module `TypeRefIR`/`ConstRefExprIR` production; `ModuleIR.dependencies` correctness.
- **Validate** (`tests/test_validate_engine.py`): unknown-type, cross-module cycles (2-node, 3-node, mixed), three FR-8 collision sub-cases.
- **Namespace** (`tests/test_namespace_validation.py`): duplicate-basename without `--namespace`.
- **Static check** (`tests/test_no_inline_imports.py`): AC-23 across the six backend files. Includes positive test cases (legitimate code is not flagged) and negative test cases (constructed bad patterns ARE flagged).

### Integration tests (golden-file)

- **Primary cross-module fixture** (`tests/test_gen_cross_module.py`): full `piketype gen` run on `cross_module_type_refs/` fixture; byte-compare every generated file against goldens.
- **Multiple-of fixture**: golden comparison.
- **Cycle fixture**: assert non-zero exit and error message; or `RepoIR`-only.

### Existing tests

All existing tests pass byte-identical at every commit. CI runs the full suite on each push.

### Python runtime correctness

- Round-trip test in `tests/test_runtime_py.py`: instantiate `bar_t` with cross-module Enum/Flags members; assert `to_bytes()` produces expected bytes; assert `from_bytes()` round-trips.

### Idempotency

- Existing idempotency test infrastructure applies to the new fixture (run `piketype gen` twice, compare).

## Open Risks Mitigated by Spec

The spec already addresses these explicitly; they are listed here as a summary of risks the spec mitigates:

- **Object identity instability** → FR-1 snapshot-and-restore.
- **Backend resolution gap** → FR-7 repo-wide index.
- **Template-first emission** → FR-13 + AC-23 AST static check.
- **Name collisions** → FR-8.
- **Cycle detection across modules** → FR-6.
- **Same-name modules in disjoint subtrees** → FR-9a unconditional uniqueness.

No additional open risks beyond those listed in "Risks and Mitigations" above.
