# Retrospect — 013-unpack-signed-cast-explicit-slices

## Workflow Summary

| Stage           | Iterations | Verdict trail              | Forge | Gauge  |
|-----------------|------------|----------------------------|-------|--------|
| Specification   | 2          | REVISE → APPROVE           | claude| gemini |
| Clarification   | 2          | REVISE → APPROVE           | claude| gemini |
| Planning        | 1          | APPROVE                    | claude| gemini |
| Task breakdown  | 1          | APPROVE                    | claude| gemini |
| Implementation  | 1 cycle    | APPROVE (T-001 + T-002 in one Gauge call) | claude| gemini |
| Validation      | 1          | APPROVE (10 PASS / 0 FAIL / 0 DEFERRED) | claude| gemini |
| Retrospect      | (current)  | —                          | claude| gemini |

**Total Forge-Gauge cycles:** 8 distinct Gauge invocations (2 specification + 2 clarification + 1 planning + 1 task_breakdown + 1 implementation + 1 validation). All loops converged within `maxIterations: 5`.

**Skills invoked:** `[]` at every stage. The feature is a pure SystemVerilog backend codegen edit (one `view.py` Python edit + one Jinja template edit + golden refresh). The closest registered skill (`systemverilog-core`) is documented as "creating, modifying, refactoring, linting, debugging, or reviewing any SystemVerilog file (.sv, .svh)" — but the only `.sv` files I touched are the regenerated GOLDEN outputs, which are not human-authored RTL. The actual edits are in a Python view-builder and a Jinja template. None of the project's registered skills target that combination, and inventing one is not justified for an 18-line view-builder change + 12-line template change.

## Memories to Save

### M-1. Project — Existing `tests/fixtures/struct_signed/` already exercises the four signed-handling paths

- **Type:** project
- **Name:** `project_struct_signed_fixture_coverage`
- **Content:** `tests/fixtures/struct_signed/project/alpha/piketype/types.py` is a high-coverage test fixture for SystemVerilog signedness handling: it declares two top-level signed scalar aliases (`signed_4_t = Logic(4, signed=True)`, `signed_5_t = Logic(5, signed=True)`) and a struct `mixed_t` with one type-ref signed field (`field_s = signed_4_t`) and one inline signed field (`field_u = Logic(5, signed=True)`). Both fields have padding bits, exercising signed-padding extension. **Why:** When working on signed-related codegen changes, do NOT add a new fixture before checking this one. **How to apply:** Before adding any new fixture for "signed inline struct field" / "signed scalar alias unpack" / "signed type-ref struct field" / "signed-padded field" coverage, verify whether the existing `struct_signed` fixture already exercises the path. In iteration 1 of spec 013 the Forge over-mandated a new fixture (`struct_signed_inline`) without doing this check; the clarification stage caught it.
- **Evidence:** `tests/fixtures/struct_signed/project/alpha/piketype/types.py` (4-line DSL covers all four cases); `tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv` shows `unpack_signed_4 / unpack_signed_5 / unpack_mixed.field_s / unpack_mixed.field_u` covering each path; `specs/013-unpack-signed-cast-explicit-slices/clarifications.md` Q1 records the over-mandate and the correction.
- **Rationale:** Future signed-related work will recur and the same over-mandate could happen again. Saves a clarification-stage revise cycle.

### M-2. Project — Goldens regenerate via per-fixture run_gen + tree-replace pattern

