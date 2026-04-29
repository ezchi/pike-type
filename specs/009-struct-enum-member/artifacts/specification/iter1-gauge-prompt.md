# Gauge Review — Spec 009: Struct Accepts Enum as Member

You are a strict specification reviewer. Your job is to evaluate the following specification for completeness, clarity, testability, consistency, and feasibility.

## Context

This project (pike-type) is a Python DSL-to-code-generator for hardware-oriented types. It generates SystemVerilog, Python, and C++ code from a Python DSL.

The specification adds Enum type support as Struct members. Enum types (spec 008) are already fully implemented as standalone types across all backends. This spec extends Struct to accept Enum as a member type, following the same pattern established by spec 007 (Flags as Struct member).

## Project Constitution (excerpt — highest authority)

Key rules:
1. Single source of truth: types defined in Python DSL, all outputs derived from that.
2. Immutable boundaries: pipeline stages (Discovery → DSL → IR → Backends) with frozen handoff.
3. Deterministic output: byte-for-byte reproducible.
4. Correctness over convenience: strict type checking, explicit validation passes.
5. Template-first generation (where practical).
6. Packed types only: all SV types must be `typedef struct packed`.
7. Same-module constraint: no cross-module type references this milestone.
8. Python ≥ 3.12, frozen dataclasses for IR, mutable with `slots=True` for DSL.
9. Golden-file integration tests are the primary correctness mechanism.

## Specification to Review

Read the specification at: /Users/ezchi/Projects/pike-type/specs/009-struct-enum-member/spec.md

## Prior Art

The pattern being followed is spec 007 (Flags as Struct member). For reference, that spec is at: /Users/ezchi/Projects/pike-type/specs/007-struct-flags-member/spec.md

The Enum type itself was defined in spec 008: /Users/ezchi/Projects/pike-type/specs/008-enum-dsl-type/spec.md

## Current Code References

Key files that will need changes:
- DSL Struct: `src/piketype/dsl/struct.py` — `add_member()` type union
- Freeze: `src/piketype/dsl/freeze.py` — `_freeze_field_type()`, `_serialized_width_from_dsl()`, `_freeze_struct_field()` padding
- Validation: `src/piketype/validate/engine.py` — TypeRefIR target allowlist
- SV backend: `src/piketype/backends/sv/emitter.py` — `_is_sv_composite_ref()`, `_render_sv_helper_field_decl()`
- Python backend: `src/piketype/backends/py/emitter.py` — field coercer
- C++ backend: `src/piketype/backends/cpp/emitter.py` — pack/unpack allowlists, clone, `_is_enum_ref()`

## Review Checklist

1. Review for completeness — are all pipeline stages covered (DSL → Freeze → IR → Validation → Backends → Tests)?
2. Review for clarity — are requirements unambiguous? Can an implementer follow them without guesswork?
3. Review for testability — are acceptance criteria specific and verifiable?
4. Review for consistency — does the spec follow the patterns established by spec 007?
5. Review for feasibility — are the changes actually implementable given the current codebase?
6. Check alignment with the Project Constitution.
7. Check that no existing behavior is broken.
8. List issues with severity: BLOCKING / WARNING / NOTE
9. End with exactly: `VERDICT: APPROVE` or `VERDICT: REVISE`
