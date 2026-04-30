# Gauge Review — Task Breakdown Iteration 2

## Summary

The two iter1 BLOCKING issues are resolved: T26b now directly tests same-process `RepoIR` identity, and T37 has a concrete NFR-3 dependency metadata check. Do not approve yet: W3 is only partially fixed because the plan now claims `basedpyright` is run in every integration-check task, but the task breakdown does not enforce that consistently and still contains stale CI wording.

## Iter1 Issue Resolution

- B1: ✓ resolved. T26b is placed after the `cross_module_type_refs` fixture exists and explicitly requires loading that fixture twice in the same Python process via `prepare_run` + `freeze_repo`, then deeply comparing the two `RepoIR` instances. That is the missing AC-7 same-process IR identity evidence, distinct from T25's generated-file idempotency check.

- B2: ✓ resolved. T37's NFR-3 line is concrete: `git diff develop -- pyproject.toml` must show no additions to `[project].dependencies`, with only the existing `jinja2` runtime dependency allowed.

- W1: ✓ resolved. T32's file list now includes `tests/test_namespace_validation.py` and its verification names the new duplicate-basename-without-namespace test.

- W2: ✓ resolved. T12 now assigns the R8 invariant documentation to `_freeze_field_type` in `src/piketype/dsl/freeze.py`.

- W3: ~ partial. The AC-22 plan section correctly drops the basedpyright CI commitment and says the command is manual because this repo has no CI. The task breakdown still does not match the new plan statement that `basedpyright src/piketype tests/` runs in every integration check: T11 mentions it only in the description, while T17, T28, and T35 do not mention it at all. The plan also still says "CI runs the full suite on each push" and "CI runs [the perf test] as a separate gated job", which contradicts the same AC-22 section's no-CI statement.

## New Issues

### BLOCKING

None.

### WARNING

- AC-22 task/plan mismatch remains. Either add `basedpyright src/piketype tests/` to the description and verification criteria for T11, T17, T28, and T35, or weaken the plan wording so it no longer says every integration-check task runs it. As written, the implementation plan promises a per-commit type-check gate that the task list will not actually execute.

- Stale CI wording remains in the plan. `plan.md` still claims CI runs the full suite and the perf gate, while the AC-22 section says no CI configuration exists and adding CI is out of scope. That contradiction should be removed before approval.

### NOTE

- The summary says "**Total tasks: 37**" even though T1-T37 plus T26b gives 38 task blocks. If T26b is intentionally a subtask, say that explicitly; otherwise update the count.

## Strengths

- T26b fixes the important AC-7 gap at the correct layer: it compares frozen IR identity rather than generated output.

- T37's NFR-3 check is specific, cheap, and tied to the dependency metadata file that matters for runtime dependency growth.

- T12 and T32 now contain the exact file ownership and verification hooks needed for the R8 docstring and duplicate-basename fixes.

- The A-F sequencing remains intact; the new T26b dependency on T22/T23 keeps it after the cross-module fixture and goldens exist.

VERDICT: REVISE
