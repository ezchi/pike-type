# Implementation Plan: 015-scanner-exclude-venv-dirs

**Spec:** `specs/015-scanner-exclude-venv-dirs/spec.md`
**Clarifications:** `specs/015-scanner-exclude-venv-dirs/clarifications.md`
**Branch:** `feature/015-scanner-exclude-venv-dirs`

## Architecture Overview

This is a one-file bug fix in the discovery layer of the pipeline. The pipeline (`Discovery -> DSL -> IR -> Backends`, per Constitution Principle 2) only requires a change at the discovery boundary: filter the `.py` paths returned by the filesystem walk before they leave `find_piketype_modules`. No DSL, IR, validation, backend, manifest, or template change is involved. No new module is introduced; one module-level constant is added and one comprehension predicate is extended.

```
┌──────────────────────────────────────────────────────────┐
│ piketype.discovery.scanner (modified)                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │ EXCLUDED_DIRS: frozenset[str]   (NEW constant)     │  │
│  │ find_piketype_modules(repo_root)  (modified)       │  │
│  │   rglob → filter:                                  │  │
│  │     - skip __init__.py            (existing)       │  │
│  │     - skip GEN_DIRNAME parts      (existing)       │  │
│  │     - require piketype ancestor   (existing)       │  │
│  │     - reject any EXCLUDED_DIRS    (NEW)            │  │
│  │   → sorted list[Path]                              │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
              ▲                              ▲
              │                              │
   piketype/commands/gen.py:36     tests/test_scanner.py (NEW)
   (sole production caller,        (focused unit test,
    NOT modified)                   AC-1 + AC-5 coverage)
```

## Components

### 1. `src/piketype/discovery/scanner.py` — modified

**Responsibility:** filter the recursive `.py` walk so that paths under non-source directories are excluded.

**Changes:**
- Add `EXCLUDED_DIRS: frozenset[str]` module-level constant containing exactly the six entries from FR-3.
- Add a fourth predicate to the comprehension inside `find_piketype_modules`: `not (set(rel.parts) & EXCLUDED_DIRS)`.
- Hoist `path.relative_to(repo_root)` into a single local binding (`rel`) so all predicates read from the same value (avoids repeated `relative_to` calls; keeps the diff readable).

**Out of scope (per spec OOS-5, OOS-6, OOS-7):**
- `is_under_piketype_dir`: untouched.
- `ensure_cli_path_is_valid`: untouched (CLI path validator, intentionally permissive about ancestor dirs).
- `GEN_DIRNAME` handling: untouched.
- Symlink resolution: not added.

### 2. `tests/test_scanner.py` — new

**Responsibility:** focused `unittest.TestCase` covering AC-1 and AC-5 for `find_piketype_modules`.

**Test cases:**
- `test_excludes_venv_duplicate` — repo with `src/piketype/example/foo.py` AND `.venv/lib/python3.13/site-packages/piketype/example/foo.py`; assert only the `src` path is returned. (AC-1)
- `test_all_six_excluded_names_rejected` — repo with one fixture per excluded name (`.venv`, `venv`, `.git`, `node_modules`, `.tox`, `__pycache__`), each containing a nested `piketype/foo.py`; assert the result is empty. (AC-5)
- `test_clean_repo_unchanged` — repo with only `src/piketype/foo.py`; assert exactly that one path returned. (AC-3, regression sentinel)
- `test_sorted_output` — repo with two real modules; assert sorted order preserved. (NFR-2 / FR-7 sentinel)

All test cases use `unittest.TestCase` and `tempfile.TemporaryDirectory()`. No pytest fixtures, no parametrize.

### 3. Existing tests — unchanged

The integration tests under `tests/test_gen_*.py` and module-level tests (`test_loader.py`, `test_view_*.py`, `test_freeze.py`) all import `find_piketype_modules` indirectly via `commands.gen`. They are run via the standard `python -m unittest discover` regression to verify NFR-3 / AC-3 (no regression).

## Data Model

No data-model changes. `find_piketype_modules` returns the same `list[Path]` contract.

## API Design

No public-API changes:
- `find_piketype_modules(repo_root: Path) -> list[Path]` signature unchanged.
- `is_under_piketype_dir`, `ensure_cli_path_is_valid` signatures unchanged.

The new `EXCLUDED_DIRS` constant is a module-level export; no underscore prefix, since it's documented as part of the scanner's public configuration surface for future maintainers (per Constitution §Coding Standards: `UPPER_SNAKE_CASE` for module-level constants).

## Dependencies

None added. Constitution mandates "No external runtime dependencies beyond Jinja2", and this fix uses only `pathlib` (stdlib) and `frozenset` (builtin).

## Implementation Strategy

Single-phase, single-PR. The change is small enough that splitting phases would be ceremony.

### Step-by-step

1. **Edit `scanner.py`**:
   - Add `EXCLUDED_DIRS = frozenset({".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"})` near the top (after the module docstring + imports, before `is_under_piketype_dir`).
   - Modify `find_piketype_modules` to bind `rel = path.relative_to(repo_root)` once, and add the new predicate.
