# Gauge Review — Specification Iteration 1

You are a strict technical reviewer (the "Gauge") for a code generation tool called **typist**. Your job is to review the specification below for completeness, clarity, testability, consistency, and feasibility.

## Context

**Project:** typist — a Python tool that generates SystemVerilog, C++, and Python code from a Python DSL for hardware-oriented types.

**Project Constitution (excerpt — highest authority):**
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

  Example of the struct type (this is only the example)
  Python defintion
    from typist.dsl import Logic, Struct

    foo_t = Logic(13)

    bar_t = Struct().add_member("flag_a", Logic(1)).add_member("field_1", foo_t).add_member("status", Logic(4)).add_member("flag_b", Logic(1))

  Generated SV
    package some_pkg;

       localparam int LP_FOO_WIDTH = 13;
       localparam int LP_FOO_BYTE_COUNT = 2;

       typedef logic [LP_FOO_WIDTH-1:0] foo_t;

       function logic[LP_FOO_WIDTH-1:0] pack_foo(foo_t a);
           return a;
       endfunction // pack_foo

       function foo_t unpack_foo(logic[LP_FOO_WIDTH-1:0] a);
           return a;
       endfunction // unpack_foo

       localparam int LP_BAR_WIDTH = 19;   // 1-bit flag_a, 13-bit field_1, 4-bit status, 1-bit flag_b
       localparam int LP_BAR_BYTE_COUNT = 5; // 1-byte flag_a, 2-byte field_1, 1-byte status, 1-byte flag_b

       typedef struct packed {
          logic [6:0] flag_a_padding;
          logic flag_a;

          logic [2:0] field_1_padding;
           foo_t field_1;

          logic [3:0] status_padding;
          logic [3:0] status;

          logic [6:0] flag_b_padding;
          logic       flag_b;
       } bar_t;

       function logic[LP_BAR_WIDTH-1:0] pack_bar(bar_t a);
           return {a.flag_a, pack_foo(a.field_1), a.status, a.flag_b};
       endfunction // pack_bar

       function bar_t unpack_bar(logic[LP_BAR_WIDTH-1:0] a);
           bar_t result = '0;
           result.flag_b = a[0];
           result.status = a[4:1];
           result.field_1 = unpack_foo(a[17:5]);
           result.flag_a = a[18];
           return result;
       endfunction // unpack_bar

    endpackage

  For c++ the scalar type which width is <= 64-bit, it should be mapped to minimum width of native c++ type, uint8_t, uint16_t, uint32_t, uint64_t and signed types.

  for example, a `logic [36:0] foo;` field should be defined as `std::uint64_t foo;`, foo = 37'h12_3456_789A. to_bytes() should return {0x12, 0x34, 0x56, 0x78, 0x9A}. SystemVerilog verification class's to_bytes() should return same order byte array.
```

**Current codebase state (what already exists):**
- DSL: `Struct().add_member()` exists but does NOT compute padding. `sw=` parameter is explicitly rejected.
- IR: `StructFieldIR` has no `padding_bits` field. `StructIR` has no stored width/byte_count.
- SV backend: Emits `typedef struct packed` without padding. Verification helper classes have WIDTH, BYTE_COUNT, to_bytes(), from_bytes(). No standalone pack/unpack in synthesizable package. No LP_ localparams in synthesizable package.
- C++ backend: Emits classes with kWidth, kByteCount, to_bytes(), from_bytes(). Uses helper pack/unpack methods.
- Python backend: Emits dataclasses with WIDTH, BYTE_COUNT, to_bytes(), from_bytes().
- Templates: All template directories contain only `.gitkeep` — emitters use direct Python code generation currently.
- Tests: Golden-file integration tests exist for struct_sv_basic, nested_struct_sv_basic, scalar_sv_basic.

## Specification to Review

Read the file at: /Users/ezchi/Projects/typist/specs/001-byte-aligned-struct-codegen/spec.md

## Review Instructions

1. Review for **completeness**: Are all requirements from the original document addressed? Are there gaps?
2. Review for **clarity**: Is each requirement unambiguous? Could two developers interpret any requirement differently?
3. Review for **testability**: Can each functional requirement be verified with a concrete test? Are acceptance criteria measurable?
4. Review for **consistency**: Do requirements contradict each other or the Project Constitution?
5. Review for **feasibility**: Given the current codebase, are all requirements implementable within the stated constraints?
6. Check **alignment with the Project Constitution**: Does the spec respect all governing principles and constraints?

List issues with severity:
- **BLOCKING**: Must be fixed before proceeding. Spec is incorrect, contradictory, or missing critical requirements.
- **WARNING**: Should be addressed. Ambiguity, potential edge case, or deviation from best practice.
- **NOTE**: Minor suggestion or observation. Not required to fix.

End your review with exactly one of:
```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
