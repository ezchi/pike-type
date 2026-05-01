# Gauge Review — Planning Iteration 2

## Summary

REVISE. The plan fixes the core architecture and most of the iter1 issues, especially the template-first backend model and the `--namespace=proj::lib` C++ coverage. One B3 verification item is still broken: the planned basedpyright command is not a valid basedpyright CLI invocation, so AC-22 is not actually gated.

## Iter1 Issue Resolution

- ~ partial — **B1: Backend view models and template-first import emission.** The updated plan now states the correct principle: view models carry semantic parts only, while Jinja templates render `import`, `#include`, and `from ... import` lines (`plan.md:62`). The SV fields are bare basenames (`plan.md:67-73`), Python uses dotted module name plus wrapper class name (`plan.md:77-78`), and C++ uses include-path tails (`plan.md:82-84`). Those planned fields should not trip AC-23 because none is a rendered import/include/from-import line. Minor issue: Commit D still says the existing same-module import moves "into a view-model field consumed by `module_test.j2`" (`plan.md:199`), which is imprecise because the field must not contain the rendered `import` line. The component section is clear enough to implement correctly, so this is not blocking.

- ✓ resolved — **B2: AC-6 user namespace coverage.** The plan adds a dedicated `piketype gen --namespace=proj::lib` integration path and asserts `::proj::lib::foo::byte_t_ct` plus the unchanged include path (`plan.md:301-308`). It also commits corresponding goldens under `tests/goldens/gen/cross_module_type_refs_namespace_proj/`, which makes the branch verifiable.

- ~ partial — **B3: NFR-4 and AC-22 gates.** NFR-4 is materially improved: `tests/test_perf_gen.py`, `tests/perf_baseline.json`, median-of-5 measurement, a 5% threshold, baseline capture before Commit A, and a separate CI-gated opt-in job are all concrete (`plan.md:310-319`). The basedpyright gate is not resolved: the plan requires `basedpyright --strict src/piketype tests/` (`plan.md:321-323`), but local basedpyright rejects `--strict` with `Unexpected option --strict`; strict mode is already configured in `pyproject.toml`. AC-22 needs an executable command such as `basedpyright -p pyproject.toml src/piketype tests/` or the project-standard equivalent.

- ~ partial — **W1: FR-8 test enumeration.** The detailed tests section correctly names four sub-cases: local-vs-imported type, imported-vs-imported type, imported-vs-imported enum literal, and local-vs-imported enum literal (`plan.md:92-94`). The Testing Strategy summary still says "three FR-8 collision sub-cases" (`plan.md:287`). That stale summary is not enough to block approval by itself, but it should be corrected because it contradicts the resolution.

- ✓ resolved — **W2: Loader shim risk.** The plan removes `load_module_from_path` entirely in Commit A, migrates all callers atomically, and makes `load_or_get_module` raise `RuntimeError` outside `prepare_run` (`plan.md:20-23`). That removes the unsafe shim path.

- ✓ resolved — **W3: C++ qualification API.** The C++ section explicitly reads `field_ir.type_ir.module` and passes it to `_build_namespace_view`; no separate module index is needed (`plan.md:82-83`).

- ✓ resolved — **W4: AC-23 positive cases.** The static-check plan now includes named positive cases for legitimate `.join`, `.format`, `%`, comments, and non-include preprocessor strings (`plan.md:96-99`).

## New Issues

### BLOCKING

- **AC-22 gate command is invalid.** `basedpyright --strict src/piketype tests/` is not accepted by the installed basedpyright CLI; it exits with code 4 and `Unexpected option --strict`. Since `pyproject.toml` already sets `typeCheckingMode = "strict"`, the plan should use an executable project-configured command and name it precisely. Until that is fixed, AC-22 remains unverifiable and B3 is only partial.

### WARNING

- **The performance gate measures a single fixture, not the existing fixture suite.** NFR-4 is phrased as "generation latency for the existing fixture suite" (`spec.md:370`), and the risk mitigation also says to benchmark using the existing fixture suite (`plan.md:261`). The concrete gate instead uses one fixed fixture, "the largest existing single-module fixture" (`plan.md:314-315`). This may be acceptable as a pragmatic proxy, but the plan should either benchmark the full existing fixture suite or explicitly justify why the proxy is sufficient.

- **The FR-8 count is internally inconsistent.** The detailed test list has the required four cases (`plan.md:94`), but the Testing Strategy summary still says three (`plan.md:287`). Fix the stale summary before implementation so the task breakdown does not drop one enum-literal case.

- **Commit D wording still hints at a rendered same-module import field.** The component section correctly moves literal import text to templates, but Commit D says to move the current f-string "into a view-model field" (`plan.md:199`). This should be rewritten to say the view model carries the current module basename and the template renders the line.

### NOTE

- CL-1 through CL-10 remain reflected: SV synth import whitespace, Python import placement, contiguous SV test imports, loader helper migration, exact constitution replacement, N-node cycle messages, empty AC-23 allowlist after refactor, FR-9a wording, always-present manifest dependencies, and const-ref collection are all represented in the plan.
- The new R8 invariant is present and accurate: ordinary cross-module `TypeRefIR` targets named top-level DSL types, not anonymous `ScalarTypeSpecIR` values (`plan.md:269-273`).

## Strengths

- The backend sections now separate semantic view data from emitted syntax cleanly enough for AC-23 to enforce the template-first rule.
- The `--namespace=proj::lib` C++ coverage is concrete and directly targets the branch iter1 called out.
- The loader migration plan is now atomic and removes the risky compatibility shim.

VERDICT: REVISE
