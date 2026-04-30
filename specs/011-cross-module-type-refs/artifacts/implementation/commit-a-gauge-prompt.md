# Gauge Code Review — Commit A (Tasks T1-T6)

You are the **Gauge** in a Forge-Gauge dual-LLM implementation loop. The forge has implemented Commit A — loader isolation. Review the code for correctness, code quality, constitution compliance, security, error handling, test coverage, and scope.

## Context

- Spec: `specs/011-cross-module-type-refs/spec.md` — see FR-1 (lines 134-160) for the loader contract.
- Plan: `specs/011-cross-module-type-refs/plan.md` — see Components > Loader and Commit A.
- Tasks: `specs/011-cross-module-type-refs/tasks.md` T1-T6.
- Constitution: `.steel/constitution.md` — coding standards section (`from __future__ import annotations`, frozen dataclasses, snake_case, no wildcard imports, type union syntax `X | Y`, basedpyright strict).
- Forge artifact: `specs/011-cross-module-type-refs/artifacts/implementation/commit-a-forge.md`.

## Code to review

Run `git diff HEAD~1` (the just-landed forge commit) against the working directory, OR read these files directly:

- `src/piketype/loader/python_loader.py` (rewritten)
- `src/piketype/commands/gen.py` (modified)
- `tests/test_view_py.py` (modified — `_load_fixture_module` migration)
- `tests/test_view_cpp.py` (modified — same migration)
- `tests/test_view_sv.py` (modified — same migration)
- `tests/test_loader.py` (created)
- `tests/test_perf_gen.py` (created)

## Review checklist

For each task:

### T1: `prepare_run` and `load_or_get_module`

1. **FR-1 contract.** Does `prepare_run` snapshot originals, pop owned keys, yield, restore in `finally`? Are originals restored correctly when keys did or did not pre-exist?
2. **Owned-key set.** Does `_compute_owned_keys` include every dotted prefix of every discovered module name? Are namespace packages handled?
3. **Identity stability.** Does `load_or_get_module` reuse cached `sys.modules` entries to preserve `id()` across cross-module imports?
4. **Scope guard.** Does `load_or_get_module` raise `RuntimeError` when called outside `prepare_run`? When the requested module name is not in the owned set?
5. **Constitution compliance.** `from __future__ import annotations` present? `snake_case` naming? No wildcard imports? Module-level state (`_active_owned_keys`) acceptable for this contract?

### T2: `run_gen` migration

1. Does `run_gen` correctly enter `prepare_run` before the load loop and exit after `write_manifest`? All work that touches DSL objects must be inside the scope.
2. No `load_module_from_path` reference remains.

### T3: Test helper migration

1. Each `_load_fixture_module` helper enters `prepare_run` around its load loop and exits after returning the frozen module.
2. The return statement is inside the `with` block (so the module reference is captured before sys.modules cleanup — note: this is OK because the function returns `module_ir`, which is a frozen IR data structure that does not depend on sys.modules state).

### T4: `tests/test_loader.py`

1. Six tests cover: snapshot/restore, no-leak, sequential isolation, nested-raise, outside-scope-raise, repeated-call identity.
2. Tests use `unittest.TestCase` per repo convention (constitution requires `unittest`, not pytest).
3. Tests clean up `sys.modules` in `finally` blocks where they inject sentinels.

### T5: `tests/test_perf_gen.py`

1. Opt-in via env var; skips when baseline file absent.
2. Per-fixture and total budgets enforced.
3. Subprocess uses `uv run piketype gen <path>` matching the project's run pattern.

### T6: Integration check

1. Full test suite passes (the forge artifact claims 253 tests, 0 failures, 1 skipped).
2. basedpyright on changed files is clean (forge claims pre-existing 62 errors in `src/piketype` is unchanged).

## Output format

```
# Gauge Code Review — Commit A

## Summary
(2-3 sentences)

## Per-Task Verdict

For each task T1-T6:
- ✓ APPROVE (with brief justification)
- or ~ partial (explain) — task needs more work
- or ✗ REVISE (explain) — task has a defect

## Issues

### BLOCKING
- (issue with file:line and suggested fix)

### WARNING
- ...

### NOTE
- ...

## Strengths
- ...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If every task passes the per-task review AND no BLOCKING issue is present, APPROVE.

Save to `specs/011-cross-module-type-refs/artifacts/implementation/commit-a-gauge.md`.

Be strict. Cite file:line. Verify against source.
