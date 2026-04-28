# Gauge Review — Iteration 2

## Issues

- **BLOCKING:** AC-4 is not mechanically valid as written. The plain `grep -ri` command does not exclude binary files or `__pycache__/`. Current tree also has `src/typist.egg-info/` under `src/`, which AC-4 will scan and the spec never says to delete or exclude. Fix AC-4/NFR-3 to use an exact command with exclusions, or explicitly require deleting stale egg-info and all relevant cache dirs before the check.

- **WARNING:** FR-13 says all docs must be updated, but the explicit list omits `docs/requirements.org`, while AC-4 scans all of `docs/`. That file currently contains `typist`. Add it explicitly or state that every file under `docs/` is included.

- **WARNING:** FR-15 freezes `__version__` at `0.1.0`, while `pyproject.toml` currently declares distribution version `0.2.0`. AC-11 only says "prints the version string," not which version contract matters. Clarify that package `piketype.__version__` remains `0.1.0` even though the distribution metadata remains `0.2.0`.

- **NOTE:** Repository name change to `pike-type` vs local checkout directory name. Clarify whether the local checkout directory name is in scope. If not, say repository rename means project/distribution naming only.

VERDICT: REVISE
