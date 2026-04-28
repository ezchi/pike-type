# Gauge Review — Spec 006: Rename Repository to pike-type (Iteration 2)

You are a specification reviewer (Gauge). This is iteration 2 — the spec has been revised to address BLOCKING feedback from iteration 1.

## Changes from Iteration 1

1. **Resolved contradictory open questions**: Removed Open Questions section entirely. FR-13 now explicitly lists all docs files to update including `docs/rfc-v1.md` (which is the pyproject.toml readme). FR-14 explicitly requires updating `.steel/constitution.md`.
2. **Fixed AC-3 test runner**: AC-3 now uses `python3 -m unittest discover -s tests` as the primary gate (per constitution), with `python3 -m pytest` as secondary.
3. **Harmonized NFR-3 and AC-4**: Both now check `src/`, `tests/`, `pyproject.toml`, `README.md`, `docs/`, `.steel/constitution.md`. Explicitly excludes `.git/`, `specs/`, `uv.lock`, and binary files. Requires deleting `__pycache__` dirs before the check.
4. **Added FR-9 for public symbol rename**: `TypistError` → `PikeTypeError` with explicit guidance on all call sites.
5. **Expanded FR-10 fixture migration**: Now covers `outside_typist/not_typist` → `outside_piketype/not_piketype`, fixture DSL imports, and `__pycache__` deletion.
6. **Added AC-11**: Verifies `import piketype` works.
7. **Added AC-12**: Verifies `PikeTypeError` is the base exception.
8. **Added FR-16**: `uv.lock` regeneration.
9. **Clarified version**: FR-15 explicitly states `__version__` stays at current value; version bump is out of scope.

## Project Constitution (Authority — highest priority)

Key constitutional rules:
- Test runner: unittest (stdlib), golden-file / fixture-based integration tests
- CLI framework: argparse
- Branch naming: `feature/<name>` from `develop`
- Conventional Commits format
- basedpyright strict mode, zero errors
- Frozen dataclasses for IR, mutable for DSL

## Specification to Review

Read the specification at: /Users/ezchi/Projects/typist/specs/006-rename-to-pike-type/spec.md

## Review Criteria

1. **Completeness**: Are all areas requiring changes identified? Are there missing functional requirements?
2. **Clarity**: Is each requirement unambiguous? Can an implementer follow it without guessing?
3. **Testability**: Can each acceptance criterion be verified mechanically?
4. **Consistency**: Do the naming conventions hold throughout? Are there contradictions?
5. **Feasibility**: Are there technical risks or ordering challenges?
6. **Constitution Alignment**: Does the spec respect the project's governing principles?

## Required Output Format

List issues with severity levels:
- **BLOCKING**: Must be fixed before implementation can proceed
- **WARNING**: Should be fixed but won't prevent implementation
- **NOTE**: Informational observation or minor suggestion

End your review with exactly one of:
- `VERDICT: APPROVE`
- `VERDICT: REVISE`
