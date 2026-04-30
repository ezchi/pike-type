# Gauge Verification — Retrospect Stage, Iteration 2

You are the **Gauge** in a retrospect loop. Iter1 issued REVISE with multiple BLOCKING items. Iter2 has been revised:

- **M2 removed** (unsupported user-preference claim)
- **M6 removed** (derivable from loader docstring)
- **M3 reworded** to remove the inaccurate "cannot count" claim
- **S1 rewritten**: real issue is missing gauge artifacts for Commits B-F (verified by `ls`)
- **P1 corrected**: NFR-4 was valid policy enforcement, not churn
- **P7 added**: stale-prose carryover during reclassification
- **S4 count corrected** from 6 → 7 SPEC UPDATE items
- **P5 clarified**: distinguishes workflow from domain skills
- **Workflow Summary table corrected**: implementation has 0 gauges for B-F (only commit-a-{forge,gauge,iter2-gauge}.md and commit-{b,c,d}-forge.md exist); validation has 4 gauges not 5 (iter1, iter3, iter4, iter5)

## What to verify

1. Are the iter1 BLOCKING items resolved?
2. Are the citations in the revised retrospect accurate?
3. Did iter2 introduce new errors?

## Output format

```
# Gauge Verification — Retrospect Iteration 2

## Iter1 Issue Resolution
For each iter1 BLOCKING:
- ✓ resolved
- ✗ unresolved

## New Issues
### BLOCKING
...
### WARNING
...

VERDICT: APPROVE
```
or REVISE.

Save to `specs/011-cross-module-type-refs/artifacts/retrospect/iter2-gauge.md`.
