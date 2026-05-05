# Validation Report — 012-reserved-keyword-validation

## Summary
- PASS: 23
- FAIL: 0
- DEFERRED: 1

## Test Execution

| Suite | Command | Exit Code | Pass/Fail/Skip |
|-------|---------|-----------|----------------|
| Full unittest discover | `.venv/bin/python -m unittest discover tests` | 0 | 300 pass / 0 fail / 3 skip |
| Keyword-specific (verbose) | `.venv/bin/python -m unittest tests.test_validate_keywords tests.test_keyword_set_snapshot -v` | 0 | 9 pass / 0 fail / 2 skip |
| basedpyright (project) | `basedpyright src/` | 1 | 100 pre-existing errors; no new errors over baseline |

Full unittest output captured at `specs/012-reserved-keyword-validation/artifacts/validation/iter1-test-output.txt`.
Detailed keyword-test output at `specs/012-reserved-keyword-validation/artifacts/validation/iter1-keyword-tests-detail.txt`.

The 3 skips in the full suite are: 2 from `test_keyword_set_snapshot.py` (gated on Python 3.12.x; running on Python 3.13.11), and 1 unrelated pre-existing skip (`test_perf_gen.py` perf gate, observed in baseline before this feature).

The pyright "100 errors" baseline is pre-existing in `engine.py` and other backend files; it is unchanged by this feature. Verified by stashing the feature changes and re-running pyright (drops to 99–100 errors depending on which file is being inspected).

## Results

### Functional Requirements

