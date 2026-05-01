diff --git a/specs/011-cross-module-type-refs/spec.md b/specs/011-cross-module-type-refs/spec.md
index 099b163..2f6cecb 100644
--- a/specs/011-cross-module-type-refs/spec.md
+++ b/specs/011-cross-module-type-refs/spec.md
@@ -204,7 +204,9 @@ In `src/piketype/validate/engine.py`:
 - Build the graph at the **repo** level: nodes are `(module_python_name, struct_name)`; edges go from a struct to every `TypeRefIR` target whose target type is a `StructIR` (regardless of module).
 - A cycle anywhere in this graph raises `ValidationError`.
 - Same-module cycles continue to use the existing single-module phrasing (preserves existing negative-test goldens): `"recursive struct dependency detected at {name}"`.
-- Cross-module cycles use a new phrasing that names every node on the cycle: `"recursive cross-module struct dependency detected: {mod_a}::{type_a} -> {mod_b}::{type_b} -> {mod_a}::{type_a}"`. The path is rotated so the lexicographically-smallest `(module, name)` node appears first, ensuring deterministic output.
+- Cross-module cycles use a new phrasing that names every node on the cycle, separated by ` -> `, with the lex-smallest `(module, name)` node appearing first AND repeated at the end so the cycle is visually closed. For an N-node cycle (N ≥ 2): `"recursive cross-module struct dependency detected: {n_1} -> {n_2} -> ... -> {n_N} -> {n_1}"` where each `{n_i}` is `{module}::{type_name}` and `{n_1}` is the lex-smallest. Examples:
+  - 2-node: `recursive cross-module struct dependency detected: alpha.piketype.bar::a_t -> alpha.piketype.foo::b_t -> alpha.piketype.bar::a_t`
+  - 3-node: `recursive cross-module struct dependency detected: alpha.piketype.bar::a_t -> alpha.piketype.foo::b_t -> alpha.piketype.qux::c_t -> alpha.piketype.bar::a_t`
 
 ### FR-7: Backend — Repo-Wide Type Index in All View Builders and Emitters
 
@@ -250,7 +252,7 @@ In `src/piketype/backends/sv/`, the synth-package emitter must emit one `import
 - **Wildcard, not per-symbol.** Existing `synth_unpack_fn` and `synth_pack_fn` macros (`src/piketype/backends/sv/templates/_macros.j2:91-138`) reference cross-module symbols by **multiple** unqualified names: the typedef (`{name} field;`), the pack helper (`pack_{base}`), the unpack helper (`unpack_{base}`), and the width localparam (`LP_{BASE}_WIDTH`). A per-symbol import of just the typedef would produce un-elaborable SV. Wildcard import is the simplest correct rule and matches the existing test-package precedent at `view.py:704` (`import {basename}_pkg::*;`).
 - One import line per unique target's `python_module_name` (not basename — see FR-9a). Multiple type refs to the same target module dedupe to one line.
 - Lines are sorted ascending by `target.python_module_name`.
-- Lines are placed inside the `package {basename}_pkg;` block, immediately after the opening `package` line and before any `localparam` declaration, separated from the body by one blank line.
+- Lines are placed inside the `package {basename}_pkg;` block, immediately after the opening `package {basename}_pkg;` line, with **no blank line** between the package line and the first `import` line; **one blank line** separates the import block from the first `localparam`/declaration. (Matches the user-supplied expected output and the existing `_test_pkg` style at `tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:5-6`.)
 - The struct-field type rendering at `_render_sv_struct_field_type` (`src/piketype/backends/sv/view.py:360-367`) and `_render_sv_helper_field_decl` (`view.py:370-378`) continues to emit the **unqualified** type name; the wildcard import resolves it.
 - All emission goes through Jinja templates (NFR-7); no inline string concatenation.
 
@@ -275,7 +277,7 @@ Helper classes are emitted into `{basename}_test_pkg`, not the synth package —
 - These are in **addition** to the existing `import {basename}_pkg::*;` line for the same-module synth package (`view.py:704`).
 - Both lines are emitted per cross-module target.
 - Sort order: each list (synth-import lines, test-import lines) sorted ascending by `target.python_module_name`. Synth imports as a block come before test imports as a block.
-- Placement: immediately after the existing same-module synth import, before any class declarations.
+- Placement: immediately after the existing same-module synth import. **All import lines (same-module synth, cross-module synth block, cross-module test block) are contiguous with no blank lines between them**; one blank line separates the entire import section from the first `class` declaration. (Matches the existing single-import test-package style.)
 
 ### FR-11: Python Backend — Cross-Module Imports in Generated Modules
 
@@ -284,7 +286,7 @@ In `src/piketype/backends/py/`, the generated `*_types.py` for a module containi
 - One `from {target.python_module_name}_types import {WrapperClassName}` line per distinct cross-module type reference. The target module name is `target.python_module_name` (the dotted module name of the defining module's source `.py` file) plus the `_types` suffix on the basename — the same naming rule used today for the local `_types.py` filename.
   - Example: a reference to `byte_t` defined in `alpha.piketype.foo` becomes `from alpha.piketype.foo_types import byte_t_ct`.
 - Sorted ascending by `(target_module_name, wrapper_class_name)`.
-- Placed in the imports section after stdlib imports and after the runtime import.
+- Placed after `from __future__ import annotations` and after stdlib imports (e.g., `from dataclasses import dataclass, field`). Layout: `from __future__ ...` → blank line → stdlib imports → blank line → cross-module-imports block → blank line → first declaration. (Existing Python goldens have only `from __future__ import annotations` followed by stdlib; there is no piketype runtime import in any current `_types.py`. The cross-module block slots between stdlib and declarations.)
 - Field type annotations use the **unqualified** wrapper class name (`byte_t_ct`), since the import brings it into the local module's namespace.
 
 ### FR-12: C++ Backend — Cross-Module `#include` Directives + Qualified Field Type
