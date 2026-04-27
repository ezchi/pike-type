# Gauge Review — Iteration 1

## Issues

### [BLOCKING] Invalid C++ Identifiers Are Still Accepted
- **Requirement:** FR-2 / FR-3
- **Issue:** The regex accepts C++ keywords and reserved identifiers such as `class`, `namespace`, `__foo`, or `_Bar`. Those can produce invalid or reserved C++ namespaces/include guards despite passing validation. The final namespace also includes `<module_basename>`, but the spec does not require validating that segment.
- **Suggestion:** Define validation for every generated namespace segment: user-provided segments plus module basename. Reject C++17 keywords and reserved identifier forms, not just regex failures.

### [BLOCKING] Duplicate Module Basenames Can Collapse Namespaces
- **Requirement:** FR-3 / FR-7
- **Issue:** Applying one prefix to every discovered module and appending only `<module_basename>` means `alpha/typist/types.py` and `beta/typist/types.py` both generate `foo::bar::types`. That silently destroys the path-derived namespace uniqueness the current design relies on.
- **Suggestion:** Specify collision handling. Either reject duplicate module basenames when `--namespace` is used, or include enough path-derived identity in the composed namespace to keep modules distinct. Add a test for two modules with the same basename.

### [WARNING] Negative "Golden-File" Test Is Not Coherent
- **Requirement:** AC-7
- **Issue:** An invalid namespace should exit before generation, so there is no generated output tree to compare against a golden. Calling this a golden-file integration test is wrong.
- **Suggestion:** Split AC-7 into positive golden-file tests and negative CLI validation tests that assert non-zero exit and a specific error substring.

### [WARNING] Invalid Namespace Coverage Is Underspecified
- **Requirement:** AC-4 / AC-5 / AC-7
- **Issue:** AC-4 and AC-5 name two invalid cases, but AC-7 only requires "one negative case." That leaves one acceptance criterion untested.
- **Suggestion:** Require tests for both malformed separators and invalid leading-character cases, plus keyword/reserved-name cases if FR-2 is fixed.

## VERDICT: REVISE
