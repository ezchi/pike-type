# Spec 011 — Cross-Module Type References

## Overview

Allow a `Struct()` member (and any future user-type member) to reference a named DSL type that is **defined in a different Python DSL module**, and have the generated SystemVerilog, C++, and Python outputs preserve that named reference and emit the appropriate cross-package import.

### The Bug This Replaces

Today, when one DSL module imports a named type from another module and uses it as a struct member, two things go wrong:

1. **Silent flattening.** The cross-module type identity is lost during freeze. The struct field is emitted as if the user had written an inline scalar with the same width.
2. **Validator never fires.** The validation rule at `src/piketype/validate/engine.py:69-73` ("cross-module type references are not supported in this milestone") is unreachable for scalar aliases because the `TypeRefIR` is never constructed in the first place.

The root cause is in the loader/freeze path:

- `src/piketype/loader/python_loader.py` calls `sys.modules.pop(module_name, None)` and then `exec_module` for each piketype module, in the **discovery-sorted (but dependency-unaware) order** returned by `find_piketype_modules` (see `src/piketype/discovery/scanner.py:26-34`, which calls `sorted(...)`).
- When `bar.py` is processed before `foo.py`, the line `from alpha.piketype.foo import byte_t` triggers Python's standard import machinery, which executes `foo.py` and creates **ScalarType instance #1**.
- piketype later processes `foo.py` itself: it pops `foo` from `sys.modules`, re-executes it, and produces **ScalarType instance #2**.
- `build_type_definition_map` (`src/piketype/dsl/freeze.py:92`) keys on `id(value)` and registers instance #2 under `(foo_ref, "byte_t")`.
- `bar.py`'s `__dict__` still holds instance #1.
- During `_freeze_field_type` for `bar_t.field1`, `type_definition_map.get(id(instance_1))` is `None`, so freeze falls through to `ScalarTypeSpecIR(state_kind="logic", resolved_width=8, ...)` instead of `TypeRefIR(module=foo_ref, name="byte_t")`.
- The struct field is emitted as `logic [7:0] field1`, no `TypeRefIR` exists, and the cross-module validator is never invoked.

This bug is reproducible today on `develop` and proves that the existing constitution constraint *"No cross-module type references"* is **not actually enforced** for scalar-alias references — it is silently bypassed. This spec closes that hole by **enforcing the relaxed-constraint behavior**: cross-module references work correctly, end-to-end.

### Constitution Impact

This spec relaxes the *current-milestone* constraint #4 in `.steel/constitution.md`:

> **No cross-module type references (current milestone).** Struct fields referencing types from other modules are rejected by validation. This constraint will be relaxed in a future milestone.

This is the future-milestone work referenced by that note. Landing this spec requires editing the constitution to remove the constraint and to describe the new cross-module rules. The constitution amendment is part of this feature's scope (see FR-15).

### Implementation Staging Note (constitution principle: byte-parity at every commit)

The user's auto-memory captures a hard rule for this repo: **every commit must preserve byte-parity against existing goldens** (transitional passthroughs are required). Once FR-2 starts producing cross-module `TypeRefIR`, the existing validator at `engine.py:69-73` rejects it and existing backends index types only locally — a naïve mid-stack commit breaks every existing golden in the suite.

To respect byte-parity, the implementation MUST stage as follows:

- **Commit A — Loader isolation.** Implement FR-1 alone. No new behavior; existing fixtures pass byte-identical.
- **Commit B — Repo-wide type index plumbing.** Add the repo-wide index (FR-7) to all three backends as a new optional input. Backends still consult the local view first; the repo-wide index is unused. Existing fixtures pass byte-identical.
- **Commit C — Freeze produces cross-module `TypeRefIR`, validator accepts, manifest dependencies populate.** This is the first commit that *could* break byte-parity. To preserve it, add only the new fixture (`tests/fixtures/cross_module_type_refs/`) and its goldens in this commit; do not modify any existing fixture.
- **Commit D — Backend emission of imports / includes / from-imports.** Wire the import lines in SV/C++/Python backends and add the cross-module goldens.
- **Commit E — Validation extensions** (cycles, name conflicts, unknown-target unit tests).
- **Commit F — Constitution amendment** (FR-15).

Each commit's existing-golden diff is empty until Commit C, and Commit C only *adds* new goldens. Commit D may rewrite the new fixture's goldens but must not touch any existing golden.

### Example

`alpha/piketype/foo.py`:

```python
from piketype.dsl import Logic

byte_t = Logic(8)
```

`alpha/piketype/bar.py`:

```python
from piketype.dsl import Struct

from alpha.piketype.foo import byte_t

bar_t = (
    Struct()
    .add_member("field1", byte_t)
    .add_member("field2", byte_t)
)
```

Expected `gen/sv/alpha/piketype/bar_pkg.sv`:

