# Gauge Review — Clarification Iteration 1

## Summary

Most of the direct spec edits from CL-1, CL-2, CL-3, CL-5, CL-6, and CL-7 were applied accurately and match the source/golden facts I checked. Do not approve this iteration: the staging note still contains a blocking cross-step contradiction, CL-8's "no spec change" conflicts with existing spec text, and CL-10 overstates existing cross-module const-ref behavior.

## Per-Clarification Verdict

- ✓ CL-1 correct and applied. FR-9 now pins no blank line between `package {basename}_pkg;` and the first import, with one blank line before the first declaration (`specs/011-cross-module-type-refs/spec.md:248-257`). The expected example already uses that layout (`specs/011-cross-module-type-refs/spec.md:80-83`), and the existing `_test_pkg` golden has `package` immediately followed by `import` (`tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:5-7`). Changelog entry exists (`specs/011-cross-module-type-refs/spec.md:434`).

- ✓ CL-2 correct and applied. FR-11 removed the nonexistent "runtime import" reference and specifies `__future__`, stdlib, cross-module imports, declarations (`specs/011-cross-module-type-refs/spec.md:282-290`). I found 19 existing `*_types.py` goldens; `rg "piketype_runtime|runtime|from piketype" tests/goldens/gen -g '*_types.py'` returned no matches. Representative current layout is `from __future__ import annotations`, blank, then stdlib imports (`tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:5-7`). Changelog entry exists (`specs/011-cross-module-type-refs/spec.md:435`).

- ✓ CL-3 correct and applied. FR-10 now requires the same-module synth import, cross-module synth imports, and cross-module test imports to be contiguous, with one blank before the first class (`specs/011-cross-module-type-refs/spec.md:270-280`). Existing `_test_pkg` style matches the one-import precedent (`tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:5-8`). Changelog entry exists (`specs/011-cross-module-type-refs/spec.md:436`).

- ✓ CL-4 correct as a no-spec-change item, but implementation must remember the other helpers. FR-1 already covers `tests/test_view_py.py` and "any other entry point" (`specs/011-cross-module-type-refs/spec.md:134-160`). The cited helper still calls `load_module_from_path` in a loop (`tests/test_view_py.py:35-45`), and the same pattern also exists in `tests/test_view_cpp.py:29-45` and `tests/test_view_sv.py:29-45`; the clarification's instruction to search all tests is necessary.

- ✓ CL-5 correct and applied. FR-15 now contains exact replacement text for constitution constraint #4 (`specs/011-cross-module-type-refs/spec.md:331-341`), replacing the current no-cross-module constraint (`.steel/constitution.md:105-111`). Changelog entry exists (`specs/011-cross-module-type-refs/spec.md:437`).

- ✓ CL-6 correct and applied. FR-6 now defines N-node cycle formatting, lexicographic rotation, and repetition of the first node at the end (`specs/011-cross-module-type-refs/spec.md:200-209`). Changelog entry exists (`specs/011-cross-module-type-refs/spec.md:438`).

- ✓ CL-7 correct and applied. FR-13 now covers all import-style lines, including the existing same-module SV import currently built at `src/piketype/backends/sv/view.py:704` (`specs/011-cross-module-type-refs/spec.md:307-315`; `src/piketype/backends/sv/view.py:701-705`). AC-23's allowlist is now specified as empty after that refactor (`specs/011-cross-module-type-refs/spec.md:397-415`). A spot-check of the six inspected backend Python files found only the intended current f-string at `src/piketype/backends/sv/view.py:704`, so I found no additional false-positive problem. Changelog entry exists (`specs/011-cross-module-type-refs/spec.md:439`).

- ~ CL-8 partial. The "existing tests pass without modification" claim is true: the test checks only the stem and conflicting paths (`tests/test_namespace_validation.py:176-182`), while the implementation currently has the old lead-in at `src/piketype/validate/namespace.py:117-119`. But the spec still says those fragment-based assertions "are updated to match the new wording" (`specs/011-cross-module-type-refs/spec.md:263-267`). That conflicts with CL-8's no-spec-change resolution (`specs/011-cross-module-type-refs/clarifications.md:113-119`). This needs a spec edit removing or rewording the test-update sentence.

