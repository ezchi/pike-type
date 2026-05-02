# Task 6: Add positive smoke fixture (`type_id` near-miss) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_near_miss/project/.git/HEAD` — new (fake repo-root marker matching existing fixture convention; contents `ref: refs/heads/main`).
- `tests/fixtures/keyword_near_miss/project/alpha/piketype/types.py` — new. Defines `near_miss_t` struct with two fields (`type_id`, `payload`) — `type_id` is the substring near-miss for AC-7.
- `tests/goldens/gen/keyword_near_miss/...` — new. 13 generated files captured from a clean `piketype gen` run against the fixture (SV pkg + test_pkg, C++ header, Python module, runtime support files, manifest).

## Key Implementation Decisions

- **Two-field struct.** Existing structural rule rejects empty structs; included `payload` as a non-keyword sibling so the focus stays on `type_id`.
- **`.git/HEAD` marker.** Existing fixtures use this convention (verified against `tests/fixtures/struct_sv_basic/project/.git/HEAD`). The piketype loader walks upward looking for `.git` or `pyproject.toml` to mark the repo root. Without this, `piketype gen` errors out with "could not find repo root."
- **Golden capture.** Generated under `tempfile.TemporaryDirectory()` per the existing test convention (otherwise the cross-fixture basename-uniqueness check fires across all repo fixtures). Captured byte-for-byte into `tests/goldens/gen/keyword_near_miss/`.

## Deviations from Plan

None substantive. The plan §Implementation Strategy / Commit B / "Add **one** positive smoke fixture" is implemented as written.

## Tests Added

The smoke test itself is in T-007 (`test_keyword_near_miss_type_id_passes`); this task creates the fixture+golden it consumes.
