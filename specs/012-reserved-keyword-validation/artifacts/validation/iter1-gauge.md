Ripgrep is not available. Falling back to GrepTool.
MCP issues detected. Run /mcp list for status.Error executing tool list_directory: Error: Failed to list directory.
# Gauge Verification — Validation Iteration 1

## Summary
The implementation of the reserved-keyword validation feature is complete, correct, and rigorously tested. The validation logic accurately follows the per-language emission rules (e.g., `<base>_pkg` for SystemVerilog) and maintains strict constitutional compliance with frozen sets and deterministic error messages. All acceptance criteria are met, and the provided test suite confirms the feature's behavioral correctness across all identifier types.

## Verification of PASS claims

- **FR-1.1 (Type names):** CONFIRMED. `engine.py:559-572` checks the full `type_ir.name` (e.g., `class_t`) and does not strip the `_t` suffix to check the base.
- **FR-1.2 (Struct fields):** CONFIRMED. `engine.py:574-587` iterates and validates every field name.
- **FR-1.3 (Flags fields):** CONFIRMED. `engine.py:588-601` iterates and validates every flag name.
- **FR-1.4 (Enum values):** CONFIRMED. `engine.py:602-615` iterates and validates every enum value name.
- **FR-1.5 (Constants):** CONFIRMED. `engine.py:547-558` iterates and validates every constant name.
- **FR-1.6 (Module basenames):** CONFIRMED. `engine.py:535-545` calls `_module_name_languages` which correctly implements per-language suffix logic.
- **FR-2 (Keyword sets):** CONFIRMED. `keywords.py` defines the four frozen sets as literals with comprehensive standard citations in the header.
- **FR-3 (Error format):** CONFIRMED. `engine.py:471-501` implements the normative shape, verified verbatim in `test_validate_keywords.py`.
- **FR-4 (Exact-case):** CONFIRMED. `keywords.py:140-164` uses `in` on `frozenset[str]`, and `test_enum_value_while_is_accepted` verifies `WHILE` passes.
- **FR-5 (Entry point):** CONFIRMED. `engine.py:170` is the final call in `validate_repo`.
- **FR-6 (Raises ValidationError):** CONFIRMED. `engine.py:5` imports and uses `ValidationError`.
- **FR-7 (First-fail):** CONFIRMED. `engine.py:524-615` raises immediately in the inner-most loop without collection.
- **FR-8 (Always on):** CONFIRMED. Logic in `_validate_reserved_keywords` is unconditional.
- **FR-9 (Interaction):** CONFIRMED. Validations fire in order; `test_uppercase_check_fires_before_keyword_check` proves precedence.
- **NFR-1 (Performance):** CONFIRMED. O(N) complexity; total test execution time (0.68s) indicates negligible overhead.
- **NFR-2 (Determinism):** CONFIRMED. Frozen sets and `hits.sort()` in `keywords.py:162` ensure byte-identical output.
- **NFR-3 (Test coverage):** CONFIRMED. All 9 integration tests and 2 snapshot canary tests are present and passing.
- **NFR-4 (No dependencies):** CONFIRMED. `keywords.py` has no runtime imports.
- **NFR-5 (Documentation):** CONFIRMED. `keywords.py:1-49` header and `docs/architecture.md` are updated.
- **AC-1 (type field):** CONFIRMED. `test_struct_field_type_is_rejected` verifies rejection with Python (soft) and SV.
- **AC-2 (class_t type):** CONFIRMED. `test_type_name_class_t_is_accepted` verifies acceptance.
- **AC-3 (WHILE enum):** CONFIRMED. `test_enum_value_while_is_accepted` and its golden verify acceptance.
- **AC-4 (class.py):** CONFIRMED. `test_module_name_class_is_rejected` verifies rejection for C++/Python.
- **AC-4b (logic.py):** CONFIRMED. `test_module_name_logic_is_accepted` verifies acceptance.
- **AC-5 (for constant):** CONFIRMED. `test_constant_for_is_rejected` verifies rejection for all three languages.
- **AC-6 (try flag):** CONFIRMED. `test_flags_field_try_is_rejected` verifies rejection for C++/Python.
- **AC-7 (type_id):** CONFIRMED. `test_keyword_near_miss_type_id_passes` and its fixture verify exact-token matching.
- **AC-8 (Goldens unchanged):** CONFIRMED. Test output shows zero modifications to existing goldens.
- **AC-9 (Single file):** CONFIRMED. `keywords.py` encapsulates all keyword data and classifier logic.
- **AC-11 (Precedence):** CONFIRMED. `test_uppercase_check_fires_before_keyword_check` asserts the structural error fires first.

## Verification of DEFERRED items

- **AC-10 (Idempotent stdout/stderr):** CONFIRMED-LEGITIMATE. The implementation is deterministic-by-construction (frozen sets, alphabetical sorting, no environmental inputs). Deferral was explicitly planned, and the risk is mitigated by the stable-substring assertions in the negative test suite.

## Coverage gaps

- none found.

## Test validity findings

- none found. All tests use non-trivial assertions: negative tests check both return code and specific error substrings; positive tests check return code and perform full tree comparisons against goldens.

## Constitutional compliance findings

- **Frozen sets:** CONFIRMED. `keywords.py` uses `frozenset[str]` for all keyword sets.
- **Keyword-only args:** CONFIRMED. `engine.py:471, 486, 503, 524, 618` all use `(*,` signatures.
- **Future annotations:** CONFIRMED. `from __future__ import annotations` is present in `keywords.py`, `test_keyword_set_snapshot.py`, and `test_validate_keywords.py`.

VERDICT: APPROVE
