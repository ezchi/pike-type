# Gauge Verification Prompt — Validation, Iteration 1

You are the **Gauge** in a strict dual-agent Forge-Gauge validation loop. Your job is NOT to rubber-stamp the Forge's report. Independently verify every claim by reading source/test files and comparing against the spec.

## Inputs

- **Validation report under review:** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/validation.md`
- **Specification (post-clarification):** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/spec.md`
- **Plan:** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/plan.md`
- **Clarifications:** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/clarifications.md`
- **Verbatim test output:** `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/artifacts/validation/iter1-test-output.txt`
- **Modified scanner source:** `/Users/ezchi/Projects/pike-type/src/piketype/discovery/scanner.py` (45 lines after edit)
- **New test source:** `/Users/ezchi/Projects/pike-type/tests/test_scanner.py`
- **Constitution:** `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

## Forge's Summary

The Forge reports: **PASS: 26 | FAIL: 0 | DEFERRED: 0**, covering 8 FRs, 4 NFRs, 7 ACs, and 7 OOS-boundary checks.

## Required Verification Checks

### 1. PASS-claim spot-checks

For each item below, OPEN the cited file/line and confirm the report's claim is factually accurate:

- **FR-3** ("EXCLUDED_DIRS contains EXACTLY the six entries"): Read `scanner.py:11-13` and confirm the frozenset literal contains exactly `{".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}` and no extras.
- **FR-7** ("sorted list[Path]"): Confirm `scanner.py:44` calls `sorted(...)`. Confirm `tests/test_scanner.py::test_sorted_output` actually asserts sorted order (not just a tautological self-comparison).
- **FR-8** ("`is_under_piketype_dir` and `ensure_cli_path_is_valid` byte-identical to pre-change"): Verify by examining lines 16-28. Or run `git diff develop -- src/piketype/discovery/scanner.py` mentally and confirm only L11-13 (new constant) and L31-44 (find_piketype_modules) changed.
- **AC-1**: Read `tests/test_scanner.py::test_excludes_venv_duplicate` and confirm the fixture matches: a real `src/piketype/example/foo.py` AND a duplicate at `.venv/lib/python3.13/site-packages/piketype/example/foo.py`. Confirm the assertion is `== [real]`, not just `len == 1`.
- **AC-4**: Read `tests/test_scanner.py::test_all_six_excluded_names_rejected` and confirm: each fixture path includes a `piketype/` ancestor (so `is_under_piketype_dir` would otherwise admit it); assertion is `== []`.
- **AC-7**: Confirm `0 errors, 0 warnings, 0 notes` appears in `iter1-test-output.txt` after the basedpyright header.
- **307 tests / OK skipped=3**: Confirm `Ran 307 tests in 5.720s` and `OK (skipped=3)` appear in the test output. Confirm test_scanner.* shows up four times.

### 2. Test validity

For each new test method:
- Does it actually exercise the FR/AC it claims, or does it pass via a tautology?
- Specifically: does `test_sorted_output` only check `result == sorted(result)` (which is vacuously true for any pre-sorted result)? The Forge claims it ALSO asserts `[aaa, zzz]` explicitly — verify.

### 3. DEFERRED-policy compliance

The Forge reports zero DEFERRED items. Confirm there are no requirements that should have been deferred (i.e., no in-scope items silently treated as PASS without evidence).

### 4. Missing coverage

Cross-check the Forge's mappings against the full FR/NFR/AC list in `spec.md`. Are any spec items not covered in the report? Hidden in OOS items? List specifically:
- FR-1 through FR-8 — all addressed?
- NFR-1 through NFR-4 — all addressed?
- AC-1 through AC-7 — all addressed?
- OOS-1 through OOS-7 — all addressed (these are scope-boundary checks, expected as PASS-by-absence)?
- Risks R-1 through R-2 — these are not requirements, so absence from the report is fine.

### 5. Self-check verification

The Forge claims it ran the self-check (Step 3e of the validate skill). Verify:
1. The Summary line `PASS: 26 | FAIL: 0 | DEFERRED: 0` matches the actual count of PASS/FAIL/DEFERRED verdicts in the Results tables. Recount.
2. Cited line numbers are correct (you'll verify a sample as part of (1) above).

### 6. Adversarial reading

Look for items where the report uses unfalsifiable language ("ensures", "appropriately", "as required") without evidence. Look for cases where a test name is cited but the test doesn't actually exercise the claim. Look for places where "no measurable regression" is claimed without baseline data.

## Output Format

### Issues
List concrete issues with severity **BLOCKING / WARNING / NOTE**, citing the report section, FR/AC/NFR, and the specific file:line that contradicts (if any). Be terse.

### Carry-Over
N/A — first validation iteration.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Approve only if zero BLOCKING issues remain. WARNING and NOTE are fine.

## Important

- Be adversarial. Do NOT take the report's word for anything you can verify cheaply.
- The user explicitly approved earlier scope decisions (six-entry list, rglob post-filter, manual T5 instead of integration test). Do NOT re-litigate those.
- Do NOT propose extending EXCLUDED_DIRS, switching to `Path.walk()`, or adding integration tests as BLOCKING — they were resolved against in clarifications.
- The Constitution is the highest authority.
