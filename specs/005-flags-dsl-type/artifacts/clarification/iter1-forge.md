# Clarification — Iteration 1

## Assessment

The specification went through 5 Forge-Gauge iterations during the specification stage, resolving all ambiguities:

1. **Bit layout** — MSB-first, explicitly different from Struct per-field layout (resolved iter 2-3)
2. **SV pack/unpack** — Data-only width matching Struct pattern (resolved iter 3)
3. **C++ from_bytes** — Instance method `void from_bytes(const std::vector<std::uint8_t>&)` (resolved iter 5)
4. **C++ operator==** — Custom masked comparison, not `= default` (resolved iter 4)
5. **Padding masking** — Literal inline hex values, not named constants (resolved iter 5)
6. **Validation layers** — Eager DSL checks + post-freeze IR checks, clearly delineated (resolved iter 4)
7. **Manifest** — `kind: "flags"` with `flag_count` and `flag_names` (resolved iter 5)
8. **Name collisions** — Minimal reserved API names + broader keyword check scoped out (resolved iter 3)
9. **Test coverage** — 1, 3, 8, 9, 33 flag fixtures + nonzero padding test (resolved iter 4-5)

## Open Questions

None. All design decisions are fully resolved.

## Verdict

No clarification needed. Specification is ready for planning.
