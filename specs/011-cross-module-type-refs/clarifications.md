# Clarifications — Spec 011 Cross-Module Type References

This stage scans the spec for implicit assumptions, contradictions, and unresolved details. There are no remaining `[NEEDS CLARIFICATION]` markers from the specification stage; this document captures items that surfaced when the spec text was cross-checked against the existing codebase and goldens.

---

## CL-1: Exact Whitespace Layout of SV Synth Imports — [SPEC UPDATE]

**Issue.** FR-9 says cross-module imports are "placed inside the `package {basename}_pkg;` block, immediately after the opening `package` line and before any `localparam` declaration, separated from the body by one blank line." Two interpretations are consistent with that wording:

- **(a)** `package` line → import lines (no blank between) → blank → `localparam`s.
- **(b)** `package` line → blank → import lines → blank → `localparam`s.

The user-supplied expected output in the Overview shows interpretation **(a)**:

```
package bar_pkg;
  import foo_pkg::*;

  localparam int LP_BAR_WIDTH = 16;
```

**Resolution.** Choose **(a)** to match the user's expected output and to keep the synth package compact. Update FR-9 to say: "no blank line between the `package` line and the first `import` line; one blank line between the import block and the first `localparam`/declaration."

**Why.** The user explicitly showed (a) in the spec example. Existing same-module test packages also use the no-blank-between-`package`-and-`import` style (see `tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:5-6`).

---

## CL-2: Python Import Section Has No Runtime Import — [SPEC UPDATE]

**Issue.** FR-11 says cross-module `from ... import` lines are "placed in the imports section after stdlib imports and after the runtime import." There is **no** runtime import in any existing Python golden — surveyed `tests/goldens/gen/*/py/**/*.py`, every file has only `from __future__ import annotations` followed by stdlib (`from dataclasses import dataclass, field` or `from enum import IntEnum`).

**Resolution.** Update FR-11 to say: "placed after `from __future__ import annotations` and after stdlib imports (e.g., `from dataclasses import dataclass, field`), with one blank line separating the cross-module-imports block from the preceding stdlib block and one blank line separating it from the first non-import line." Drop the "runtime import" reference.

**Why.** The runtime-import claim was inaccurate. Existing layout is `__future__` → blank → stdlib → blank → declarations. Cross-module `from <pkg>_types import <ct>` lines slot between the stdlib block and the declarations.

---

## CL-3: SV Test-Package Import Block Separation — [SPEC UPDATE]

**Issue.** FR-10 specifies three blocks (same-module synth, cross-module synth, cross-module test) but does not say if blocks are separated by blank lines. Existing `_test_pkg` golden has `import types_pkg::*;` followed by one blank line and then the first class, with no separator within the import section because there's only one line today.

**Resolution.** Update FR-10 to say: "import lines are contiguous (no blank lines between blocks); a single blank line separates the entire import section from the first class declaration." So `bar_test_pkg.sv` looks like:

```
package bar_test_pkg;
  import bar_pkg::*;
  import foo_pkg::*;
  import foo_test_pkg::*;

  class bar_ct;
```

**Why.** Compactness matches the existing single-import style and keeps the import section visually one block.

---

## CL-4: Loader Snapshot Contract Applies to Test Helpers — [NO SPEC CHANGE]

**Issue.** FR-1 says "any other entry point that loads piketype modules — including the test helpers in `tests/test_view_py.py`" must use the new contract. The test helper at `tests/test_view_py.py:35-56` (`_load_fixture_module`) does not currently use a context manager — it iterates module paths and calls `load_module_from_path` directly.

**Clarification (no spec change).** The implementation MUST refactor `_load_fixture_module` to enter the new `prepare_run` context manager around its load loop and to call `load_or_get_module` instead of `load_module_from_path`. Equivalent refactors apply to any other test helper that bulk-loads piketype modules (search for callers of `load_module_from_path` in `tests/`). The spec already mandates this in FR-1; the resolution here is operational guidance for the implementer, not a new requirement.

**Why.** The spec already covers it; flagging this here so the planning stage allocates time for the test-helper refactor.

---

## CL-5: Constitution Amendment Exact Replacement Text — [SPEC UPDATE]

**Issue.** FR-15 says constraint #4 is "removed" and "a new constraint is added in its place that codifies the new rules." The exact replacement text is left to the implementer.

**Resolution.** Specify the replacement text in FR-15. The new constraint #4 reads:

> **Cross-module type references.** Struct fields may reference named types defined in other DSL modules. Cross-module references:
> - Must not form cycles across modules. Cross-module struct cycles are rejected at validation time.
> - Must not produce local-vs-imported, imported-vs-imported, or imported-vs-local enum literal name collisions. Such collisions are rejected at validation time.
> - Produce explicit `import {target}_pkg::*;` lines in SystemVerilog synth packages, dual `_pkg` + `_test_pkg` imports in test packages, fully-qualified field types in C++ headers with the corresponding `#include`, and `from <target>_types import <wrapper>` lines in Python.
> - Require unique module basenames across the repo (this validation runs unconditionally for every `piketype gen` invocation).

**Why.** Locking the exact text removes a small implementation ambiguity and ensures FR-15 is verifiable.

---

## CL-6: Cycle-Detection Message Format for N>2 Nodes — [SPEC UPDATE]

**Issue.** FR-6 gives an example with two modules: `"recursive cross-module struct dependency detected: {mod_a}::{type_a} -> {mod_b}::{type_b} -> {mod_a}::{type_a}"`. It does not specify the format for cycles with three or more nodes (e.g., `A -> B -> C -> A`).

