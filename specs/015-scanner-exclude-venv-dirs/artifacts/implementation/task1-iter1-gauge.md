# Gauge Code Review — Task 1, Iteration 1

**Reviewer:** gemini (gemini-3.1-pro-preview via gemini CLI 0.40.1)
**Under review:** `src/piketype/discovery/scanner.py` (forge commit `22cdf01`)

### Issues

None.

### Analysis

1.  **Correctness (FR-1 to FR-6)**:
    *   The `EXCLUDED_DIRS` constant contains exactly the six mandated entries (`{".venv", "venv", ".git", "node_modules", ".tox", "__pycache__"}`).
    *   The `_included` helper correctly implements the intersection check against `rel_parts`, ensuring that any path with an ancestor in `EXCLUDED_DIRS` is rejected (FR-1, FR-6).
    *   Existing rules for `__init__.py`, `GEN_DIRNAME`, and `piketype` directory requirements are preserved (FR-4).
    *   The `set(rel.parts)` intersection with `frozenset[str]` ensures exact, case-sensitive directory name matching (FR-5).
2.  **Interface Integrity (FR-7, FR-8)**:
    *   The return value of `find_piketype_modules` remains a sorted `list[Path]` (FR-7).
    *   `is_under_piketype_dir` and `ensure_cli_path_is_valid` are byte-for-byte identical to the original implementation (FR-8).
3.  **Constitution & Standards**:
    *   `from __future__ import annotations` is present on line 3.
    *   `EXCLUDED_DIRS` follows `UPPER_SNAKE_CASE` for module constants.
    *   `_included` is a private helper correctly prefixed with `_`.
    *   The use of `frozenset[str]` and `set` operations is idiomatic and compatible with `basedpyright` strict mode.
4.  **Performance (NFR-1)**:
    *   The `rglob("*.py")` strategy is maintained, with filtering performed in a post-scan pass as mandated.

VERDICT: APPROVE
