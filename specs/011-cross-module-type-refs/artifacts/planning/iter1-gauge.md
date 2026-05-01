# Gauge Review - Planning Iteration 1

## Summary

REVISE. The staging shape is mostly sound, and the plan correctly identifies the loader, freeze, validation, backend, manifest, and constitution touch points. It still has hard spec-coverage failures: the backend view-model design violates FR-13/AC-23, the `--namespace` branch of AC-6 is untested, and NFR-4/AC-22 are not made verifiable.

## Spec Coverage Audit

### Functional Requirements

| ID | Plan mapping | Status |
|----|--------------|--------|
| FR-1 | `plan.md:20-23`, `plan.md:154-162`, `plan.md:228-233` | Covered, with a loader-shim warning below. |
| FR-2 | `plan.md:31-32`, `plan.md:121-125`, `plan.md:185` | Covered. Source confirms `_freeze_field_type` already returns `TypeRefIR` on definition-map hits (`src/piketype/dsl/freeze.py:355-358`). |
| FR-3 | `plan.md:102-104`, `plan.md:213`, `plan.md:283` | Covered by the `multiple_of` fixture. |
| FR-4 | `plan.md:34-35`, `plan.md:181-185`, `plan.md:84-86` | Covered. Current source still hard-codes `dependencies=()` (`src/piketype/dsl/freeze.py:271-277`). |
| FR-5 | `plan.md:44-47`, `plan.md:181-186` | Covered. Current validator has the exact rejection to remove (`src/piketype/validate/engine.py:69-73`). |
| FR-6 | `plan.md:48`, `plan.md:208`, `plan.md:276` | Covered. Current cycle pass is same-module only (`src/piketype/validate/engine.py:185-215`). |
| FR-7 | `plan.md:40`, `plan.md:57-60`, `plan.md:165-175` | Covered. Current backends still build module-local indexes (`src/piketype/backends/sv/view.py:661-672`, `src/piketype/backends/py/view.py:459`, `src/piketype/backends/cpp/view.py:604-617`). |
| FR-8 | `plan.md:49`, `plan.md:209`, `plan.md:276` | Mostly covered; test enumeration is too loose for the two enum-literal diagnostics. |
| FR-9 | `plan.md:66`, `plan.md:71`, `plan.md:190-200` | Covered in intent, blocked by template-first violation. |
| FR-9a | `plan.md:50-53`, `plan.md:210-211`, `plan.md:277` | Covered. Current command gates duplicate-basename checking under `--namespace` (`src/piketype/commands/gen.py:31-32`). |
| FR-10 | `plan.md:67-72`, `plan.md:190-200` | Covered in intent, blocked by template-first violation. |
| FR-11 | `plan.md:76-77`, `plan.md:190-200` | Covered in intent, blocked by template-first violation. |
| FR-12 | `plan.md:81-82`, `plan.md:197` | Covered, but the C++ namespace-helper API needs tightening. |
| FR-13 | `plan.md:12`, `plan.md:65`, `plan.md:194-199` | Not covered correctly; see BLOCKING issue 1. |
| FR-14 | `plan.md:84-86`, `plan.md:184` | Covered. Current manifest emits `"dependencies": []` unconditionally (`src/piketype/manifest/write_json.py:103`). |
| FR-15 | `plan.md:218-223` | Covered. Current constitution still has the old constraint (`.steel/constitution.md:110`). |
| FR-16 | `plan.md:88-115`, `plan.md:190-215`, `plan.md:270-296` | Mostly covered; AC-6/AC-22/NFR-4 gaps remain. |

### Non-Functional Requirements

| ID | Plan mapping | Status |
|----|--------------|--------|
| NFR-1 | `plan.md:14`, `plan.md:152-175`, `plan.md:188`, `plan.md:202`, `plan.md:288` | Covered. |
| NFR-2 | `plan.md:34`, `plan.md:66`, `plan.md:76`, `plan.md:81`, `plan.md:86` | Covered. |
| NFR-3 | `plan.md:143-148` | Covered. |
| NFR-4 | `plan.md:252-256` | Not testable as written; see BLOCKING issue 3. |
| NFR-5 | `plan.md:145-148` only implies typed stdlib work | Not verified; see BLOCKING issue 3. |
| NFR-6 | `plan.md:218-224` | Covered. |
| NFR-7 | `plan.md:65-82`, `plan.md:194-199`, `plan.md:278` | Not covered correctly; see BLOCKING issue 1. |

