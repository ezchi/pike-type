# Spec Diff — Clarification Iteration 1

## FR-3

**Before:**
> EXCLUDED_DIRS MUST contain at minimum these six entries: `".venv"`, `"venv"`, `".git"`, `"node_modules"`, `".tox"`, `"__pycache__"`.

**After:**
> EXCLUDED_DIRS MUST contain **exactly** these six entries (no more, no fewer): `".venv"`, `"venv"`, `".git"`, `"node_modules"`, `".tox"`, `"__pycache__"`. Future extension is an explicit follow-up decision, not silent scope creep.

**Source clarification:** C-1.

---

## NFR-1

**Before:**
> No measurable performance regression in `piketype gen` end-to-end runtime versus the current scanner on a typical project (no populated `.venv` adjacent to the source tree). The spec does NOT prescribe an implementation strategy: post-filtering an `rglob` walk and pruning via `os.walk` / `pathlib.Path.walk()` are both acceptable, provided the observable behavior matches the FRs and ACs. Implementations that traverse into excluded directories before discarding their contents are permitted but discouraged where pruning is straightforward; the implementer makes the call (see Q-3).

**After:**
> No measurable performance regression in `piketype gen` end-to-end runtime versus the current scanner on a typical project (no populated `.venv` adjacent to the source tree). The implementation MUST use the `rglob` post-filter strategy: keep the existing `repo_root.rglob("*.py")` walk and add the excluded-directory check as an additional filter predicate alongside the existing checks. The Python 3.12+ `pathlib.Path.walk()` pruning approach is explicitly out of scope for this fix (see clarification C-2); it may be revisited if scan time becomes a measured problem.

**Source clarification:** C-2.

---

## AC-6

**Before:**
> A new automated test under `tests/` exercises AC-1 (or an equivalent) via the same fixture-and-subprocess pattern used by other golden tests, OR a focused unit test on `find_piketype_modules`. Pre-existing integration tests continue to pass without modification.

**After:**
> A new **focused unit test** for `find_piketype_modules` is added under `tests/`, using `unittest.TestCase` and `tempfile.TemporaryDirectory()` (no pytest fixtures, no parametrize). The unit test MUST cover at least AC-1 (venv duplicate excluded) and AC-5 (all six excluded dir names rejected). Pre-existing integration tests continue to pass without modification. An additional negative-path integration test for AC-2 is OPTIONAL and may be added if the implementer judges it adds diagnostic value.

**Source clarification:** C-4.

---

## Open Questions section

**Before:** Q-1 (extend list?) and Q-2 (rglob vs Path.walk) listed as `[NEEDS CLARIFICATION]`.

**After:** Both removed. Section now reads:
> (All open questions resolved in Clarification iteration 1. See `clarifications.md`.)

**Source clarifications:** C-1 (resolved Q-1), C-2 (resolved Q-2).

---

## Changelog section

**Before:** Did not exist.

**After:** Appended at end of spec.md with four entries documenting the FR-3, NFR-1, AC-6, and Q-1/Q-2 changes.

---

## Sections NOT Modified

- Overview, Background, User Stories (US-1, US-2, US-3)
- FR-1, FR-2, FR-4, FR-5, FR-6, FR-7, FR-8
- NFR-2, NFR-3, NFR-4
- AC-1, AC-2, AC-3, AC-4, AC-5, AC-7
- Out of Scope (OOS-1 through OOS-6)
- Risks (R-1, R-2)
- References
