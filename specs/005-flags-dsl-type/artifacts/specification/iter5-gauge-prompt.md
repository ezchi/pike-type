# Gauge Review — Spec 005: Flags() DSL Type (Iteration 5 — Final)

You are a technical reviewer (the "Gauge") for a hardware-type code generation tool called **typist**. Your job is to critically review the specification below for completeness, clarity, testability, consistency, and feasibility.

## Context

**Project:** typist — a Python DSL that defines hardware-oriented types and generates SystemVerilog, C++, and Python code from a single definition.

**Constitution (key principles):**
1. Single source of truth — types defined once in Python DSL.
2. Immutable boundaries — pipeline has 4 stages (Discovery -> DSL -> IR -> Backends) with frozen handoffs.
3. Deterministic output — byte-for-byte reproducible.
4. Correctness over convenience — strict validation, golden-file testing.
5. Template-first generation — backends use Jinja2 templates where practical.
6. Generated runtime, not handwritten.

**Existing patterns:** SV pack/unpack uses data-only LP_*_WIDTH. C++ from_bytes is `void from_bytes(const std::vector<std::uint8_t>&)` (instance method). Python from_bytes is `@classmethod`. C++ operator== uses `= default` for existing types (Flags diverges intentionally — see FR-17). C++ constexpr names use UPPER_SNAKE_CASE. Manifest uses `kind` field to distinguish type kinds.

## Iteration 4 Issues (addressed in iteration 5)

1. **WARNING (resolved):** C++ from_bytes signature → FR-17 now shows exact C++ signatures: `void from_bytes(const std::vector<std::uint8_t>& bytes)` with size validation and `std::invalid_argument` on mismatch.
2. **WARNING (resolved):** Padding mask contradiction → FR-17 now uses literal hex values (e.g., `0xE0U`) in all code examples. No symbolic names like `PADDING_MASK` or `alignment_bits` in generated code.
3. **WARNING (resolved):** Manifest → New FR-10a specifies `kind: "flags"` with `flag_count` and `flag_names` fields. AC-15 requires manifest coverage.
4. **WARNING (resolved):** Nonzero padding deserialization → FR-24 item 6 adds an explicit test with nonzero padding bits. AC-14 verifies padding masking behavior.

## Specification to Review

Read the file at: /Users/ezchi/Projects/typist/specs/005-flags-dsl-type/spec.md

## Review Instructions

1. Read the specification thoroughly.
2. For each issue found, classify severity as BLOCKING / WARNING / NOTE.
3. Verify iteration 4 issues are resolved.
4. End with exactly: `VERDICT: APPROVE` or `VERDICT: REVISE`
