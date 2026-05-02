# Gauge Review Prompt — Clarification, Iteration 2

You are the **Gauge** in a strict dual-agent Forge-Gauge clarification loop. The Forge has revised in response to your iter1 review.

## Inputs

- **Updated clarifications:** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/clarifications.md`
- **Updated spec:** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/spec.md`
- **Iter2 spec diff (changes vs iter1):** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/artifacts/clarification/iter2-spec-diff.md`
- **Your iter1 review:** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/artifacts/clarification/iter1-gauge.md`
- **Project Constitution:** `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

## What changed in iter2

The Forge addressed your three iter1 issues as follows:

1. **BLOCKING #1 (C-1 / FR-3 ordering inconsistency)** — Reconciled by removing the inaccurate "in this order" phrase from C-1's spec-impact line in `clarifications.md`. FR-3 in spec.md was NOT changed because adding "in this order" to a frozenset is semantically wrong (frozensets are unordered). The reconciliation goes the other direction: the clarification matches the spec.
2. **BLOCKING #2 (C-2 / NFR-1 predicate-ordering tweak)** — Reconciled by removing the predicate-ordering "tweak" sentence from C-2's resolution in `clarifications.md`. NFR-1 in spec.md was NOT changed because predicate ordering is an implementation detail (Python's `and` short-circuits naturally) and NFR-1 already pins the rglob post-filter strategy. The clarification was over-specifying.
3. **WARNING (C-3 / OOS-7)** — Adopted. C-3 is promoted from [NO SPEC CHANGE] to [SPEC UPDATE]. OOS-7 added to spec.md describing the symlink boundary. Changelog entry added.

## Your task

Re-review focused on the iter2 delta:

1. Confirm both BLOCKING items from iter1 are resolved by the new direction (Forge's decision to fix the clarifications rather than the spec, where the clarifications were the inaccurate side).
2. Confirm the WARNING is adopted: OOS-7 is present in spec.md, accurately describes the symlink-not-resolved behavior, and the changelog records it.
3. Look for NEW issues introduced by these targeted edits.
4. Confirm no unrelated sections were modified.

## Output Format

### Issues
**BLOCKING / WARNING / NOTE**, terse, with identifiers.

### Carry-Over from Iter 1
For each iter1 issue: RESOLVED / STILL BLOCKING / DOWNGRADED / WITHDRAWN.

### Verdict

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

## Important

- Be strict and blunt.
- Do not re-raise resolved items as BLOCKING.
- Do not propose implementation code.
- Acknowledge that for BLOCKING #1 and #2, the Forge chose to fix the clarifications (which were over-specifying or semantically wrong) rather than expand the spec. This is a defensible direction; only flag if you believe the spec should have been expanded instead and provide a concrete reason.
