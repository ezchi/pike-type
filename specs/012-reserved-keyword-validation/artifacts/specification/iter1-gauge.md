Ripgrep is not available. Falling back to GrepTool.
MCP issues detected. Run /mcp list for status.# Gauge Review — Specification Iteration 1

## Summary
The specification is a high-quality proposal that correctly identifies the risk of silent keyword collisions and aligns with the Project Constitution's "correctness-over-convenience" principle. The primary areas for improvement are the over-restrictive checking of type "base forms" that are never emitted raw, and the need to resolve design forks regarding determinism and case sensitivity to ensure a consistent implementation.

## Issues

### BLOCKING
- None.

### WARNING
- **FR-1.1 & AC-2 (Type base names):** The requirement to check the "base form" of types (e.g., `class` for `class_t`) against keyword sets is over-restrictive. Analysis of the current SystemVerilog and C++ backends (and `_macros.j2` templates) shows that type base forms are always transformed (e.g., `pack_class`, `LP_CLASS_WIDTH`, `class_ct`) before emission and are never used as standalone identifiers. Rejecting common type names like `type_t` or `int_t` simply because their base forms are keywords provides no correctness benefit while imposing a significant naming burden on users.
- **FR-4 & AC-3 (Case Sensitivity):** The spec contains a contradiction between the "exact-case" rule in FR-4 and the "case-insensitive" suggestion in AC-3. Per Constitution Principle 4 (Correctness over convenience), the validator should only reject what is actually illegal. Since SV, C++, and Python are case-sensitive regarding keywords, `WHILE` is a perfectly valid and common identifier in hardware contexts. The spec should commit to exact-case matching only.

### NOTE
- **FR-2 (Python Keywords):** Snapshotting `keyword.kwlist` in the proposed `keywords.py` module is the correct path for Principle 3 (Determinism). A live lookup at validation time would violate this principle if the environment's Python version or patch level changes.
- **FR-2 (SV Version):** Including IEEE 1800-2023 keywords (e.g., `nettype`, `interconnect`) in the SV set is recommended for forward compatibility, even if the current project target is 1800-2017.

## Constitutional alignment
The specification strengthens Principle 4 (Correctness over convenience) by preventing downstream compilation failures. It also respects Principle 3 (Deterministic output) by requiring data-driven, frozen keyword sets and deterministic error reporting. The proposed integration into the `validate/` sub-package preserves the "Immutable boundaries" of the pipeline (Principle 2).

## Open questions assessment
1. **SV standard revision:** **KEEP**. 1800-2023 is preferred for future-proofing.
2. **C++ contextual identifiers:** **KEEP**. `import` and `module` are high-risk in C++20; `final`/`override` are low-risk.
3. **Python keyword source:** **DECIDE**. Use a static snapshot in `keywords.py` to ensure byte-identical results across different execution environments (Principle 3).
4. **Case sensitivity:** **DECIDE**. Stick to exact-case (FR-4). Do not relax this for enums; it avoids unnecessary restrictions on valid identifiers.
5. **Error reporting strategy:** **DECIDE**. First-fail. Maintain consistency with all existing validators in `engine.py`.
6. **CLI escape hatch:** **DECIDE**. Defer. Keep the validation strict for the initial implementation to ensure correctness.
7. **Base form check for types:** **DECIDE**. Remove the base-form check for types in FR-1.1; check only the full `_t` name against keywords.
8. **Constant base names:** **DECIDE**. No. The raw constant name is already checked, and macro forms like `LP_<NAME>_WIDTH` are safe.

VERDICT: REVISE