@@ -302,9 +304,13 @@ In `src/piketype/backends/cpp/`, `_build_namespace_view` (`src/piketype/backends
 - Verified against current goldens: `tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:13` opens `namespace alpha::types {`, confirming the `"piketype"`-filtered namespace structure.
 - The same qualification rule applies to every C++ rendering site that today emits `_type_class_name(...)` from a `TypeRefIR`: pack/unpack steps, clone, default-construct, etc.
 
-### FR-13: Backend — Template-First Emission of New Lines
+### FR-13: Backend — Template-First Emission of All Import-Style Lines
 
-All new emitted output added by this spec — SV `import` lines, C++ `#include` lines, Python `from ... import` lines — MUST be emitted via the existing Jinja templates and view-model machinery in each backend's `templates/` directory and `view.py`. No backend may concatenate import / include / from-import strings inline in Python code.
+All emitted import / include / from-import output — both new (cross-module) and existing (same-module) — MUST be emitted via the existing Jinja templates and view-model machinery in each backend's `templates/` directory and `view.py`. No backend may concatenate import / include / from-import strings inline in Python code.
+
+This includes a refactor: the **existing same-module synth-import construction at `src/piketype/backends/sv/view.py:704`** (currently `f"  import {module.ref.basename}_pkg::*;"`) must be moved into the synth/test-package template + view model as part of this work. After the refactor, AC-23's allowlist is empty — there is no permitted Python-side import-line construction anywhere in the backend codebase.
+
+The implementer is free to land the move in Commit B (repo-wide type index plumbing) or Commit D (backend emission of imports), provided the existing same-module synth-import golden remains byte-identical.
 
 This is required by constitution principle 5 ("Template-first generation").
 
@@ -324,10 +330,13 @@ The manifest serializer at `src/piketype/manifest/` must serialize each `ModuleI
 
 ### FR-15: Constitution Amendment
 
-`.steel/constitution.md` must be updated as part of this feature's implementation:
+`.steel/constitution.md` must be updated as part of this feature's implementation. The current constraint #4 (line 110) is replaced verbatim with the following text:
 
-- **Constraint #4** ("No cross-module type references") is removed.
-- A new constraint is added in its place that codifies the new rules: cross-module references are allowed; they must not form cycles across modules; they must not produce local-vs-imported, imported-vs-imported, or wildcard literal collisions; and they produce explicit `import` / `#include` / `from ... import` lines in generated outputs per FR-9 through FR-12.
+> 4. **Cross-module type references.** Struct fields may reference named types defined in other DSL modules. Cross-module references:
+>    - Must not form cycles across modules. Cross-module struct cycles are rejected at validation time.
+>    - Must not produce local-vs-imported, imported-vs-imported, or imported-vs-local enum literal name collisions. Such collisions are rejected at validation time.
+>    - Produce explicit `import {target}_pkg::*;` lines in SystemVerilog synth packages, dual `_pkg` + `_test_pkg` imports in test packages, fully-qualified field types in C++ headers with the corresponding `#include`, and `from <target>_types import <wrapper>` lines in Python.
+>    - Require unique module basenames across the repo (this validation runs unconditionally for every `piketype gen` invocation).
 
 The constitution edit lands in Commit F per the staging note above, in the same merge as the implementation.
 
@@ -399,7 +408,7 @@ The following test artifacts must be added or extended.
     Captures `" ".join(["import", basename, "_pkg::*"])` (skeleton: `"import <DYN> _pkg::*"`, starts with `"import "`).
   - `ast.BinOp(op=Mod, left=Constant(value=str))` (`%`-formatting) where the left-hand `Constant` value begins with one of the three prefixes. Captures `"import %s_pkg::*;" % target` and `"#include \"%s\"" % path`. (Note: `%` formatting on strings is `BinOp(op=Mod)`, not a method `Call`; it must be checked separately from the `.format`/`.join` cases.)
 
-  **Allowlist.** The test maintains a single explicit allowlist entry: the existing same-module synth-import construction at `src/piketype/backends/sv/view.py:704` (`f"  import {module.ref.basename}_pkg::*;"`) is the **only** permitted Python-side construction. The allowlist key is the file path plus the line number; if the line number changes, the allowlist must be updated in the same diff that moves the line.
+  **Allowlist.** Per FR-13, the existing same-module synth-import construction at `src/piketype/backends/sv/view.py:704` is moved into Jinja templates as part of this work. After that refactor, the allowlist is **empty** — no Python-side import-line construction is permitted anywhere in the backend codebase. The allowlist exists in the test framework as an extension point but is unused at the point this spec lands; if a future spec needs to grandfather a line, it adds an entry keyed by file path + AST node line.
 
   **Out-of-scope for this AC.** Top-of-module `import` statements (`ast.Import`, `ast.ImportFrom`) in the inspected files are not string literals and are not flagged; they are real Python imports for piketype's own runtime, not generated output.
 
@@ -422,6 +431,12 @@ None. Q1, Q2, Q3 from iteration 1 are resolved in FR-1 (scoped sys.modules), FR-
 
 ## Changelog
 
+- [Clarification iter1] CL-1 → FR-9: pinned exact whitespace (no blank between `package` line and first `import`; one blank between import block and first `localparam`).
+- [Clarification iter1] CL-2 → FR-11: corrected import-section description (existing goldens have no runtime import); cross-module `from ... import` block goes between stdlib and declarations.
+- [Clarification iter1] CL-3 → FR-10: import lines in `_test_pkg.sv` are contiguous (no blank lines between same-module synth, cross-module synth, cross-module test blocks); one blank line before the first class.
+- [Clarification iter1] CL-5 → FR-15: locked the exact replacement text for the constitution's amended constraint #4.
+- [Clarification iter1] CL-6 → FR-6: generalized cross-module cycle error message to N-node cycles; added 2-node and 3-node concrete examples.
+- [Clarification iter1] CL-7 → FR-13, AC-23: existing same-module synth-import line at `view.py:704` moves into Jinja templates as part of this work; AC-23 allowlist becomes empty after the refactor.
 - [Gauge iter4] AC-23: rewrote the `.join` rule to reduce the join AST to a static string skeleton (using `"<DYN>"` for non-Constant elements) and flag if the skeleton starts with the import/include/from lead-in. Captures `" ".join(["import", basename, "_pkg::*"])` correctly (the iter3 wording missed it because the receiver `" "` did not begin with a generated-output prefix).
 - [Gauge iter4] AC-23: corrected the `%`-formatting rule to specify `ast.BinOp(op=Mod, left=Constant(value=str))`, not `ast.Call`. Python represents `s % args` as a `BinOp`.
 - [Gauge iter3] AC-23: hardened the AST static check to catch f-string prefixes, `BinOp` Add concatenation chains, `.format`/`.join` calls, and `%`-formatting that would produce generated-output import lines from Python-side string assembly. Single-file/line allowlist for the existing `view.py:704` line.
