# Gauge Review — Iteration 4

## Issues

### [BLOCKING] Include-Guard Validation Conflicts With Basename Deferral
- **Requirement:** FR-2 / FR-4 / FR-7 / Out of Scope
- **Issue:** FR-2 says the CLI validates `<value>` before processing begins, but the composition-level check says to compute the include guard using FR-4 rules. FR-4 includes `<MODULE_BASENAME>`, and FR-7 applies this to every discovered module. That requires discovery and also partially validates basename-derived reserved identifiers, which the Out of Scope section says is deferred.
- **Suggestion:** Either validate only the namespace-derived guard prefix before discovery, or make full per-module include-guard validation in scope.

### [WARNING] Composition-Level Guard Check Is Not Directly Tested
- **Requirement:** FR-2 / AC-10 / AC-11 / AC-15
- **Issue:** AC-10 (`foo_`) and AC-11 (`foo::_Bar`) fail segment-level validation, so they do not prove the composition-level check works. `foo::_bar` passes all segment rules but produces `FOO__BAR` in the guard.
- **Suggestion:** Add a negative test for `typist gen --namespace "foo::_bar" <path>`.

## VERDICT: REVISE
