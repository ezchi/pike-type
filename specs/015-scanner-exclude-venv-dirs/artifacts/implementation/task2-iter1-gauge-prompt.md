# Gauge Code Review — Task 2, Iteration 1

You are the **Gauge** in a strict dual-agent Forge-Gauge implementation loop. The Forge has implemented Task 2 (focused unit test for `find_piketype_modules`).

## Task Description

**Title:** Create focused unit test file `tests/test_scanner.py`

**From `tasks.md` T2:** Create a new `tests/test_scanner.py` containing four `unittest.TestCase` methods covering AC-1 (venv duplicate excluded), AC-3 (clean repo unchanged), AC-4 (excluded-dir filter beats `is_under_piketype_dir`), AC-5 (all six excluded names rejected), and FR-7 / NFR-2 (sorted output preserved). Use `tempfile.TemporaryDirectory()`. No pytest fixtures, no parametrize.

**Must satisfy:** AC-1, AC-3, AC-4, AC-5, AC-6, FR-7, NFR-2, AC-7 (basedpyright clean).

## Spec / plan / clarification reference

- Spec: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/spec.md`
- Plan: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/plan.md`
- Clarifications: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/clarifications.md`
- Forge artifact: `/Users/ezchi/Projects/pike-type/specs/015-scanner-exclude-venv-dirs/artifacts/implementation/task2-iter1-forge.md`
- Constitution: `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

Specifically, Clarification C-4 mandates a focused `unittest.TestCase` unit test using `tempfile.TemporaryDirectory()`; no pytest fixtures, no parametrize. Constitution §Testing prescribes `unittest.TestCase`.

## Code under review — full content of `tests/test_scanner.py`

```python
"""Tests for piketype.discovery.scanner.find_piketype_modules."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from piketype.discovery.scanner import find_piketype_modules


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


class FindPiketypeModulesTests(unittest.TestCase):
    """Cover the discovery scanner's exclusion behavior."""

    def test_excludes_venv_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "src" / "piketype" / "example" / "foo.py"
            venv_dup = (
                root
                / ".venv"
                / "lib"
                / "python3.13"
                / "site-packages"
                / "piketype"
                / "example"
                / "foo.py"
            )
            _touch(real)
            _touch(venv_dup)

            self.assertEqual(find_piketype_modules(root), [real])

    def test_all_six_excluded_names_rejected(self) -> None:
        excluded_names = (".venv", "venv", ".git", "node_modules", ".tox", "__pycache__")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in excluded_names:
                _touch(root / name / "piketype" / "foo.py")

            self.assertEqual(find_piketype_modules(root), [])

    def test_clean_repo_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "piketype" / "foo.py"
            _touch(target)

            self.assertEqual(find_piketype_modules(root), [target])

    def test_sorted_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zzz = root / "src" / "piketype" / "zzz.py"
            aaa = root / "src" / "piketype" / "aaa.py"
            _touch(zzz)
            _touch(aaa)

            result = find_piketype_modules(root)
            self.assertEqual(result, sorted(result))
            self.assertEqual(result, [aaa, zzz])


if __name__ == "__main__":
    unittest.main()
```

## Diff (forge commit, HEAD~1..HEAD)

The whole file was added in this commit. See above for content.

## Review criteria

1. **Correctness**: Does each test method correctly construct its fixture and make the right assertion? Specifically:
   - `test_excludes_venv_duplicate` — assert `== [real]` (not just absence of `venv_dup`); does this match AC-1?
   - `test_all_six_excluded_names_rejected` — does it construct one fixture per FR-3 entry, each under a `piketype/` ancestor (so `is_under_piketype_dir` would otherwise admit them)? Does the assertion `== []` correctly verify AC-5 + AC-4 (filter beats piketype-ancestor rule)?
   - `test_clean_repo_unchanged` — AC-3 sentinel.
   - `test_sorted_output` — FR-7 / NFR-2.
2. **Constitution compliance**:
   - `from __future__ import annotations` present (line 3).
   - `unittest.TestCase` (line 16).
   - No pytest fixtures, no parametrize, no `subTest` (per Clarification C-4).
   - `tempfile.TemporaryDirectory()` used.
3. **basedpyright strict**: Will this file pass with zero errors?
4. **Quality**:
   - Is the `_touch` helper appropriate (vs inlining)?
   - Are the assertions specific enough that a regression that returns a superset/subset is caught?
   - Are paths constructed in a portable way (`/` joining) — but is the test OS-portable for Linux/macOS only (acceptable; the project targets Unix-like)?
5. **No scope creep**: did the test file accidentally test things outside the FRs/ACs? (e.g., `EXCLUDED_DIRS` constant identity, internal helper functions). Tests should test the public API.
6. **Determinism**: `sorted(result)` — is the assertion `result == sorted(result)` rigorous, or could it pass tautologically?  Note the second assertion `result == [aaa, zzz]` provides explicit ground truth.
7. **Edge cases potentially missed**:
   - Should there be a test for a file directly at `repo_root/foo.py` (no `piketype` ancestor) being correctly excluded by the existing rule? — That's pre-existing behavior, NOT this fix's scope. The Gauge should NOT raise this as BLOCKING.
   - Should there be a test for `__init__.py` exclusion? — Also pre-existing behavior, not this fix's scope. Should NOT be raised as BLOCKING.

## Important

- Be strict and blunt.
- Do NOT raise pre-existing-behavior coverage gaps as BLOCKING.
- Do NOT push for parametrize / `subTest` — Clarification C-4 explicitly forbids them.
- Do NOT propose alternative test runner or fixture patterns.

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
