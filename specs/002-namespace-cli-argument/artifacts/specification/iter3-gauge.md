# Gauge Review — Iteration 3

Resolved from prior iterations: duplicate basename rejection is now specified;
runtime C++ headers are explicitly out of scope; the positive golden test now
requires multiple modules; and invalid namespace tests are split out from golden
output comparison. The remaining problems are below.

### [BLOCKING] Valid Namespace Values Can Produce Reserved Include Guard Macros
- **Requirement:** FR-2 / FR-4 / AC-2 / AC-13
- **Issue:** FR-2 validates namespace segments individually, but FR-4 creates the
  include guard by replacing `::` with `_` and uppercasing the result. That means
  namespace values that pass FR-2 can still generate reserved macro identifiers.
  For example, `--namespace foo_` with `constants.py` produces
  `FOO__CONSTANTS_TYPES_HPP`, and `--namespace foo::_bar` produces
  `FOO__BAR_CONSTANTS_TYPES_HPP`. Both contain `__`, which is reserved in C++.
  This is not an edge case in the module basename; it can be triggered by the
  user-provided namespace alone.
- **Suggestion:** Add validation for the composed include guard identifier, or
  constrain namespace segments so guard composition cannot create reserved macro
  names. At minimum, reject namespace values that would make the final guard
  contain `__` or begin with `_`, and add negative CLI tests for those cases.

### [WARNING] Acceptance Tests Miss Nested Underscore-Uppercase Segments
- **Requirement:** FR-2 / AC-13
- **Issue:** FR-2 rejects any segment beginning with underscore followed by an
  uppercase letter, but AC-13 does not require a test for that category unless it
  appears as the first segment. The listed "leading underscore at global scope"
  test can pass with `_foo` while leaving `foo::_Bar` untested.
- **Suggestion:** Add a negative CLI acceptance case such as
  `typist gen --namespace "foo::_Bar" <path>` and assert the reserved identifier
  error substring.

### [NOTE] Module Basename Validation Remains Deferred
- **Requirement:** FR-3 / Out of Scope
- **Issue:** Iteration 1 raised that `<module_basename>` is also a generated C++
  namespace segment. Iteration 3 explicitly moves basename keyword/identifier
  validation out of scope. That is acceptable for this feature only because the
  current generator already emits file-stem-derived C++ namespace segments, but
  it means FR-2 must not be read as validating the full generated namespace.
- **Suggestion:** Leave the out-of-scope statement in place for this feature, but
  track basename/path-derived namespace validation as a separate correctness
  item if the project wants all generated C++ identifiers to be validated.

VERDICT: REVISE
