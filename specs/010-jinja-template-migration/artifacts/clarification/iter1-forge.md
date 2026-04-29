# Clarification — Iteration 1 Forge Output

## Inputs

- Specification: `specs/010-jinja-template-migration/spec.md` (post-specification, 4 open questions Q-1..Q-4).
- User decision (from `/steel-run-all` invocation with no overrides supplied): "accept all recommendations" for the four open questions.

## Resolutions Applied to spec.md

| Was  | Now   | Decision |
|------|-------|----------|
| Q-1  | CL-1  | Multiple contiguous commits per backend; squash-on-merge optional. |
| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
| Q-3  | CL-3  | No `PackageLoader` escape hatch; `pip install -e .` semantics accepted. |
| Q-4  | CL-4  | Baseline captured before first migration commit; stored in `perf.md`; authoritative. |

## New requirements introduced by clarification

- **FR-23.** Concrete CLI signature for `tools/perf_bench.py` (line-based output for table-row append).
- **FR-24.** `docs/templates.md` "Custom Filters" section with per-filter checklist.
- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.

## Sections preserved unchanged

- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.

## Why these decisions hold together

- CL-1 (multi-commit) + NFR-6 (revertability) compose: a contiguous range revert affects only one backend.
- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
- CL-3 (no escape hatch) + FR-2/FR-3 (single loader strategy) compose: one loader, one code path, one set of failure modes.
- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.
