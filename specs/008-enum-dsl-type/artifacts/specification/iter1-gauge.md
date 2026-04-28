# Gauge Review — Specification Iteration 1

**BLOCKING**: Python/C++ enum naming is wrong. The draft uses the original DSL name (`state_t`) for the generated `IntEnum` / `enum class`, but v1 requires `state_t -> state_enum_t`; only the wrapper is `state_ct`. Fix FR-20, FR-22, and all wrapper references.

**BLOCKING**: Python/C++ wrappers omit `to_slv()` and `from_slv()`. v1 requires those APIs, and enum `from_slv()` must reject unknown numeric values. The draft only specifies `to_bytes()` / `from_bytes()`.

**BLOCKING**: Manifest serialization drops numeric enum values. `value_names` is insufficient because explicit/sparse enum values are allowed. Emit ordered entries with at least `name` and `resolved_value`.

**BLOCKING**: SV enum literal collision validation is missing. SystemVerilog enum literals live in package scope, so two enums with `IDLE`, or a const named `IDLE`, can break generation. FR-15 only checks uniqueness within one enum; FR-16 only reserves helper identifiers.

**BLOCKING**: Enum width validation is incomplete. Validation must verify `resolved_width` and `width_expr` match the minimum width for the maximum resolved value, and that every value fits. Checking only `resolved_width > 0` and `<= 64` is not enough.

**WARNING**: Test coverage is under-specified. Add explicit tests for auto-fill gaps (`0, 2, None, None -> 0, 2, 1, 3`), 1-bit SV enum emission, missing `_t`, width > 64, wrong byte count, unknown `from_bytes()` / `from_slv()` values, and 64-bit enum values.

**WARNING**: `EnumType.width` is undefined for an empty enum. Existing `Flags().width` returns `0`; specify whether `Enum().width` returns `0` or raises before validation rejects the empty enum.

**WARNING**: Byte order authority is inconsistent. The draft's big-endian/MSB-padding matches existing emitters, but v1 still says canonical little-endian bytes. Resolve or explicitly override that conflict.

**NOTE**: C++ underlying type selection by width is correct, but the spec should require unsigned-safe literal spelling/casts for enum values above `INT64_MAX`.

**NOTE**: Enum-as-struct-member is correctly out of scope, but add an explicit rejection requirement/test for `Struct().add_member(..., EnumType)` until that milestone exists.

VERDICT: REVISE
