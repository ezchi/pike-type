# Gauge Review — Plan Iteration 1

## Findings

- **BLOCKING** — Plan does not mention `FlagsType.width` property. FR-3/AC-1 require `width == len(flags)`.
- **BLOCKING** — SV test helper description says "follow Struct pattern" but Struct serializes per-field with byte-aligned fields. Flags need whole-struct bit-level serialization.
- **WARNING** — `FlagsIR.alignment_bits` default of 0 weakens the IR invariant. Require constructor argument.
- **WARNING** — Plan adds large ad hoc string-building emitters, conflicting with constitution's template-first rule.
- **WARNING** — No explicit `basedpyright` strict mode verification step.
- **NOTE** — IR-before-DSL ordering is acceptable.

VERDICT: REVISE
