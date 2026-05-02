# Tasks: 015-scanner-exclude-venv-dirs

**Spec:** `specs/015-scanner-exclude-venv-dirs/spec.md`
**Plan:** `specs/015-scanner-exclude-venv-dirs/plan.md`
**Branch:** `feature/015-scanner-exclude-venv-dirs`

## Plan Corrections Required

None. All paths and tools cited in `plan.md` were verified against the current repo state at task-breakdown time:

- `src/piketype/discovery/scanner.py` — exists.
- `src/piketype/commands/gen.py` — exists.
- `tests/` directory — exists; contains 26 sibling `test_*.py` files.
- `tests/test_scanner.py` — does NOT exist (correct; T2 creates it).
- `basedpyright` — available at `/Users/ezchi/.local/bin/basedpyright` and `.venv/bin/basedpyright`.
- `.venv/bin/python` — exists and is the canonical Python for this project (project memory: system Python lacks Jinja2; use `.venv/bin/python` for ad-hoc invocations).

## Conventions

- All ad-hoc Python invocations MUST use `.venv/bin/python`.
- All commits MUST follow Conventional Commits (per Constitution §Branching & Commits): `<type>(<scope>): <description>`. Use scope `dsl` for `scanner.py` (it lives in `src/piketype/discovery/`, the discovery subsystem; the closest scope listed in the constitution is `dsl` or `init` — prefer `dsl` since the file is on the dsl-input side; if the implementer has a better-justified scope they may use it).

## Task List

---

### T1. Add EXCLUDED_DIRS constant and exclusion predicate to scanner.py

**Description:**
Modify `src/piketype/discovery/scanner.py` to add a module-level `EXCLUDED_DIRS: frozenset[str]` constant and a new filter predicate inside `find_piketype_modules` that rejects any path whose relative-to-`repo_root` parts intersect `EXCLUDED_DIRS`.

**Specific edits:**
1. After the existing `from piketype.paths import GEN_DIRNAME` import and before `def is_under_piketype_dir`, add:
   ```python
   EXCLUDED_DIRS: frozenset[str] = frozenset(
       {".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}
   )
   ```
2. In `find_piketype_modules`, hoist the relative path into a local binding and add the new predicate. The post-edit body of the comprehension should compute `rel = path.relative_to(repo_root)` once and apply four predicates: `path.name != "__init__.py"`, no EXCLUDED_DIRS intersection, no `GEN_DIRNAME` part, `is_under_piketype_dir(rel)`.

**Files:** `src/piketype/discovery/scanner.py` (modified, single file)

**Dependencies:** none

**Verification (covers FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8):**
- `EXCLUDED_DIRS` is defined as a module-level `frozenset[str]` with exactly six entries: `.venv`, `venv`, `.git`, `node_modules`, `.tox`, `__pycache__` (no more, no fewer).
- `is_under_piketype_dir` and `ensure_cli_path_is_valid` are byte-identical to their pre-change versions.
- `find_piketype_modules` still returns `sorted(...)` and still returns `list[Path]`.
- The change keeps the `from __future__ import annotations` import already present.

---

### T2. Create focused unit test file `tests/test_scanner.py`

**Description:**
Create a new `tests/test_scanner.py` file containing four `unittest.TestCase` test methods exercising `find_piketype_modules`. Each test creates an isolated repo tree under `tempfile.TemporaryDirectory()`, populates it with the relevant `.py` files, calls `find_piketype_modules(Path(tmpdir))`, and asserts the returned `list[Path]`.

**Required test methods:**
1. `test_excludes_venv_duplicate` — repo with both `src/piketype/example/foo.py` AND `.venv/lib/python3.13/site-packages/piketype/example/foo.py`. Assert the result equals exactly `[<tmpdir>/src/piketype/example/foo.py]`. Covers AC-1.
2. `test_all_six_excluded_names_rejected` — repo with one fixture per excluded name (`.venv/piketype/foo.py`, `venv/piketype/foo.py`, `.git/piketype/foo.py`, `node_modules/piketype/foo.py`, `.tox/piketype/foo.py`, `__pycache__/piketype/foo.py`) and NO real source modules. Assert the result is `[]`. Covers AC-4 and AC-5.
3. `test_clean_repo_unchanged` — repo with only `src/piketype/foo.py`. Assert the result equals `[<tmpdir>/src/piketype/foo.py]`. Covers AC-3.
4. `test_sorted_output` — repo with `src/piketype/aaa.py` and `src/piketype/zzz.py`. Assert the result is sorted ascending. Covers FR-7 / NFR-2.

