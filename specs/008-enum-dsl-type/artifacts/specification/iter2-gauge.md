# Gauge Review — Specification Iteration 2

**BLOCKING**: `operator== ... = default;` requires C++20, but the constitution targets C++17. Use a manual equality operator or explicitly change the target standard.

**BLOCKING**: Enum literals are not checked against generated SV identifiers. An enumerator named `LP_STATE_WIDTH` passes UPPER_CASE validation but collides with the generated localparam. Add validation and a negative test.

**WARNING**: No negative test for `resolved_width > 64`. Add a test with value `2**64` or larger.

**WARNING**: Python/C++ `from_bytes` padding behavior is underspecified. SV explicitly masks padding bits, but Python/C++ only say reject unknown values. State whether padding bits are masked before enum validation.

**NOTE**: All previous iteration 1 issues (naming, manifest values, FR-17 literal collision, width-fit validation, empty-width behavior, byte-order documentation, Python/C++ `to_slv()` scoping) are addressed.

VERDICT: REVISE
