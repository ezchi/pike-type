# Gauge Review — Spec 009 Iteration 1

## BLOCKING
None.

## WARNING
- Spec 009 omits the dependency-ordering note that spec 007 had. Enum definitions must be emitted before structs that reference them in SV/Python/C++; current output relies on source-line ordering, not topological sorting. Add that assumption or require topological sorting/tests.
- Test requirements are too happy-path focused. AC-5 and AC-22 require anonymous enum rejection and cross-module enum rejection, but FR-14 only lists fixture/golden/runtime positives. Add explicit negative tests there.

## NOTE
- The spec is feasible against the current code. The named touch points are correct: DSL union, freeze field handling/padding/serialized width, validation allowlist, SV helper allowlists, Python coercer, and C++ pack/unpack/clone.
- Add one concrete byte vector for a 2-bit enum member, e.g. value `2` serializes as `0x02`, to remove any ambiguity about padding side.

VERDICT: APPROVE
