# Gauge Review — Planning Stage, Iteration 1

You are the **Gauge** in a Forge-Gauge dual-LLM planning loop. The forge has produced a technical implementation plan for spec 011.

## What to do

1. Read the spec at `specs/011-cross-module-type-refs/spec.md`.
2. Read the clarifications at `specs/011-cross-module-type-refs/clarifications.md`.
3. Read the plan at `specs/011-cross-module-type-refs/plan.md`.
4. Read `.steel/constitution.md`.
5. Spot-check source files cited by the plan to verify the proposed component changes are accurate.

## What to evaluate

### A. Spec coverage

- Does the plan cover every FR (FR-1 through FR-16)?
- Does the plan cover every NFR (NFR-1 through NFR-7)?
- Does each AC (AC-1 through AC-24) have at least one test (unit or integration) that exercises it?
- Are all 10 clarifications (CL-1 through CL-10) reflected in the plan?

### B. Architecture soundness

- Does the staging plan (Commits A-F) preserve byte-parity at every commit?
- Does Commit B's "full switchover" really preserve byte-parity, or could there be subtle differences when same-module refs use the new repo-wide index path?
- Is FR-1's snapshot-and-restore implementable as described, or are there edge cases the plan misses (e.g., test discovery imports, `__pycache__` interactions)?
- Does FR-7's `build_repo_type_index` correctly handle a repo with zero modules (degenerate empty case)? With one module? With duplicate-basename modules (since FR-9a only catches them at validation time, not earlier)?

### C. Simplicity

- Is anything over-engineered?
- Are there gratuitous new abstractions or helper modules that could be inlined?
- Is the public API surface minimal?

### D. Risk assessment

- Are the listed risks (R1-R7) the right ones?
- Are mitigations concrete and testable?
- Are there missing risks? Specifically:
  - What if a cross-module reference targets a `ScalarTypeSpecIR` (inline scalar) instead of a named type? (Cannot happen by construction, but does the plan handle this assumption explicitly?)
  - What if `_freeze_expr` is called on a `Const` whose source.path is the current module but whose object identity matches an instance from another module? (Edge case in FR-1 design.)
  - What if two cross-module references in the same module have the same target module but different types? Sort-order guarantees?
  - C++ rendering: what about pack/unpack steps that emit `target.field.to_bytes(...)` for a cross-module field — is the namespace-qualified field type required in those code paths too, or is it scoped to the field declaration only?

### E. Testing strategy

- Are unit and integration tests well-separated?
- Is there a test for every FR's negative case?
- Does `tests/test_no_inline_imports.py` (AC-23) include positive test cases (legitimate code is not flagged)? The plan mentions both positive and negative test cases — verify this is concretely enough described.
- Is there a performance test for NFR-4's 5% budget? The plan says "benchmark before/after Commit E" — is this a real test in the suite or just an instruction?

### F. Constitution alignment

- Constitution principle 5 (Template-first generation): plan moves `view.py:704` into templates — verified.
- Constitution principle 1 (Single source of truth): no new sources of truth introduced — verified.
- Constitution principle 3 (Deterministic output): all new emitted lists have explicit sort orders — verified by reference to spec.
- Constitution constraint 6 (Minimal runtime dependencies): no new deps — verified.
- Are there any constitution principles or constraints the plan violates?

## Output format

```
# Gauge Review — Planning Iteration 1

## Summary
(2-3 sentences)

## Spec Coverage Audit

(Quick table or list: every FR/NFR/AC mapped to plan section. Flag any gaps.)

## Issues

### BLOCKING
- (issue, with reference and suggested fix)

### WARNING
- ...

### NOTE
- ...

## Strengths
- ...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If the plan covers every FR/NFR/AC AND has no BLOCKING architecture/risk issues, APPROVE. WARNINGs alone do not require revision.

Save to `specs/011-cross-module-type-refs/artifacts/planning/iter1-gauge.md`.

Be strict. Cite line numbers. Verify against source.
