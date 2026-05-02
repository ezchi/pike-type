# Gauge Code Review — Task 1, Iteration 1

You are the **Gauge** in a strict dual-agent Forge-Gauge implementation loop. The Forge has implemented Task 1 of spec `015-scanner-exclude-venv-dirs`. Critically code-review the implementation.

## Task Description

**Title:** Add EXCLUDED_DIRS constant and exclusion predicate to scanner.py

**From `tasks.md` T1:** Modify `src/piketype/discovery/scanner.py` to add a module-level `EXCLUDED_DIRS: frozenset[str]` constant and a new filter predicate inside `find_piketype_modules` that rejects any path whose relative-to-`repo_root` parts intersect `EXCLUDED_DIRS`.

**Must satisfy:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8.

## Spec excerpts (load and read for full context)

- Spec: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/spec.md`
- Plan: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/plan.md`
- Tasks: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/tasks.md`
- Forge artifact for this task: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/artifacts/implementation/task1-iter1-forge.md`
- Constitution: `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

Specifically:
- **FR-3** mandates EXCLUDED_DIRS contains EXACTLY the six entries `{".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}` — no more, no fewer.
- **FR-7** mandates the return value remains a sorted `list[Path]`.
- **FR-8** forbids any change to `is_under_piketype_dir` or `ensure_cli_path_is_valid`.
- **NFR-1** requires the `rglob` post-filter strategy (not `Path.walk()` pruning).
- **Constitution §Coding Standards Python:** `from __future__ import annotations`, `UPPER_SNAKE_CASE` for module constants, `basedpyright` strict-mode clean.

## Code under review — full content of `src/piketype/discovery/scanner.py` after the change

```python
"""Filesystem scanning for piketype modules."""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError
from piketype.paths import GEN_DIRNAME


EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}
)


def is_under_piketype_dir(path: Path) -> bool:
    """Return whether the path lives under a directory named ``piketype``."""
    return "piketype" in path.parts


def ensure_cli_path_is_valid(path: Path) -> None:
    """Validate that the CLI path is a concrete DSL module path."""
    if path.suffix != ".py":
        raise PikeTypeError(f"expected a Python file path, got {path}")
    if path.name == "__init__.py":
        raise PikeTypeError(f"{path} is not a valid piketype module")
    if not is_under_piketype_dir(path):
        raise PikeTypeError(f"{path} is not under a piketype/ directory")


def find_piketype_modules(repo_root: Path) -> list[Path]:
    """Return all DSL module files under piketype/ directories."""
    def _included(path: Path) -> bool:
        if path.name == "__init__.py":
            return False
        rel = path.relative_to(repo_root)
        rel_parts = set(rel.parts)
        if rel_parts & EXCLUDED_DIRS:
            return False
        if GEN_DIRNAME in rel_parts:
            return False
        return is_under_piketype_dir(rel)

    return sorted(path for path in repo_root.rglob("*.py") if _included(path))
```

## Diff (forge commit, HEAD~1..HEAD)

```diff
diff --git a/src/piketype/discovery/scanner.py b/src/piketype/discovery/scanner.py
index 33bad92..e3f01d7 100644
--- a/src/piketype/discovery/scanner.py
+++ b/src/piketype/discovery/scanner.py
@@ -8,6 +8,11 @@ from piketype.errors import PikeTypeError
 from piketype.paths import GEN_DIRNAME


+EXCLUDED_DIRS: frozenset[str] = frozenset(
+    {".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}
+)
+
+
 def is_under_piketype_dir(path: Path) -> bool:
     """Return whether the path lives under a directory named ``piketype``."""
     return "piketype" in path.parts
@@ -25,10 +30,15 @@ def ensure_cli_path_is_valid(path: Path) -> None:

 def find_piketype_modules(repo_root: Path) -> list[Path]:
     """Return all DSL module files under piketype/ directories."""
-    return sorted(
-        path
-        for path in repo_root.rglob("*.py")
-        if path.name != "__init__.py"
-        and GEN_DIRNAME not in path.relative_to(repo_root).parts
-        and is_under_piketype_dir(path.relative_to(repo_root))
-    )
+    def _included(path: Path) -> bool:
+        if path.name == "__init__.py":
+            return False
+        rel = path.relative_to(repo_root)
+        rel_parts = set(rel.parts)
+        if rel_parts & EXCLUDED_DIRS:
+            return False
+        if GEN_DIRNAME in rel_parts:
+            return False
+        return is_under_piketype_dir(rel)
+
+    return sorted(path for path in repo_root.rglob("*.py") if _included(path))
```

## Tests

No tests added in Task 1 (Task 2 introduces `tests/test_scanner.py` separately). The Gauge MUST evaluate Task 1 in isolation: code-correctness review only, no "missing tests" complaint — Task 2 is the test task.

## Review criteria

1. **Correctness**: Does the new code correctly implement FR-1 (excluded-dir intersection), FR-3 (exactly the six entries, byte-equal), FR-4 (preserve existing __init__/GEN_DIRNAME/piketype-ancestor rules), FR-5 (exact directory-component name match, case-sensitive), FR-6 (relative-to-`repo_root` parts only), FR-7 (sorted list[Path]), FR-8 (`is_under_piketype_dir` and `ensure_cli_path_is_valid` byte-for-byte unchanged)?
2. **Constitution compliance**: `from __future__ import annotations` (yes — line 3); `UPPER_SNAKE_CASE` for module constant (yes — `EXCLUDED_DIRS`); will `basedpyright` strict be clean on this file?
3. **Code quality**: Is the nested `_included` helper an appropriate refactor for hoisting `rel`, or is it over-engineering for what could have been a one-line addition to the comprehension? Is the type annotation `frozenset[str]` correct under Python 3.12+?
4. **Security**: any path-traversal risk introduced? (Note: `relative_to` raises if `path` is not under `repo_root`, but `rglob` only returns descendants of `repo_root`, so this is safe.)
5. **Error handling**: any swallowed exceptions? (Note: `relative_to` could raise; this was the case before this change too — no new exposure.)
6. **No scope creep**: did the implementation stay within the task? Specifically, were `is_under_piketype_dir` and `ensure_cli_path_is_valid` left byte-identical?
7. **Performance**: NFR-1 — is the rglob post-filter strategy preserved (not converted to Path.walk pruning)? Is the per-file cost reasonable?

## Important

- Constitution is highest authority.
- Do NOT raise "Path.walk() would be faster" as BLOCKING; clarification C-2 settled this against your suggestion in earlier stages.
- Do NOT raise "extend EXCLUDED_DIRS" as BLOCKING; clarification C-1 settled this.
- Do NOT raise "missing tests" — Task 2 covers tests.
- Be strict on FR-8 (`is_under_piketype_dir` / `ensure_cli_path_is_valid` byte-identical).
- Do NOT propose alternative implementations as BLOCKING unless the current code is incorrect; style-only suggestions belong as NOTE.

## Output

### Issues
**BLOCKING / WARNING / NOTE**, file:line cites where possible.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
