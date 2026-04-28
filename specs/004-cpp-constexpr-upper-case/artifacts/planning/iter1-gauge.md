# Gauge Review — Planning Iteration 1

## Issues

- **BLOCKING**: Verification is too weak. The plan only checks remaining `kCamelCase constexpr`, but the spec also requires all references to be renamed and bans lowercase generated `constexpr` names like `mask`. Add an explicit grep over generated `.hpp` files for old identifiers anywhere, not just declarations: `kWidth`, `kSigned`, `kByteCount`, `kMask`, `kMaxValue`, `kMinValue`, `kVerboseDefault`, and `constexpr ... mask`.

- **WARNING**: Golden regeneration is underspecified. The plan says to run `typist gen` against each fixture, but fixtures include negative cases without goldens and `namespace_override` requires `--namespace foo::bar`. The plan needs exact regeneration commands or a script.

- **NOTE**: Source coverage is otherwise aligned with the listed emitter sites.

VERDICT: REVISE