**Resolution.** Generalize FR-6: the error message lists every node on the cycle in order, separated by ` -> `, with the lex-smallest `(module, name)` node appearing first AND repeated at the end to make the cycle visually closed. For an N-node cycle, the format is:

```
recursive cross-module struct dependency detected: {n_1} -> {n_2} -> ... -> {n_N} -> {n_1}
```

where each `{n_i}` is `{module}::{type_name}` and `{n_1}` is the lex-smallest node on the cycle.

**Why.** Removes ambiguity for cycles with three or more modules. The deterministic-rotation rule already handles ordering; this just makes the format explicit.

---

## CL-7: AC-23 Allowlist Becomes Empty After FR-9 Refactor — [SPEC UPDATE]

**Issue.** AC-23 grandfathers `src/piketype/backends/sv/view.py:704` (`f"  import {module.ref.basename}_pkg::*;"`) as the only permitted Python-side import-line construction. But FR-13 / NFR-7 require **all** import-line emission to go through Jinja templates. FR-9's wildcard import lines for cross-module references must be in templates. To be consistent, the existing same-module synth import should ALSO move into the template/view-model machinery, leaving AC-23's allowlist empty.

**Resolution.** Update FR-13 and AC-23 to say:

- The existing same-module synth-import construction at `view.py:704` is moved into the synth-package template + view model as part of this work. After the move, AC-23's allowlist is **empty**.
- The implementer is free to land the move in Commit B (repo-wide type index plumbing) or Commit D (backend emission of imports), provided the existing same-module synth-import golden remains byte-identical.

**Why.** Avoids an inconsistency where same-module imports are emitted from Python while cross-module imports are emitted from templates. One mechanism for both.

---

## CL-8: Same-Basename Validation Wording Change — [SPEC UPDATE]

**Issue.** FR-9a (in the spec text from the specification stage) said the fragment-based assertions in `tests/test_namespace_validation.py:176-182` "are updated to match the new wording." That is incorrect: the test checks only the stem name and conflicting paths, not the lead-in phrase, so the new error message is fragment-compatible with the existing assertions.

**Resolution.** Update FR-9a to say: "Existing fragment-based assertions in `tests/test_namespace_validation.py:176-182` continue to pass without modification — they check the stem name and conflicting paths only, not the lead-in phrase." (Already applied in the spec.)

**Why.** Avoids a spurious test-update item in planning; the new wording is fragment-compatible with the existing assertions.

---

## CL-9: Manifest `dependencies` Empty-List vs Absent — [NO SPEC CHANGE]

**Issue.** FR-14 requires the manifest's per-module `dependencies` field to be populated. Existing manifest goldens have `"dependencies": []`. After this change, single-module-fixture manifests still have `"dependencies": []` (no cross-module refs), so they remain byte-identical. Should the field always be present (even empty) or omitted when empty?

**Clarification (no spec change).** Keep the existing behavior: the field is always present. The serializer outputs `"dependencies": []` for modules with no cross-module references (matching every current golden). FR-14's new behavior is to populate the list when entries exist; absence-of-entries continues to render as `[]`.

**Why.** Matches existing goldens and preserves byte-parity in Commit C.

---

## CL-10: Cross-Module Const-Refs in Const Expressions — [NO SPEC CHANGE]

**Issue.** FR-4 says cross-module `ConstRefExprIR` produces a `kind="const_ref"` dependency. The existing `ConstRefExprIR` machinery (`_freeze_expr` in `src/piketype/dsl/freeze.py:374-408`) handles `Const` references by id lookup against `definition_map` (`freeze.py:73-89`), which has the **same object-identity bug** as the type case (FR-1) — it only resolves correctly when discovery+load order happens to preserve the referenced `Const` object identity, which today is not guaranteed because the loader pops and re-executes (`src/piketype/loader/python_loader.py:29-44`) and discovery is dependency-unaware (`src/piketype/discovery/scanner.py:26-34`).

**Clarification (no spec change).** After FR-1 stabilizes object identity, cross-module `Const` references will resolve reliably via the existing `_freeze_expr` machinery — no new freeze logic is needed. Implementation: add a dependency-accumulation visitor that walks every `ExprIR` in a frozen module (constant `expr`, scalar alias `width_expr`, struct field `width_expr`, enum value `expr`) and collects cross-module `ConstRefExprIR.module.python_module_name`. The visitor is the only new code in this area; the existing const-ref freeze path is unchanged.

**Why.** Avoids accidentally over-scoping FR-4 to "rewrite const-ref handling". The fix is downstream of FR-1, additive on top of existing freeze code.

---

## Summary

| ID | Affects spec? | Section(s) updated |
|----|---------------|---------------------|
| CL-1 | YES | FR-9 (whitespace layout), Example output already matches |
| CL-2 | YES | FR-11 (Python import placement) |
| CL-3 | YES | FR-10 (test-pkg block separation) |
| CL-4 | NO | — |
| CL-5 | YES | FR-15 (exact constitution replacement text) |
| CL-6 | YES | FR-6 (N-node cycle message format) |
| CL-7 | YES | FR-13, AC-23 (empty allowlist after refactor) |
| CL-8 | YES | FR-9a (test-update sentence rewritten to "continue to pass without modification") |
| CL-9 | NO | — |
| CL-10 | NO | — |

Seven items result in spec updates. The other three are operational guidance for the implementer that the spec already covers in spirit.
