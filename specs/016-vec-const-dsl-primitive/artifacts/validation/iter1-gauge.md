# Gauge Verification Report — Validation, Iteration 1

**Reviewer:** gemini (gemini-3.1-pro-preview via gemini CLI 0.40.1)

### Issues

- **BLOCKING**: `src/piketype/validate/engine.py` is missing name validation for `VecConst`.
    - `_validate_reserved_keywords`: Does not iterate over `module.vec_constants`, allowing collisions with SystemVerilog/C++/Python keywords (e.g., `while = VecConst(...)`).
    - `validate_repo`: Does not check `vec_constants` for duplicate names within the module or collisions with types/constants.
    - `_validate_generated_identifier_collision`: Does not check `vec_constants` against reserved names like `LP_{NAME}_WIDTH` or `pack_{name}`.
    - `_validate_enum_literal_collision`: Does not check for collisions between `VecConst` names and enum literals.
    - *Rationale:* This violates Constitution Principle 4 ("Correctness over convenience") and creates a significant safety gap compared to the legacy `Const` primitive.
- **NOTE**: `tests/test_vec_const_validation.py:test_negative_value_rejected` verifies negative rejection but does not explicitly assert the "three-substring contract" (offending value, width N, formula `2**N - 1`) for the negative case, unlike the overflow test. The implementation in `freeze.py:456` correctly includes all three, so this is purely a minor test-coverage gap.

### Verdict

VERDICT: REVISE
