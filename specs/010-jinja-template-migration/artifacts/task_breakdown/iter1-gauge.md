# Gauge Review — Task Breakdown Iteration 1 (Claude self-review)

**Gauge provider:** codex (configured) — rate limit until 2026-04-30 12:49Z. Falling back to Claude self-review per the steel-specify `claude` provider pattern. Tasks.md is derived from the already-codex-approved plan.md, so the bias risk is limited; codex iter1 plan review caught the major architectural flaws before tasks were written.

## Coverage check vs. plan.md

| Plan element | Task coverage |
|--------------|---------------|
| Phase 0 commit 1 (render.py + tests) | T-01 |
| Phase 0 commit 2 (check_templates) | T-02 |
| Phase 0 commit 3 (perf_bench) | T-03 |
| Phase 0 commit 4 (wheel packaging) | T-04 |
| Phase 0 commit 5 (docs/templates.md) | T-05 |
| Phase 0 commit 6 (baseline_ms) | T-06 |
| Phase 1 commits 1–7 | T-07..T-13 |
| Phase 2 commits 1–7 | T-14..T-20 |
| Phase 3 commits 1–7 | T-21..T-27 |
| Phase 4 (AC-F1..F8) | T-28..T-33 |
| Phase 5 retrospect | T-34 |

All plan commits map 1:1 to a task. Validation actions (T-28..T-32) collapse multiple AC checks into related tasks; only T-33 is a commit.

## FR / AC coverage

| FR/AC | Task |
|-------|------|
| FR-1 view-model module | T-07, T-14, T-21 |
| FR-2 environment config | T-01 |
| FR-3 render helper | T-01 |
| FR-4 emit signature unchanged | enforced across T-08..T-12, T-15..T-19, T-22..T-26 (no signature changes) |
| FR-5 migration order | enforced by task numbering Phase 1 → 2 → 3 |
| FR-6 sub-step order | T-08/T-09/T-10/T-11 (Py); T-15/T-16/T-17/T-18 (Cpp); T-22/T-23/T-24/T-25 (Sv) |
| FR-7 byte parity at end of each backend | T-12 / T-19 / T-26 cleanup commits |
| FR-8 view-model field types | T-07/T-14/T-21 |
| FR-9 view-model exclusions | T-07/T-14/T-21 (no `frozenset`/`dict`/IR-refs) |
| FR-10 templates no semantics | enforced by T-02 (lint) running after every commit |
| FR-11 indirection ≤ 2 levels | enforced by structure of `_macros.j2` (one indirection) |
| FR-12 templates layout | T-08, T-09, T-15, T-16, T-22, T-23 |
| FR-13 `.j2` extension, header via view field | T-07/T-14/T-21 |
| FR-14 wheel packaging | T-04, T-30 |
| FR-15 determinism (sorted tuple, no set) | enforced by T-07/T-14/T-21 builder code; covered by AC-7-* idempotency tests |
| FR-16 single-file env audit | T-01 |
| FR-17 basedpyright clean | enforced as exit criterion on every task |
| FR-18 view-model + builder file location | T-07/T-14/T-21 |
| FR-19 remove inline helpers | T-12, T-19, T-26 |
| FR-20 separate commit if golden bytes change | not exercised in this migration (parity preserved); documented in T-31 doc check |
| FR-21 lint script | T-02 |
| FR-22 docs | T-05 |
| FR-23 perf_bench | T-03 |
| FR-24 docs custom-filters section | T-05 |
| FR-25 perf.md schema | T-06, T-13, T-20, T-27, T-29 |
| NFR-1 perf gate | T-29 (AC-F4) |
| NFR-2 deps surface | enforced (no new deps; Jinja2 already declared) |
| NFR-3 determinism | covered by AC-7-* idempotency |
| NFR-4 type safety | exit criterion every task |
| NFR-5 auditability (single template + 1 macro layer) | enforced by FR-12 macro convention |
| NFR-6 reversibility | enforced by per-backend contiguous commit ranges; T-32 dry-run revert |
| NFR-7 stability of public API | enforced (emit_* signatures unchanged) |
| AC-1-Py..AC-7-Py | T-07..T-13 (full set, gate at T-13) |
| AC-1-Cpp..AC-7-Cpp | T-14..T-20 |
| AC-1-Sv..AC-7-Sv | T-21..T-27 |
| AC-F1 unit-test discover | T-28 |
| AC-F2 basedpyright | T-28 |
| AC-F3 lint exit 0 | T-28 |
| AC-F4 perf gate | T-29 |
| AC-F5 wheel install | T-30 |
| AC-F6 docs check | T-31 |
| AC-F7 audit form | T-28 (script identical to AC-F3) |
| AC-F8 commit/revert audit | T-32 |
| CL-1 multi-commit per backend | enforced by 7 tasks per backend phase |
| CL-2 filter location in render.py | T-01 |
| CL-3 no hot-reload escape | T-01 (PackageLoader-only) |
| CL-4 baseline before first migration | T-06 (before T-08 first migration commit) |

Every binding requirement maps to at least one task. No coverage gaps found.

## Internal consistency

- Each implementation task's exit criterion is "all relevant goldens byte-identical" (per FR-7) plus the local commit's specific file/line check.
- Phase gates correctly reference the Phase's per-backend AC set.
- Wheel-packaging smoke check is explicitly placed at T-08 (first .j2 lands), not T-04 (configuration only) — this addresses the codex iter1 BLOCKING about meaningless smoke checks before any template exists.
- Performance rows are appended in correct order (T-06 baseline → T-13 py-complete → T-20 cpp-complete → T-27 sv-complete → T-29 feature-final), matching FR-25's table schema.

## New issues found in self-review

1. **NOTE — Parallelism note ambiguity.** The dependency-graph paragraph says T-07 "may begin in parallel with later Phase 0 tasks once T-01 lands" but then says "the plan keeps them serial for review clarity." This is contradictory only if read as a binding rule. **Recommended fix:** clarify that the serial path is the *required* execution path per CL-1's contiguous commit rule; parallel execution is mentioned only as a theoretical possibility for branching workflows that this plan does not use.

2. **NOTE — T-08 emit_py construction logic.** The task says `emit_py constructs ModuleView with body_lines = tuple(legacy_render_body_lines(module))` — but the legacy `render_module_py` returns the entire post-header string (header + body), not just body lines. The implementer must either factor a `_legacy_body_lines` helper out of the existing emitter (so both the legacy path and the new template path can call it during T-08), or have T-08 retain the full legacy `render_module_py` and instead call it for the body section via a `tuple(legacy_lines.split("\n"))`. **Recommended fix:** T-08 description should explicitly mention factoring `_legacy_render_py_body` out of `render_module_py` as a prerequisite refactor within the same commit. (Not BLOCKING because the implementer can adjust.)

3. **NOTE — T-09 `kind: str` discriminator vs. FR-9.** `kind: str` is a primitive `str`, FR-8/9 compliant. But the codex review pattern would likely prefer enum-like discrimination via the existing `is_*: bool` discriminators (which are already on `StructFieldView` etc.) for consistency. **Recommended fix:** mirror the `is_scalar / is_struct / is_enum / is_flags` discriminator boolean style on each TypeView in T-07, dropping the proposed `kind: str`. (Cosmetic; FR-compliance unchanged.)

These are NOTEs, not BLOCKING. The task list is otherwise complete and concretely actionable.

## Verdict

VERDICT: APPROVE
