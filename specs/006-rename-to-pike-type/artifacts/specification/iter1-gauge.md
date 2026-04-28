# Gauge Review — Iteration 1

## Issues

**BLOCKING** Open questions contradict requirements. FR-12/FR-13 require updating `docs/` and `.steel/constitution.md`, but Open Questions ask whether to update `docs/rfc-v1.md` and the constitution. Decide this before implementation. `docs/rfc-v1.md` is also the package readme in `pyproject.toml`, so treating it as untouched history is not neutral.

**BLOCKING** AC-3 violates the constitution. The spec requires `python3 -m pytest`, but the constitution says the test runner is `unittest`. Use the unittest command as the primary gate.

**BLOCKING** The "no stale references" gate is internally inconsistent. NFR-3 says repo-wide grep excluding `.git/`, `.steel/`, `specs/`; AC-4 only checks `src/ tests/ pyproject.toml README.md`, missing `docs/` and `uv.lock`. Also `tests/fixtures/**/__pycache__/*.pyc` can make `grep -ri "typist" tests/` fail. The spec must define whether to delete caches, exclude binaries, and update lockfiles.

**BLOCKING** Public symbol rename is unspecified. `TypistError` exists and must be renamed to satisfy case-insensitive no-stale rules, but the spec never says whether the new class is `PiketypeError`, `PikeTypeError`, or something else.

**BLOCKING** Fixture migration is incomplete. FR-9 only mentions `alpha/typist` and `beta/typist` directory segments. It does not specify fixture module imports like `from typist.dsl import ...`, the negative fixture `outside_typist/not_typist`, or expected renamed error text. Implementers would have to guess.

**WARNING** US-2 says `import piketype` must work, but no acceptance criterion verifies it. Add an explicit import check and, because aliases are out of scope, preferably verify `import typist` is not retained.

**WARNING** The version requirement is unclear. The spec says version remains `0.2.0`, but `src/typist/__init__.py` exposes `__version__` and manifests use that value. Clarify whether this rename must align runtime `__version__` and golden manifest `tool_version`.

VERDICT: REVISE
