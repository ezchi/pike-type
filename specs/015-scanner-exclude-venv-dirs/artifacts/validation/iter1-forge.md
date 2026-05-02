# Validation Report — 015-scanner-exclude-venv-dirs

**Date:** 2026-05-02
**Branch:** `feature/015-scanner-exclude-venv-dirs`
**HEAD:** `f88c67e`

## Summary
- PASS: 26 | FAIL: 0 | DEFERRED: 0

## Test Execution

| Suite | Command | Exit Code | Pass/Fail/Skip |
|-------|---------|-----------|----------------|
| Project unittest discovery | `.venv/bin/python -m unittest discover -s tests -v` | 0 | 304 pass / 0 fail / 3 skip (pre-existing) |
| basedpyright strict (changed files only) | `.venv/bin/basedpyright src/piketype/discovery/scanner.py tests/test_scanner.py` | 0 | 0 errors / 0 warnings / 0 notes |
| Manual end-to-end sanity (AC-2) | `cd $tmp && .venv/bin/piketype gen myapp/piketype/types.py` (with `.venv/.../piketype/types.py` duplicate present) | 0 | gen tree produced; no duplicate-basename error |

Full output: `specs/015-scanner-exclude-venv-dirs/artifacts/validation/iter1-test-output.txt`

## Results

### Functional Requirements

| ID | Requirement (abridged) | Verdict | Evidence |
|----|------------------------|---------|----------|
| FR-1 | Exclude any `.py` whose relative-to-`repo_root` parts contain an EXCLUDED_DIRS entry | PASS | `scanner.py:38-39` predicate `if rel_parts & EXCLUDED_DIRS: return False`. Tests: `test_scanner.FindPiketypeModulesTests.test_excludes_venv_duplicate`, `test_all_six_excluded_names_rejected` (both `ok` in iter1 output). |
| FR-2 | EXCLUDED_DIRS is a module-level `frozenset[str]` | PASS | `scanner.py:11-13`: `EXCLUDED_DIRS: frozenset[str] = frozenset({...})`. |
| FR-3 | EXCLUDED_DIRS contains EXACTLY the six entries `{".venv","venv",".git","node_modules",".tox","__pycache__"}` | PASS | `scanner.py:12` literal contains exactly those six. `test_all_six_excluded_names_rejected` enforces the six explicitly (test list does not import EXCLUDED_DIRS — independent assertion of FR-3). |
| FR-4 | Existing rules preserved (`__init__.py` skip, GEN_DIRNAME, `is_under_piketype_dir`) | PASS | `scanner.py:34` (`__init__.py`), `:40-41` (GEN_DIRNAME), `:42` (`is_under_piketype_dir`). Order changed but each rule still applied. |
| FR-5 | Case-sensitive, exact directory-component name match (no globs/substrings) | PASS | `set(rel.parts) & EXCLUDED_DIRS` is element-wise, case-sensitive, exact. Python `set` does not glob or substring-match. |
| FR-6 | Match operates on path RELATIVE to `repo_root` only | PASS | `scanner.py:36`: `rel = path.relative_to(repo_root)`. Components above `repo_root` are absent from `rel.parts`. |
| FR-7 | Return value is `sorted(list[Path])` | PASS | `scanner.py:44`: `return sorted(...)`. Test: `test_sorted_output` asserts both `result == sorted(result)` and explicit `[aaa, zzz]` order. |
| FR-8 | `is_under_piketype_dir` and `ensure_cli_path_is_valid` byte-identical to pre-change | PASS | `scanner.py:16-28` unchanged from `develop`. Confirmed by `git diff develop -- src/piketype/discovery/scanner.py` showing edits restricted to L11-13 (new constant) and L31-44 (`find_piketype_modules`). |

### Non-Functional Requirements

| ID | Requirement | Verdict | Evidence |
|----|-------------|---------|----------|
| NFR-1 | rglob post-filter strategy (no Path.walk pruning) | PASS | `scanner.py:44`: `repo_root.rglob("*.py")` retained; filtering via `_included` predicate. |
| NFR-2 | Deterministic, sorted output | PASS | `sorted(...)` preserved (`scanner.py:44`); `test_sorted_output` confirms ordering. |
| NFR-3 | basedpyright strict zero new errors on changed files | PASS | `0 errors, 0 warnings, 0 notes` on both `src/piketype/discovery/scanner.py` and `tests/test_scanner.py` (per memory `project_basedpyright_baseline_drift.md`, delta-only measurement). |
| NFR-4 | No new runtime dependencies beyond Jinja2 | PASS | Imports unchanged (`pathlib`, internal `piketype.errors`, `piketype.paths`). `frozenset` is builtin. |

