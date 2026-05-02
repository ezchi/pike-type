# Task 1: Add EXCLUDED_DIRS constant and exclusion predicate to scanner.py — Forge Iteration 1

## Files Changed
- `src/piketype/discovery/scanner.py` — modified. Added `EXCLUDED_DIRS` module-level frozenset and replaced the inline filter chain in `find_piketype_modules` with a nested `_included` helper that binds `rel` and `rel_parts` once.

## Key Implementation Decisions
- **Nested `_included` function inside `find_piketype_modules`** rather than inlining the filters into the comprehension. The plan explicitly directed: "Hoist `path.relative_to(repo_root)` into a single local binding (`rel`) so all predicates read from the same value (avoids repeated `relative_to` calls; keeps the diff readable)." A walrus-operator approach inside the comprehension is awkward when three predicates need to read both `rel` and `rel.parts`; the nested helper is the cleanest way to bind once and short-circuit early. The helper has no public surface (it's a local, not exported).
- **`set(rel.parts)` constructed once** and reused for both the `EXCLUDED_DIRS` intersection and the `GEN_DIRNAME` membership test. The intersection check is the new behavior; the `GEN_DIRNAME` check is unchanged in semantics but now reads from the cached `rel_parts` for free.
- **Order of predicates inside `_included`** follows `path.name` first (cheapest, no `relative_to` call), then `EXCLUDED_DIRS` intersection (this is the bug-fix predicate; checking it early skips the `is_under_piketype_dir` work for the noisy `.venv` case), then `GEN_DIRNAME`, then `is_under_piketype_dir`. This is a perf nicety, not a correctness requirement.
- **Type annotation `EXCLUDED_DIRS: frozenset[str]`** is explicit (not relying on inference) so basedpyright strict and human readers see the contract immediately. Constitution §Coding Standards mandates `UPPER_SNAKE_CASE` for module constants — satisfied.
- **Preserved `is_under_piketype_dir` and `ensure_cli_path_is_valid` byte-for-byte**, per spec FR-8 / OOS-5.

## Deviations from Plan
- The plan's "Specific edits" section describes the change in pseudocode using a comprehension shape; my implementation uses a nested `_included` helper. This is a structural deviation from the literal example but satisfies the plan's stated intent verbatim ("bind `rel = path.relative_to(repo_root)` once, and add the new predicate"). The nested-helper form is what the plan explicitly endorsed in §Architecture Overview ("Hoist `path.relative_to(repo_root)` into a single local binding"). No semantic deviation.

## Tests Added
- None in this task. Tests live in Task 2.