2. **Create `tests/test_scanner.py`** with the four test cases above.
3. **Run `python -m unittest discover -s tests`** and confirm green.
4. **Run `basedpyright`** in strict mode on the modified file; confirm zero new errors (NFR-3, AC-7).
5. **Sanity check the bug**: in a temp dir, simulate `repo_root/.venv/lib/.../piketype/foo.py` + `repo_root/src/piketype/foo.py`, run `piketype gen` (or directly call `find_piketype_modules`), confirm AC-2.

### Files touched

| File | Status | Notes |
|------|--------|-------|
| `src/piketype/discovery/scanner.py` | modified | +~5 LOC: EXCLUDED_DIRS constant + one predicate |
| `tests/test_scanner.py` | new | ~80 LOC: 4 unittest test cases |

No other files (CMakeLists, build config, docs, goldens, fixtures) need to change.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **R-1.** A real DSL module legitimately under `__pycache__/` etc. is silently ignored. | Vanishingly low (Python convention forbids placing source in `__pycache__/`). | High *if* it occurred. | Spec R-1 already accepts this. Documented in OOS via the explicit list. |
| **R-2.** `path.relative_to(repo_root)` raises if `repo_root` is not an ancestor of `path`. | Low — `rglob` returns descendants of `repo_root` only. | Medium (existing behavior; this fix neither introduces nor mitigates it). | Out of scope; leave existing semantics untouched. |
| **R-3.** Test fixture directories named `.venv`, `__pycache__`, etc. inside `tests/fixtures/` would be silently dropped from the integration test scan. | Low — verified at spec time via `find tests -type d -name '.venv' -o -name 'venv' -o -name '.tox'` returning no matches; clarification C-1 / Q-1 considered and resolved. | Medium if a future fixture is named that way. | Documented in spec OOS-7 boundary. New fixtures must avoid these names; if needed, gauntlet via PR review. |
| **R-4.** Breaking idempotency tests (running `piketype gen` twice produces identical output). | Very low — the change is in discovery, not emission. Discovery output is sorted; the new filter is deterministic. | High if hit. | Existing idempotency tests in `tests/test_gen_*.py` will catch regressions on `python -m unittest discover` step 3. |
| **R-5.** Symlink in `repo_root` pointing into `.venv` is not excluded (not the bug being fixed). | Low (unusual setup). | Low (worst case: same symptom as today, scoped narrower). | OOS-7 documents the limitation; defer until reported. |

## Testing Strategy

**Per Constitution §Testing**, the project uses `unittest.TestCase` and golden-file integration tests as the primary correctness mechanism. This fix sits in discovery (no output format change), so:

1. **Focused unit test** (new) — `tests/test_scanner.py` covers AC-1, AC-3, AC-5, and FR-7 ordering. This is the **primary** verification per AC-6 / clarification C-4.
2. **Existing integration tests** (unchanged) — must pass as-is. They cover NFR-3 / AC-3 (no regression in module discovery for legit repos) transitively.
3. **basedpyright strict** — must pass with zero new errors on `scanner.py` (NFR-3, AC-7).
4. **Manual sanity** — the implementer reproduces the original bug in a temp tree and confirms AC-2 (no "duplicate basenames" error). This is not a permanent automated test, but is required as a release-readiness gate.

**Not pursued:**
- A new integration test under `tests/test_gen_*.py` for AC-2 — clarification C-4 marks it OPTIONAL. The unit test is sufficient because the validation pipeline downstream of `find_piketype_modules` is unchanged.
- Performance benchmark — NFR-1 is "no measurable regression on a typical project." A formal benchmark adds CI weight without commensurate value for this scope.

## Acceptance Criteria Mapping

| AC | Verification |
|----|--------------|
| AC-1 | `test_excludes_venv_duplicate` |
| AC-2 | Manual sanity check (step 5); transitive guarantee from AC-1 + unchanged validation path |
| AC-3 | `test_clean_repo_unchanged` + existing integration tests |
| AC-4 | `test_all_six_excluded_names_rejected` (constructs `.git/piketype/foo.py` etc.) |
| AC-5 | `test_all_six_excluded_names_rejected` |
| AC-6 | The new `tests/test_scanner.py` itself |
| AC-7 | `basedpyright` clean run |

## Constitution Compliance Check

| Constitution clause | Compliance |
|---------------------|------------|
| Principle 1 (single source of truth) | N/A — discovery layer, no generated output |
| Principle 2 (immutable boundaries) | Respected — change is contained to discovery; no leakage into DSL/IR |
| Principle 3 (deterministic output) | Preserved — `sorted(...)` retained; filter is deterministic |
| Principle 4 (correctness over convenience) | Strengthened — fixes a silent over-inclusion bug |
| Principle 5 (template-first) | N/A — no generated output |
| Principle 6 (generated runtime) | N/A |
| §Coding Standards Python: `from __future__ import annotations` | Already present in `scanner.py` |
| §Coding Standards Python: basedpyright strict | Verified in step 4 of impl strategy |
| §Coding Standards Python: `UPPER_SNAKE_CASE` for module constants | `EXCLUDED_DIRS` follows this |
| §Testing: `unittest.TestCase` | New test uses `unittest.TestCase` per C-4 |
| §Constraints item 4 (unique-basename validation) | Preserved unchanged; this fix removes the false-positive trigger |

## Open Items

None. All clarifications are resolved; spec acceptance criteria all map to a verification step.
