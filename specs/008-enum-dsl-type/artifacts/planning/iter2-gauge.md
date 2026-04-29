# Gauge Review — Planning Iteration 2

**BLOCKING**: FR-32 requires explicit `0, 2` followed by two auto-fills yielding `0, 2, 3, 4`. The `cmd_t` fixture only tests `0` then auto-fills `1, 2`, which also passes the old wrong "smallest unused" behavior.

**BLOCKING**: Freeze description still uses `ceil(log2(max_val + 1))`. Must use `max(1, max_value.bit_length())` consistently throughout the plan.

**WARNING**: C++ backend section doesn't mention `_cpp_unsigned_literal()` for enum initializer values. Needed for the `2**63` fixture.

VERDICT: REVISE
