# Clarifications: 015-scanner-exclude-venv-dirs

**Iteration:** 1
**Source:** User's original `/steel-specify` prompt + Constitution + Forge analysis

## Resolutions

### C-1. EXCLUDED_DIRS list scope — RESOLVED [SPEC UPDATE]

**Open question:** Q-1 in spec — extend list with `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `build`, `dist`, `.eggs`, or ship exactly the six user-supplied entries?

**Resolution:** Ship **exactly** the six entries the user enumerated:
`{".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}`.

**Rationale:**
- The user's prompt is explicit: `Add an EXCLUDED_DIRS frozenset ({".venv", "venv", ".git", "node_modules", "__pycache__", ".tox"}) ...`. This is a six-entry literal, not a "starting list".
- The Constitution (§Constraints item 4) does not mandate any specific exclusion list; this is a pure scope decision and the user owns scope.
- Extending the list silently would (a) widen blast radius beyond the bug report, (b) risk silent exclusion of edge cases like a `build/` directory that, in some other repo, contains DSL modules.
- Future extension is cheap: adding to a `frozenset` literal is a one-line change with no churn elsewhere. Defer until a second user reports it.

**Spec impact:** FR-3 is tightened from "at minimum these six entries" to "exactly these six entries, in this order". Q-1 is removed.

---

### C-2. Implementation strategy — RESOLVED [SPEC UPDATE]

**Open question:** Q-2 in spec — minimal `rglob` post-filter, or rewrite with `pathlib.Path.walk()` (Python 3.12+) pruning `dirnames` in-place?

**Resolution:** Use the **`rglob` post-filter** approach (the user's "minimal change" patch), with one tweak: the EXCLUDED_DIRS check happens before the existing `GEN_DIRNAME` and `is_under_piketype_dir` checks (short-circuit cheapest condition first; the relative-parts set construction is shared across all three).

**Rationale:**
- The user's prompt explicitly labels the rglob post-filter as `Real fix — Minimal change:` and supplied the exact code shape. This is the user's chosen design.
- `rglob` post-filter is correct (passes all FRs and ACs); the cost is wasted I/O on populated `.venv` directories.
- The Gauge (gemini iter1 NOTE, iter2 NOTE) preferred `pathlib.Path.walk()` for efficiency, but the Constitution does not mandate any scanning algorithm. NFR-1 ("no measurable perf regression vs. status quo") is met by the post-filter.
- A `Path.walk()` rewrite is a more invasive change for a bug fix and would expand testing surface (symlink behavior, dirname mutation contract, ordering semantics). Out of scope for this fix; can be revisited if scan time becomes a measured problem.

**Spec impact:** NFR-1 is pinned to permit-but-prefer the rglob post-filter; the "permitted but discouraged" language is replaced with a concrete decision. Q-2 is removed.

---

### C-3. Symlinks inside `repo_root` — RESOLVED [NO SPEC CHANGE]

**Implicit assumption:** What if `repo_root` contains a symlink pointing into a directory that, after resolution, lives under an excluded name (e.g., `repo_root/extlib -> /opt/projectx/.venv/...`)?

**Resolution:** Out of scope. `Path.rglob` returns paths constructed by walking from `repo_root` without resolving symlinks; the relative-parts set check uses those raw parts. So `repo_root/extlib/.../foo.py` is NOT excluded by this fix even if its physical location is under a `.venv`. We accept this gap because:
- The original bug is about `repo_root/.venv/...` (a physical, in-tree venv), not symlinked external venvs.
- Symlinking a venv into a piketype repo is unusual; if it ever causes real pain, address it then.
- Adding `Path.resolve()` would change ordering, change behavior for legitimate in-tree symlinks (rare but plausible), and is outside the user's stated minimal-change intent.

**Spec impact:** None. (Documented here for future maintainers and to close the implicit assumption.)

---

### C-4. Test approach — RESOLVED [SPEC UPDATE]

**Implicit assumption:** AC-6 says "a new automated test ... OR a focused unit test on `find_piketype_modules`". Which is preferred for this codebase?

**Resolution:** **Focused unit test** on `find_piketype_modules`, plus optionally one negative-path integration test if the duplicate-basename error message is part of the contract being verified.

**Rationale:**
- The Constitution §Testing prescribes golden-file integration tests for new feature behavior, but explicitly mentions "Negative tests verify that invalid inputs produce specific error messages and non-zero exit codes." This bug fix changes scanner internals, not output formats — no golden file changes.
- A focused unit test (constructing a `tmp_path` with `.venv/lib/.../piketype/foo.py` and `src/piketype/foo.py`, calling `find_piketype_modules`, asserting only the `src` path is returned) is cheaper, faster, and more diagnostic than a full subprocess run.
- An additional integration test that runs `piketype gen` against the same fixture and asserts a clean (non-error) exit is *useful* but not strictly required if the unit test covers AC-1 and AC-5; AC-2 is implied transitively because the validation logic is unchanged.
- This choice aligns with §Testing's `unittest.TestCase` style — the new test will use `unittest.TestCase` and `tempfile.TemporaryDirectory()` (no pytest fixtures, no parametrize).

**Spec impact:** AC-6 is tightened to specifically call for a focused unit test using `unittest.TestCase`, plus an optional negative-path integration test for AC-2.

---

### C-5. Determinism guarantee — RESOLVED [NO SPEC CHANGE]

**Implicit assumption:** Does the new exclusion check affect output ordering?

**Resolution:** No. The implementation continues to return `sorted(...)`. NFR-2 already states "Determinism preserved". The exclusion is a filter, not a re-orderer. No spec change needed.

---

## Summary

- **2 [SPEC UPDATE] clarifications** (C-1, C-2, C-4) → spec.md is being updated to lock down EXCLUDED_DIRS to exactly six entries, pin the `rglob` post-filter strategy, and tighten the test approach in AC-6.
- **2 [NO SPEC CHANGE] clarifications** (C-3, C-5) → recorded here for future maintainers; no spec edits.
- **All `[NEEDS CLARIFICATION]` markers in spec.md are resolved.** Q-1 and Q-2 are removed.
