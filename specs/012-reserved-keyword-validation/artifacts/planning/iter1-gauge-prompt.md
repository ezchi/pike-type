# Gauge Review Prompt — Planning Iteration 1

You are the **Gauge** in a Forge-Gauge dual-agent loop. You are reviewing the **planning stage** for spec `012-reserved-keyword-validation`. The Forge wrote a technical plan describing how to implement the spec.

You are NOT a cheerleader. Be strict. Be blunt. Conversely, do not invent issues to look thorough. The Forge is instructed to ignore your feedback that contradicts the Project Constitution, so do not soften legitimate criticism.

## Inputs to read

1. **Project Constitution** — `.steel/constitution.md` (highest authority).
2. **Specification (post-clarification)** — `specs/012-reserved-keyword-validation/spec.md`.
3. **Clarifications** — `specs/012-reserved-keyword-validation/clarifications.md`.
4. **Plan under review** — `specs/012-reserved-keyword-validation/plan.md`.
5. **Existing validation code** — `src/piketype/validate/engine.py`.
6. **Existing IR types** — `src/piketype/ir/nodes.py` (especially `ModuleRefIR`, `ModuleIR`, `RepoIR`).
7. **Existing test patterns** — `tests/test_gen_const_sv.py` (negative-test pattern), `tests/test_validate_engine.py`.
8. **SV view layer** — `src/piketype/backends/sv/view.py` (to verify how `_pkg` names are constructed).

All paths relative to `/Users/ezchi/Projects/pike-type`.

## Review dimensions

1. **Spec coverage.** Every FR in the spec has a corresponding component or implementation note in the plan. Every AC has a test in the test matrix. Anything missing is BLOCKING.
2. **Architecture soundness.** The plan respects the four-stage pipeline (Discovery → DSL → IR → Backends). The new validator consumes only frozen IR. The plan does not propose any IR mutation. Backend code is not touched.
3. **Simplicity.** No needless abstractions, no premature factoring. Helpers are named for what they do. The plan does not introduce a new exception class (correctly reuses `ValidationError`).
4. **Risk assessment.** Are the listed risks real? Are likelihoods/impacts honest? Is anything missing? In particular:
   - Did the Forge miss any failure mode of `module.ref.basename` vs `python_module_name`? (The plan claims `basename` is the right field; verify in `nodes.py` and `sv/view.py`.)
   - Is the AC-11 ordering claim (UPPER_CASE check fires before keyword check) actually true given the existing `engine.py` ordering?
5. **Testing strategy.** Test layout follows existing conventions. The plan correctly uses `assertIn(<substring>, result.stderr)` instead of inventing a new byte-for-byte expected-error file convention. The Python-snapshot unit test is appropriately scoped.
6. **Constitutional alignment.** Audit principle by principle:
   - P1 (Single source of truth): keyword sets are data not derived; ✓ if plan keeps them in one file.
   - P2 (Immutable boundaries): no IR mutation; ✓ to verify.
   - P3 (Deterministic output): error format byte-stable; ✓ to verify the alphabetical-sort and frozen-set claims.
   - P4 (Correctness over convenience): all three languages always on; ✓ to verify.
   - P5 (Template-first): N/A for this validator.
   - P6 (Generated runtime): N/A.
7. **Phased schedule.** Are the four commits genuinely byte-parity at each step? Is anything in commit B that should be in commit A or C? Is the LOC estimate plausible?
8. **Adherence to coding standards.** `from __future__ import annotations`, frozen sets, keyword-only args, no wildcard imports.

## Specific risk points to audit

A. **`basename` vs `python_module_name`.** The plan claims FR-1.6 should use `module.ref.basename`. Verify against `src/piketype/ir/nodes.py:28` (ModuleRefIR fields) and `src/piketype/backends/sv/view.py:699` (`f"{module.ref.basename}_pkg"`). If the SV view uses `basename`, the plan is right. If it uses `python_module_name`, the plan is wrong.

B. **Ordering of validations.** The plan calls `_validate_reserved_keywords` "at the end of `validate_repo`, after `_validate_repo_struct_cycles` and `_validate_cross_module_name_conflicts`." Verify this is consistent with FR-9 ("structural validations first, then keyword validation"). Does this break or duplicate `_validate_generated_identifier_collision`?

C. **Test fixture path convention.** The plan claims fixtures live at `tests/fixtures/<case>/project/...` and tests live in `tests/test_validate_engine.py`. Confirm this matches the existing convention. Is there an `__init__.py` requirement?

D. **`logic_pkg` SV check (R-7).** The plan says checking `<base>_pkg` against the SV keyword set is a "free no-op." Is that actually true for the proposed keyword set? Spot-check: any SV keyword that ends in `_pkg`? If not, mention it explicitly.

E. **Commit A independence.** Commit A adds `keywords.py` but doesn't wire it. Is there any way an unwired keyword module breaks `basedpyright --strict`? Stale imports, unused exports, etc.

F. **Documentation location.** Plan says docs go in "the appropriate `docs/` file" but defers. Is this acceptable, or should the plan name the file?

G. **AC-11 enum-value-keyword interaction.** The plan claims a fixture named `keyword_enum_value_for` *proves* the UPPER_CASE rule fires before the keyword rule. But `for` is lowercase. The UPPER_CASE rule will reject `for` for being lowercase, regardless of whether the keyword check ran. So the fixture proves the UPPER_CASE error wins **at the structural-defect level**, not at the keyword level specifically. Is this what the plan intended? Is there a cleaner way to test ordering?

## Output format

```
# Gauge Review — Planning Iteration 1

## Summary
(2–4 sentences: overall verdict and the 1–2 highest-impact issues, if any.)

## Specific risk audits
(For each A–G above: confirmed-correct / under-specified / wrong / out-of-scope.)

## Issues

### BLOCKING
- (cite section)

### WARNING

### NOTE

## Constitutional alignment
(One paragraph.)

## Spec coverage
(Confirm every FR has a plan element and every AC has a test, OR list gaps.)

VERDICT: APPROVE
```

OR

```
VERDICT: REVISE
```

The verdict line MUST appear exactly once at the end, on its own line. The Forge parses this string verbatim.

## Notes

- A first-iteration plan that gets APPROVE is rare but allowed. Do not invent issues.
- Do not contradict the Project Constitution.
- Surgical, citation-based feedback only.