- ✓ CL-9 correct as a no-spec-change item. FR-14 already says the manifest module record's `dependencies` key is populated from `ModuleIR.dependencies` and is currently always `[]` (`specs/011-cross-module-type-refs/spec.md:317-329`). The serializer always emits `"dependencies": []` today (`src/piketype/manifest/write_json.py:71-104`), and current manifest goldens contain empty dependency arrays for every existing module record.

- ~ CL-10 partial. The implementation guidance is right that, after FR-1 stabilizes object identity, no new `_freeze_expr` behavior is needed and a dependency visitor over existing `ExprIR` sites is enough (`src/piketype/dsl/freeze.py:374-408`; `specs/011-cross-module-type-refs/spec.md:176-190`). The existing-behavior claim is false as written. Current discovery is sorted but dependency-unaware (`src/piketype/discovery/scanner.py:26-34`), the loader pops and re-executes the module currently being loaded (`src/piketype/loader/python_loader.py:29-44`), definition maps ignore imported Const objects whose source path is not the loaded module (`src/piketype/dsl/freeze.py:73-89`), and `_freeze_expr` raises on an unrecognized Const object id (`src/piketype/dsl/freeze.py:385-389`). So cross-module const refs do not reliably "already work today"; they only work when load order happens to preserve the referenced object identity.

## Missed Clarifications

- BLOCKING: The implementation staging note is internally inconsistent. Commit B says the repo-wide index is added but "unused" and local lookup remains first (`specs/011-cross-module-type-refs/spec.md:40-42`), while Commit C says freeze starts producing cross-module `TypeRefIR` and adds the new fixture/goldens (`specs/011-cross-module-type-refs/spec.md:42-43`, `specs/011-cross-module-type-refs/spec.md:47`). Current backend helpers resolve `TypeRefIR` through module-local indexes (`src/piketype/backends/sv/view.py:339-342`, `src/piketype/backends/py/view.py:459-472`, `src/piketype/backends/cpp/view.py:461-477`), so Commit C cannot generate the cross-module fixture unless the repo-wide index is actually used by then. Fix the staging note: either make Commit B wire repo-wide lookup for all `TypeRefIR` resolutions while preserving byte-identical output, or move the new cross-module fixture/goldens to Commit D.

- WARNING: CL-8 should not remain a no-op. The spec text still instructs a test update that CL-8 says is unnecessary (`specs/011-cross-module-type-refs/spec.md:263-267`; `specs/011-cross-module-type-refs/clarifications.md:113-119`).

- WARNING: CL-10 should correct the current-behavior claim. The spec itself can probably stay unchanged, but the clarification should say the existing expression-freeze machinery is sufficient after FR-1, not that cross-module const refs already work reliably today.

## Issues

### BLOCKING

- Staging contradiction: Commit C introduces cross-module `TypeRefIR` and new goldens before the staging note requires backend `TypeRefIR` lookups to use the repo-wide index. This is not implementable with the current local lookup code.

### WARNING

- CL-8's no-spec-change decision leaves stale spec wording that says duplicate-basename assertions are updated, despite the clarification saying existing fragment assertions need no change.
- CL-10's "already work today" claim is wrong under the current dependency-unaware loader order and object-id based definition maps.

### NOTE

- AC-23's empty allowlist direction is coherent. A spot-check of the six inspected backend Python files found no current legitimate Python string false positives besides the existing `sv/view.py:704` f-string that CL-7 intentionally removes.
- Manifest backward compatibility is covered: the field is always present today, and FR-14's wording is enough to keep empty dependencies serialized as `[]`.
- The FR-16 cycle fixture fallback is acceptable. If a Python-level cross-module cycle cannot be constructed without import failure, the spec permits direct `RepoIR` unit construction (`specs/011-cross-module-type-refs/spec.md:353-355`).

## Strengths

- The whitespace and import-block decisions are now precise enough for byte-for-byte goldens.
- The AC-23 static-check wording is much stronger than a grep rule and correctly includes f-strings, concatenation, `.format`, `.join`, and `%` formatting.
- The manifest and Python import placement clarifications match current goldens.

VERDICT: REVISE
