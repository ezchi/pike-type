# Gauge Review Prompt — Planning Iteration 4

This is iteration 4. Iteration 3 returned `VERDICT: REVISE` with three BLOCKINGs:

1. Leftover prose at Phase 1 commit 5 still said `body_lines` was "always None" — contradicting the new tuple-plus-bool mechanism.
2. `SvPackUnpackFnView` precomputed `pack_lines` / `unpack_lines` as Python-built body strings — meaningful structure had to move into templates.
3. C++ scalar dataclasses missed primitives needed for current helper branches (signed-padding branch booleans, full-range literal, byte-total mask literal).

All three were addressed in iter4.

## Inputs

- `specs/010-jinja-template-migration/plan.md` (iter4).
- `specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md`.

## Review

1. Confirm the Phase 1 commit 5 description now uses the empty-tuple + `has_body_lines=False` language.
2. Confirm `SvPackUnpackFnView` is now a union of four structured variants (scalar/flags/enum/struct) with no pre-rendered body strings.
3. Confirm `CppScalarAliasView` now exposes:
   - `is_narrow_signed` / `is_narrow_unsigned` / `is_wide` discriminators.
   - `has_signed_padding` and `has_signed_short_width` branch booleans.
   - `full_range_literal`, `byte_total_mask_literal`, in addition to the previously existing literals.
4. Look for any new contradictions introduced by these surgical edits.

This is the **maxIterations=5 budget**. After this round there is one more REVISE allowed before the loop exits without an APPROVE; bias APPROVE if the three BLOCKINGs are mechanically resolved and no new BLOCKING is introduced.

End with `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.
