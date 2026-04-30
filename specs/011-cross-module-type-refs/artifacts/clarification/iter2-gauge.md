# Gauge Review — Clarification Iteration 2

## Summary

The original iter1 repo-wide lookup blocker is fixed: Commit B now performs the full backend lookup switchover before Commit C creates cross-module `TypeRefIR`s. Do not approve this iteration: the revised staging note introduces a new blocking contradiction by adding cross-module fixture goldens in Commit C while deferring the import/include/from-import emission needed for those goldens to Commit D.

## Iter1 Issue Resolution

- ✓ resolved — iter1 BLOCKING, repo-wide `TypeRefIR` lookup staging. Commit B now says it updates all SV/Python/C++ backend `TypeRefIR` resolutions to use `(module_python_name, type_name)` and removes module-local shortcuts wherever a `TypeRefIR` is dereferenced (`specs/011-cross-module-type-refs/spec.md:40-42`). That resolves the specific iter1 failure where Commit C was asked to produce cross-module fixture goldens while backends still only had module-local lookup (`specs/011-cross-module-type-refs/artifacts/clarification/iter1-gauge.md:29-32`). Same-module byte-parity is plausible because same-module refs already carry the current module in `field.type_ir.module`, and FR-7 explicitly requires repo-key lookup while preserving same-module behavior (`specs/011-cross-module-type-refs/spec.md:219-232`).

- ✓ resolved — iter1 WARNING, CL-8 stale spec text. FR-9a now says existing fragment assertions continue to pass without modification and explains that they check the stem and paths only (`specs/011-cross-module-type-refs/spec.md:263-267`). The referenced test confirms that: it asserts `"types"`, `"alpha/piketype/types.py"`, and `"beta/piketype/types.py"`, not the lead-in phrase (`tests/test_namespace_validation.py:176-182`).

- ✓ resolved — iter1 WARNING, CL-10 inaccurate "already work today" claim. CL-10 no longer says cross-module const refs already work; it says they resolve reliably after FR-1 stabilizes object identity, then only a dependency-accumulation visitor is needed (`specs/011-cross-module-type-refs/clarifications.md:133-139`). That matches current source: discovery is sorted but dependency-unaware (`src/piketype/discovery/scanner.py:26-34`), the loader currently pops and re-executes modules (`src/piketype/loader/python_loader.py:29-44`), const definition maps skip imported objects from other source paths (`src/piketype/dsl/freeze.py:73-89`), and `_freeze_expr` still depends on object-id lookup (`src/piketype/dsl/freeze.py:374-389`).

## New Issues

### BLOCKING

- Commit C cannot truthfully add compile-correct final cross-module fixture goldens while FR-9 through FR-12 emission is deferred to Commit D. Commit C is scoped to FR-2/3/4, FR-5, FR-14, and the new fixture/goldens, with the claim that those goldens compile correctly because Commit B already plumbed repo-wide lookup (`specs/011-cross-module-type-refs/spec.md:42`). Commit D is where the actual SV imports, Python `from ... import` lines, and C++ includes/qualified names are implemented (`specs/011-cross-module-type-refs/spec.md:43`; FR-9 through FR-12 at `specs/011-cross-module-type-refs/spec.md:248-305`). Repo-wide lookup alone is not enough: current SV synth template has no import block (`src/piketype/backends/sv/templates/module_synth.j2:1-8`), current SV test template only emits the same-module synth import supplied by `synth_package_import` (`src/piketype/backends/sv/templates/module_test.j2:3-5`; `src/piketype/backends/sv/view.py:689-705`), current Python template has only `__future__`, dataclasses, and enum imports (`src/piketype/backends/py/templates/module.j2:3-14`), and current C++ template has only std includes (`src/piketype/backends/cpp/templates/module.j2:6-12`). The staging note must either move the cross-module fixture/goldens to Commit D, move FR-9/10/11/12 into Commit C, or explicitly state that Commit C's new goldens are transitional and Commit D rewrites only those new goldens.

- The same staging note contradicts itself on whether Commit D may modify goldens. Commit D says cross-module fixture goldens may be rewritten if needed (`specs/011-cross-module-type-refs/spec.md:43`), but the summary immediately says Commits D-F do not modify any golden (`specs/011-cross-module-type-refs/spec.md:47`). That is not a wording nit; it changes what a staged implementation is allowed to do.

### WARNING

- CL-8 bookkeeping is now stale. The clarification still says "No spec update needed" (`specs/011-cross-module-type-refs/clarifications.md:113-119`) and the summary still marks CL-8 as no-spec-change (`specs/011-cross-module-type-refs/clarifications.md:143-158`), but iter2 did update FR-9a and added a changelog entry for that update (`specs/011-cross-module-type-refs/spec.md:263-267`, `specs/011-cross-module-type-refs/spec.md:434-435`). This does not break the requirement text, but the clarification artifact is inaccurate.

### NOTE

- The Commit B byte-parity claim for existing same-module fixtures is plausible. The current backends resolve `TypeRefIR`s through name-only module-local indexes (`src/piketype/backends/sv/view.py:339-357`, `src/piketype/backends/py/view.py:338-364`, `src/piketype/backends/cpp/view.py:461-478`); switching those lookups to the same target through `field.type_ir.module` should not change rendered text for existing same-module fixtures.

## Strengths

- FR-9a now matches the actual namespace validation test assertions.
- CL-10 now correctly ties const-ref reliability to FR-1 instead of overstating current behavior.
- FR-7's emitter-wiring requirements are precise enough to prevent a half-plumbed repo index.

VERDICT: REVISE
