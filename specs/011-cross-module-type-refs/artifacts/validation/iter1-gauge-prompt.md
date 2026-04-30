# Gauge Verification — Validation Stage, Iteration 1

You are the **Gauge** in a validation loop. Your job is to factually verify the Forge's validation report. Be adversarial — do NOT rubber-stamp.

## Inputs

- **Validation report**: `specs/011-cross-module-type-refs/validation.md`
- **Spec**: `specs/011-cross-module-type-refs/spec.md`
- **Plan**: `specs/011-cross-module-type-refs/plan.md`
- **Test output**: `specs/011-cross-module-type-refs/artifacts/validation/iter1-test-output.txt`
- **Source code**: read the actual files cited by PASS claims.
- **Goldens**: `tests/goldens/gen/cross_module_type_refs/` for byte-content claims.

## What to verify

### 1. PASS claims

For each PASS in the FR/NFR/AC tables, verify:
- The cited test name exists in the test suite output and passed.
- The cited file/line actually contains what the report claims.
- The implementation actually does what the test names suggest (read the code, don't trust names alone).

Spot-check at least 5 randomly-chosen PASS entries with full source verification.

### 2. PASS (partial) claims

Several entries are marked "PASS (partial)" — distinguish whether each is genuinely partial (some sub-cases not tested but code present) versus actually FAIL (untested = unverified). Verify the partial-coverage rationale.

### 3. PASS (code, not test) claims

AC-13 and AC-14 are marked "PASS (code, not test)". Verify the code is present at the cited lines AND that without a test, calling it "PASS" is justified. If the code path is reachable from existing tests indirectly, fine. If it is dead code with no exercise path, flag as DEFERRED or FAIL.

### 4. FAIL accuracy

There are no FAIL claims. Verify by walking the spec one more time: are there FRs/ACs the Forge silently dropped without putting them in DEFERRED?

### 5. DEFERRED legitimacy

For each DEFERRED entry (NFR-4, FR-3+AC-18, AC-19), apply the DEFERRED policy:

DEFERRED is acceptable when ALL true:
- Item depends on infrastructure/tooling/environment in the spec's "Out of Scope" section
- Untested code path is isolated (does not affect in-scope correctness)
- A clear test plan exists for follow-up

DEFERRED is NOT acceptable (must be FAIL) when ANY true:
- Item covers core FR functionality
- Inability to test reveals a design flaw
- Item was not listed as out-of-scope
- Deferring would hide a regression risk in in-scope code

Specifically:
- **NFR-4**: spec memory says "AC-F4 perf gate is open from spec 010". Is this a legitimate deferral?
- **FR-3 + AC-18**: multiple_of with cross-module member. Is the code path truly isolated, or does this expose a real regression risk?
- **AC-19**: Python runtime byte-value test. The Forge claims golden comparison covers structural correctness but admits the runtime semantic could be broken in lockstep with the golden.

Reject any DEFERRED that should be FAIL.

### 6. Missing coverage

Are there requirements from the spec the Forge did not address at all? Walk every FR-1..FR-16, NFR-1..NFR-7, AC-1..AC-24 and confirm each appears in the validation report.

### 7. Test validity

Spot-check at least 3 of the new tests. Do they actually test what they claim? Are there assertions that pass trivially (e.g., always-true, mocked-out)?

### 8. Self-check the report

The validation report's Summary line says "PASS: 44, FAIL: 0, DEFERRED: 4". Recount the verdicts in the FR/NFR/AC tables and confirm the totals match. If they don't, that's a credibility hit worth flagging.

## Output format

```
# Gauge Verification — Validation Iteration 1

## Summary
(2-3 sentences on whether the Forge's report is factually accurate.)

## PASS claim verification
(spot-check at least 5)

## PASS (partial) and PASS (code, not test) verification
(walk each one)

## DEFERRED legitimacy
(walk each one against policy)

## Missing coverage
(any FR/NFR/AC silently dropped?)

## Test validity
(at least 3 tests inspected for triviality)

## Self-check
(does the Summary count match the table content?)

## Issues

### BLOCKING
- (issue, with file:line/test ref)

### WARNING
- ...

### NOTE
- ...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If any DEFERRED is illegitimate or any PASS is unsupported, REVISE. Otherwise APPROVE.

Save to `specs/011-cross-module-type-refs/artifacts/validation/iter1-gauge.md`.