- **Type:** project
- **Name:** `project_golden_regen_pattern`
- **Content:** Pike-type does not ship a `piketype gen --update-goldens` flag or a tools/regen-goldens.py. To regenerate goldens after a backend change: (1) walk every `tests/fixtures/<name>/` that has both a `project/` tree AND a matching `tests/goldens/gen/<name>/` directory; (2) for each, copy `project/` to a tempdir, `os.chdir` into it, find the first `.py` file under `<ns>/piketype/` and pass it to `piketype.commands.gen.run_gen(str(path))`, then `shutil.rmtree(golden_dir); shutil.copytree(tmp/gen, golden_dir)`; (3) for fixtures whose tests pass `--namespace=<value>` to the CLI (e.g. `namespace_override`, `cross_module_type_refs_namespace_proj`), regenerate them separately by calling `run_gen(str(path), namespace="<value>")`. The throwaway script lived at `/tmp/regen_goldens.py` for spec 013; it can be re-derived but is worth keeping as a utility. **Why:** Manual per-fixture regeneration is tedious and error-prone; the namespace-flag fixtures are easy to forget. **How to apply:** When a backend edit forces a goldens refresh, write a one-shot regen script following this pattern. Run `unittest` after to confirm nothing was missed (any namespace-flag fixture you skip will fail loudly).
- **Evidence:** Spec 013 implementation stage: T-002 used this pattern, regenerating 23 goldens via the walk script and 2 namespace-flag goldens via a separate script. `tests/test_gen_const_sv.py:373-374` shows the per-test pattern that the regen script reproduces.
- **Rationale:** Will recur on every backend feature that changes generated SV/C++/Python output.

### M-3. Project — `cross_module_type_refs_namespace_proj` golden has no matching fixture name

- **Type:** project
- **Name:** `project_namespace_proj_golden_orphan`
- **Content:** `tests/goldens/gen/cross_module_type_refs_namespace_proj/` is generated from the `tests/fixtures/cross_module_type_refs/` fixture WITH the `--namespace=proj::lib` CLI flag, not from a fixture of the same name. There is no `tests/fixtures/cross_module_type_refs_namespace_proj/`. **Why:** A naive regen-goldens script that walks `tests/fixtures/` will miss this golden and produce false test failures after a backend change. **How to apply:** Goldens-refresh scripts must enumerate the golden directories AND map each to its source fixture + CLI invocation. The mapping for namespace-flag goldens lives in the test code under `tests/test_gen_cross_module.py` and `tests/test_gen_const_sv.py:test_namespace_override_multi_module`.
- **Evidence:** `tests/test_gen_cross_module.py:test_namespace_proj_generates_qualified_field_types` lines define the mapping (`fixture=cross_module_type_refs`, `golden=cross_module_type_refs_namespace_proj`, `namespace=proj::lib`).
- **Rationale:** Concrete trap; non-obvious from the directory layout.

### M-4. Feedback — `_is_field_signed(*, field, repo_type_index)` returns True for signed type-ref fields

- **Type:** feedback
- **Name:** `feedback_is_field_signed_returns_true_for_typeref`
- **Content:** `src/piketype/backends/sv/view.py:_is_field_signed` returns True for a struct field whose `type_ir` is a `TypeRefIR` to a signed scalar alias. When using this helper to gate codegen behaviour that should differ between "inline signed" and "type-ref to signed alias", combine the result with `not isinstance(field.type_ir, TypeRefIR)` to distinguish the two cases. **Why:** Spec 013's signed-cast rule (`signed'(...)`) applies only to inline signed fields, not to type-ref fields (where `unpack_<inner>` already returns the signed declared type — wrapping its return in another `signed'(...)` is redundant and lint-noisy). **How to apply:** Whenever you emit code based on "is this field signed?", first decide whether type-ref signedness is relevant to your decision; if not, AND with `not is_type_ref` to suppress the type-ref case.
- **Evidence:** `src/piketype/backends/sv/view.py:511,515` (the `is_signed_eff = ... and not is_type_ref` line in `_build_struct_pack_unpack`); spec 013 clarification Q6 captured the contract.
- **Rationale:** This will recur for any future signedness-conditional codegen — e.g. C++ backend integer cast emission, Python backend struct.pack format-char selection.

### M-5. Reference — Verilator 5.046 `-Wall` does NOT flag implicit unsigned→signed return as a warning

