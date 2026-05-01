# Commit B — Forge Artifact (Tasks T7-T11)

Repo-wide type index plumbing across all three backends.

## Files Changed

- `src/piketype/ir/repo_index.py` — created. `build_repo_type_index(repo)` returns `dict[(module_python_name, type_name), TypeDefIR]`.
- `tests/test_repo_index.py` — created. 4 unit tests: empty repo, single module, multi-module same-name distinct keys, multiple type kinds indexed.
- `src/piketype/backends/sv/emitter.py` — modified. Calls `build_repo_type_index(repo)` once and passes through.
- `src/piketype/backends/sv/view.py` — modified. All `TypeRefIR` resolutions now use `(module.python_module_name, name)` keying.
- `src/piketype/backends/py/emitter.py` — modified. Same pattern.
- `src/piketype/backends/py/view.py` — modified. Same pattern.
- `src/piketype/backends/cpp/emitter.py` — modified. Same pattern.
- `src/piketype/backends/cpp/view.py` — modified. Same pattern.

## Key Implementation Decisions

- **Backward-compatible signature.** Each `build_*_module_view` takes `repo_type_index` as a keyword argument with default `None`. When `None`, a single-module fallback index is constructed from the input module's types. This keeps the public API stable for the `tests/test_view_*.py` callers (which build a single-module view independently of an emitter run).
- **Lookup key.** `(module.python_module_name, type_name)` matches the key already used by `validate/engine.py:19-23`, so no new keying scheme.
- **Same-module byte-parity preserved.** For same-module `TypeRefIR.module` already equals the current module's `ModuleRefIR`, so keyed lookup returns the same `TypeDefIR` as the prior name-only `module.types` index. No existing fixture changes its output.

## Deviations from Plan

- **Module-local shortcut retained as fallback.** The plan said "remove the module-local shortcut wherever a `TypeRefIR` is dereferenced." All shortcut uses for `TypeRefIR` lookups have been removed; the shortcut now exists only as the `repo_type_index=None` fallback in the public `build_*_module_view` entry points. This allows test helpers that don't have a full `RepoIR` to keep working; the production emitters always pass a real index.

## Tests Added

- `tests/test_repo_index.py::BuildRepoTypeIndexTests::test_empty_repo_returns_empty_index`
- `tests/test_repo_index.py::BuildRepoTypeIndexTests::test_single_module_with_one_type`
- `tests/test_repo_index.py::BuildRepoTypeIndexTests::test_multi_module_same_type_name_distinct_keys`
- `tests/test_repo_index.py::BuildRepoTypeIndexTests::test_multiple_type_kinds_indexed`

## Integration Check (T11)

- `uv run python -m unittest discover tests/` — **259 tests, 0 failures, 1 skipped** (perf gate). All pre-existing fixtures byte-identical.
- `uv run basedpyright src/piketype/ir/repo_index.py src/piketype/backends/{sv,py,cpp}/{emitter,view}.py tests/test_repo_index.py` — improvement: 9 → 7 errors in `src/piketype/backends/sv/view.py` (the remaining 7 are pre-existing unused-import / `# type: ignore`-marked functions).
