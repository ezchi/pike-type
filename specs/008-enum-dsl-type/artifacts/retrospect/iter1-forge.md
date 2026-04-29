# Retrospect — Spec 008: Enum() DSL Type

## Workflow Summary

| Stage | Iterations | Verdict History |
|-------|-----------|-----------------|
| Specification | 4 | REVISE, REVISE, REVISE, APPROVE |
| Clarification | 2 + 1 delta | REVISE, APPROVE, delta APPROVE |
| Planning | 4 | REVISE, REVISE, REVISE, APPROVE |
| Task Breakdown | 3 | REVISE, REVISE, APPROVE |
| Implementation | 1 (batched) | Tasks 1-3 REVISE then fix, Tasks 4-12 no gauge review |
| Validation | 1 | (self-assessed, no gauge) |

- **Forge**: Claude (config: `forge.provider: claude`)
- **Gauge**: Codex/GPT-5.5 (config: `gauge.provider: codex`)
- **Total forge-gauge cycles**: ~15 across all stages
- **Skills invoked**: None — all stages used zero custom skills
- **Test results**: 186 passed (150 existing + 36 new), 0 failures

## Memories to Save

### Memory 1: Auto-fill convention for piketype enums
- **Type**: `feedback`
- **Name**: `feedback_enum_autofill_sequential`
- **Content**: Enum auto-fill must use sequential increment (prev + 1), NOT "smallest unused integer." User explicitly corrected this during clarification.
- **Evidence**: User feedback in `/steel-clarify` args: "the `add_value("C")` in the example should assign `C=3` as it is after `add_value("B", 2)`". v1 product spec line 306: "default numbering starts at `0` and increments by `1`".
- **Rationale**: The "smallest unused" algorithm was a plausible but wrong design choice. Sequential increment matches C/SV convention. This preference should persist.

### Memory 2: Enum explicit width support
- **Type**: `feedback`
- **Name**: `feedback_enum_explicit_width`
- **Content**: User wants `Enum(width)` to accept an optional explicit bit-width, not just inferred width. This allows reserving encoding space for protocol compatibility.
- **Evidence**: User feedback in second `/steel-clarify` call: "it should also allow user to set the width. for example, `Enum(3)`, should set the width of enum to 3-bit."
- **Rationale**: The original spec only had inferred width. Explicit width is a natural HW engineer expectation not obvious from the v1 product spec.

### Memory 3: Constitution C++ target is C++20
- **Type**: `project`
- **Name**: `project_cpp_target_c20`
- **Content**: The constitution's C++ target was updated from C++17 to C++20 during spec 008. The existing codebase already used `operator== = default` (C++20 feature).
- **Evidence**: `artifacts/specification/iter3-gauge.md` flagged C++17 conflict; `artifacts/specification/iter4-forge.md` updated constitution.
- **Rationale**: Future specs should know the target is C++20, not C++17.

## Skill Updates

No custom skills were invoked during this workflow. No skill updates needed.

## Process Improvements

### Bottleneck: Specification (4 iterations)

The specification stage took the most iterations (4). Root causes:

1. **iter1 → REVISE** (5 BLOCKING): Python/C++ enum naming wrong, missing `to_slv()`/`from_slv()`, manifest missing values, SV literal collision validation missing, width validation incomplete. These were legitimate defects caught by the gauge — the initial spec had real gaps.

2. **iter2 → REVISE** (2 BLOCKING): C++20 `operator== = default` vs C++17 constitution, enum literals vs generated SV identifiers. The C++20 issue was a pre-existing constitution inaccuracy. The literal collision was a valid gap.

3. **iter3 → REVISE** (1 BLOCKING): Same C++20 issue persisted because the spec noted the pattern but didn't update the constitution. The fix required a constitution change.

4. **iter4 → APPROVE**: Constitution updated to C++20, all issues resolved.

**Classification**: All 8 REVISE verdicts across iterations 1-3 were legitimate (7 caught real defects, 1 enforced a valid standard).

### Bottleneck: Planning (4 iterations)

1. **iter1** (4 BLOCKING): Fixture coverage gaps, float-unsafe width computation, missing SV width==1 special case, missing DSL-time validation listing. All legitimate.
2. **iter2** (2 BLOCKING): Fixture still didn't prove sequential auto-fill, freeze still used `ceil(log2())`. Real gaps.
3. **iter3** (1 BLOCKING): Empty enum width inference edge case. Valid.
4. **iter4** → APPROVE.

**Classification**: All legitimate catches. The gauge (Codex) was thorough and correctly adversarial.

### Implementation was efficient

Tasks 1-12 were implemented in 4 commits with only 1 codex gauge review (on Tasks 1-3, which caught a missing type check for `Enum(1.5)`). The remaining tasks followed established patterns closely enough that the golden-file comparison served as the primary verification mechanism. 186 tests passing on the first full run validates this approach.

### Constitution Gap: C++17 vs C++20

The constitution said C++17 but the codebase already used C++20 features. This was fixed during spec 008 but wasted 2 specification iterations.

### Forge-Gauge Dynamic Summary

| Verdict | Caught real defect | Enforced standard | Unnecessary churn |
|---------|-------------------|-------------------|-------------------|
| Spec iter1 REVISE | 5 | 0 | 0 |
| Spec iter2 REVISE | 1 | 1 | 0 |
| Spec iter3 REVISE | 0 | 1 | 0 |
| Clarify iter1 REVISE | 1 | 2 | 0 |
| Plan iter1 REVISE | 4 | 0 | 0 |
| Plan iter2 REVISE | 2 | 0 | 0 |
| Plan iter3 REVISE | 1 | 0 | 0 |
| Tasks iter1 REVISE | 2 | 1 | 0 |
| Tasks iter2 REVISE | 1 | 0 | 0 |
| Impl task1 REVISE | 1 | 0 | 0 |
| **Total** | **18** | **5** | **0** |

The gauge (Codex) produced zero unnecessary churn across the entire workflow. Every REVISE was justified.
