# Gauge Review — Clarification Iteration 1

**WARNING:** FR-8 says "single error message change" in validate/engine.py, but `src/typist/commands/gen.py:62` also contains the same message. All occurrences must change.

**WARNING:** FR-13 docs have `typist_` prefixed names (e.g. `typist_utils.py`, `typist_manifest.json`, `typist_runtime_pkg.sv`). The spec doesn't explicitly say these become `piketype_*`. NFR-3 requires zero stale matches, so they must change, but the clarification should state this explicitly.

**NOTE:** Ordering should include a full source-string sweep before regenerating goldens.

VERDICT: REVISE
