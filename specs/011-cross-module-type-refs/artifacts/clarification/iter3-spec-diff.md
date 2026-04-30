diff --git a/specs/011-cross-module-type-refs/spec.md b/specs/011-cross-module-type-refs/spec.md
index fc1303f..6580d60 100644
--- a/specs/011-cross-module-type-refs/spec.md
+++ b/specs/011-cross-module-type-refs/spec.md
@@ -37,14 +37,16 @@ The user's auto-memory captures a hard rule for this repo: **every commit must p
 
 To respect byte-parity, the implementation MUST stage as follows:
 
-- **Commit A — Loader isolation.** Implement FR-1 alone. No new behavior; existing fixtures pass byte-identical.
-- **Commit B — Repo-wide type index plumbing (full switchover).** Add the repo-wide index (FR-7), update **all** backend `TypeRefIR` resolutions in SV / Python / C++ view builders to look up via `(module_python_name, type_name)` instead of `name`-only, and remove the module-local `{t.name: t for t in module.types}` shortcut wherever a `TypeRefIR` is dereferenced. Same-module behavior is preserved bit-for-bit because `field.type_ir.module` already equals the current module's `ModuleRefIR` for same-module refs. Existing fixtures pass byte-identical.
-- **Commit C — Freeze produces cross-module `TypeRefIR`, validator accepts, manifest dependencies populate, new fixture lands.** Implement FR-2/3/4, FR-5, and FR-14. Add the new fixture (`tests/fixtures/cross_module_type_refs/`) and its goldens. Because Commit B already plumbed the repo-wide lookup through the backends, the new fixture's goldens compile correctly. Existing fixtures still byte-identical (no existing fixture has cross-module refs; existing manifest goldens still emit `"dependencies": []`).
-- **Commit D — Template-first refactor of all import-style emission.** Move the existing same-module SV synth-import construction at `view.py:704` into the synth/test-package Jinja templates. Implement FR-9 / FR-10 / FR-11 / FR-12 cross-module import emission via templates. AC-23 allowlist becomes empty. Existing fixtures remain byte-identical (template move is a structural refactor, not a content change); cross-module fixture goldens may be rewritten in this commit if needed.
-- **Commit E — Validation extensions.** Implement FR-6 (cross-module struct cycles), FR-8 (name collisions), FR-9a (unconditional duplicate-basename), and the FR-16 unit tests on `RepoIR` directly. Existing fixtures and existing test wording continue to pass.
+- **Commit A — Loader isolation.** Implement FR-1 alone. No new behavior; existing fixtures pass byte-identical. Add `tests/test_loader.py` cases for the per-run snapshot/restore contract and for cross-module object identity within a run.
+- **Commit B — Repo-wide type index plumbing (full switchover).** Add `build_repo_type_index` (FR-7), update **all** backend `TypeRefIR` resolutions in SV / Python / C++ view builders to look up via `(module_python_name, type_name)` instead of `name`-only, and remove the module-local `{t.name: t for t in module.types}` shortcut wherever a `TypeRefIR` is dereferenced. Same-module behavior is preserved bit-for-bit because `field.type_ir.module` already equals the current module's `ModuleRefIR` for same-module refs. Existing fixtures pass byte-identical.
+- **Commit C — Freeze produces cross-module `TypeRefIR`, validator accepts, manifest dependencies populate (IR-only).** Implement FR-2/3/4, FR-5, and FR-14. **No new generated-output fixture in this commit** — backend emission of imports/includes/from-imports is not wired yet, so an integration fixture would not produce valid output. Coverage for the new IR-level behavior is via:
+  - Direct `RepoIR` unit tests under `tests/test_freeze.py` and `tests/test_validate_engine.py` that construct cross-module `TypeRefIR` and assert freeze/validate behavior.
+  - Existing fixtures continue to pass byte-identical (no existing fixture has cross-module refs; existing manifest goldens still emit `"dependencies": []`).
+- **Commit D — Template-first emission + new cross-module fixture lands.** Move the existing same-module SV synth-import construction at `view.py:704` into the synth/test-package Jinja templates. Implement FR-9 / FR-10 / FR-11 / FR-12 cross-module import emission via templates. AC-23 allowlist becomes empty. Add the new fixture `tests/fixtures/cross_module_type_refs/` with its full SV/Python/C++/manifest goldens. Existing fixtures remain byte-identical (template move is a structural refactor, not a content change). The new fixture's goldens are committed for the first time here.
+- **Commit E — Validation extensions.** Implement FR-6 (cross-module struct cycles), FR-8 (name collisions), FR-9a (unconditional duplicate-basename), and the FR-16 unit tests on `RepoIR` directly. Add the `tests/fixtures/cross_module_struct_multiple_of/` and `tests/fixtures/cross_module_cycle/` fixtures (the cycle fixture may be implemented as a `RepoIR`-only unit test if a Python-loadable cycle is infeasible, per FR-16). Existing fixtures and existing test wording continue to pass.
 - **Commit F — Constitution amendment.** Apply FR-15 (the exact replacement text).
 
-Each commit's existing-golden diff is empty throughout. New goldens are added in Commit C. Commits D-F do not modify any golden.
+**Existing-golden invariant.** No existing golden file is modified by any of Commits A-F. New goldens are added in Commits D and E (cross-module fixtures only). After Commit F, the only constitution change is the constraint #4 replacement text in FR-15.
 
 ### Example
 
@@ -431,6 +433,8 @@ None. Q1, Q2, Q3 from iteration 1 are resolved in FR-1 (scoped sys.modules), FR-
 
 ## Changelog
 
+- [Clarification iter3] Staging note: deferred the new cross-module fixture/goldens from Commit C to Commit D so they land alongside the FR-9/10/11/12 emission that produces them. Commit C is now IR-only with `RepoIR` unit tests. Removed the self-contradictory "Commits D-F do not modify any golden" line.
+- [Clarification iter3] CL-8: bookkeeping fix — moved CL-8 from [NO SPEC CHANGE] to [SPEC UPDATE]; the FR-9a wording change in iter1 was a spec update, the clarifications-summary table now reflects this.
 - [Clarification iter2] Staging note: rewrote Commit B to **fully** plumb the repo-wide `TypeRefIR` lookup through all backends (instead of leaving it unused), so Commit C's new cross-module fixture/goldens compile correctly.
 - [Clarification iter2] FR-9a: corrected wording — existing fragment-based assertions in `tests/test_namespace_validation.py` continue to pass without modification (the test only checks stem and paths, not the lead-in phrase).
 - [Clarification iter1] CL-1 → FR-9: pinned exact whitespace (no blank between `package` line and first `import`; one blank between import block and first `localparam`).
