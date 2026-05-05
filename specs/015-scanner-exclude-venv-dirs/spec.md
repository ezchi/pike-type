# Specification: Scanner excludes virtual-env and other non-source directories

**Spec ID:** 015-scanner-exclude-venv-dirs
**Branch:** feature/015-scanner-exclude-venv-dirs
**Status:** Clarified (post-Clarification iteration 2)

## Overview

`piketype.discovery.scanner.find_piketype_modules` walks `repo_root.rglob("*.py")` and accepts any `.py` file whose path parts contain `"piketype"`. It does not skip well-known non-source directories. When a project has piketype installed inside a virtual environment at `.venv/lib/python3.13/site-packages/piketype/`, the scanner returns those installed-package files alongside the project's real DSL modules. The repo-wide unique-basename validation (Constitution Constraint 4) then fires with:

> piketype requires unique module basenames across the repo, but duplicates were found: ...

This blocks `piketype gen` for any user who runs the CLI from a checkout that contains a populated `.venv/`. The fix adds a fixed exclusion list of non-source directory names to `find_piketype_modules` so the scanner does not descend into them.

## Background

- `find_piketype_modules` is invoked unconditionally by `piketype gen` (`src/piketype/commands/gen.py:36`).
- The duplicate-basename validation is mandated by the Project Constitution (§Constraints, item 4) and runs on every invocation. It is correct; the bug is in scanning, not in validation.
- Today the scanner has only three exclusion rules: skip files named `__init__.py`, skip paths whose parts contain `GEN_DIRNAME` (`gen`), and require `piketype` somewhere in the relative path parts.

## User Stories

- **US-1.** As a piketype developer with a populated `.venv/` (containing piketype installed as a dependency or in editable mode), I want `piketype gen` to ignore the venv copy of piketype, so that I do not get spurious "duplicate basename" errors when running the CLI from my checkout.
- **US-2.** As a piketype developer with `__pycache__/` directories scattered throughout my source tree (from prior `python -m` invocations), I want the scanner to skip them, so that compiled bytecode caches cannot pollute discovery.
- **US-3.** As a maintainer reading the scanner code, I want the exclusion list to be a named module-level constant, so that the rationale is discoverable and the list is easy to extend.

## Functional Requirements

