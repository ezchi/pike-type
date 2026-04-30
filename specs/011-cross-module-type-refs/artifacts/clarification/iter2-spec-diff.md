diff --git a/specs/011-cross-module-type-refs/spec.md b/specs/011-cross-module-type-refs/spec.md
index 2f6cecb..fc1303f 100644
--- a/specs/011-cross-module-type-refs/spec.md
+++ b/specs/011-cross-module-type-refs/spec.md
@@ -38,13 +38,13 @@ The user's auto-memory captures a hard rule for this repo: **every commit must p
 To respect byte-parity, the implementation MUST stage as follows:
 
 - **Commit A — Loader isolation.** Implement FR-1 alone. No new behavior; existing fixtures pass byte-identical.
-- **Commit B — Repo-wide type index plumbing.** Add the repo-wide index (FR-7) to all three backends as a new optional input. Backends still consult the local view first; the repo-wide index is unused. Existing fixtures pass byte-identical.
-- **Commit C — Freeze produces cross-module `TypeRefIR`, validator accepts, manifest dependencies populate.** This is the first commit that *could* break byte-parity. To preserve it, add only the new fixture (`tests/fixtures/cross_module_type_refs/`) and its goldens in this commit; do not modify any existing fixture.
-- **Commit D — Backend emission of imports / includes / from-imports.** Wire the import lines in SV/C++/Python backends and add the cross-module goldens.
-- **Commit E — Validation extensions** (cycles, name conflicts, unknown-target unit tests).
-- **Commit F — Constitution amendment** (FR-15).
+- **Commit B — Repo-wide type index plumbing (full switchover).** Add the repo-wide index (FR-7), update **all** backend `TypeRefIR` resolutions in SV / Python / C++ view builders to look up via `(module_python_name, type_name)` instead of `name`-only, and remove the module-local `{t.name: t for t in module.types}` shortcut wherever a `TypeRefIR` is dereferenced. Same-module behavior is preserved bit-for-bit because `field.type_ir.module` already equals the current module's `ModuleRefIR` for same-module refs. Existing fixtures pass byte-identical.
+- **Commit C — Freeze produces cross-module `TypeRefIR`, validator accepts, manifest dependencies populate, new fixture lands.** Implement FR-2/3/4, FR-5, and FR-14. Add the new fixture (`tests/fixtures/cross_module_type_refs/`) and its goldens. Because Commit B already plumbed the repo-wide lookup through the backends, the new fixture's goldens compile correctly. Existing fixtures still byte-identical (no existing fixture has cross-module refs; existing manifest goldens still emit `"dependencies": []`).
+- **Commit D — Template-first refactor of all import-style emission.** Move the existing same-module SV synth-import construction at `view.py:704` into the synth/test-package Jinja templates. Implement FR-9 / FR-10 / FR-11 / FR-12 cross-module import emission via templates. AC-23 allowlist becomes empty. Existing fixtures remain byte-identical (template move is a structural refactor, not a content change); cross-module fixture goldens may be rewritten in this commit if needed.
+- **Commit E — Validation extensions.** Implement FR-6 (cross-module struct cycles), FR-8 (name collisions), FR-9a (unconditional duplicate-basename), and the FR-16 unit tests on `RepoIR` directly. Existing fixtures and existing test wording continue to pass.
+- **Commit F — Constitution amendment.** Apply FR-15 (the exact replacement text).
 
-Each commit's existing-golden diff is empty until Commit C, and Commit C only *adds* new goldens. Commit D may rewrite the new fixture's goldens but must not touch any existing golden.
+Each commit's existing-golden diff is empty throughout. New goldens are added in Commit C. Commits D-F do not modify any golden.
 
 ### Example
 
@@ -263,7 +263,7 @@ Today `check_duplicate_basenames` (`src/piketype/validate/namespace.py`) only ru
 After this change:
 
 - `check_duplicate_basenames` runs **unconditionally** for every `piketype gen` invocation, not just under `--namespace`.
-- The current error message at `src/piketype/validate/namespace.py:113-119` is `"--namespace requires unique module basenames, but duplicates were found:\n  '{stem}': ..."`. After this change the message is updated to drop the `--namespace` precondition wording: `"piketype requires unique module basenames across the repo, but duplicates were found:\n  '{stem}': ..."`. The fragment-based assertions in `tests/test_namespace_validation.py:176-182` (which check for the stem name and the conflicting paths but not the lead-in phrase) are updated to match the new wording.
+- The current error message at `src/piketype/validate/namespace.py:113-119` is `"--namespace requires unique module basenames, but duplicates were found:\n  '{stem}': ..."`. After this change the message is updated to drop the `--namespace` precondition wording: `"piketype requires unique module basenames across the repo, but duplicates were found:\n  '{stem}': ..."`. Existing fragment-based assertions in `tests/test_namespace_validation.py:176-182` continue to pass without modification — they check the stem name and conflicting paths only, not the lead-in phrase.
 - Same-basename modules in disjoint subtrees are rejected at validation time, before any SV/C++/Python emission.
 - This is independent of whether any cross-module reference exists; a same-basename collision is rejected even in a single-module workload (this is a stricter rule than today, justified by the new emission semantics).
 
@@ -431,6 +431,8 @@ None. Q1, Q2, Q3 from iteration 1 are resolved in FR-1 (scoped sys.modules), FR-
 
 ## Changelog
 
+- [Clarification iter2] Staging note: rewrote Commit B to **fully** plumb the repo-wide `TypeRefIR` lookup through all backends (instead of leaving it unused), so Commit C's new cross-module fixture/goldens compile correctly.
+- [Clarification iter2] FR-9a: corrected wording — existing fragment-based assertions in `tests/test_namespace_validation.py` continue to pass without modification (the test only checks stem and paths, not the lead-in phrase).
 - [Clarification iter1] CL-1 → FR-9: pinned exact whitespace (no blank between `package` line and first `import`; one blank between import block and first `localparam`).
 - [Clarification iter1] CL-2 → FR-11: corrected import-section description (existing goldens have no runtime import); cross-module `from ... import` block goes between stdlib and declarations.
 - [Clarification iter1] CL-3 → FR-10: import lines in `_test_pkg.sv` are contiguous (no blank lines between same-module synth, cross-module synth, cross-module test blocks); one blank line before the first class.
