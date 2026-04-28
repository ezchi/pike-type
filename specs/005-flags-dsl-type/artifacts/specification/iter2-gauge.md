# Gauge Review — Iteration 2

## Findings

1. **BLOCKING** — SV `pack`/`unpack` is still contradictory. FR-13 says it operates on `BYTE_COUNT * 8` and accepts individual flags; also says this matches `Struct()`. It does not. Existing `Struct()` pack/unpack uses data-only `WIDTH`. Define exact SV signatures and whether this intentionally diverges from `Struct()`.

2. **BLOCKING** — The serialization contract claim is false. The overview says Flags follows `Struct()`, but FR-11 puts data in MSBs with LSB padding. Existing scalar/struct serialization puts narrow unsigned values in low bits. State this as an intentional Flags-specific layout, or change it.

3. **BLOCKING** — Name collision handling is not adequately resolved. `to_bytes`, `from_bytes`, `clone`, `class`, `logic`, etc. are valid snake_case names that would generate invalid code. Punting to a separate spec is insufficient when the generated code would be syntactically invalid.

4. **WARNING** — The 64-flag boundary is still untested. Fixtures cover 1, 3, 8, and 9 flags, but not 64.

5. **WARNING** — AC-4 claims round-trips work in all three backends, "verified by Python runtime tests." Python tests cannot verify C++ or SV behavior. Narrow the claim.

6. **WARNING** — Python `__init__` behavior is not specified. No constructor arguments or initial `_value` state.

7. **NOTE** — C++ `operator==` compares raw `value` which may include padding bits. Specify whether equality masks padding.

VERDICT: REVISE
