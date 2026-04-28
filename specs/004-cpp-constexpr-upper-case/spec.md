# Spec 004 — C++ constexpr UPPER_SNAKE_CASE Naming

## Overview

All `constexpr` variables in generated C++ output currently use mixed naming: some use `kCamelCase` (e.g., `kWidth`, `kByteCount`, `kMaxValue`) and some use plain lowercase (e.g., `mask`). This feature renames every non-user-defined generated C++ `constexpr` to use `UPPER_SNAKE_CASE` (e.g., `WIDTH`, `BYTE_COUNT`, `MAX_VALUE`, `MASK`), establishing a consistent naming convention for generated C++ constants.

**Rationale:** This is a project style decision for generated C++ output. The project constitution mandates `UPPER_SNAKE_CASE` for Python module-level constants; this feature extends the same convention to generated C++ `constexpr` identifiers for cross-language consistency. The constitution does not currently prescribe C++ constant naming explicitly.

## User Stories

- **US-1:** As a C++ developer consuming typist-generated headers, I want all `constexpr` names to follow `UPPER_SNAKE_CASE` convention, so that the generated code is consistent across all generated languages.
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

All references to these names within the entire generated class scope must also be updated — including constructor initializer lists, constructors, all public member functions, private helpers, and any helper-local expressions.

### FR-2: Struct Class Static Constants

All `static constexpr` members in generated struct wrapper classes must use `UPPER_SNAKE_CASE`:

| Before       | After        |
|--------------|--------------|
| `kWidth`     | `WIDTH`      |
| `kByteCount` | `BYTE_COUNT` |

All references within the entire generated class scope must also be updated.

### FR-3: Local constexpr in Helper Functions

All local `constexpr` variables inside generated per-field helper functions must use `UPPER_SNAKE_CASE`:

| Before      | After       | Location                                         |
|-------------|-------------|--------------------------------------------------|
| `kMaxValue` | `MAX_VALUE` | `validate_<field>` helpers (unsigned and signed)  |
| `kMinValue` | `MIN_VALUE` | `validate_<field>` helpers (signed)               |
| `mask`      | `MASK`      | `encode_<field>` and `decode_<field>` helpers     |

All references to these local constants within their enclosing function must also be updated.

### FR-4: Runtime Header Constants

The `inline constexpr` in `typist_runtime.hpp` must use `UPPER_SNAKE_CASE`:

| Before            | After              |
|-------------------|--------------------|
| `kVerboseDefault` | `VERBOSE_DEFAULT`  |

### FR-5: Golden File Updates

All golden files under `tests/goldens/gen/` that contain C++ headers must be regenerated to reflect the new naming. The updated golden files must match `typist gen` output byte-for-byte.

### FR-6: User-Defined Constants Unchanged

Module-level constants whose names come from user DSL definitions (e.g., `FOO`, `BAR`, `W`, `A`, `B`, `C`, `D`, `E`) are already `UPPER_SNAKE_CASE` and must not be affected by this change.

## Non-Functional Requirements

- **NFR-1:** No behavioral change — serialization/deserialization logic, byte layouts, and values remain identical. Only symbol names change.
- **NFR-2:** Deterministic output — the rename must not introduce ordering or content non-determinism.
- **NFR-3:** All existing tests must pass after updating golden files.
- **NFR-4:** `basedpyright` strict mode must pass with zero errors on all modified Python files.

## Acceptance Criteria

- **AC-1:** The C++ emitter (`src/typist/backends/cpp/emitter.py`) produces `UPPER_SNAKE_CASE` for all non-user-defined `constexpr` names as listed in FR-1, FR-2, and FR-3.
- **AC-2:** The runtime emitter (`src/typist/backends/runtime/emitter.py`) produces `VERBOSE_DEFAULT` instead of `kVerboseDefault`.
- **AC-3:** Running `typist gen` on every existing fixture produces output that matches the updated golden files byte-for-byte.
- **AC-4:** All integration, idempotency, and negative tests pass (`python -m pytest tests/`).
- **AC-5:** `basedpyright` reports zero errors.
- **AC-6:** No non-user-defined `constexpr` identifiers in any golden `.hpp` file use `kCamelCase` or plain lowercase naming. All must be `UPPER_SNAKE_CASE`.
- **AC-7:** Module-level constants that originate from user DSL definitions (e.g., `FOO`, `BAR`, `W`) remain unchanged.

## Out of Scope

- Renaming anything in SystemVerilog or Python generated outputs.
- Changing C++ class names, method names, or variable names that are not `constexpr`.
- Introducing Jinja2 templates for the C++ backend. **Exemption rationale:** This feature is a mechanical rename within existing string-built emitter functions and does not introduce new generated file structure or layout. Template migration is a separate initiative tracked independently.
- Changing any IR node definitions or DSL semantics.

## Open Questions

None — the scope is well-defined and purely mechanical.
