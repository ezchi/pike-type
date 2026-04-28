# Gauge Review — Iteration 1

**Provider:** codex (gpt-5.5)

## Issues

- **BLOCKING** — Freeze alignment is incomplete. FR-2 only covers `_freeze_field_type()`, but `Struct.multiple_of()` uses `_serialized_width_from_dsl()` and that currently only counts scalar and struct members. A Flags member would be ignored when computing trailing alignment. Add a requirement and AC for Flags members inside `.multiple_of()` structs.

- **BLOCKING** — SV test/helper package behavior is missing. FR-4 covers typedef, `pack_*`, and `unpack_*`, but generated SV also includes helper classes. Current struct helper logic treats non-struct type refs as scalar-like fields, which is wrong for `FlagsIR` serialization because flags occupy MSB positions with alignment padding. Add requirements for `*_ct.to_bytes()`, `from_bytes()`, `copy()`, `compare()`, and likely helper field representation.

- **BLOCKING** — Python and C++ width/byte-count helpers are under-specified. The spec mentions Python `_type_byte_count()` but not `_resolved_type_width()`. Both Python and C++ currently treat all non-scalar types as struct-like and will fail on `FlagsIR.fields` because `FlagFieldIR` has no `type_ir`. Add explicit `FlagsIR` handling requirements for width and byte count in both backends.

- **BLOCKING** — C++ FR-6 says `kByteCount`, but generated C++ uses `BYTE_COUNT`. This conflicts with existing patterns and Spec 004 uppercase constexpr naming. Use `BYTE_COUNT`.

- **WARNING** — FR-7 says round-trip tests must cover "all generated backends," but the repo has executable Python runtime tests and golden text checks for SV/C++. Specify whether C++ must be compiled and SV simulated, or whether golden assertions are enough.

- **WARNING** — The dependency-ordering statement says "existing dependency-first ordering," but current type output is source-line sorted, not topological. The common case still works because Python requires the flags object before use, but the spec should not claim a nonexistent ordering mechanism.

- **NOTE** — AC-15's "all 139 tests" is brittle. Say "the existing test suite" instead of freezing a count into the spec.

## Dimension Assessment

Completeness: fails due to missing freeze alignment, SV helper generation, and backend helper width paths.

Clarity: mostly clear, but C++ `kByteCount` is wrong and backend testing expectations are ambiguous.

Testability: incomplete; add ACs for `.multiple_of()`, generated `WIDTH`/`BYTE_COUNT`, Python coercion rejecting `None`, and SV helper serialization.

Consistency: TypeRefIR reuse aligns with the architecture. The C++ naming and dependency-ordering claims do not.

Feasibility: feasible after revision. No IR blocker.

VERDICT: REVISE