- **FR-1.** `find_piketype_modules(repo_root)` MUST exclude any `.py` file whose path, expressed relative to `repo_root`, contains a directory component whose name appears in the EXCLUDED_DIRS set.
- **FR-2.** EXCLUDED_DIRS MUST be defined as a module-level `frozenset[str]` constant in `src/piketype/discovery/scanner.py`.
- **FR-3.** EXCLUDED_DIRS MUST contain **exactly** these six entries (no more, no fewer): `".venv"`, `"venv"`, `".git"`, `"node_modules"`, `".tox"`, `"__pycache__"`. Future extension is an explicit follow-up decision, not silent scope creep.
- **FR-4.** The new exclusion check MUST be applied in addition to (not in place of) the existing rules: skip `__init__.py`, skip paths containing `GEN_DIRNAME`, require a `piketype` directory ancestor.
- **FR-5.** The matching MUST be by exact directory-component name (case-sensitive equality on a single path component). Substring matching, glob expansion, and case-insensitive matching are NOT permitted (e.g. a file at `repo_root/.venvy/foo.py` is NOT excluded, but `repo_root/.venv/foo.py` is).
- **FR-6.** The check MUST operate on the path relative to `repo_root`, so an excluded directory name appearing in the absolute path *above* `repo_root` (e.g. the user's home directory contains a `.git/`) MUST NOT cause exclusion.
- **FR-7.** The scanner's return value MUST remain a sorted `list[Path]` (existing contract preserved).
- **FR-8.** `is_under_piketype_dir` and `ensure_cli_path_is_valid` are NOT in scope and MUST be left unchanged. The `ensure_cli_path_is_valid` function operates on a user-supplied CLI path and is intentionally permissive about ancestor directories.

## Non-Functional Requirements

- **NFR-1.** No measurable performance regression in `piketype gen` end-to-end runtime versus the current scanner on a typical project (no populated `.venv` adjacent to the source tree). The implementation MUST use the `rglob` post-filter strategy: keep the existing `repo_root.rglob("*.py")` walk and add the excluded-directory check as an additional filter predicate alongside the existing checks. The Python 3.12+ `pathlib.Path.walk()` pruning approach is explicitly out of scope for this fix (see clarification C-2); it may be revisited if scan time becomes a measured problem.
- **NFR-2.** Determinism preserved: scanner output remains stable across runs given identical input.
- **NFR-3.** basedpyright strict mode MUST continue to pass with zero new errors in `scanner.py`.
- **NFR-4.** No new runtime dependencies (Constitution: Jinja2 only).

## Acceptance Criteria

- **AC-1.** Given a temp repo containing both `src/piketype/example/foo.py` and `.venv/lib/python3.13/site-packages/piketype/example/foo.py`, `find_piketype_modules(repo_root)` returns exactly the `src/piketype/example/foo.py` path; the venv copy is absent from the result.
- **AC-2.** Given the same repo, `piketype gen` does NOT raise the "requires unique module basenames" error.
- **AC-3.** Given a repo whose only piketype DSL module is at `src/piketype/foo.py` and which contains no excluded directories, `find_piketype_modules` returns `[<repo_root>/src/piketype/foo.py]` (no behavior change for the happy path).
- **AC-4.** Any `.py` path whose relative-to-`repo_root` parts contain ANY directory component listed in EXCLUDED_DIRS is excluded from the result, unconditionally. Specifically: a hypothetical file at `repo_root/.git/piketype/foo.py` is NOT returned, even though it satisfies the `is_under_piketype_dir` rule. Excluded-directory filtering takes precedence over every other rule that would otherwise admit a file.
- **AC-5.** Given a repo with `.venv/`, `__pycache__/`, `node_modules/`, `.tox/`, `.git/`, and `venv/` directories all containing nested `piketype/` paths with `.py` files, `find_piketype_modules` returns an empty list (assuming no real source modules exist).
- **AC-6.** A new **focused unit test** for `find_piketype_modules` is added under `tests/`, using `unittest.TestCase` and `tempfile.TemporaryDirectory()` (no pytest fixtures, no parametrize). The unit test MUST cover at least AC-1 (venv duplicate excluded) and AC-5 (all six excluded dir names rejected). Pre-existing integration tests continue to pass without modification. An additional negative-path integration test for AC-2 is OPTIONAL and may be added if the implementer judges it adds diagnostic value.
- **AC-7.** `basedpyright` strict mode reports zero errors on the modified `scanner.py`.

## Out of Scope

- **OOS-1.** Modifying the duplicate-basename validation itself. The validation is correct and required by the Constitution.
- **OOS-2.** Making EXCLUDED_DIRS configurable via CLI flag, environment variable, `pyproject.toml`, or `.gitignore` parsing. This change ships a fixed list.
- **OOS-3.** Honoring `.gitignore` patterns generally. This is a well-known scanning concern, but is deferred.
- **OOS-4.** Excluding hidden directories (anything starting with `.`) wholesale. The list is explicit; we do not sweep all dotfiles.
- **OOS-5.** Refactoring `is_under_piketype_dir`, `ensure_cli_path_is_valid`, or callers in `commands/gen.py`.
- **OOS-6.** Changes to `paths.GEN_DIRNAME` handling.
- **OOS-7.** Resolving symlinks before the excluded-directory check. A symlink in `repo_root` that points to a path physically under an excluded directory name (e.g., `repo_root/extlib -> /opt/projectx/.venv/...`) will NOT be excluded by this fix; only directly named `.venv/`, `__pycache__/`, etc. inside `repo_root` are filtered. See clarification C-3.

## Open Questions

(All open questions resolved in Clarification iteration 1. See `clarifications.md`.)

## Risks

- **R-1.** A real piketype DSL module legitimately placed under a path component named `__pycache__` (etc.) would be silently ignored. This is judged extremely unlikely given Python conventions, and intentional given the explicit scope of the fix.
- **R-2.** A user with a checkout layout like `<repo>/.git/<…>/piketype/<…>/foo.py` (e.g. submodule weirdness) would observe a behavior change. Treated as desirable: `.git` should never be a source root.

## References

- `src/piketype/discovery/scanner.py:26` — `find_piketype_modules`
- `src/piketype/commands/gen.py:36` — sole caller in production
- `src/piketype/paths.py:8` — `GEN_DIRNAME = "gen"`
- Project Constitution, §Constraints item 4 — unique basename validation requirement

## Changelog

- [Clarification iter1] FR-3: tightened from "at minimum these six entries" to "exactly these six entries" — user explicitly enumerated six, scope is fixed (C-1).
- [Clarification iter1] NFR-1: pinned implementation strategy to the `rglob` post-filter; `pathlib.Path.walk()` pruning is out of scope for this fix (C-2).
- [Clarification iter1] AC-6: tightened test requirement to a focused `unittest.TestCase` unit test covering AC-1 and AC-5; an integration test for AC-2 is optional, not required (C-4).
- [Clarification iter1] Q-1, Q-2: removed (resolved by C-1 and C-2).
- [Clarification iter2] OOS-7: added; symlinks pointing into excluded paths are NOT resolved by this fix (C-3, promoted from [NO SPEC CHANGE] to [SPEC UPDATE] per Gauge iter1 WARNING).