```systemverilog
// Generated by piketype
// Source: alpha/piketype/bar.py
// Do not edit by hand.

package bar_pkg;
  import foo_pkg::*;

  localparam int LP_BAR_WIDTH = 16;
  localparam int LP_BAR_BYTE_COUNT = 2;

  typedef struct packed {
    byte_t field1;
    byte_t field2;
  } bar_t;

  function automatic logic [LP_BAR_WIDTH-1:0] pack_bar(bar_t a);
    return {a.field1, a.field2};
  endfunction

  function automatic bar_t unpack_bar(logic [LP_BAR_WIDTH-1:0] a);
    bar_t result;
    int unsigned offset;
    result = '0;
    offset = 0;
    result.field2 = a[offset +: LP_BYTE_WIDTH];
    offset += LP_BYTE_WIDTH;
    result.field1 = a[offset +: LP_BYTE_WIDTH];
    offset += LP_BYTE_WIDTH;
    return result;
  endfunction
endpackage
```

The wildcard `import foo_pkg::*;` brings `byte_t`, `LP_BYTE_WIDTH`, `LP_BYTE_BYTE_COUNT`, `pack_byte`, and `unpack_byte` into scope, all of which the existing macros (`src/piketype/backends/sv/templates/_macros.j2:108-138`) expect to reach by unqualified name in the unpack body. (The user-supplied "expected" snippet wrote `import foo_pkg::byte_t;` as illustrative; the actual emission uses wildcard for the reasons documented in FR-9.)

Today's actual output (the bug):

```systemverilog
package bar_pkg;

  ...

  typedef struct packed {
    logic [7:0] field1;
    logic [7:0] field2;
  } bar_t;
  ...
```

## User Stories

- **US-1:** As a hardware engineer, I want to define a reusable scalar alias (e.g., `byte_t`, `addr_t`) in one DSL module and reference it from struct fields in other modules, so I can share named types across a project the same way I share constants today.
- **US-2:** As a verification engineer, I want generated SystemVerilog packages to bring exactly the cross-package symbols they need into scope, so the generated `_pkg.sv` files compile against multi-package designs without name pollution and without manual `import` editing.
- **US-3:** As a firmware developer, I want generated C++ headers and Python modules that reference cross-module types to include the right `#include` / `from ... import` line and emit the correct namespace-qualified or fully-dotted name, so the generated outputs build and run without hand-editing.
- **US-4:** As a tooling user, I want piketype to reject cross-module type cycles and name collisions with a clear error, so I do not silently produce un-buildable SV/C++/Python.

## Functional Requirements

### FR-1: Loader — Per-Run sys.modules Isolation (Snapshot/Restore)

`src/piketype/loader/python_loader.py` and `src/piketype/commands/gen.py` (and any other entry point that loads piketype modules — including the test helpers in `tests/test_view_py.py`) must guarantee that, for a given DSL type defined in module `M` within a single run, every other module `N` that does `from M import T` resolves to **the same Python object** that piketype tracks for `M`, while still preventing module leakage and stale-object effects between consecutive runs in the same process (e.g., across fixture-repo loads).

The mechanism is a **per-run scoped session** with the following contract. The contract is exception-safe via `try/finally` and uses **snapshot-and-restore** semantics, not "pop additions only":