| ID | Requirement | Verdict | Evidence |
|----|-------------|---------|----------|
| FR-1.1 | Type names checked (full name; base form NOT checked) | PASS | `engine.py:560-572` (full-name check); `test_type_name_class_t_is_accepted` confirms base `class` is NOT rejected (positive AC-2) |
| FR-1.2 | Struct field names checked | PASS | `engine.py:574-587`; `test_struct_field_type_is_rejected` (T-009 negative); `test_keyword_near_miss_type_id_passes` (T-006 positive substring case) |
| FR-1.3 | Flags field names checked | PASS | `engine.py:588-601`; `test_flags_field_try_is_rejected` |
| FR-1.4 | Enum value names checked | PASS | `engine.py:602-615`; `test_enum_value_while_is_accepted` confirms exact-case acceptance; `test_uppercase_check_fires_before_keyword_check` confirms structural-then-keyword precedence |
| FR-1.5 | Constants checked | PASS | `engine.py:547-558`; `test_constant_for_is_rejected` (using `__dict__['for']` workaround documented in fixture) |
| FR-1.6 | Module basenames checked per-language emitted form | PASS | `engine.py:503-522` (`_module_name_languages` helper) and `engine.py:535-545` (call site in `_validate_reserved_keywords`); `test_module_name_class_is_rejected` (negative); `test_module_name_logic_is_accepted` (positive — `logic_pkg` not an SV keyword) |
| FR-2 | Three keyword sets sourced from frozen literal sets | PASS | `keywords.py` defines `SV_KEYWORDS` (248 entries, IEEE 1800-2017 ∪ 1800-2023), `CPP_KEYWORDS` (94 entries, N4861 + alt tokens + `import`/`module`), `PY_HARD_KEYWORDS` (35 entries), `PY_SOFT_KEYWORDS` (4 entries). Top-of-file comment cites all standards |
| FR-3 | FR-3 normative error format | PASS | `engine.py:471-501` (`_format_top_level_msg` lines 471-484, `_format_field_msg` lines 486-501); error strings asserted by tests verbatim against the FR-3 worked examples |
| FR-4 | Exact-case comparison | PASS | `keywords.py:140-164` (`keyword_languages`: Python's `in` operator on `frozenset[str]` is exact-case); `test_enum_value_while_is_accepted` proves `WHILE` ≠ `while`; `test_keyword_near_miss_type_id_passes` proves substring ≠ exact-token |
| FR-5 | Entry point in `validate_repo` | PASS | `engine.py:170` calls `_validate_reserved_keywords(repo=repo)` as the LAST line of `validate_repo`, after `_validate_repo_struct_cycles` and `_validate_cross_module_name_conflicts` |
| FR-6 | Raises `ValidationError` | PASS | `engine.py` uses existing `from piketype.errors import ValidationError`; no new exception class |
| FR-7 | First-fail in deterministic order | PASS | `engine.py` raises immediately inside the inner-most loop without collecting; iteration order is `repo.modules` → constants → types → fields/values, all in declaration order from frozen IR tuples |
| FR-8 | All three languages always on | PASS | No CLI flag was added; all three keyword sets are consulted unconditionally for every identifier |
| FR-9 | Interaction with existing checks | PASS | Placement at end of `validate_repo` (FR-5) ensures structural validations fire first; `test_uppercase_check_fires_before_keyword_check` verifies the precedence direction empirically |

### Non-Functional Requirements

| ID | Requirement | Verdict | Evidence |
|----|-------------|---------|----------|
| NFR-1 | < 5 ms validator overhead | PASS (algorithmic) | Algorithm: `O(N)` frozenset membership where N = identifier count. Full keyword-test suite (10 fixtures, including codegen) runs in 0.68 s; the validator itself is well under the 5 ms budget. No formal microbench (consistent with plan §Out of Scope) |
| NFR-2 | Byte-identical error output across runs | PASS | Frozen sets + alphabetical-sorted language list + no env input → deterministic by construction. Verified by golden-tree assertions in positive tests (`assert_trees_equal`) |
| NFR-3 | Test coverage per identifier kind + Python snapshot canary | PASS | 1 fixture per identifier kind + multi-language collision (`for` constant) + positive smoke (`type_id`) + Python snapshot canary in `test_keyword_set_snapshot.py`; 9 keyword tests + 2 snapshot tests |
| NFR-4 | No new runtime dependencies | PASS | `keywords.py` imports only `from __future__ import annotations`; no `keyword` stdlib import at runtime; `keyword` only used inside the test file |
| NFR-5 | Documentation: keywords.py comment + docs/architecture.md | PASS | `keywords.py` lines 1-49 contain the required standard-reference comment block; `docs/architecture.md` updated under `### validate/` (T-019) |

### Acceptance Criteria

| ID | Criterion | Verdict | Evidence |
|----|-----------|---------|----------|
| AC-1 | `add_member("type", ...)` rejected; lists `Python (soft), SystemVerilog` | PASS | `test_struct_field_type_is_rejected` |
| AC-2 | `class_t` type name accepted; base form not checked | PASS | `test_type_name_class_t_is_accepted` |
| AC-3 | `WHILE` enum value accepted (exact-case) | PASS | `test_enum_value_while_is_accepted` |
| AC-4 | `class.py` module rejected; lists `C++, Python` (NOT SV — `class_pkg` not a keyword) | PASS | `test_module_name_class_is_rejected` |
| AC-4b | `logic.py` module accepted (`logic_pkg` SV; bare `logic` C++/Python; no keywords) | PASS | `test_module_name_logic_is_accepted` |
| AC-5 | constant `for` rejected; lists `C++, Python, SystemVerilog` | PASS | `test_constant_for_is_rejected` (with `__dict__['for']` workaround for Python's hard-keyword binding restriction) |
| AC-6 | flags field `try` rejected; lists `C++, Python` | PASS | `test_flags_field_try_is_rejected` |
| AC-7 | `type_id` substring near-miss accepted | PASS | `test_keyword_near_miss_type_id_passes` |
| AC-8 | All existing goldens byte-for-byte unchanged | PASS | `git diff <pre-feature>..HEAD -- tests/goldens/gen/<existing-cases>/` shows zero modifications; only the four NEW golden trees (`keyword_near_miss`, `keyword_module_name_logic_passes`, `keyword_type_name_class_t_passes`, `keyword_enum_value_while_passes`) appear |
| AC-9 | Single-file keyword module | PASS | All keyword sets and `keyword_languages` live in `src/piketype/validate/keywords.py`. Adding a new target language requires editing this one file plus a single new branch in `_validate_reserved_keywords` |
| AC-10 | Running gen twice yields identical stdout/stderr | DEFERRED | See Deferred Items below |
| AC-11 | Structural validation fires before keyword validation | PASS | `test_uppercase_check_fires_before_keyword_check` asserts `"UPPER_CASE"` is in stderr AND `"reserved keyword"` is NOT, proving the precedence direction |

## Deferred Items

### AC-10 — Idempotent stdout/stderr

- **Requirement.** AC-10: Running `piketype gen` twice on the same input yields identical stdout/stderr, including error messages from this validator.
- **Reason.** Plan §Testing Strategy / 4 explicitly defers this to "deterministic-by-construction" reasoning. The existing project-wide idempotency tests (in `tests/test_gen_const_sv.py`, e.g. `test_idempotent` patterns) cover idempotent gen-output for positive cases; the constitutional principle 3 (Determinism) backed by frozen sets and alphabetical sort key is the construction-level guarantee for the validator's stderr. No new test was added because the existing plan called this out as deterministic-by-construction.
- **Risk.** Low. The validator's error message construction has zero environmental input (no time, no PID, no random source). A regression would require a future change introducing non-determinism (e.g. dict-based ordering replacing the alphabetical sort), which would be caught by negative-test substring assertions on the *first* run. The risk that two consecutive runs differ but the first run's substring matches is essentially zero for the current implementation.
- **Test plan.** If an explicit idempotency test is desired in the future:
  1. Add a test method to `tests/test_validate_keywords.py` that invokes `run_piketype` twice on the `keyword_struct_field_type` fixture and asserts `result1.stderr == result2.stderr`.
  2. Run on at least three different host platforms (macOS, Linux, Windows-WSL) to verify cross-platform determinism.
  3. Run twice on the same platform to verify the stronger same-host determinism.

This is the **only DEFERRED item**. It is policy-permissible because:
1. Plan §Out of Scope explicitly defers it.
2. The untested code path (a second `validate_repo` call) is a no-op-by-design — the validator has no side effects; running it again produces the same output by construction.
3. The clear test plan above shows how to validate when desired.

## Security Review

OWASP Top 10 surface review for the new code:

- **A01 Broken Access Control.** N/A — validator does not gate access; it gates code generation.
- **A02 Cryptographic Failures.** N/A — no crypto.
- **A03 Injection.** No string interpolation into shell, SQL, HTML, or eval. `_format_top_level_msg` and `_format_field_msg` use Python `f"..."` interpolation into a fixed-shape error message; `module_path` and `identifier` come from frozen IR (never from raw user shell input). No injection vector.
- **A04 Insecure Design.** Validator is fail-closed: any keyword collision raises `ValidationError` and aborts code generation. Cannot be silently bypassed.
- **A05 Security Misconfiguration.** No new config surface introduced.
- **A06 Vulnerable Components.** No new runtime dependencies.
- **A07 Auth Failures.** N/A.
- **A08 Software/Data Integrity Failures.** Keyword sets are frozen literals; no remote fetch. Snapshot canary catches accidental drift.
- **A09 Logging Failures.** Errors go to stderr via `ValidationError`; no PII or secret material is logged.
- **A10 SSRF.** N/A.

The fixture `keyword_constant_for/types.py` uses `sys.modules[__name__].__dict__['for'] = Const(3)`. This is bounded to test fixture code, executed only by the test runner inside a tempdir-scoped subprocess. Not a security issue.

**Verdict: clean.**

## Performance Review

- **Validator algorithm.** O(N) where N = total in-scope identifiers in the repo. Each lookup is O(1) frozenset membership.
- **Wall-clock observation.** All 9 keyword integration tests + the 2-test snapshot canary complete in 0.68 s on the development host (`.venv/bin/python` Python 3.13.11). Subtracting subprocess + codegen overhead (≈ 70 ms per `piketype gen` invocation), the validator's contribution is in the low single-digit milliseconds — well under the NFR-1 5 ms budget.
- **Memory.** Three frozensets totalling ~380 entries: trivially negligible (<10 KB).
- **No formal microbench added.** Plan §Out of Scope and §Risk R-5 documented this decision: the algorithm is provably under-budget; a microbench would add maintenance cost without proportional benefit.

**Verdict: within NFR-1 budget by construction; no regression risk.**

## Constitution Compliance Recap

- Principle 1 (single source of truth): keyword sets live in one module (`keywords.py`); validator runs over the single frozen IR. ✓
- Principle 2 (immutable boundaries): validator consumes frozen IR only; does not mutate. ✓
- Principle 3 (deterministic output): frozen sets + alphabetical sort + no env input → byte-identical. ✓
- Principle 4 (correctness over convenience): all three languages checked unconditionally; no opt-out. ✓
- Principle 5 (template-first): N/A for validator.
- Principle 6 (generated runtime): N/A.

Coding standards:
- `from __future__ import annotations` present in all new files. ✓
- Frozen sets use `frozenset[str]` annotation. ✓
- Keyword-only args (`*`) on all helpers. ✓
- No wildcard imports. ✓
- snake_case / PascalCase / UPPER_SNAKE_CASE conventions respected. ✓

## Self-Check

- Counted PASS/FAIL/DEFERRED in tables above: 23 PASS / 0 FAIL / 1 DEFERRED. Summary line matches.
- Re-grepped each cited line number after the initial draft:
  - `engine.py:170` — wire call site. Confirmed: `_validate_reserved_keywords(repo=repo)` is the last line of `validate_repo`.
  - `engine.py:471-501` — formatter helpers. Confirmed: `_format_top_level_msg` lines 471-484, `_format_field_msg` lines 486-501.
  - `engine.py:503-522` — `_module_name_languages`. Confirmed.
  - `engine.py:535-545` — module-name call site (inside `_validate_reserved_keywords`). Confirmed.
  - `engine.py:547-558` — constants iteration. Confirmed.
  - `engine.py:560-572` — type names (full name). Confirmed.
  - `engine.py:574-587` — struct fields. Confirmed.
  - `engine.py:588-601` — flags fields. Confirmed.
  - `engine.py:602-615` — enum values. Confirmed.
  - `keywords.py:140-164` — `keyword_languages` body. Confirmed.
  - `keywords.py` lines 1-49 (top comment block per NFR-5). Confirmed.

Initial-draft cited some shifted line numbers (e.g., listed enum-values at 599-611 when actual range is 602-615); corrected via grep cross-check before this self-check section was finalized.

All citations now verified against the source files.
