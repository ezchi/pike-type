# Gauge Review — Iteration 4

## Findings

- **WARNING** — C++ `from_bytes()` has no signature specified. Existing C++ wrappers use `void from_bytes(const std::vector<std::uint8_t>&)`. Spec leaves room for incompatibility.

- **WARNING** — Padding-mask wording contradicts itself: says masking is inline and not named, but the `operator==` example emits `PADDING_MASK` and uses `alignment_bits` as if the IR field exists in generated C++. Specify literal substitution.

- **WARNING** — Manifest output is unspecified. Current manifest only handles scalar_alias and struct kinds. Flags need `kind: "flags"` in the manifest.

- **WARNING** — Tests do not require nonzero-padding deserialization cases. Round-tripping canonical bytes won't catch a broken implementation that fails to mask padding.

VERDICT: REVISE