**File-creation helper:** the test module SHOULD include a small `_touch(path: Path) -> None` helper that creates intermediate directories (`path.parent.mkdir(parents=True, exist_ok=True)`) and writes an empty file. Inline if cleaner.

**Files:** `tests/test_scanner.py` (new)

**Dependencies:** T1 (the EXCLUDED_DIRS constant must exist for the tests to import meaningfully; tests do NOT need to import the constant directly but their assertions assume it).

**Verification (covers AC-1, AC-3, AC-4, AC-5, AC-6, FR-7, NFR-2):**
- File uses `unittest.TestCase`; no pytest fixtures, no parametrize.
- Uses `tempfile.TemporaryDirectory()` (per Constitution §Testing pattern and clarification C-4).
- File starts with `from __future__ import annotations`.
- All four test methods present and named exactly as specified above.

---

### T3. Run the full unittest suite and confirm green

**Description:**
Run the project's unittest discovery from the repo root using `.venv/bin/python` to confirm:
1. The new `tests/test_scanner.py` passes.
2. All pre-existing tests still pass (NFR-3, AC-3 regression sentinel).

**Command:**
```
.venv/bin/python -m unittest discover -s tests -v
```

**Files:** none modified

**Dependencies:** T1, T2

**Verification:**
- Exit code 0.
- `OK` line at the bottom of test output.
- The four new `test_scanner` methods appear in the verbose output and each says `ok`.
- No previously-passing test transitions to fail/error.

---

### T4. Run basedpyright strict on scanner.py

**Description:**
Run `basedpyright` in strict mode (project's pyrightconfig is already strict per Constitution §Coding Standards) on the modified scanner file and the new test file. Confirm zero new errors.

**Command:**
```
.venv/bin/basedpyright src/piketype/discovery/scanner.py tests/test_scanner.py
```

(Or `basedpyright` from PATH; the project's strict-mode config controls behavior.)

**Files:** none modified

**Dependencies:** T1, T2

**Verification (covers AC-7, NFR-3):**
- Zero errors reported on `src/piketype/discovery/scanner.py`.
- Zero errors reported on `tests/test_scanner.py`.
- (Project memory: `develop` baseline has 100 pre-existing errors elsewhere. Measure delta on the two changed files only — they MUST contribute zero of those.)

---

### T5. Manual end-to-end sanity check (AC-2)

**Description:**
Reproduce the original bug environment manually, then re-run `piketype gen` with the patched scanner to confirm the duplicate-basename error no longer fires.

**Steps:**
1. Create a temp directory with a minimal piketype project layout: `tmp/piketype/example.py` containing one trivial DSL declaration.
2. Inside the same temp directory, simulate a populated venv: `tmp/.venv/lib/python3.13/site-packages/piketype/example.py` with the same module name.
3. Run `cd tmp && /Users/ezchi/Projects/pike-type/.venv/bin/python -m piketype gen` (or equivalent CLI invocation).
4. Confirm exit code 0 and absence of the substring `requires unique module basenames` in stderr.

**Files:** none modified

**Dependencies:** T1, T3 (only run after the unit tests pass)

**Verification (covers AC-2):**
- `piketype gen` exits 0 with the duplicate present in `.venv`.
- No "requires unique module basenames" error in stderr.

**Notes:**
- This task is a release-readiness gate, NOT a permanent automated test (clarification C-4 makes the integration test optional).
- The implementer MAY skip this task only if T2's `test_excludes_venv_duplicate` test reproduces the same scenario at unit level AND the implementer is confident no integration-layer behavior depends on the scanner output beyond what unit tests cover. (In practice this is true for this fix — the discovery output flows directly to validation, which is unchanged.) If skipped, document the decision in the implementation commit message.

---

## Task Dependency Graph

```
T1 ──┬──► T2 ──┬──► T3 ──► T5
     │         │
     └─────────┴──► T4
```

T1 must be first (constant + predicate). T2 follows. T3 and T4 can run in either order after T2. T5 depends on T3 (you should not validate end-to-end before unit tests pass).

## Out-of-Task Concerns (already resolved by Plan/Spec)

- **No new fixture or golden** — no generated-output change.
- **No CMake / build / config edits** — no impact on Verilator, build infra, or pyproject.toml.
- **No CI / settings.json edits** — no harness change.
- **No docs / RFC updates** — internal bug fix, not user-visible API change.
- **No backport / changelog file edits** — Spec changelog is internal to `spec.md`; no top-level CHANGELOG.md exists in this repo to update.
