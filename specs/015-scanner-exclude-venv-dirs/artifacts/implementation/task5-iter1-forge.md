# Task 5: Manual end-to-end sanity check (AC-2) — Forge Iteration 1

## Files Changed
- None. Verification task.

## Setup
Created an isolated temp repo to reproduce the original bug shape:
```
$SANITY/
  .git                                                         (touch — repo-root marker for find_repo_root)
  myapp/piketype/types.py                                      (real DSL module)
  .venv/lib/python3.13/site-packages/piketype/types.py         (duplicate from "installed" piketype)
```

Both `.py` files have identical basename `types.py`, both live under a directory named `piketype/` (the second satisfies `is_under_piketype_dir` via the path component `piketype/`). Without the fix, `find_piketype_modules` would have returned both, and `check_duplicate_basenames` would have raised the original error.

## Commands Executed

```
cd $SANITY && /Users/ezchi/Projects/pike-type/.venv/bin/piketype gen myapp/piketype/types.py
```

Result: `EXIT: 0`. No "requires unique module basenames" message. `gen/` tree was produced normally:
```
gen/
  sv/myapp/...
  py/myapp/...
  cpp/myapp/...
  piketype_manifest.json
  sv/runtime/  py/runtime/  cpp/runtime/
```

## Direct scanner check

```
.venv/bin/python -c "
from pathlib import Path
from piketype.discovery.scanner import find_piketype_modules
result = find_piketype_modules(Path('$SANITY'))
for p in result:
    print('FOUND:', p.relative_to('$SANITY'))
print('TOTAL:', len(result))
"
```

Output:
```
FOUND: myapp/piketype/types.py
TOTAL: 1
```

The venv duplicate is excluded; only the real DSL module is returned. AC-1 confirmed at the live-code integration level (in addition to the unit test).

## Result

AC-2 satisfied: `piketype gen` exits 0 with a `.venv/lib/.../piketype/types.py` duplicate present in the repo root, and emits no "requires unique module basenames" error.

## Cleanup

Both temp dirs (`tmp.noH2q3J8lh`, `tmp.rxk07cGRST`) removed.

## Key Implementation Decisions
- Used the proper CLI entrypoint `.venv/bin/piketype gen <path>` (not `python -m piketype`, which fails because the package has no `__main__`).
- `touch .git` (empty file, not a real git directory) is the cheapest way to satisfy `find_repo_root`'s `(candidate / ".git").exists()` check; using `pyproject.toml` would also work but a single empty file is clearer.
- Cross-checked at two levels: the CLI exit code (AC-2) AND the direct `find_piketype_modules` call (AC-1 integration sentinel).

## Deviations from Plan
- The plan suggested skipping T5 if T2's `test_excludes_venv_duplicate` covered the scenario at unit level. I ran T5 anyway because the cost was low and the manual repro provides higher-confidence evidence that the duplicate-basename validation downstream is also unaffected.

## Tests Added
- None — this is a manual gate.