### Acceptance Criteria

| ID | Plan mapping | Status |
|----|--------------|--------|
| AC-1 | `plan.md:100-115`, `plan.md:282` | Covered. |
| AC-2 | `plan.md:71`, `plan.md:115`, `plan.md:282` | Covered by primary SV golden. |
| AC-3 | `plan.md:71`, `plan.md:197-200`, `plan.md:282` | Covered by primary SV golden. |
| AC-4 | `plan.md:67-72`, `plan.md:244`, `plan.md:282` | Covered by primary SV golden. |
| AC-5 | `plan.md:76-77`, `plan.md:282` | Covered by primary Python golden, subject to template-first fix. |
| AC-6 | `plan.md:81-82`, `plan.md:282` | Default case covered; `--namespace` case missing. |
| AC-7 | `plan.md:161`, `plan.md:274` | Covered. |
| AC-8 | `plan.md:100-104`, `plan.md:282` | Covered by primary fixture using scalar, struct, enum, and flags refs. |
| AC-9 | `plan.md:186`, `plan.md:357` | Covered. |
| AC-10 | `plan.md:276` | Covered. |
| AC-11 | `plan.md:48`, `plan.md:276`, existing negative golden retained | Covered. |
| AC-12 | `plan.md:92`, `plan.md:276` | Covered. |
| AC-13 | `plan.md:92`, `plan.md:276` | Covered. |
| AC-14 | `plan.md:92`, `plan.md:276` | Partially covered; both enum-literal collision messages should be explicit. |
| AC-15 | `plan.md:34`, `plan.md:91`, `plan.md:185` | Covered. |
| AC-16 | `plan.md:84-86`, `plan.md:108-115`, `plan.md:282` | Covered. |
| AC-17 | `plan.md:294-296` | Covered. |
| AC-18 | `plan.md:102-104`, `plan.md:213`, `plan.md:283` | Covered. |
| AC-19 | `plan.md:290-292` | Covered. |
| AC-20 | `plan.md:152-175`, `plan.md:188`, `plan.md:202`, `plan.md:288` | Covered. |
| AC-21 | `plan.md:218-224` | Covered. |
| AC-22 | No explicit verification command or CI step in plan | Missing. |
| AC-23 | `plan.md:194-199`, `plan.md:278` | Test planned, but planned backend view-model strings would fail it. |
| AC-24 | `plan.md:100-115`, `plan.md:282` | Covered by primary fixture/golden. |

## Issues

### BLOCKING

- The backend view-model design violates FR-13, NFR-7, AC-23, and constitution principle 5. The spec requires all import/include/from-import output to be emitted by Jinja templates, with no backend Python string construction (`spec.md:309-313`), and AC-23's allowlist is empty (`spec.md:399-413`). The plan still proposes rendered line strings: `same_module_synth_import: str` (`plan.md:68`), SV cross-module import fields (`plan.md:66-70`), Python entries that are "the rendered `from ... import ...` line" (`plan.md:76`), and C++ include entries (`plan.md:81`). That reproduces the exact anti-pattern currently present at `src/piketype/backends/sv/view.py:704` and would be caught by the planned AST test. Fix: view models must carry semantic parts only, such as package basename, target module name, wrapper class name, and bare include path. Templates must render `import {{ package }}::*;`, `from {{ module }}_types import {{ wrapper }}`, and `#include "{{ path }}"`.

- AC-6 is not fully tested. The spec requires both default C++ qualification and the `--namespace=<user_namespace>` qualification (`spec.md:381-382`). The plan's primary golden run covers the default path only (`plan.md:282`), and there is no namespace-specific cross-module integration or view test in `plan.md:270-296`. This branch is real: `_build_namespace_view` switches behavior when `namespace is not None` (`src/piketype/backends/cpp/view.py:241-245`). Add a test that exercises cross-module C++ field rendering with `namespace="proj::lib"` or an equivalent `piketype gen --namespace` run and asserts `::proj::lib::foo::byte_t_ct`.