1. At the start of a run (`run_gen`, `_load_fixture_module`, or any equivalent caller), compute the **owned key set**:
   - `module_paths = find_piketype_modules(repo_root)`
   - `module_names = {module_name_from_path(p, repo_root=repo_root) for p in module_paths}`
   - `owned_keys = module_names ∪ {every prefix of every name in module_names}` — i.e., for `alpha.piketype.foo`, the set adds `alpha`, `alpha.piketype`, `alpha.piketype.foo`. (The prefix rule covers parent namespace packages that Python's import system creates implicitly when loading the leaf modules.)
2. Snapshot the **original objects** for every owned key that pre-exists in `sys.modules`:
   - `pre_owned: dict[str, ModuleType] = {k: sys.modules[k] for k in owned_keys if k in sys.modules}`
3. Pre-clean: for each `k in owned_keys`, `sys.modules.pop(k, None)`. After this step, no owned key is present in `sys.modules`.
4. Load each module via `importlib.util.spec_from_file_location` + `exec_module`, **without** popping again inside the loop. The first execution of `foo.py` (whether triggered directly by piketype's loop or transitively via another module's `from foo import ...`) is cached in `sys.modules`; the explicit piketype loader iteration MUST detect that and reuse the cached instance instead of re-executing it.
5. In the `finally` block at the end of the run (success or exception):
   - For each `k in owned_keys`: pop the run's instance (if any). I.e., `sys.modules.pop(k, None)`.
   - For each `(k, original_module) in pre_owned.items()`: restore `sys.modules[k] = original_module`.
   - Net effect: every owned key is either restored to its pre-run object (if it existed before) or removed entirely (if it did not).

This guarantees:

- **Single execution per `*.py` file per run** — eliminating the duplicate-instance bug.
- **No leakage between runs** — `tests/test_view_py.py` and other multi-fixture callers see exactly the same `sys.modules` state after a run as before, including for owned keys that pre-existed.
- **Deterministic load order** — modules are processed in the existing `find_piketype_modules` sorted order; transitive imports cache as a side effect.

`load_module_from_path` is split into two helpers: `prepare_run(...)` (steps 1-3, returns a context manager that performs step 5 on exit) and `load_or_get_module(...)` (step 4, returns the cached `sys.modules` entry if present, otherwise executes and caches).

### FR-2: Freeze — TypeRefIR Carries Defining-Module Reference for All Type Kinds

`_freeze_field_type` (`src/piketype/dsl/freeze.py:347`) must construct a `TypeRefIR` whenever the struct member's type object is a top-level named DSL type, regardless of whether the type was defined in the same module or in another module.

- The `module` field of the resulting `TypeRefIR` is the `ModuleRefIR` of the **defining** module (where the type's `name = ...` assignment lives).
- This applies uniformly to `ScalarType`, `StructType`, `FlagsType`, and `EnumType` members.
- After FR-1 lands, `type_definition_map.get(id(type_obj))` resolves correctly for cross-module references because object identity is now stable.
- An anonymous (un-named) type instance from another module is impossible by construction — only named top-level types are importable from another module.

### FR-3: Freeze — `_serialized_width_from_dsl` Walks Cross-Module Refs

`_serialized_width_from_dsl` in `src/piketype/dsl/freeze.py:287-303` already recurses through DSL objects to compute serialized width for `Struct.multiple_of()`. After FR-1, the function continues to work unchanged when a struct member's type is defined in another module, because object identity is preserved and the function reads `member.type.<width|members|flags|width_value>` directly from the DSL object.

No semantic change is required, but a fixture (FR-16) must exercise cross-module `multiple_of()` width contribution.

### FR-4: Freeze — Populate `ModuleIR.dependencies` (Type and Constant References)

Today `freeze_module` (`src/piketype/dsl/freeze.py:276`) sets `dependencies=()`. After this change, freeze must populate `ModuleIR.dependencies` with one `ModuleDependencyIR(target=<ModuleRefIR of cross-module target>, kind=<"type_ref"|"const_ref">)` entry per **distinct** cross-module reference target/kind pair.

Sources of cross-module dependencies that MUST be detected:

- **`type_ref`:** Every `TypeRefIR` constructed during this module's freeze whose `module.python_module_name != current_module.python_module_name`. This includes type refs in struct member fields **and** type refs encountered transitively inside the same module (e.g., a same-module struct that has a cross-module member).
- **`const_ref`:** Every `ConstRefExprIR` produced by `_freeze_expr` (`freeze.py:374-408`) whose `module.python_module_name != current_module.python_module_name`. The freeze pipeline must traverse all `ExprIR` sites that contribute to the module's IR (constant `expr`, scalar alias `width_expr`, struct field type spec `width_expr`, enum value `expr`) and accumulate cross-module `ConstRefExprIR` targets.

Sort and deduplication rules:

- **Dedupe key:** `(target.python_module_name, kind)`.
- **Sort:** ascending by `(target.python_module_name, kind)` — the full tuple, so that when a module has both a `type_ref` and a `const_ref` to the same target, the order is deterministic (`const_ref` before `type_ref` lexicographically).
- Same-module references do not produce dependency entries.

### FR-5: Validation — Cross-Module Resolution + Allowlist Preserved

In `src/piketype/validate/engine.py`:

- **Remove** the rejection at lines 69-73 (`"cross-module type references are not supported in this milestone"`).
- The struct-field `TypeRefIR` validation must look up the target type using the module-qualified key `(field.type_ir.module.python_module_name, field.type_ir.name)` against the existing `type_index` (already keyed that way at `engine.py:19-23`).
- If no target is found, raise `ValidationError`: `"struct {struct_name} field {field_name} references unknown type {module}::{type_name}"`.
- The existing allowlist `(ScalarAliasIR, StructIR, FlagsIR, EnumIR)` for valid `TypeRefIR` targets is preserved.

### FR-6: Validation — Detect Cross-Module Struct Cycles

`_validate_struct_cycles` in `src/piketype/validate/engine.py:185-215` currently scans only same-module references. Extend (or add a new pass) to detect cycles **across modules**.

- Build the graph at the **repo** level: nodes are `(module_python_name, struct_name)`; edges go from a struct to every `TypeRefIR` target whose target type is a `StructIR` (regardless of module).
- A cycle anywhere in this graph raises `ValidationError`.
- Same-module cycles continue to use the existing single-module phrasing (preserves existing negative-test goldens): `"recursive struct dependency detected at {name}"`.
- Cross-module cycles use a new phrasing that names every node on the cycle: `"recursive cross-module struct dependency detected: {mod_a}::{type_a} -> {mod_b}::{type_b} -> {mod_a}::{type_a}"`. The path is rotated so the lexicographically-smallest `(module, name)` node appears first, ensuring deterministic output.

### FR-7: Backend — Repo-Wide Type Index in All View Builders and Emitters

The current backend view builders construct a module-local type index:

- SV: `src/piketype/backends/sv/view.py:662` (`{t.name: t for t in module.types}`)
- Python: `src/piketype/backends/py/view.py:459`
- C++: `src/piketype/backends/cpp/view.py:604-605`

After this change, every `build_*_module_view` entry point and the helpers it calls (any function that resolves a `TypeRefIR.name` to a `TypeDefIR`) must consume a **repo-wide** `RepoTypeIndex` keyed by `(module_python_name, type_name)`:

- A new helper `build_repo_type_index(repo: RepoIR) -> dict[tuple[str, str], TypeDefIR]` is added to `src/piketype/ir/builders.py` (or a sibling module).
- The signature of every `build_*_module_view`, `_build_struct_field_view`, `_build_struct_pack_unpack`, `_render_*` helper that currently reads `type_index[field.type_ir.name]` is updated to read `repo_type_index[(field.type_ir.module.python_module_name, field.type_ir.name)]`.
- Same-module lookups continue to work because `field.type_ir.module` is set to the current module's `ModuleRefIR` for same-module refs.
- The local `{t.name: t for t in module.types}` shortcut is removed wherever a `TypeRefIR` lookup occurs; it MAY be retained for module-local enumeration loops where no `TypeRefIR` resolution happens.

**Emitter wiring (explicit).** The three emitter modules at `src/piketype/backends/sv/emitter.py`, `src/piketype/backends/py/emitter.py`, and `src/piketype/backends/cpp/emitter.py` each currently iterate `repo.modules` and call `build_*_module_view(module=module)`. After this change:

1. Each emitter's top-level entry (`emit_sv(repo)`, `emit_py(repo)`, `emit_cpp(repo, namespace=...)`) calls `build_repo_type_index(repo)` exactly once.
2. The repo type index is passed by keyword argument to every `build_*_module_view(...)` call inside that emitter's loop.
3. `build_*_module_view` accepts the new keyword argument `repo_type_index` and threads it down to all helpers that resolve `TypeRefIR`s.

This is the prerequisite that lets backends correctly render cross-module references; without it, the SV/Python/C++ rendering paths would either crash on `KeyError` or silently mis-bind to a same-named local type.

### FR-8: Validation — Cross-Module Name Conflicts

The presence of cross-module type references plus wildcard SV imports introduces the possibility that a wildcard import collides with a local definition. Validation must reject these conflicts before emission:

- **Local-vs-imported type-name conflict.** If module `M` defines a type named `X` AND module `M` has a `TypeRefIR` whose target is module `N` (`N != M`) and the target type's name is also `X`, raise `ValidationError`: `"module {M}: local type {X} shadows cross-module reference to {N}::{X}"`. (This catches the case where wildcard `import N_pkg::*;` would otherwise produce ambiguous unqualified `X` references in `M`'s struct fields.)
- **Imported-vs-imported type-name conflict.** If module `M` has cross-module references to two different modules `N1` and `N2` (both different from `M`) and both of those modules define a type with the same name `X`, raise `ValidationError`: `"module {M}: cross-module references to {N1}::{X} and {N2}::{X} create an ambiguous import"`.
- **Imported enum literal name collision.** Wildcard import `N_pkg::*` brings every enum literal name from `N` into the importing package's scope (enum literals are package-level identifiers in the SV typedef at `src/piketype/backends/sv/templates/_macros.j2:80-84`). If module `M` has wildcard imports from `N1` and `N2` and they each define an enum literal named `Y`, raise `ValidationError`: `"module {M}: wildcard import of {N1} and {N2} creates ambiguous enum literal {Y}"`. Same rule applies if `M` has a local enum literal named `Y` and an imported wildcard brings in another `Y`.

(Note: flag-bit names are **not** in this rule. Flag bits are struct-field members inside the flags typedef at `src/piketype/backends/sv/templates/_macros.j2:64-76`, not package-level imported symbols, so wildcard import does not bring them into scope.)

These rules apply only to **direct** cross-module references emitted by `M` (the modules listed in `M.dependencies`); transitive references through nested types do not produce wildcard imports in `M` and therefore do not introduce literal-collision risk in `M`.

### FR-9: SystemVerilog Backend — Wildcard Import in Synth Package

In `src/piketype/backends/sv/`, the synth-package emitter must emit one `import {target_basename}_pkg::*;` line per **distinct** cross-module target referenced by any struct field in the current module's types.

- **Wildcard, not per-symbol.** Existing `synth_unpack_fn` and `synth_pack_fn` macros (`src/piketype/backends/sv/templates/_macros.j2:91-138`) reference cross-module symbols by **multiple** unqualified names: the typedef (`{name} field;`), the pack helper (`pack_{base}`), the unpack helper (`unpack_{base}`), and the width localparam (`LP_{BASE}_WIDTH`). A per-symbol import of just the typedef would produce un-elaborable SV. Wildcard import is the simplest correct rule and matches the existing test-package precedent at `view.py:704` (`import {basename}_pkg::*;`).
- One import line per unique target's `python_module_name` (not basename — see FR-9a). Multiple type refs to the same target module dedupe to one line.
- Lines are sorted ascending by `target.python_module_name`.
- Lines are placed inside the `package {basename}_pkg;` block, immediately after the opening `package` line and before any `localparam` declaration, separated from the body by one blank line.
- The struct-field type rendering at `_render_sv_struct_field_type` (`src/piketype/backends/sv/view.py:360-367`) and `_render_sv_helper_field_decl` (`view.py:370-378`) continues to emit the **unqualified** type name; the wildcard import resolves it.
- All emission goes through Jinja templates (NFR-7); no inline string concatenation.

### FR-9a: Validation — Unique Package Basenames Across the Repo

Today `check_duplicate_basenames` (`src/piketype/validate/namespace.py`) only runs when `--namespace` is provided (gated at `src/piketype/commands/gen.py:31-32`). With cross-module references in play, two different modules with the same basename produce conflicting `_pkg` package names in SV, conflicting `_types` filenames in Python, and indistinguishable `import {basename}_pkg::*;` lines (FR-9, FR-10) — silently routing a cross-module reference to the wrong target.

After this change:

- `check_duplicate_basenames` runs **unconditionally** for every `piketype gen` invocation, not just under `--namespace`.
- The error message is: `"duplicate piketype module basename {basename}: {path1}, {path2}"` — same wording as today.
- Same-basename modules in disjoint subtrees are rejected at validation time, before any SV/C++/Python emission.
- This is independent of whether any cross-module reference exists; a same-basename collision is rejected even in a single-module workload (this is a stricter rule than today, justified by the new emission semantics).

### FR-10: SystemVerilog Backend — Test-Package Imports (Both Synth and Test Packages)

Helper classes are emitted into `{basename}_test_pkg`, not the synth package — confirmed at `src/piketype/backends/sv/templates/module_test.j2`. The test package's helper class field declarations reference both the cross-module **typedef** (e.g., `byte_t field1;` for a scalar `TypeRefIR` — see `_render_sv_helper_field_decl` at `src/piketype/backends/sv/view.py:370-378`) **and** the cross-module **helper class** (e.g., `byte_t_ct` for composite refs). Package wildcard imports are not transitive in SystemVerilog, so the test package must import both the cross-module synth and test packages directly:

- For every distinct cross-module target referenced by any struct field in the current module, the test package emits **two** import lines:
  - `import {target_basename}_pkg::*;` — brings the typedef and synth helpers into scope for raw helper-class field decls.
  - `import {target_basename}_test_pkg::*;` — brings the cross-module helper class (`{name}_ct`) into scope.
- These are in **addition** to the existing `import {basename}_pkg::*;` line for the same-module synth package (`view.py:704`).
- Both lines are emitted per cross-module target.
- Sort order: each list (synth-import lines, test-import lines) sorted ascending by `target.python_module_name`. Synth imports as a block come before test imports as a block.
- Placement: immediately after the existing same-module synth import, before any class declarations.

### FR-11: Python Backend — Cross-Module Imports in Generated Modules

In `src/piketype/backends/py/`, the generated `*_types.py` for a module containing cross-module references must emit:

- One `from {target.python_module_name}_types import {WrapperClassName}` line per distinct cross-module type reference. The target module name is `target.python_module_name` (the dotted module name of the defining module's source `.py` file) plus the `_types` suffix on the basename — the same naming rule used today for the local `_types.py` filename.
  - Example: a reference to `byte_t` defined in `alpha.piketype.foo` becomes `from alpha.piketype.foo_types import byte_t_ct`.
- Sorted ascending by `(target_module_name, wrapper_class_name)`.
- Placed in the imports section after stdlib imports and after the runtime import.
- Field type annotations use the **unqualified** wrapper class name (`byte_t_ct`), since the import brings it into the local module's namespace.

### FR-12: C++ Backend — Cross-Module `#include` Directives + Qualified Field Type

In `src/piketype/backends/cpp/`, `_build_namespace_view` (`src/piketype/backends/cpp/view.py:241-253`) places each generated module under its own namespace (`alpha::piketype::foo`, etc., or `{user_namespace}::{basename}` when `--namespace` is given). A cross-module reference therefore requires both an include and a fully-qualified type name.

- One `#include "{namespace_path}/{target_basename}_types.hpp"` line per distinct cross-module **defining module** (deduplicated across multiple type refs to the same target module).
  - `namespace_path` is the same path-segment join the existing emitter uses for the output file location (e.g., `alpha/piketype`), confirmed via `module.ref.namespace_parts`.
- Includes sorted ascending by include path string.
- Includes placed after `<piketype_runtime.hpp>` and any standard includes, before the `namespace` open.
- **Field type rendering for cross-module `TypeRefIR`** in `_build_struct_field_view` (`src/piketype/backends/cpp/view.py:467-489`) emits the fully-qualified name. The qualification is computed by reusing `_build_namespace_view(module=<target_module>, namespace=<emit_namespace>)` and prefixing with `::`. The current `_build_namespace_view` filters out the literal segment `"piketype"` (`src/piketype/backends/cpp/view.py:241-245`), so:
  - Default (no `--namespace`): namespace_parts `("alpha", "piketype", "foo")` → filtered to `("alpha", "foo")` → field type `::alpha::foo::byte_t_ct`.
  - With `--namespace=N`: target namespace is `N::foo` → field type `::N::foo::byte_t_ct`.
  - Same-module references continue to emit the unqualified name (`byte_t_ct`) — no behavior change.
- Verified against current goldens: `tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:13` opens `namespace alpha::types {`, confirming the `"piketype"`-filtered namespace structure.
- The same qualification rule applies to every C++ rendering site that today emits `_type_class_name(...)` from a `TypeRefIR`: pack/unpack steps, clone, default-construct, etc.

### FR-13: Backend — Template-First Emission of New Lines

All new emitted output added by this spec — SV `import` lines, C++ `#include` lines, Python `from ... import` lines — MUST be emitted via the existing Jinja templates and view-model machinery in each backend's `templates/` directory and `view.py`. No backend may concatenate import / include / from-import strings inline in Python code.

This is required by constitution principle 5 ("Template-first generation").

### FR-14: Manifest — Surface Cross-Module Dependencies

The manifest serializer at `src/piketype/manifest/` must serialize each `ModuleIR.dependencies` entry as an object:

```json
{
  "target_module": "alpha.piketype.foo",
  "kind": "type_ref"
}
```

- The `dependencies` key in the manifest module record (currently always `[]`) is populated from `ModuleIR.dependencies`.
- Sort order matches FR-4 (ascending by `(target_module_name, kind)`).

### FR-15: Constitution Amendment

`.steel/constitution.md` must be updated as part of this feature's implementation:

- **Constraint #4** ("No cross-module type references") is removed.
- A new constraint is added in its place that codifies the new rules: cross-module references are allowed; they must not form cycles across modules; they must not produce local-vs-imported, imported-vs-imported, or wildcard literal collisions; and they produce explicit `import` / `#include` / `from ... import` lines in generated outputs per FR-9 through FR-12.

The constitution edit lands in Commit F per the staging note above, in the same merge as the implementation.

### FR-16: Test Fixtures and Golden Files

The following test artifacts must be added or extended.

- **Primary fixture** `tests/fixtures/cross_module_type_refs/`:
  - `project/alpha/piketype/foo.py`: defines `byte_t = Logic(8)`, `addr_t = Struct().add_member("hi", Bit(8)).add_member("lo", Bit(8))`, `cmd_t = Enum().add_value("IDLE", 0).add_value("READ", 1).add_value("WRITE", 2)`, and `perms_t = Flags().add_flag("READ").add_flag("WRITE")`.
  - `project/alpha/piketype/bar.py`: imports all four types from `alpha.piketype.foo` and defines `bar_t = Struct().add_member("field1", byte_t).add_member("field2", byte_t).add_member("hdr", addr_t).add_member("op", cmd_t).add_member("perm", perms_t)`.
  - Goldens cover SV (`bar_pkg.sv`, `bar_test_pkg.sv`, `foo_pkg.sv`, `foo_test_pkg.sv`), Python (`bar_types.py`, `foo_types.py`), and C++ (`bar_types.hpp`, `foo_types.hpp`), plus the manifest `piketype_manifest.json`.
- **`multiple_of()` fixture** `tests/fixtures/cross_module_struct_multiple_of/`:
  - A struct in `bar.py` uses cross-module `byte_t` and applies `.multiple_of(32)`. Goldens verify trailing alignment is computed across module boundaries.
- **Cycle negative fixture** `tests/fixtures/cross_module_cycle/`:
  - `foo.py` and `bar.py` mutually reference each other's structs (must be wired so both Python files can import without a Python-level circular import — typically via `Struct().add_member("x", lazy_ref)` style is NOT supported, so the cycle is constructed by importing one direction at the Python level and arranging the ref through that direction). If a runtime-only cycle is not constructible without violating Python import rules, the cycle-detection test is implemented as a **unit test** that constructs `RepoIR` directly with cycling `TypeRefIR`s and asserts the `ValidationError` from `_validate_struct_cycles`. Choose whichever is feasible; the AC is that the validator itself is exercised.
- **Unit test for FR-5 unknown-type validation:** `tests/test_validate_engine.py` constructs a `RepoIR` directly containing a struct with a `TypeRefIR` whose `(module, name)` does not exist in any loaded module's types. Assert the `"struct {struct_name} field {field_name} references unknown type {module}::{type_name}"` error. (This replaces the former integration-fixture approach, which was infeasible because Python's `from M import nonexistent_t` raises `ImportError` during `exec_module` and the loader wraps that as `PikeTypeError` before validation runs.)
- **Unit tests for FR-8 name-collision validation:** in `tests/test_validate_engine.py`, three cases — local-vs-imported, imported-vs-imported, and wildcard literal collision — each constructed via direct `RepoIR` assembly.
- **Loader isolation tests** in `tests/test_loader.py`:
  - Test that loading two different fixture repos sequentially in the same Python process does not leak modules between runs (assert `sys.modules` returns to its prior set).
  - Test that within a single run, `id(byte_t)` accessed via `bar.module.__dict__["byte_t"]` equals `id(byte_t)` accessed via `foo.module.__dict__["byte_t"]`.
- **Python runtime test:** Round-trip and explicit `to_bytes()` byte-value test for a struct with a cross-module Enum and Flags member.
- **Idempotency:** Existing idempotency test infrastructure must apply to the cross-module fixture — running `piketype gen` twice produces identical output.

## Non-Functional Requirements

- **NFR-1: Backward compatibility.** Existing single-module fixtures and goldens remain byte-identical after this change. No existing golden file is rewritten by this work, except as transitional updates documented in the staging note (which expects no existing-golden diffs).
- **NFR-2: Deterministic output.** All emitted import / include / from-import lines are sorted and deduplicated; output remains byte-for-byte reproducible. Sort keys are explicit at every list (FR-4, FR-9, FR-10, FR-11, FR-12, FR-14).
- **NFR-3: No runtime dependency growth.** Implementation uses only the existing template engine (Jinja2) and stdlib. No new third-party packages.
- **NFR-4: Performance.** Generation latency for the existing fixture suite must not regress more than 5% relative to the post-spec-010 baseline. (The `piketype gen` perf gate from spec 010 is currently open per project memory; this spec must not widen it.)
- **NFR-5: basedpyright strict.** All new Python code passes `basedpyright` strict-mode with zero errors.
- **NFR-6: Constitution alignment.** After FR-15 lands, no remaining text in `.steel/constitution.md` contradicts cross-module references.
- **NFR-7: Template-first generation.** All emitted import / include / from-import lines are produced by Jinja templates, not by ad hoc string concatenation in `view.py` or emitter modules. (Restated as a hard NFR for clarity even though it is also captured in FR-13.)

## Acceptance Criteria

- **AC-1:** Running `piketype gen` on the primary fixture (FR-16) produces byte-identical output to the goldens, on a clean checkout.
- **AC-2:** The generated `bar_pkg.sv` for the user-supplied example contains exactly one `import foo_pkg::*;` line, placed inside the package block, after the opening `package` line, before any `localparam`, separated from the body by exactly one blank line.
- **AC-3:** The generated `bar_pkg.sv` `typedef struct packed` uses the unqualified type name `byte_t` for `field1` and `field2` (not `logic [7:0]`), and the generated `unpack_bar` body references `LP_BYTE_WIDTH` and `unpack_byte` by unqualified name.
- **AC-4:** The generated `bar_test_pkg.sv` contains, in this exact order: (1) `import bar_pkg::*;` (same-module synth, existing); (2) one `import {target_basename}_pkg::*;` line per cross-module target sorted by `target.python_module_name` (FR-10 cross-module synth block); (3) one `import {target_basename}_test_pkg::*;` line per cross-module target sorted by `target.python_module_name` (FR-10 cross-module test block). For the user-supplied example: `import bar_pkg::*; import foo_pkg::*; import foo_test_pkg::*;`.
- **AC-5:** The generated `bar_types.py` contains `from alpha.piketype.foo_types import byte_t_ct` and uses `byte_t_ct` (unqualified) as the field type annotation.
- **AC-6:** The generated `bar_types.hpp` contains `#include "alpha/piketype/foo_types.hpp"` and the field type for `field1`/`field2` is the fully-qualified `::alpha::foo::byte_t_ct` under default namespacing (after the existing `"piketype"` segment is filtered out per `_build_namespace_view`), or `::{user_namespace}::foo::byte_t_ct` when `--namespace=<user_namespace>` is given.
- **AC-7:** Loading the cross-module fixture twice in the same Python process produces identical IR (object-identity-stable). Loading two *different* fixture repos sequentially leaves no piketype module entries in `sys.modules` after the second run completes.
- **AC-8:** Validation accepts a struct field whose `TypeRefIR` target is in another module and that target is a `ScalarAliasIR`, `StructIR`, `FlagsIR`, or `EnumIR`.
- **AC-9:** Unit test verifies validation rejects a struct field whose `TypeRefIR` target's `(module_python_name, name)` does not exist in the repo IR, with an error message containing both module and type name.
- **AC-10:** Validation rejects a cross-module struct cycle with an error message that names every node on the cycle, with deterministic rotation (lex-smallest node first).
- **AC-11:** Validation continues to reject same-module struct cycles with the existing error wording (no regression in the existing negative-test golden).
- **AC-12:** Validation rejects a local-type-vs-imported-type name collision with the FR-8 error message.
- **AC-13:** Validation rejects two imported wildcards with the same type name (imported-vs-imported collision) with the FR-8 error message.
- **AC-14:** Validation rejects two imported wildcards with the same enum literal name (or a local enum literal that collides with an imported wildcard's enum literal) with the FR-8 error message. Flag-bit names are not in this rule (see FR-8 note).
- **AC-15:** `ModuleIR.dependencies` contains one entry per distinct `(target.python_module_name, kind)` pair, sorted by that tuple ascending.
- **AC-16:** `gen/piketype_manifest.json` contains the FR-14 schema for cross-module `dependencies` entries.
- **AC-17:** Idempotency: running `piketype gen` twice on the cross-module fixture produces identical `gen/` trees, and the second run does not rescan generated files as DSL modules.
- **AC-18:** A struct that uses a cross-module member with `.multiple_of(N)` produces serialized width and trailing alignment that match the same-module behavior bit-for-bit (golden comparison).
- **AC-19:** Python runtime test: `bar_t(field1=byte_t_ct(0xAB), field2=byte_t_ct(0xCD)).to_bytes() == b"\xab\xcd"` and `bar_t.from_bytes(b"\xab\xcd")` round-trips to a struct with the same field values.
- **AC-20:** All existing tests continue to pass with no goldens modified (per staging note Commits A-F).
- **AC-21:** `.steel/constitution.md` no longer contains the "No cross-module type references" constraint and contains the new cross-module rules.
- **AC-22:** `basedpyright` strict-mode passes with zero errors after the change.
- **AC-23:** A static check (implemented as a unit test under `tests/test_no_inline_imports.py`) parses the AST of `src/piketype/backends/sv/view.py`, `src/piketype/backends/cpp/view.py`, `src/piketype/backends/py/view.py`, `src/piketype/backends/sv/emitter.py`, `src/piketype/backends/cpp/emitter.py`, and `src/piketype/backends/py/emitter.py`, walks all string literals (including f-string `Constant` and `JoinedStr` parts), and asserts that no string literal contains the substring `"import "` followed by a `_pkg`/`_test_pkg`/`_types` token, **except** for the existing same-module synth-import construction at `src/piketype/backends/sv/view.py:704` which is grandfathered via an explicit allowlist entry. New backend code must produce import lines via Jinja templates with view-model data, not via Python-side string construction. (The test also asserts no `f-string` containing `"#include"` or `"from "` patterns aimed at generated outputs; existing `import` statements at module top of `view.py`/`emitter.py` are not string literals and are exempt.)
- **AC-24:** The reproducer from the bug overview generates output matching the "Expected" snippet exactly (including the wildcard import).

## Out of Scope

- **Cross-module unpacked types.** Constraint #3 (packed types only) remains in force.
- **Selective SV imports of individual symbols.** Wildcard import is the chosen rule (FR-9). Per-symbol import (`import foo_pkg::byte_t;`) is out of scope; users who want narrower import surface can split modules.
- **Re-exports / type aliases of cross-module types.** Defining `foo_byte_t = byte_t` in `bar.py` to "re-export" is not addressed — `foo_byte_t` would be a same-object reference; whether that should be emitted as an alias in `bar_pkg` is left for a follow-up.
- **Star imports in user DSL.** `from alpha.piketype.foo import *` is not supported by this spec — users must import each type explicitly. Discovery may or may not detect star-imported names; behavior is undefined.
- **Generated runtime cross-module ordering.** Runtime support packages (`piketype_runtime_pkg.sv`, `piketype_runtime.hpp`) are not affected.
- **Multi-repo / multi-package piketype.** Cross-module references are only resolved within a single piketype repo (single `piketype gen` invocation).
- **Order of inter-module file emission.** Files within `gen/` may be written in any order across modules; the user has not requested a particular order. Within a single file, declaration order follows the existing `(source.line, name)` rule.

## Open Questions

None. Q1, Q2, Q3 from iteration 1 are resolved in FR-1 (scoped sys.modules), FR-9 (wildcard), and FR-12 (fully-qualified C++ field type) respectively. Q4 (literal collisions) is resolved by FR-8. Q5 (file-emission order) is moved to Out of Scope.

## Changelog

- [Gauge iter2] FR-1: rewrote restore semantics to **snapshot-and-restore** (not "pop additions only"). Pre-existing owned `sys.modules` entries are now preserved across runs.
- [Gauge iter2] FR-7: added explicit emitter-wiring sub-section requiring each emitter to call `build_repo_type_index` once and pass it down to every `build_*_module_view` invocation.
- [Gauge iter2] FR-8: removed flag-bit names from the wildcard-literal-collision rule; clarified that only enum literals are package-level imported symbols.
- [Gauge iter2] FR-9: changed dedup key from `target_basename` to `target.python_module_name` to support disjoint paths.
- [Gauge iter2] Added FR-9a: unconditional duplicate-basename validation across the repo, regardless of `--namespace`.
- [Gauge iter2] FR-10: test packages now emit **both** `import {target_basename}_pkg::*;` AND `import {target_basename}_test_pkg::*;` per cross-module target, since SV package wildcard imports are not transitive.
- [Gauge iter2] FR-12: corrected the C++ qualified field type to `::alpha::foo::byte_t_ct` (filtered `"piketype"` segment); cited existing golden `tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:13` as ground truth.
- [Gauge iter2] AC-4: rewrote to specify the exact 3-block import order in `bar_test_pkg.sv`.
- [Gauge iter2] AC-6: corrected to `::alpha::foo::byte_t_ct`.
- [Gauge iter2] AC-14: scoped to enum literals only; flag-bit names dropped.
- [Gauge iter2] AC-23: replaced the brittle literal-string grep with an AST-walk unit test that catches f-string construction of imports across all view and emitter modules; grandfathers the single existing same-module import at `view.py:704`.
- [Gauge iter1] Resolved Q1 (loader strategy) → FR-1: scoped per-run `sys.modules` snapshot/cleanup with fixture-isolation tests.
- [Gauge iter1] Resolved Q2 (SV import granularity) → FR-9: wildcard `import {target}_pkg::*;` for synth packages, with rationale.
- [Gauge iter1] Resolved Q3 (C++ namespacing) → FR-12: fully-qualified field type `::{ns}::{basename}::{type_ct}` and per-module includes.
- [Gauge iter1] Resolved Q4 (literal collisions) → new FR-8: validation rules for local-vs-imported, imported-vs-imported, and wildcard literal collisions.
- [Gauge iter1] Added FR-7 (repo-wide type index in all view builders) to fix the backend resolution gap.
- [Gauge iter1] Corrected FR-9/FR-10 (formerly FR-7/FR-8): synth package emits wildcard import for typedef + LP_*_WIDTH + pack/unpack symbols; helper-class concerns moved to test-package import (FR-10) since helper classes live in `_test_pkg`, not `_pkg`.
- [Gauge iter1] Replaced infeasible unknown-type integration fixture with a unit test on `RepoIR` directly (FR-16).
- [Gauge iter1] Added FR-13 + NFR-7 making template-first emission a hard requirement, with AC-23 grep check.
- [Gauge iter1] Tightened FR-4 dependency sort key to the full `(target.python_module_name, kind)` tuple; clarified expression-traversal scope for `const_ref` dependency detection.
- [Gauge iter1] Added the implementation staging note to preserve byte-parity-per-commit per project memory.
- [Gauge iter1] Corrected Overview wording ("arbitrary discovery order" → "discovery-sorted but dependency-unaware order").
