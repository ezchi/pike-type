# Gauge Review — Spec 005: Flags() DSL Type (Iteration 1)

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

**Technology:** Python >= 3.12, Jinja2, basedpyright strict mode, unittest golden-file tests, GPL-3.0.

**Coding standards:** Frozen dataclasses for IR nodes, mutable dataclasses with slots for DSL objects, snake_case, PascalCase for classes, `_t` suffix for type names, `_ct` suffix for wrapper classes.

## Specification to Review

Read the file at: /Users/ezchi/Projects/typist/specs/005-flags-dsl-type/spec.md

## Review Instructions

1. Read the specification thoroughly.
2. For each issue found, classify severity as:
   - **BLOCKING** — Must fix before implementation (missing requirements, contradictions, untestable criteria).
   - **WARNING** — Should fix (ambiguity, edge case gaps, inconsistency with constitution).
   - **NOTE** — Nice to have (style, minor clarity improvements).

3. Check specifically for:
   - Completeness: Are all pipeline stages covered (DSL, IR, freeze, validation, 3 backends, tests)?
   - Clarity: Can an implementer produce the code unambiguously from the spec?
   - Testability: Are acceptance criteria measurable and verifiable?
   - Consistency: Does the spec align with the project constitution and existing patterns (Struct, ScalarAlias)?
   - Feasibility: Are there any technical blockers or unreasonable assumptions?
   - Edge cases: 0 flags, 1 flag, 8 flags, 64 flags, >64 flags.
   - C++ mask values: Are the bit positions correct for big-endian MSB-first ordering?
   - Serialization: Is the to_bytes/from_bytes contract clear for all three backends?

4. End your review with exactly one of:
   - `VERDICT: APPROVE`
   - `VERDICT: REVISE`