- NFR-4 and AC-22 are not made verifiable. The performance budget is a hard NFR (`spec.md:370`), but the plan only says to "Benchmark before/after Commit E" (`plan.md:256`); that is an instruction, not a test or gate. AC-22 requires basedpyright strict mode to pass (`spec.md:398`), but the plan has no explicit verification step. Add concrete validation commands or CI gates for both, with an artifact/threshold for the 5% performance budget.

### WARNING

- FR-8 tests are under-enumerated. The spec defines separate enum-literal collision diagnostics for imported-vs-imported and local-vs-imported cases (`spec.md:242-244`), but the plan says "three sub-cases" for FR-8 (`plan.md:92`, `plan.md:276`). That risks testing only one wildcard-literal path. Spell out four validation tests: local-vs-imported type, imported-vs-imported type, imported-vs-imported enum literal, and local-vs-imported enum literal.

- The loader shim is risky. The spec says every entry point that loads piketype modules must use the scoped snapshot/restore contract (`spec.md:138-162`). The plan keeps `load_module_from_path` as a thin shim that can still be called outside `prepare_run` (`plan.md:20-23`). Since current callers in tests use `load_module_from_path` directly (`tests/test_view_py.py:41`, `tests/test_view_cpp.py:34`, `tests/test_view_sv.py:34`), Commit A must migrate all callers in the same commit and should either make the shim private/legacy-only or make misuse fail loudly.

- The C++ qualification API is underspecified. The plan says to reuse `_build_namespace_view(module=<target_module>, namespace=<emit_namespace>)` (`plan.md:81`), but the new `build_repo_type_index` returns only `TypeDefIR` (`plan.md:40`), not the target `ModuleIR`. The implementation can use `field_ir.type_ir.module` directly or add a module index; the plan should say which.

- `tests/test_no_inline_imports.py` is described as including positive cases (`plan.md:278`), but the concrete Commit D bullet lists only detection patterns (`plan.md:199`). Add named positive cases so this does not become a brittle "only fails bad strings" test.

### NOTE

- Commit B's full switchover should preserve same-module byte parity if every lookup uses `(field.type_ir.module.python_module_name, field.type_ir.name)`. Current same-module `TypeRefIR` already carries the current module reference, and the existing validator's repo-wide `type_index` is keyed that way (`src/piketype/validate/engine.py:19-23`, `src/piketype/validate/engine.py:74`).

- `build_repo_type_index` should handle zero modules and one module naturally by returning an empty or one-module dict. Duplicate basenames do not affect that index because it is keyed by Python module name, but duplicate type names in different modules should be covered by a unit test to protect the switchover.

- A cross-module `ScalarTypeSpecIR` target is impossible through ordinary DSL construction because only top-level named type objects are importable, and `_freeze_field_type` emits `ScalarTypeSpecIR` only when the object is not in `type_definition_map` (`src/piketype/dsl/freeze.py:355-370`). The plan should state this assumption in the risk section because the prompt explicitly calls it out.

- C++ pack/unpack rendering does not appear to need extra qualification beyond `field_type_str` for cross-module ref fields. Current templates call the field object's methods (`src/piketype/backends/cpp/templates/_macros.j2:383-410`) and use type names mainly in declarations or inline scalar helpers (`src/piketype/backends/cpp/templates/_macros.j2:267-340`, `src/piketype/backends/cpp/templates/_macros.j2:374`). The plan's "pack/unpack/clone helpers" wording is conservative but imprecise.

## Strengths

- The A-F staging is directionally correct and keeps existing goldens stable while deferring new cross-module goldens until emission exists (`spec.md:38-49`, `plan.md:150-224`).
- The plan correctly identifies the current source choke points: loader re-exec (`src/piketype/loader/python_loader.py:36-44`), empty dependencies (`src/piketype/dsl/freeze.py:271-277`), validation rejection (`src/piketype/validate/engine.py:69-73`), local backend indexes (`src/piketype/backends/sv/view.py:661-672`, `src/piketype/backends/py/view.py:459`, `src/piketype/backends/cpp/view.py:604-617`), and manifest empty dependency serialization (`src/piketype/manifest/write_json.py:103`).
- Direct `RepoIR` tests for unknown-type and cycle cases are the right choice where Python import mechanics make fixture construction impossible.

VERDICT: REVISE
