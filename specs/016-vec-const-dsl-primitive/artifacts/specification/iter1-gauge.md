# Gauge Review — Specification, Iteration 1

**Reviewer:** gemini (gemini-3.1-pro-preview via gemini CLI 0.40.1)
**Spec under review:** `specs/016-vec-const-dsl-primitive/spec.md`

### Issues

**BLOCKING**, citing **Principle 1** and **Q-4**. The spec fails to define behavior for C++ and Python backends, leaving it as an Open Question. This violates the "Single source of truth" principle; if `VecConst` is SV-only, it must be explicitly required as a no-op/omission for other backends in the FRs, or fully specified for all backends to maintain cross-language parity.

**WARNING**, citing **FR-7**. The requirement for the validation message should explicitly state the bound formula (`2**width - 1`) to ensure implementers produce consistent error text.

**NOTE**, citing **FR-5**. A 64-bit width cap is consistent with `Const` but significantly more restrictive than native SystemVerilog `logic` vectors. While acceptable for v1, it may become a bottleneck for protocol constants (e.g., 128-bit IPv6 addresses or hashes).

### Strengths

*   **Precision:** FR-9/10/11 provide exceptionally clear rendering rules (padding, casing, base letters) that guarantee idiomatic and deterministic SystemVerilog output.
*   **Constitutional Safety:** The FR-14 amendment is well-scoped, preserving the legacy behavior and validation constraints of `Const` while providing a clean legal path for `VecConst`.
*   **Testability:** Acceptance criteria are comprehensive, covering cross-module imports, expression evaluation, and negative validation cases.

### Verdict

VERDICT: REVISE