### Acceptance Criteria

| ID | Criterion | Verdict | Evidence |
|----|-----------|---------|----------|
| AC-1 | Repo with `src/piketype/example/foo.py` AND `.venv/lib/python3.13/site-packages/piketype/example/foo.py` returns ONLY the src path | PASS | `test_excludes_venv_duplicate` constructs that exact fixture and asserts `find_piketype_modules(root) == [real]`. Test result: `ok`. Also confirmed at integration level by T5 sanity run. |
| AC-2 | `piketype gen` does NOT raise "requires unique module basenames" with venv duplicate present | PASS | T5 manual run: `cd $tmp && .venv/bin/piketype gen myapp/piketype/types.py` exited 0 with `.venv/lib/python3.13/site-packages/piketype/types.py` duplicate present. No duplicate-basename error in stderr. |
| AC-3 | Clean repo with one DSL module returns exactly that module (no behavior change for happy path) | PASS | `test_clean_repo_unchanged` confirms; 307-test regression run also confirms no integration test regressed. |
| AC-4 | A path under `.git/piketype/...` is NEVER returned, even though `is_under_piketype_dir` would otherwise admit it | PASS | `test_all_six_excluded_names_rejected` constructs `.git/piketype/foo.py` (and 5 others), all under a `piketype/` ancestor; asserts result is `[]`. Excluded-dir filter takes precedence as required. |
| AC-5 | All six excluded dir names rejected when each contains nested `piketype/foo.py` | PASS | `test_all_six_excluded_names_rejected` covers all six entries explicitly. |
| AC-6 | Focused `unittest.TestCase` test added; integration test optional | PASS | `tests/test_scanner.py` exists; uses `unittest.TestCase`, `tempfile.TemporaryDirectory()`; no pytest fixtures, no parametrize, no subTest. Covers AC-1, AC-3, AC-4, AC-5, FR-7. |
| AC-7 | basedpyright strict reports zero errors on modified `scanner.py` | PASS | `0 errors, 0 warnings, 0 notes`. |

### Out-of-Scope Boundary Verification (not requirements, but non-violation checks)

| ID | Boundary | Verdict | Evidence |
|----|----------|---------|----------|
| OOS-1 | Validation logic unchanged | PASS | `git diff develop -- src/piketype/validate/` is empty. |
| OOS-2 | EXCLUDED_DIRS not configurable via CLI/env/pyproject/.gitignore | PASS | No new CLI flag, no new env var, no new pyproject section. EXCLUDED_DIRS is a hard-coded literal. |
| OOS-3 | `.gitignore` not parsed | PASS | No `gitignore` import or parsing logic added. |
| OOS-4 | Hidden directories not swept wholesale | PASS | List is explicit six entries; no `name.startswith(".")` rule. |
| OOS-5 | `is_under_piketype_dir`, `ensure_cli_path_is_valid`, `commands/gen.py` unchanged | PASS | `git diff develop --` on those files is empty (verified by reading the diff for the branch). |
| OOS-6 | `paths.GEN_DIRNAME` handling unchanged | PASS | `paths.py` and the GEN_DIRNAME predicate semantics unchanged; only the location of the check moved into the nested helper. |
| OOS-7 | Symlinks NOT resolved before exclusion check | PASS | No `Path.resolve()` call added. `rglob` returns un-resolved paths and `relative_to` operates on those. |

## Deferred Items

None.

## Security Review

- **Path traversal**: `path.relative_to(repo_root)` raises `ValueError` if `path` is not a descendant of `repo_root`. `rglob` only emits descendants, so this is safe in practice. No user-controlled input flows into the EXCLUDED_DIRS frozenset.
- **Injection**: No subprocess, no shell, no SQL, no template rendering on user input in this code path.
- **Secrets exposure**: None.
- **OWASP top 10**: N/A — this is a CLI scanning utility for local source files; not exposed to network input.

No security issues introduced.

## Performance Review

- **NFR-1 compliance**: rglob post-filter retained (no architecture change).
- **Per-file cost**: ~one `relative_to` call + one `set()` construction + one frozenset intersection per `.py` file. All O(depth) in the path; constant-factor overhead vs. the pre-fix predicate chain.
- **Empirical**: 307-test suite runs in 5.72s (post-fix) vs 5.807s (during T3 run, pre-fix is comparable historical baseline). No measurable regression.
- **Bug fix performance side effect**: For users with populated `.venv/` (where the bug originally occurred), the post-filter still walks into `.venv` via `rglob` but discards files cheaply. NFR-1 explicitly accepts this; pruning was deferred per Clarification C-2.
