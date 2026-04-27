# Gauge Review — Iteration 5 (self-review, Claude)

## Prior Issue Resolution

All BLOCKING and WARNING issues from iterations 1-4 are resolved:

| Iteration | Issue | Resolution |
|-----------|-------|------------|
| 1 | C++ keywords accepted | FR-2 rule 3: keyword set |
| 1 | Duplicate basenames collapse | FR-8: duplicate basename rejection |
| 1 | Golden-file vs negative test confusion | AC-14 (golden) / AC-15 (negative) split |
| 1 | Underspecified negative coverage | AC-15 lists all categories |
| 2 | `__` anywhere, `_` global scope, `std` | FR-2 rules 4, 5, 7 |
| 2 | Runtime header scope ambiguous | FR-5 explicit exclusion |
| 2 | Multi-module positive test not explicit | AC-14 requires 2+ modules |
| 3 | Include guard `__` from valid segments | FR-2 rule 6 + composition check |
| 3 | `foo::_Bar` untested | AC-11 |
| 4 | Composition check conflicts with basename deferral | FR-2 validates prefix only, runs before discovery |
| 4 | `foo::_bar` untested | AC-11 |

## New Issues

None. The specification is complete, clear, testable, consistent with the
project constitution, and feasible within the existing architecture.

### [NOTE] Segment rules are now orthogonal
- Rule 4 (no leading `_`) subsumes the `_[A-Z]` pattern for all segments.
- Rules 4+6 (no leading/trailing `_`) plus rule 5 (no `__`) make the
  composition-level check a pure safety net.
- FR-2 runs before discovery; FR-8 runs after. No conflict with basename deferral.

VERDICT: APPROVE
