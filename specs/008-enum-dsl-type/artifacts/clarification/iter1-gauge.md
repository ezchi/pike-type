# Gauge Review — Clarification Iteration 1

**BLOCKING**: FR-28 (spec.md line 177) still says the mixed explicit/auto-fill fixture should demonstrate "gap-filling behavior." That contradicts corrected FR-6 and FR-32. Change it to sequential auto-fill behavior.

**WARNING**: CLR-2 is marked `[SPEC UPDATE]` but says no spec change is needed beyond FR-6. Retag as `[NO SPEC CHANGE]`.

**WARNING**: CLR-1 claims the rule matches Python `enum.auto()`. That is not generally true; Python `auto()` uses the highest previous value plus one, not the immediately preceding value. Remove the Python claim.

**NOTE**: FR-6, AC-3, FR-32, and the changelog entries otherwise match the v1 product spec rule.

VERDICT: REVISE
