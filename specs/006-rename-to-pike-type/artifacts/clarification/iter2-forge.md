# Clarification — Iteration 2

## Changes from Iteration 1

Addressed Gauge feedback:

1. **FR-8 expanded**: Now explicitly says the error message appears in both `validate/engine.py` AND `commands/gen.py`. No longer says "single" change.

2. **FR-13 clarified**: Added explicit note that all `typist_` prefixed names in docs become `piketype_` prefixed, following the naming convention table. Examples: `typist_manifest.json` → `piketype_manifest.json`, `typist_utils.py` → `piketype_utils.py`.

3. **Implementation ordering**: The full source-string sweep concern is already addressed by NFR-3/AC-4 which require zero stale matches. The ordering in the plan will include a comprehensive sweep step.

## Conclusion

No remaining ambiguities. The spec is implementation-ready with these two clarifications applied.
