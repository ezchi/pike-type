# Gauge Review — Planning, Iteration 1

**Reviewer:** gemini (gemini-3.1-pro-preview via gemini CLI 0.40.1; multiple 429 + ECONNRESET retries before success)
**Plan under review:** `specs/016-vec-const-dsl-primitive/plan.md`

The implementation plan for **016-vec-const-dsl-primitive** is well-structured and follows the Project Constitution's pipeline principles, but it contains a significant contradiction regarding cross-module references.

### Issues

**BLOCKING (FR-13 / AC-11)**: The plan states `VecConst` is not a `ConstOperand` (Risk R-3), yet FR-13 explicitly requires that it "MAY be referenced from module B's DSL" and produce a corresponding SV import. If `VecConst` is not a `ConstOperand`, it cannot be used in expressions or as a value for other `VecConst`/`Const` nodes, making it a "leaf-only" primitive that violates the parity and reuse goals implied by FR-13 and US-1.

**WARNING (Component 5 / FR-11)**: The plan's padding logic `(width + 3) // 4` for hex is mathematically sound for digit count, but the implementation should explicitly confirm that `_render_sv_vec_literal` uses this calculated length in its string formatting to ensure literals like `12'h000` are correctly zero-padded to the full width.

**NOTE (R-2 / Phase D)**: Regenerating 10 manifest goldens is the correct choice for schema stability (Option A), but be aware this will inflate the PR diff with mechanical changes to unrelated fixtures.

### Strengths

- **Validation Rigor**: Explicitly implementing the FR-7 formula-substring contract (`2**N - 1`) in the freeze layer ensures high-quality error messages.
- **Architectural Integrity**: The addition of `vec_constants` to `ModuleIR` with a default value is a surgical, backwards-compatible change that honors Principle 2.
- **SV Fidelity**: The handling of non-multiple-of-4 widths for hex padding (AC-9, AC-10) demonstrates a strong understanding of SystemVerilog literal requirements.

### Verdict

VERDICT: REVISE
