# Retrospect — Spec 009: Struct Accepts Enum as Member

## Summary

Added Enum type support as Struct members across all pipeline stages. 6 files edited (~30 lines of production code), 1 fixture + 13 golden files + 1 test file (15 tests) created. Total test suite: 201 tests, 0 regressions.

## What Went Well

1. **Pattern reuse**: The Flags-as-Struct-member pattern (spec 007) transferred almost 1:1 to Enum. The spec, plan, and implementation all followed the same structure.
2. **Existing generic paths**: Most backend code already handled `TypeRefIR` generically. Only tuple expansions were needed in most places.
3. **Comprehensive test coverage**: 15 new tests covering DSL, freeze, golden, runtime, and negative cases. All 24 ACs verified.
4. **Gauge feedback was actionable**: The plan revision caught wrong golden file paths and missing negative test concreteness — both would have cost time during implementation.

## What Could Be Improved

1. **Freeze test API mismatch**: The initial freeze tests assumed a different API (`module_dict=` keyword) than the actual `LoadedModule`-based interface. This is a recurring issue when writing tests that call internal freeze functions. Consider a test helper that wraps module dict → LoadedModule construction.
2. **Gauge iteration on plan**: The first plan iteration was rejected due to wrong golden paths. This is a pattern — golden file paths are tricky because they don't follow a consistent naming convention across specs. Future specs should verify golden paths before writing them in the plan.

## Metrics

| Metric | Value |
|---|---|
| Production files changed | 6 |
| Production lines changed | ~30 |
| New test file | 1 |
| New tests | 15 |
| New golden files | 13 |
| Total test suite | 201 |
| Spec iterations | 1 (Forge) + 1 (post-Gauge revision) |
| Plan iterations | 2 (REVISE then APPROVE) |
| Task iterations | 1 (APPROVE) |
| Skills invoked | 0 |

## Learnings

- Adding a new member type to Struct is now a well-documented pattern: DSL union → freeze (field type + padding + serialized width) → validation allowlist → SV composite ref + field decl → Python coercer → C++ pack/unpack/clone.
- Enum padding is different from Flags/Struct padding (not byte-aligned by default), requiring explicit `compute_padding_bits()`. This is the key correctness-sensitive change in the pattern.
