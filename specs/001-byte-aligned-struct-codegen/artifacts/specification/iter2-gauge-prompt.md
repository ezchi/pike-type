# Gauge Review — Specification Iteration 2

You are a strict technical reviewer (the "Gauge") for a code generation tool called **typist**. Your job is to review the specification below for completeness, clarity, testability, consistency, and feasibility.

## Context

**Project:** typist — a Python tool that generates SystemVerilog, C++, and Python code from a Python DSL for hardware-oriented types.

**Project Constitution (highest authority):**
1. Single source of truth: types defined once in Python DSL, all outputs derived from it.
2. Immutable boundaries: Pipeline stages (Discovery -> DSL -> IR -> Backends) with frozen handoff.
3. Deterministic output: byte-for-byte reproducible.
4. Correctness over convenience: strict type checking, explicit validation, golden-file tests.
5. Template-first generation: Jinja2 templates preferred for structured output.
6. Generated runtime, not handwritten.

**Key constraints:**
- Python >= 3.12, basedpyright strict mode
- No UVM dependency
- Packed types only
- No cross-module type references (current milestone)
- Constants restricted to 32/64 bits
- Only Jinja2 at runtime, no other external dependencies

**Original requirements document:**
```
** Rules and example for Generated Files
- all the types must have width and byte count defined. for example, `localparam int LP_FOO_WIDTH = 17; localparam int LP_FOO_BYTE_COUNT = 3; typedef logic [LP_FOO_WIDTH-1:0] foo_t;`
- all the types must define pack_<type_name> and unpack_<type_name> function. pack_* function takes the type as input and return the logic vector with the width of the type. unpack_* take logic vector as input and return the variable of the type.
- for complex types, such as, struct:
  - the `Struct().add_member()` python DSL function should pad the member to byte aligned, for example, `foo_t = Struct().add_member("bar", Bit(13))`, it should generate the SystemVerilog struct as `typedef struct packed { logic [12:0] bar; logic [2:0] bar_pad; } foo_t`.
  - the width should be the total bits of the struct without any padding bits.
  - the byte_count should be the number of bytes of this type with all the padding bits.
  - the pack_* function should output the logic vector without any padding bits, the width of the output the type's width
  - the unpack_* function should take the logic vector with width of type width and fill all the padding bits with `0`
  - for verification package, the to_bytes() class member function converts the type to byte array with size of the byte count of the type. the byte array includes all the paddings
  - for verification package, the from_bytes() class member function takes byte array and convert the the expect type

  For c++ the scalar type which width is <= 64-bit, it should be mapped to minimum width of native c++ type, uint8_t, uint16_t, uint32_t, uint64_t and signed types.

  for example, a `logic [36:0] foo;` field should be defined as `std::uint64_t foo;`, foo = 37'h12_3456_789A. to_bytes() should return {0x12, 0x34, 0x56, 0x78, 0x9A}. SystemVerilog verification class's to_bytes() should return same order byte array.
```

## Prior Review Issues (Iteration 1)

The following BLOCKING and WARNING issues were raised in iteration 1. This iteration should resolve all of them:

**BLOCKING (all must be resolved):**
1. Nested struct sizing was contradictory — needed explicit definitions for data width, storage width, field byte count, padding bits.
2. Generated name rules were underspecified — needed to clarify `_t` suffix stripping.
3. Signed struct fields were both included and excluded — needed consistent handling.
4. Padding field name collisions were not handled — needed validation.
5. `from_bytes()` padding behavior was undefined — needed to specify ignore/zero behavior.
6. Open questions remained — needed resolution.

**WARNING:**
1. Padding should be computed at freeze time, not in `add_member()`.
2. Scalar SV typedef should preserve `bit` vs `logic` and `signed`.
3. Byte layout algorithm was not concrete enough.
4. Acceptance criteria needed exact expected byte vectors.
5. NFR-2 template language needed to be clearer.

## Specification to Review

Read the file at: /Users/ezchi/Projects/typist/specs/001-byte-aligned-struct-codegen/spec.md

## Review Instructions

1. Verify all iteration 1 BLOCKING issues are resolved.
2. Verify all iteration 1 WARNING issues are addressed.
3. Review for **completeness**: Are all requirements from the original document addressed?
4. Review for **clarity**: Is each requirement unambiguous?
5. Review for **testability**: Can each functional requirement be verified with a concrete test?
6. Review for **consistency**: Do requirements contradict each other or the Project Constitution?
7. Review for **feasibility**: Given the current codebase, are all requirements implementable?

List issues with severity:
- **BLOCKING**: Must be fixed before proceeding.
- **WARNING**: Should be addressed.
- **NOTE**: Minor suggestion.

End your review with exactly one of:
```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
