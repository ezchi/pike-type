# Gauge Review — Specification, Iteration 1

**Reviewer:** gemini (gemini-2.5-pro via gemini CLI 0.40.1)
**Spec under review:** `specs/015-scanner-exclude-venv-dirs/spec.md`

### Issues

- **BLOCKING** — NFR-1 explicitly mandates that the exclusion check "runs only for `.py` files already produced by `rglob`", effectively forcing a post-filter approach. This is an anti-pattern for directory exclusion. Since the Project Constitution mandates Python 3.12+ (Constraint 1), the implementer should use `pathlib.Path.walk()` to prune `dirnames` in-place and avoid traversing massive `.venv` or `node_modules` trees entirely, preventing severe I/O overhead. (This also resolves Q-3: pruning is required).
- **BLOCKING** — AC-4 contains a contradiction. The first sentence states "`find_piketype_modules` returns it only if the path also satisfies the existing `is_under_piketype_dir` rule...", which implies a `.git/` path *could* be returned if it met the other criteria. The second sentence correctly states it must be independently excluded. AC-4 must be rewritten to unambiguously state that any path under an excluded directory is *never* returned, regardless of other rules.
- **WARNING** — FR-3's list of excluded directories is too minimal (as noted in Q-2). It should explicitly include `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `build`, `dist`, and `.eggs` to prevent similar bugs with other common tooling directories.
- **NOTE** — Regarding Q-1: This is a non-issue. The exclusion check in FR-1 correctly operates on the path *relative* to `repo_root`. During testing, `repo_root` will be the temporary directory containing the fixture, so any `.venv` in the absolute path above it (like `tests/fixtures/.venv/...`) will not be part of the relative path components and will naturally be ignored by the exclusion logic.

### Strengths

- Clear distinction between the validation logic (which is correct and should not be touched) and the discovery logic (where the bug actually lives).
- Excellent adherence to the Constitution's `frozenset` and strict-mode requirements.
- Thorough and well-defined Acceptance Criteria that cover both happy paths and intersections with existing rules.

### Verdict

VERDICT: REVISE
