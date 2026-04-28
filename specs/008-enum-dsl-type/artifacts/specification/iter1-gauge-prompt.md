# Gauge Review — Specification Iteration 1

## Role

You are the Gauge — a strict, independent reviewer. Your job is to evaluate the specification below for completeness, clarity, testability, consistency, and feasibility.

## Context

- **Project**: piketype — a Python-based code generation tool for FPGA-oriented type definitions.
- **Spec**: `specs/008-enum-dsl-type/spec.md` — Implementing the `Enum()` DSL type across all languages (SystemVerilog, Python, C++).
- **Constitution**: `.steel/constitution.md` — the project's governing principles and coding standards.
- **V1 Product Spec**: `docs/v1-product-spec.md` — the authoritative product specification (Enum requirements at lines 298–323, delivery order at lines 648–667).
- **Existing Patterns**: The codebase already supports `Const()`, `Bit()`/`Logic()`, `Struct()`, `Flags()` across all three backends. The spec should follow established patterns.

## Files to Read

1. Read `specs/008-enum-dsl-type/spec.md` — the specification to review.
2. Read `.steel/constitution.md` — the project constitution (highest authority).
3. Read `docs/v1-product-spec.md` — the v1 product spec for Enum requirements.
4. Read `docs/ir-schema.md` — the IR schema for EnumIR/EnumValueIR definitions.
5. Skim existing implementations for pattern consistency:
   - `src/piketype/dsl/flags.py` — reference DSL type
   - `src/piketype/ir/nodes.py` — existing IR nodes
   - `src/piketype/dsl/freeze.py` — freeze logic
   - `src/piketype/validate/engine.py` — validation
   - `src/piketype/backends/sv/emitter.py` — SV backend
   - `src/piketype/backends/py/emitter.py` — Python backend
   - `src/piketype/backends/cpp/emitter.py` — C++ backend
   - `src/piketype/manifest/write_json.py` — manifest

## Review Checklist

1. **Completeness**: Does the spec cover all requirements from the v1 product spec for Enum? Are any DSL features, validation rules, backend outputs, or test cases missing?
2. **Clarity**: Are the functional requirements unambiguous? Could an implementer work from them without guessing?
3. **Testability**: Can every acceptance criterion be verified with a concrete test? Are edge cases covered?
4. **Consistency**: Does the spec follow established patterns from the existing codebase (Flags, Struct, Scalar)? Are naming conventions correct?
5. **Feasibility**: Are there any requirements that conflict with the existing architecture or would require disproportionate effort?
6. **Constitution Alignment**: Does the spec comply with all governing principles and coding standards in the constitution?

## Specific Points to Verify

- Does FR-6 (auto-fill numbering) correctly handle gaps in explicit values? (e.g., explicit 0, 2 → auto-fill should give 1, then 3)
- Does the SV backend correctly handle 1-bit enums?
- Is the Python `IntEnum` naming correct per the v1 spec? (The spec says `state_t` → `state_enum_t` for the enum type, but the proposed spec uses the original `_t` name for the IntEnum. Which is correct?)
- Is the C++ `enum class` underlying type selection correct?
- Are byte serialization semantics (big-endian, zero-padded MSB) consistent with existing types?
- Does the spec correctly exclude enum-as-struct-member (deferred to future milestone)?
- FR-17 limits enum width to 64 bits — is this consistent with the spec's non-negative-only constraint?

## Output Format

List each issue with a severity level:
- **BLOCKING**: Must be fixed before the spec can be approved. Correctness or completeness issue.
- **WARNING**: Should be fixed. Clarity, consistency, or testability concern.
- **NOTE**: Minor suggestion. Nice to have but not required.

End your review with exactly one of:
```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
