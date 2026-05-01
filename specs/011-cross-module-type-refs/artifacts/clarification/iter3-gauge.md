# Gauge Review — Clarification Iteration 3

## Summary

Iter3 fixes the iter2 staging contradiction: Commit C is now IR-only, while Commit D owns the new cross-module fixture and generated-output goldens alongside the FR-9/10/11/12 emission that makes those goldens valid. CL-8 bookkeeping is corrected in clarifications.md and the summary table; no new blocking issue appears.

## Iter2 Issue Resolution

- ✓ resolved — iter2 BLOCKING, cross-module fixture/golden staging. Commit C now explicitly says there is **no new generated-output fixture** and that coverage is through `RepoIR`-level tests (`specs/011-cross-module-type-refs/spec.md:42-44`). Commit D now adds `tests/fixtures/cross_module_type_refs/` and its full SV/Python/C++/manifest goldens in the same commit that implements FR-9/10/11/12 emission (`specs/011-cross-module-type-refs/spec.md:45`). That removes the impossible intermediate state where final cross-module goldens existed before import/include/from-import emission.
- ✓ resolved — iter2 BLOCKING, self-contradictory golden footer. The old "Commits D-F do not modify any golden" wording is gone. The replacement invariant is internally consistent: no **existing** golden is modified in Commits A-F, while new cross-module goldens are added in Commits D and E (`specs/011-cross-module-type-refs/spec.md:49`).
- ✓ resolved — iter2 WARNING, CL-8 bookkeeping. CL-8 is now marked `[SPEC UPDATE]` (`specs/011-cross-module-type-refs/clarifications.md:113`), the summary table marks CL-8 as `YES` (`specs/011-cross-module-type-refs/clarifications.md:154`), and the count now says seven spec-update items (`specs/011-cross-module-type-refs/clarifications.md:158`). The iter3 spec diff does not change FR-9a requirement text for this bookkeeping fix; it only adds the changelog entry documenting the metadata correction (`specs/011-cross-module-type-refs/spec.md:437`).

## New Issues

### BLOCKING

None.

### WARNING

None.

### NOTE

- CL-1 through CL-10 still align with the current spec text. I do not see a regression in FR-9 whitespace, FR-10 test-package import layout, FR-11 Python import placement, FR-13/AC-23 empty allowlist, FR-14 manifest dependency presence, or CL-10's const-ref scope.
- The Commit C wording about "Direct `RepoIR` unit tests under `tests/test_freeze.py`" is acceptable as long as those tests inspect freeze-produced `RepoIR` where relevant and use direct `RepoIR` construction only for validation-only cases. This is not a revision issue.

## Strengths

- The new staging note cleanly separates IR availability from generated-output validity.
- The existing-golden invariant now states the exact invariant implementers must preserve without blocking new fixture goldens.
- The CL-8 metadata now matches the actual spec history and avoids misleading planning work.

VERDICT: APPROVE
