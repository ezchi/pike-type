# Gauge Review — Planning, Iteration 2

**Reviewer:** gemini (gemini-3.1-pro-preview via gemini CLI 0.40.1; multiple 429 + ECONNRESET retries before success)

### Issues

**BLOCKING (FR-13 / AC-11)**: The proposed mechanism for cross-module `VecConst` imports is incomplete in the backend. Component 3 correctly identifies sightings and emits `ModuleDependencyIR(kind="vec_const_import")`, but Component 5 lacks any change to `src/piketype/backends/sv/view.py` to consume these dependencies. Specifically, `_collect_cross_module_synth_imports` currently only iterates over struct field type references via `_iter_cross_module_typerefs`. Without an update to this function or the view-assembly site, the `import a_pkg::*;` line will not be rendered. Furthermore, the plan's use of wildcard imports (`import a_pkg::*;`) contradicts the established synthesizable package style of explicit per-symbol imports (e.g., `import a_pkg::byte_t;`). If the intent is to "mirror `Const`'s cross-module rules" (FR-13), the plan should clarify how names are captured for explicit imports or explicitly justify the shift to wildcards for this primitive.

**WARNING (Component 3)**: The deduplication strategy for `ModuleDependencyIR` is correctly identified as being tied to the `kind` field. Since `VecConst` introduces a new kind (`vec_const_import`), a module importing both a `Const` and a `VecConst` from module A will produce two distinct IR dependency entries. While acceptable for the manifest, this is redundant for SV wildcard emission. A more defensible default would be to consolidate all constant-level sightings under a single `kind` if they produce the same emission side-effect.

### Carry-Over from Iter 1

1. **BLOCKING (FR-13 / AC-11)**: **STILL BLOCKING**. While the "sighting" mechanism in the DSL/Freeze layer is now plausibly correct, the plan still fails to bridge the gap to the SV backend. The assertion in Phase D/T9 that the golden "MUST contain" the import line is currently unbacked by implementation steps in Component 5.
2. **WARNING (Component 5 / FR-11 padding)**: **RESOLVED**. The concrete `_render_sv_vec_literal` implementation using Python format specs (`:0{digits}X`, `:0{width}b`) is unambiguous and correct.
3. **NOTE (R-2 manifest goldens)**: **RESOLVED**.

### Verdict

VERDICT: REVISE
