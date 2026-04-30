# Gauge Review Prompt — Planning Iteration 3

This is iteration 3 of the planning stage. Iteration 2 returned `VERDICT: REVISE` with:

1. BLOCKING — `tuple[str, ...] | None` violates FR-8.
2. BLOCKING — C++ byte-parity issues in `CppNamespaceView` (nested `piketype`) and `standard_includes` (alphabetization claim).
3. BLOCKING — C++/SV view-model dataclasses still under-specified.
4. WARNING — `render` accepted `dict` context, contradicting FR-3.

All four were addressed in iter3.

## Inputs

- `specs/010-jinja-template-migration/plan.md` (iter3).
- `specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md`.

## Review

1. Confirm every transitional view uses `tuple[str, ...]` + `has_body_lines: bool`, no `| None`.
2. Confirm `CppNamespaceView` matches current emitter byte output (single C++17 nested namespace line, `piketype` filtered, `has_namespace` bool guards open/close lines).
3. Confirm `standard_includes` is declaration-order (cstdint always; cstddef/stdexcept/vector if has_types) — NOT alphabetized.
4. Confirm Cpp{Guard,Constant,ScalarAlias,EnumMember,Enum,FlagField,Flags,StructField,Struct}View are explicitly defined.
5. Confirm SV typedef and helper-class variants are explicitly defined (synth and test).
6. Confirm `render` rejects dict context.
7. Look for any new contradictions, missing FR coverage, or commit-level inconsistency.

End with `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.

Bias APPROVE: only one round of REVISE remains in the maxIterations budget.
