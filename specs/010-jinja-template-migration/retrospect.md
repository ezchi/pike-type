# Retrospect — 010-jinja-template-migration

**Spec ID:** 010-jinja-template-migration
**Branch:** feature/010-jinja-template-migration
**Stage:** retrospect
**Total commits on branch:** 47

## Outcome summary

The migration shipped:

- A working Jinja2-based rendering layer (`backends/common/render.py`) used by all three primary code emitters (Python, C++, SystemVerilog).
- Frozen view-model dataclasses (`backends/<lang>/view.py`) with builders that consume frozen IR and produce primitives + nested view models for every type kind.
- Five `.j2` templates packaged in the wheel: `py/templates/{module,_macros}.j2`, `cpp/templates/module.j2`, `sv/templates/{module_synth,module_test}.j2`.
- Tooling: `tools/check_templates.py` (template-hygiene lint with 8 forbidden patterns + 15 unit tests), `tools/perf_bench.py` (FR-23-conformant benchmark CLI).
- Developer documentation: `docs/templates.md` covering architecture, custom-filter rules, indirection bound, perf and lint usage.
- 246 tests pass; goldens unchanged byte-for-byte; per-backend ACs 1, 2, 3, 4, 5, 6, 7 satisfied for Python, C++, and SV.

## What did NOT ship

1. **AC-F4 (feature-final perf budget)**: the migration regresses `piketype gen` by 5.66× on the `struct_padded` fixture (13.861 ms vs 2.448 ms baseline). The 1.25× NFR-1 budget was unrealistic given FR-2's mandate to reconstruct the Jinja env per `emit_<lang>` call. Documented mitigations (bytecode cache, module-level env amendment, NFR-1 amendment) deferred to a follow-up spec.

2. **Strict FR-19 (full inline-helper removal)**: only the Python backend converted every `_render_py_*` helper into a Jinja macro. C++ and SystemVerilog kept their `_render_<lang>_*` helpers and call them from `view.py` builders to produce per-type `body_text: str` strings, which the templates emit verbatim. The compromise is documented at the top of each `view.py` and in the corresponding implementation commit. A follow-up may convert the per-type helpers to Jinja macros to fully realize FR-19.

3. **Strict FR-17 (no new `pyright: ignore`)**: ten new `pyright: ignore[reportPrivateUsage]` suppressions were added on the calls from `cpp/view.py` and `sv/view.py` into the legacy private `_render_*` helpers. This is a corollary of point 2 — the helpers stay private until they're moved into Jinja macros. The suppressions are local and scoped, but they're new.

## What worked well

- **Forge-Gauge dual-agent loop** for spec/clarification/planning produced a substantially stronger spec than a single-pass write would have. Codex caught five separate BLOCKING-level issues during planning (FR-6 commit ordering, view-model completeness, byte-parity strategy, etc.) that would have been very expensive to discover during implementation.
- **InlineFragmentView passthrough** mechanism (`body_lines: tuple[str, ...]` + `has_body_lines: bool`) made the Python backend's sub-step migration commits each preserve byte parity, catching whitespace bugs the moment they appeared rather than after a 700-line cleanup commit.
- **Template lint script** with patterns scoped to Jinja-block contents (not raw template body) was the right design — the negative-case tests confirmed legitimate target-language text outside blocks (`padded[WIDTH-1:0]`, `BYTE_COUNT * 8`) is never falsely flagged.
- **Per-call Jinja env construction** (FR-2) made testing simple — each `emit_<lang>` call produces fresh state — but turned out to be the dominant cost driver for perf.

## What surprised me

- **Jinja whitespace control** (`{%- ... %}` / `{%- ... -%}` / `keep_trailing_newline` / `trim_blocks` / `lstrip_blocks`) interacts in non-obvious ways with `{% if %}` / `{% elif %}` / `{% else %}` / `{% endif %}` chains. Getting byte-parity required iterating on whether each branch transition stripped leading/trailing newlines. Roughly 4 of the Python sub-step commits had at least one whitespace bug that surfaced only when running the full test suite.
- **`dataclasses.asdict()`** flattens nested view-model dataclasses into nested dicts. This was intended (so templates use `{{ obj.attr }}` uniformly), but the deep copy was suspected as a perf hotspot. Profiling showed the actual cost is in Jinja's parse + AST + bytecode compilation, not asdict — but the suspicion drove a switch to shallow `**vars()`-style kwarg expansion in `render()` anyway, which is FR-9-compatible since nested dataclasses keep working via attribute access.
- **`PackageLoader` requires the templates directory to exist** at `Environment` construction time. This forced the wheel-packaging smoke test to be deferred until the first real `.j2` file landed (Phase 1 commit 2), per codex's iter1 review.

## Memory candidates

The following are user-preference and project-state observations worth carrying forward to future work in this repo. They will be saved separately as memory entries (per the user's auto-memory protocol):

- **User preference (feedback): byte-parity at every commit is the correctness mechanism.** The user explicitly approved a plan that mandated golden-file byte-identity at every Phase 1 sub-step commit, even though it required transitional view-model fields (`body_lines`, `has_body_lines`, `body_text`). When I considered "internal refactor commits with parity at end of phase only", the spec reviewers (codex) flagged it as a BLOCKING and the plan now mandates the InlineFragmentView passthrough approach. **How to apply:** for any future migration in this repo, default to a transitional passthrough (precomputed `body_text` strings or equivalent) so each commit is byte-parity-verifiable rather than batching.
- **Project state: FR-19 (helper removal) is fully done in Python only.** The C++ and SV backends still have `_render_<lang>_*` helpers that are called from `view.py` builders. Future work that touches `backends/{cpp,sv}/emitter.py` should be aware these helpers are reachable from view code, not dead.
- **Project state: AC-F4 perf gate is open.** The migration has a 5.66× regression that needs either a bytecode cache, an env-lifetime amendment to FR-2, or an NFR-1 amendment. Future work touching `emit_<lang>` should consider this.

## Skills that would have helped

- A **Jinja whitespace-debugger** skill that, given a template + expected output, identifies which `{%-` / `-%}` toggles are needed at each tag. The 4+ whitespace bug iterations during Python migration would have collapsed to 1.
- A **basedpyright-strict regression detector** skill that runs strict mode on the migration's view + render files only and reports new errors versus a baseline (the `develop` branch). I had to filter out pre-existing strict errors manually.

## Workflow improvements for next migration

- **Run codex (gauge) on tasks.md too**, not just spec.md and plan.md. The task breakdown caught no new issues from gauge review, but that's because the gauge review for tasks.md was Claude-self-review (codex was rate-limited). For a future workflow where codex is reliable, add tasks.md to the explicit gauge round.
- **Set NFR perf budgets after a feasibility prototype**, not before. NFR-1's 1.25× was set during specification without testing what `Environment` construction actually costs. Prototype the env-creation path against the baseline before committing a numeric budget.

## Tag

`steel/010-jinja-template-migration/retrospect-complete` will be applied after this stage's commit.