- **Type:** reference
- **Name:** `reference_verilator_signed_warning_gap`
- **Content:** Verilator 5.046 with `-Wall` does NOT emit a SIGNED or WIDTH warning for the assignment `return a;` where `a` is `logic [W-1:0]` (unsigned) and the function return type is a signed typedef of the same width. The user's lint complaint that motivated spec 013 must therefore come from a different toolchain — most likely a commercial linter (Spyglass, VC SpyGlass, or Verissimo). The fix `return signed'(a);` is still beneficial because: (a) it makes the signed conversion explicit at the SystemVerilog source level; (b) it composes with `-Wpedantic` and `-Werror=` flag combinations; (c) it satisfies commercial linters even if Verilator alone is silent. **Why:** Validation of "lint-clean" claims under Verilator alone may produce a false APPROVE. **How to apply:** When a feature claims to fix lint warnings, identify the actual reporting toolchain BEFORE designing the fix. If Verilator is not the reporter, do not use Verilator alone to validate the fix; instead spot-check the reporter's actual output.
- **Evidence:** `verilator --version` reports `5.046 2026-02-28`; running `verilator --lint-only -Wall` on both the pre-feature and post-feature `tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv` produces the same 4 warnings (UNUSEDPARAM ×3, UNUSEDSIGNAL ×1) — none in the SIGNED/WIDTH category.
- **Rationale:** Saves future spec authors from repeating the assumption that "Verilator lint baseline" equals "all useful lint signals". Has a known gap for the signed-mismatch case spec 013 fixes.

## Skill Updates

The project has a registered `systemverilog-core` skill but it triggers on `.sv`/`.svh` file edits. Spec 013 didn't edit any `.sv` source — only generated goldens and the Jinja template that produces them. There is no skill specifically for "Pike-type SV-backend Python codegen + Jinja template work."

### S-1. Add a `piketype-sv-backend` skill (or extend an existing skill family)

- **Skill:** new skill `piketype-sv-backend` or scope expansion of `systemverilog-core`.
- **Issue found:** The actual edits in spec 013 (a) extended a frozen Python dataclass with three new fields, (b) updated a Python view-builder to populate them with running-accumulator arithmetic, and (c) changed a Jinja template's branch structure. None of these triggered any registered skill. The Forge had to re-derive constitutional patterns (template-first generation, view-model preparation, frozen-dataclass discipline, slots=True) from `.steel/constitution.md` plus reading neighbouring code in `src/piketype/backends/sv/view.py` on every iteration.
- **Proposed change:** Create a skill that triggers on "edit, extend, or refactor any file under `src/piketype/backends/sv/` OR `src/piketype/backends/sv/templates/*.j2`" with a checklist:
  - View-model dataclasses are `@dataclass(frozen=True, slots=True)` with explicit field types.
  - Slice / offset / index arithmetic happens in Python view builders, never in Jinja templates (Constitution principle 5).
  - Templates emit literal integer values via `{{ var }}`; do not concatenate strings or compute arithmetic in Jinja.
  - Helper functions use `*` keyword-only args universally (cf. spec 012 retrospect M-6 — same constitutional rule applies here).
  - `_is_field_signed`, `_field_data_width`, `_type_base_name` are the existing helpers; reuse them, do not re-derive.
  - For any backend output change: regenerate ALL fixture goldens in the same commit; do not split.
  - Verify zero diffs in `_test_pkg.sv`, `cpp/`, `py/`, `runtime/` golden subtrees when the change is SV-synth-package-only.
- **Expected impact:** Would have made the iter-1 specification REVISE (over-restrictive scope on scalar-alias unpack) less likely, because the skill would have surfaced "every unpack variant" as a checklist item. Saves at least one iteration on similar future work.

### S-2. Add a `piketype-goldens-refresh` skill or tool

- **Skill:** could be a slash command or skill, e.g. `/refresh-goldens`.
- **Issue found:** Every backend feature has the same goldens-refresh pattern (M-2). Currently each spec author writes a throwaway script in `/tmp/`. This is fine for a one-shot but the namespace-flag mapping (M-3) is non-obvious and easy to miss.
- **Proposed change:** Add `tools/refresh_goldens.py` to the repo (not just `/tmp/`) that walks `tests/fixtures/`, regenerates each, AND knows about namespace-flag goldens via a small explicit map at the top of the file. Document its existence in `docs/architecture.md` under "Adding test fixtures". Wire it into a slash command if the project's tooling supports that.
- **Expected impact:** Saves ~15 minutes of script-writing-and-debugging per backend feature. Eliminates the "I forgot the namespace-flag goldens" failure mode (which cost ~5 minutes during spec 013's T-002).

## Process Improvements

### P-1. Bottlenecks

- **Specification — 2 iterations.** Healthy. iter 1 → REVISE was a substantive scope catch (Gauge correctly identified that excluding signed scalar aliases from FR-1.4 contradicted US-1's lint-clean goal); iter 2 → APPROVE. Single REVISE cycle, well-justified.
- **Clarification — 2 iterations.** Less healthy. iter 1 → REVISE was for two real but mechanical defects (an internal contradiction between Open Questions and AC-4 wording, and a summary-table mismatch with the spec-diff). Both were preventable: the Forge should have re-read the rendered spec.md after applying the [SPEC UPDATE] resolutions to catch the OQ-3 stale wording, and should have made the summary table reference the actual edited section rather than "Out of Scope". This is a self-inflicted REVISE caused by inconsistent post-edit verification, not a Gauge over-call.
- **Planning, Task breakdown, Implementation, Validation — 1 iteration each.** No bottlenecks. The plan's small scope (two files + golden refresh) made all downstream stages compress quickly.

### P-2. Forge-Gauge dynamics — REVISE classification

| Stage / Iter         | Classification | Source |
|----------------------|----------------|--------|
| Specification iter 1 | (a) real defect — scalar-alias signed-cast scope omission | `artifacts/specification/iter1-gauge.md` |
| Clarification iter 1 | (a) real defect ×2 — OQ-3/AC-4 contradiction; summary-table mismatch | `artifacts/clarification/iter1-gauge.md` |

**No (c) "unnecessary churn" REVISE cycles.** Both REVISEs caught real defects.

The clarification iter-1 REVISE is partly self-inflicted: had the Forge re-read spec.md after applying the [SPEC UPDATE] edits, it would have noticed the stale "OQ-3 → new fixture" wording in the Open Questions section and the summary-table reference to "Out of Scope" instead of "Open Questions". Both are one-pass-of-eyes catches. This suggests a Forge-side hygiene step: after every [SPEC UPDATE] application, re-read the FULL `spec.md` and grep for any reference to the resolved-question's old answer.

### P-3. Constitution gaps

- **The "basedpyright strict mode must pass with zero errors" mandate is still aspirational.** Baseline: 100 errors, unchanged from spec 012. Spec 013 introduced no new errors. Same observation as spec 012 retrospect M-3 / P-3. Not a new gap; flagging it again because the constitution wording hasn't been amended.

### P-4. Workflow gaps

- **Clarification stage's [SPEC UPDATE] verification is implicit.** The convention is that the Forge applies the [SPEC UPDATE] resolutions in-place to `spec.md` and records the diff in `iterN-spec-diff.md`. There is no automated check that every section flagged for update was actually edited, or that no other section was inadvertently touched. The clarification iter-1 REVISE in this spec was caught by the Gauge but could have been caught earlier by a `diff spec.md.before spec.md.after` discipline. Recommend the steel-clarify skill explicitly require the Forge to attach a verbatim before/after for every [SPEC UPDATE] section in `iterN-spec-diff.md` — this would naturally surface stale Open-Questions wording and summary-table inconsistencies.
- **Otherwise no gaps detected** in the steel-kit workflow; all 7 stages contributed value. Implementation collapsed naturally to a single Gauge call because the task list was only 2 tasks.

## Observations on the spec quality

- The spec converged tightly: 9 FRs, 5 NFRs, 10 ACs, all with concrete grep-or-eyeball verification. Both the gauge-flagged scope omission (scalar-alias signed cast) and the clarification's "reuse existing fixture" finding strengthened the spec materially.
- The plan's two-commit decomposition (T-001 view-only, T-002 template + goldens) was a clean expression of the byte-parity-per-commit user preference: T-001 left the test suite green because new view fields were unread, and T-002 atomically swapped template + goldens together.
- The validation stage's AC-9 "delta check vs pre-feature lint baseline" framing was a direct consequence of clarification Q5, which in turn was a direct response to the iter-1 spec's vague "project's existing strict lint flag set" wording. Cleaner conclusion than spec 012's AC-10 follow-up failure.
- AC-8 / NFR-3 are PARTIAL (no new pyright errors over a 100-error baseline). This is not a defect of the feature; it is a recurring constitutional-text issue that needs amendment, not per-feature handling.
