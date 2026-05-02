# Specification: Scanner excludes virtual-env and other non-source directories

**Spec ID:** 015-scanner-exclude-venv-dirs
**Branch:** feature/015-scanner-exclude-venv-dirs
**Status:** Draft (Forge iteration 2)

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
- **FR-3.** EXCLUDED_DIRS MUST contain at minimum these six entries: `".venv"`, `"venv"`, `".git"`, `"node_modules"`, `".tox"`, `"__pycache__"`.
- **FR-4.** The new exclusion check MUST be applied in addition to (not in place of) the existing rules: skip `__init__.py`, skip paths containing `GEN_DIRNAME`, require a `piketype` directory ancestor.
- **FR-5.** The matching MUST be by exact directory-component name (case-sensitive equality on a single path component). Substring matching, glob expansion, and case-insensitive matching are NOT permitted (e.g. a file at `repo_root/.venvy/foo.py` is NOT excluded, but `repo_root/.venv/foo.py` is).
- **FR-6.** The check MUST operate on the path relative to `repo_root`, so an excluded directory name appearing in the absolute path *above* `repo_root` (e.g. the user's home directory contains a `.git/`) MUST NOT cause exclusion.
- **FR-7.** The scanner's return value MUST remain a sorted `list[Path]` (existing contract preserved).
- **FR-8.** `is_under_piketype_dir` and `ensure_cli_path_is_valid` are NOT in scope and MUST be left unchanged. The `ensure_cli_path_is_valid` function operates on a user-supplied CLI path and is intentionally permissive about ancestor directories.

## Non-Functional Requirements

- **NFR-1.** No measurable performance regression in `piketype gen` end-to-end runtime versus the current scanner on a typical project (no populated `.venv` adjacent to the source tree). The spec does NOT prescribe an implementation strategy: post-filtering an `rglob` walk and pruning via `os.walk` / `pathlib.Path.walk()` are both acceptable, provided the observable behavior matches the FRs and ACs. Implementations that traverse into excluded directories before discarding their contents are permitted but discouraged where pruning is straightforward; the implementer makes the call (see Q-3).
- **NFR-2.** Determinism preserved: scanner output remains stable across runs given identical input.
- **NFR-3.** basedpyright strict mode MUST continue to pass with zero new errors in `scanner.py`.
- **NFR-4.** No new runtime dependencies (Constitution: Jinja2 only).

## Acceptance Criteria

- **AC-1.** Given a temp repo containing both `src/piketype/example/foo.py` and `.venv/lib/python3.13/site-packages/piketype/example/foo.py`, `find_piketype_modules(repo_root)` returns exactly the `src/piketype/example/foo.py` path; the venv copy is absent from the result.
- **AC-2.** Given the same repo, `piketype gen` does NOT raise the "requires unique module basenames" error.
- **AC-3.** Given a repo whose only piketype DSL module is at `src/piketype/foo.py` and which contains no excluded directories, `find_piketype_modules` returns `[<repo_root>/src/piketype/foo.py]` (no behavior change for the happy path).
- **AC-4.** Any `.py` path whose relative-to-`repo_root` parts contain ANY directory component listed in EXCLUDED_DIRS is excluded from the result, unconditionally. Specifically: a hypothetical file at `repo_root/.git/piketype/foo.py` is NOT returned, even though it satisfies the `is_under_piketype_dir` rule. Excluded-directory filtering takes precedence over every other rule that would otherwise admit a file.
- **AC-5.** Given a repo with `.venv/`, `__pycache__/`, `node_modules/`, `.tox/`, `.git/`, and `venv/` directories all containing nested `piketype/` paths with `.py` files, `find_piketype_modules` returns an empty list (assuming no real source modules exist).
- **AC-6.** A new automated test under `tests/` exercises AC-1 (or an equivalent) via the same fixture-and-subprocess pattern used by other golden tests, OR a focused unit test on `find_piketype_modules`. Pre-existing integration tests continue to pass without modification.
- **AC-7.** `basedpyright` strict mode reports zero errors on the modified `scanner.py`.

## Out of Scope

- **OOS-1.** Modifying the duplicate-basename validation itself. The validation is correct and required by the Constitution.
- **OOS-2.** Making EXCLUDED_DIRS configurable via CLI flag, environment variable, `pyproject.toml`, or `.gitignore` parsing. This change ships a fixed list.
- **OOS-3.** Honoring `.gitignore` patterns generally. This is a well-known scanning concern, but is deferred.
- **OOS-4.** Excluding hidden directories (anything starting with `.`) wholesale. The list is explicit; we do not sweep all dotfiles.
- **OOS-5.** Refactoring `is_under_piketype_dir`, `ensure_cli_path_is_valid`, or callers in `commands/gen.py`.
- **OOS-6.** Changes to `paths.GEN_DIRNAME` handling.

## Open Questions

- **Q-1.** Should the EXCLUDED_DIRS list also include `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `dist`, `build`, `.eggs`, or other Python/tooling caches not in the user's original six? Broader coverage is plausibly desirable (none of those should ever contain real DSL modules) but the user explicitly listed only the six entries in FR-3. [NEEDS CLARIFICATION — ship exactly the six, or extend?]
- **Q-2.** Should the exclusion be enforced via `pathlib.Path.walk()` (Python 3.12+) or `os.walk(..., followlinks=False)` with in-place pruning of `dirnames` instead of `rglob` followed by post-filtering? Pruning avoids descending into massive `.venv` / `node_modules` trees and is materially faster on real-world venvs. The user-supplied minimal patch keeps `rglob` for change-size reasons. NFR-1 leaves the choice to the implementer. [NEEDS CLARIFICATION — does the user want the minimal `rglob` patch, or the pruning rewrite?]

## Risks

- **R-1.** A real piketype DSL module legitimately placed under a path component named `__pycache__` (etc.) would be silently ignored. This is judged extremely unlikely given Python conventions, and intentional given the explicit scope of the fix.
- **R-2.** A user with a checkout layout like `<repo>/.git/<…>/piketype/<…>/foo.py` (e.g. submodule weirdness) would observe a behavior change. Treated as desirable: `.git` should never be a source root.

## References

- `src/piketype/discovery/scanner.py:26` — `find_piketype_modules`
- `src/piketype/commands/gen.py:36` — sole caller in production
- `src/piketype/paths.py:8` — `GEN_DIRNAME = "gen"`
- Project Constitution, §Constraints item 4 — unique basename validation requirement
