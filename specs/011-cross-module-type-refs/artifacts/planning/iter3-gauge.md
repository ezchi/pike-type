# Gauge Review — Planning Iteration 3

## Summary

APPROVE. The iter2 blocking basedpyright command defect is fixed, and the three iter2 warnings are resolved in the updated plan without introducing a new planning blocker.

One non-blocking cleanup remains in `spec.md`: the FR-8 fixture/test artifact bullet still says three cases while the plan now correctly requires four.

## Iter2 Issue Resolution

- ✓ resolved — **B1: AC-22 basedpyright command.** The plan now requires `basedpyright src/piketype tests/` with no `--strict` flag (`plan.md:323-325`). That is a valid CLI shape (`basedpyright [options] files...`), and strict mode is configured in `pyproject.toml` via `typeCheckingMode = "strict"` (`pyproject.toml:44-46`), so the gate is executable and project-configured.

- ✓ resolved — **W1: NFR-4 performance gate scope.** The perf gate now iterates every fixture in `tests/fixtures/`, records per-fixture medians, sums them into a total-suite median, and fails on either >5% total regression or >10% per-fixture regression (`plan.md:314-321`). This matches NFR-4's "existing fixture suite" wording.

- ✓ resolved — **W2: FR-8 case count.** The detailed component list names four FR-8 sub-cases (`plan.md:94`), and the Testing Strategy summary now also says "four FR-8 collision sub-cases" (`plan.md:286-289`). The plan is internally consistent.

- ✓ resolved — **W3: Commit D same-module synth import wording.** Commit D now says the same-module synth import is rendered by `module_test.j2` using `module.ref.basename`, and explicitly says no new view-model field carries a rendered import line (`plan.md:199`). That matches the Components section's semantic-parts-only rule (`plan.md:62`) and the SV component wording (`plan.md:67-73`).

## New Issues

### BLOCKING

None.

### WARNING

- **Stale FR-8 test-artifact wording remains in the spec.** `spec.md:358` still says the FR-8 name-collision unit tests have "three cases — local-vs-imported, imported-vs-imported, and wildcard literal collision." The plan is now correct, but the source spec still has the older compressed wording and could cause an implementer to miss the separate imported-vs-imported enum literal and local-vs-imported enum literal cases.

### NOTE

- No regression found in prior approvals: AC-6 namespace coverage remains concrete (`plan.md:301-308`), AC-23 positive/negative static-check coverage remains present (`plan.md:96-99`, `plan.md:289`), loader shim removal remains atomic, and the template-first backend design still uses semantic view-model fields only.

## Strengths

- The AC-22 gate is now precise and compatible with the project's `pyproject.toml` strict-mode configuration.
- The performance gate now measures the full existing fixture suite instead of a single proxy fixture.
- The plan's backend wording now consistently enforces template-first import/include/from-import emission while preserving semantic view-model data.

VERDICT: APPROVE
