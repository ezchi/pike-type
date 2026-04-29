# Gauge Review Prompt — Planning Iteration 2

This is **iteration 2** of the planning stage. Iteration 1 returned `VERDICT: REVISE` with 5 BLOCKING and 3 WARNING issues:

1. BLOCKING — Phase 1-3 commits ordered by type family, not FR-6 sub-step.
2. BLOCKING — Python view-model sketch incomplete; FlagsFieldView referenced but not defined.
3. BLOCKING — C++ plan precomputed full pack/unpack helper bodies in Python (violates FR-10/NFR-5).
4. BLOCKING — C++/SV view sketches were "same shape as Phase 1", not actionable.
5. BLOCKING — Byte-parity strategy underspecified for intermediate commits.
6. WARNING — Phase 0 wheel-packaging smoke test before any .j2 file exists is meaningless.
7. WARNING — Risk register missed Jinja trim/lstrip and frozen-IR construction.
8. WARNING — `make_environment` env options + keyword-only signature not pinned.
9. NOTE — C++ `--namespace` override.

## Inputs to Review

1. **Implementation plan:** `specs/010-jinja-template-migration/plan.md` (iteration 2).
2. **Specification (binding):** `specs/010-jinja-template-migration/spec.md`.
3. **Iteration-1 review:** `specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md`.

## Review Instructions

1. **Did each iter1 issue get resolved?** For each numbered item above, state whether it is resolved, partially resolved, or not resolved, citing the relevant section of plan.md (Phase X commit Y, view-model dataclass name, risk register row, etc.).

2. **Look for new issues introduced by iter2.** In particular:
   - Does the new `body_lines: tuple[str, ...] | None` passthrough mechanism violate FR-8/FR-9 (it's a primitive `tuple` of `str`, so it should comply, but verify)?
   - Does the FR-6 sub-step commit ordering still preserve byte parity at every commit? Walk through Phase 1 commits 2–6 and confirm each one's parity claim is consistent with how the view + template + legacy fragment interact.
   - Are the Python/C++/SV view-model dataclass sketches now complete enough that an implementer can build them without deriving missing primitives? Spot-check against the actual current emitter helpers:
     - `_render_py_enum` → `EnumView` should carry `mask`, `first_member_name`, `enum_class_name`, `width`, `byte_count`.
     - `_render_py_flags` → `FlagsView` should carry `data_mask`, `total_bits`, plus per-flag `bit_mask`.
     - `_render_py_struct_field_coercer` → `StructFieldView` discriminators must distinguish struct-ref / flags-ref / enum-ref / scalar-ref / narrow-scalar / wide-scalar.
     - `_render_cpp_*` → similar coverage.
     - `_render_sv_*` synth and test split with helper-class fields.

3. **Phase 4 wheel check.** Does the AC-F5 description correctly diff "every .j2 in source" against "every .j2 in the wheel" without hardcoding a count? Verify.

4. **Risk register.** Are the two added risks (Jinja trim/lstrip, frozen-IR construction) concrete enough? Confirm.

5. **Constitution alignment.** Same checks as iter1.

## Output Format

- Executive summary (2-4 sentences).
- Iter1 issue resolution table.
- New issues with severity tags.
- `VERDICT: APPROVE` or `VERDICT: REVISE` on the final line. No text after.

Bias toward APPROVE when no BLOCKING remains and the plan is concretely actionable.
