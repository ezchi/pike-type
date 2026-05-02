# Gauge Review — Task Breakdown Stage, Iteration 1

## Summary
The task breakdown for Specification 014 is highly precise and technically sound. It correctly identifies the scope of the change as template-only and meticulously enumerates all affected goldens, including the "orphan" golden requiring a namespace flag. The verification battery is comprehensive and enforces the project's byte-parity and determinism standards.

## Issues

### BLOCKING
None.

### WARNING
None.

### NOTE
- The Forge's proactive verification of the fixture directory structure correctly caught a significant gap in the original implementation plan's illustrative shell loop.

## Plan-corrections check
The Forge correctly identified that `tests/fixtures/cross_module_type_refs_namespace_proj/` does not exist. It accurately determined that this golden is generated from the `cross_module_type_refs` fixture using the `--namespace=proj::lib` flag. The per-fixture invocation table in `tasks.md` provides the necessary correction to the implementation plan.

## Spec coverage matrix
| FR / NFR / AC | Task(s) |
| :--- | :--- |
| **FR-1.1 – FR-1.4** (Codegen change) | T1 |
| **FR-2.1 – FR-2.4** (Scope boundary) | T1, T2 |
| **FR-3.1** (Complete golden list) | T2 |
| **FR-3.2, FR-3.3** (Golden diff scope) | T2, T3 |
| **NFR-1** (Template-first) | T1 |
| **NFR-2** (Byte-parity per commit) | T4 |
| **NFR-3** (Determinism) | T1 |
| **NFR-4** (Basedpyright) | T3 |
| **NFR-5** (Verilator-clean) | T3 |
| **NFR-6** (Test suite) | T3 |
| **AC-1, AC-2** (Grep verification) | T2, T3 |
| **AC-3, AC-4** (Correctness verification) | T2, T3 |
| **AC-5** (Python diff scope) | T3 |
| **AC-6, AC-7** (Golden diff scope) | T3 |
| **AC-8** (Unittest pass) | T3 |
| **AC-9** (Static type check) | T3 |
| **AC-10** (Verilator delta) | T3 |

## Constitution Alignment
The tasks are in strict alignment with the Project Constitution. They prioritize template-first generation (T1) and deterministic output via atomic commits of code and goldens (T4). The testing strategy relies on the mandated golden-file integration tests (T3). The proposed commit message in T4 follows the Conventional Commits standard with the appropriate `fix(sv)` scope.

## Verdict

VERDICT: APPROVE
