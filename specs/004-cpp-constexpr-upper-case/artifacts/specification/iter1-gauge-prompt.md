# Gauge Review — Specification 004: C++ constexpr UPPER_SNAKE_CASE Naming

You are a strict specification reviewer (the "Gauge"). Your job is to review the specification below for quality, completeness, and alignment with the project constitution.

## Project Constitution (excerpt of relevant rules)

- **UPPER_SNAKE_CASE** for module-level constants (Python coding standards).
- C++ headers use include guards, not `#pragma once`.
- Generated code must be deterministic and byte-for-byte reproducible.
- Golden-file integration tests are the primary correctness mechanism.
- All generated files carry a machine-readable header comment.
- `basedpyright` strict mode must pass with zero errors.

## Specification to Review

---

# Spec 004 — C++ constexpr UPPER_SNAKE_CASE Naming

## Overview

All `constexpr` variables in generated C++ output currently use `kCamelCase` naming (e.g., `kWidth`, `kByteCount`, `kMaxValue`). This feature renames every generated C++ `constexpr` to use `UPPER_SNAKE_CASE` naming (e.g., `WIDTH`, `BYTE_COUNT`, `MAX_VALUE`), aligning the generated code with the project's constitution which mandates `UPPER_SNAKE_CASE` for constants.

## User Stories

- **US-1:** As a C++ developer consuming typist-generated headers, I want all `constexpr` names to follow `UPPER_SNAKE_CASE` convention, so that the generated code is consistent with standard C++ constant naming practices and the project constitution.
- **US-2:** As a typist maintainer, I want the emitter code to produce `UPPER_SNAKE_CASE` constant names, so that golden tests reflect the canonical style and future regressions are caught.

## Functional Requirements

### FR-1: Scalar Alias Class Static Constants

All `static constexpr` members in generated scalar alias wrapper classes must use `UPPER_SNAKE_CASE`:

| Before            | After            |
|-------------------|------------------|
| `kWidth`          | `WIDTH`          |
| `kSigned`         | `SIGNED`         |
| `kByteCount`      | `BYTE_COUNT`     |
| `kMask`           | `MASK`           |
| `kMaxValue`       | `MAX_VALUE`      |
| `kMinValue`       | `MIN_VALUE`      |

All references to these names in method bodies (`to_bytes`, `from_bytes`, `validate_value`) within the same class must also be updated.

### FR-2: Struct Class Static Constants

All `static constexpr` members in generated struct wrapper classes must use `UPPER_SNAKE_CASE`:

| Before       | After        |
|--------------|--------------|
| `kWidth`     | `WIDTH`      |
| `kByteCount` | `BYTE_COUNT` |

All references in method bodies (`to_bytes`, `from_bytes`) within the same class must also be updated.

### FR-3: Inline Scalar Helper Local Constants

Local `constexpr` variables inside per-field `validate_<field>` helper functions must use `UPPER_SNAKE_CASE`:

| Before      | After      |
|-------------|------------|
| `kMaxValue` | `MAX_VALUE` |
| `kMinValue` | `MIN_VALUE` |

### FR-4: Runtime Header Constants

The `inline constexpr` in `typist_runtime.hpp` must use `UPPER_SNAKE_CASE`:

| Before            | After              |
|-------------------|--------------------|
| `kVerboseDefault` | `VERBOSE_DEFAULT`  |

### FR-5: Golden File Updates

All golden files under `tests/goldens/gen/` that contain C++ headers must be regenerated to reflect the new naming. The updated golden files must match `typist gen` output byte-for-byte.

## Non-Functional Requirements

- **NFR-1:** No behavioral change — serialization/deserialization logic, byte layouts, and values remain identical. Only symbol names change.
- **NFR-2:** Deterministic output — the rename must not introduce ordering or content non-determinism.
- **NFR-3:** All existing tests must pass after updating golden files.
- **NFR-4:** `basedpyright` strict mode must pass with zero errors on all modified Python files.

## Acceptance Criteria

- **AC-1:** The C++ emitter (`src/typist/backends/cpp/emitter.py`) produces `UPPER_SNAKE_CASE` for all `constexpr` names listed in FR-1, FR-2, and FR-3.
- **AC-2:** The runtime emitter (`src/typist/backends/runtime/emitter.py`) produces `VERBOSE_DEFAULT` instead of `kVerboseDefault`.
- **AC-3:** Running `typist gen` on every existing fixture produces output that matches the updated golden files byte-for-byte.
- **AC-4:** All integration, idempotency, and negative tests pass (`python -m pytest tests/`).
- **AC-5:** `basedpyright` reports zero errors.
- **AC-6:** No `kCamelCase`-style `constexpr` names remain in any golden `.hpp` file.
- **AC-7:** Module-level constants (e.g., `FOO`, `BAR`, `W`) that are already `UPPER_SNAKE_CASE` remain unchanged.

## Out of Scope

- Renaming anything in SystemVerilog or Python generated outputs.
- Changing C++ class names, method names, or variable names that are not `constexpr`.
- Introducing Jinja2 templates for the C++ backend (that is a separate initiative).
- Changing any IR node definitions or DSL semantics.

## Open Questions

None — the scope is well-defined and purely mechanical.

---

## Review Checklist

Please evaluate the specification against each of these criteria:

1. **Completeness**: Does the spec cover all affected constants? Are any `constexpr` names missing from the rename tables?
2. **Clarity**: Is each requirement unambiguous? Could an implementer follow this spec without asking questions?
3. **Testability**: Is every acceptance criterion measurable and verifiable?
4. **Consistency**: Is the spec internally consistent? Does it align with the project constitution?
5. **Feasibility**: Can this be implemented as described?

For each issue found, assign a severity:
- **BLOCKING**: Must be fixed before implementation can begin
- **WARNING**: Should be fixed but won't prevent implementation
- **NOTE**: Suggestion for improvement, not required

End your review with exactly one of:
- `VERDICT: APPROVE`
- `VERDICT: REVISE`
