# Retrospect: 016-vec-const-dsl-primitive

## Workflow Summary

| Stage | Iterations | Verdict trail | Notes |
|-------|-----------|---------------|-------|
| Specification | 2 | REVISE → APPROVE | Iter1 BLOCKING: Q-4 left C++/Py emission undefined → Principle 1 violation. WARNING on FR-7 phrasing. NOTE on FR-5 cap. Iter2 fixed by adding FR-16/17/18 (explicit no-op declarations + manifest array). |
| Clarification | 1 | APPROVE | All four user answers (reject signed / verbatim names / Option A separate manifest array / keep width 64) confirmed existing FR defaults; only stale Q-references removed. |
| Planning | 3 | REVISE → REVISE → APPROVE | Iter1 BLOCKING: FR-13 cross-module rule contradicted "VecConst is not a ConstOperand" — needed real cross-module mechanism. Iter2 BLOCKING: SV-side bridge missing (Component 5 didn't consume `vec_const_imports`). Iter3 fixed by introducing `VecConstImportIR` IR node + per-symbol import collection. |
| Task Breakdown | 1 | APPROVE | 13 tasks. Plan corrections required: none. |
| Implementation | 14 task-iters across 13 tasks | 13× APPROVE first try, T4 iter2 (REVISE → APPROVE) | T4 iter1 caught FR-2 signature defect: VecConst.__init__ was over-restrictive (`def __init__(self, *, width, value, base)` instead of `def __init__(self, width, value, *, base)`). Fixed in iter2 + added `test_positional_width_and_value_accepted`. |
| Validation | 2 | REVISE → APPROVE | Iter1 BLOCKING: `validate/engine.py` four passes (duplicate-name, generated-identifier collision, enum-literal collision, reserved-keyword) didn't fold in `module.vec_constants`. Iter2 fixed all four + added two new tests in `VecConstNameValidationTests`. |
| Retrospect | (in progress) | — | This document. |
| **Total** | **23 forge-gauge cycles** | **6 REVISE / 17 APPROVE first-try** | All REVISE caught real defects, zero unnecessary churn. |

- **Forge:** claude (this assistant) for every stage.
- **Gauge:** gemini (`gemini-3.1-pro-preview` via `gemini` CLI 0.40.1) for every stage. Multiple 429 RESOURCE_EXHAUSTED retries across the run; per existing memory `reference_gemini_gauge_rate_limits.md`, this is expected.
- **Skills invoked:**
  - **Planning**: `systemverilog-core` (per CLAUDE.md routing rule for SV-touching changes).
  - **Implementation**: `systemverilog-core` (carried through for the SV view + template edits in T6).
  - All other stages: none.

Branch contains 33 commits from forge/gauge/steel/stage-complete tags. Final code change: ~250 LOC in 8 production Python files + 1 SV Jinja template + Constitution edit + 8 fixture/golden/test files.

---

## Memories to Save

### M-1 (feedback) — When adding a new IR top-level type, extend `validate/engine.py` four passes in lockstep

**Type:** `feedback`

**Name:** `feedback_new_ir_type_validate_passes.md`

**Content:**
> When adding a new IR top-level entity (e.g., `VecConstIR` alongside `ConstIR`), `src/piketype/validate/engine.py` must extend FOUR validation passes in lockstep, otherwise validation gaps silently allow keyword collisions, duplicate names, and generated-identifier collisions:
> 1. `validate_repo` duplicate-name check — fold the new entity's names into the same `seen_names` set used for `module.constants`/`module.types`.
> 2. `_validate_generated_identifier_collision` — fold names into the `const_names` set checked against `LP_<NAME>_WIDTH`, `pack_<base>`, etc.
> 3. `_validate_enum_literal_collision` — fold names into the `const_names` set used for enum-literal collision.
> 4. `_validate_reserved_keywords` — add a parallel loop emitting `keyword_languages(identifier=<name>)` checks.
>
> A natural mistake (which I made on this spec) is to add the freeze + emit + manifest paths but forget the validation passes, since the validation engine is in a separate file from the IR/freeze/backend edits.
>
> **How to apply:** Whenever a `tasks.md` introduces a new IR top-level entity, ALWAYS include a discrete task that extends these four validation passes. Use `grep -n 'module.constants' src/piketype/validate/engine.py` as a checklist of edit sites.

**Evidence:**
- `specs/016-vec-const-dsl-primitive/artifacts/validation/iter1-gauge.md` BLOCKING — explicitly named all four missing passes:
  > "`_validate_reserved_keywords`: Does not iterate over `module.vec_constants`... `validate_repo`: Does not check `vec_constants` for duplicate names... `_validate_generated_identifier_collision`: Does not check `vec_constants` against reserved names like `LP_{NAME}_WIDTH` or `pack_{name}`... `_validate_enum_literal_collision`: Does not check for collisions between `VecConst` names and enum literals."
- `specs/016-vec-const-dsl-primitive/artifacts/validation/iter2-forge.md` resolved the gap with a four-pass extension.

**Rationale:** Non-obvious because: (a) the validation engine lives in a separate file from `freeze.py`, `view.py`, `manifest/write_json.py`, and is easy to forget; (b) the constitution's "Adding a New Type or Feature" recipe says "Add validation rules in validate/engine.py" but doesn't enumerate the four lockstep passes; (c) tests pass without these checks because the negative inputs (keyword names, duplicates) only happen with deliberately-broken DSL — easy to miss in fixture-based testing.

---

### M-2 (project) — Manifest in-place JSON patch for additive schema changes

**Type:** `project`

**Name:** `project_manifest_inplace_patch.md`

**Content:**
> The piketype manifest writer (`src/piketype/manifest/write_json.py`) dumps with `json.dumps(payload, indent=2, sort_keys=True) + "\n"`. So adding a NEW key to the per-module dict alphabetically sorts it; existing fields' positions shift only if the new key alphabetically precedes them.
>
> **Implication for golden regeneration:** When a spec adds a new optional/empty field per module (e.g., `"vec_constants": []`), an in-place JSON patch script that does `data['modules'][N][newkey] = []; json.dumps(data, indent=2, sort_keys=True) + '\n'` produces output BYTE-IDENTICAL to a re-run of `piketype gen` against every fixture. This sidesteps the need to know per-fixture CLI invocation args.
>
> **How to apply:** When a spec's R-2-equivalent risk requires regenerating ~20+ existing manifest goldens with a single new key, prefer the in-place patch over per-fixture `piketype gen` re-runs. Verify byte-identity by running the full unittest suite — the existing golden integration tests are the ground truth.

**Evidence:**
- `specs/016-vec-const-dsl-primitive/artifacts/implementation/task11-iter1-forge.md` — the regeneration script and its rationale.
- `specs/016-vec-const-dsl-primitive/artifacts/implementation/task11-iter1-gauge.md` — gauge confirmed byte-identity by reading the writer source.
- 24 manifest goldens regenerated; 307 tests still passed → byte-identity transitively confirmed.

**Rationale:** Non-obvious because: re-running `piketype gen` per-fixture is the "correct" approach but requires per-fixture CLI args (some fixtures need `--namespace=...`); the in-place JSON patch is functionally equivalent for purely-additive empty-field changes and saves ~hour of script wrangling.

---

### M-3 (feedback) — Cross-module imports for non-operand IR primitives need a dedicated `<Name>ImportIR` node

**Type:** `feedback`

**Name:** `feedback_cross_module_non_operand_pattern.md`

**Content:**
> For an IR top-level entity that is NOT used as an operand inside other expressions (e.g., `VecConstIR` is not a `ConstOperand`), the existing cross-module dependency mechanism — which walks `_collect_const_refs` for `ConstRefExprIR` nodes — DOES NOT detect cross-module imports of that entity. The `from a import LP_X` Python-side import doesn't naturally produce an SV `import a_pkg::LP_X;` line.
>
> Required pattern (three pieces, in lockstep):
> 1. **IR**: a new `<Name>ImportIR(target_module_ref, symbol_name)` frozen dataclass + a `module.<name>_imports: tuple[<Name>ImportIR, ...]` field on `ModuleIR`.
> 2. **Freeze**: a sibling `build_<name>_definition_map` mirroring `build_const_definition_map`, plus a `freeze_module` extension that walks each module's `__dict__` and emits `<Name>ImportIR` records for non-local sightings.
> 3. **SV view**: extend `_collect_cross_module_synth_imports` (`src/piketype/backends/sv/view.py:774`) to walk `module.<name>_imports` and add `(pkg, symbol)` pairs to the existing dedup `set`. Per-symbol import is the codebase convention (per `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv`), NOT wildcard `import a_pkg::*;`.
>
> **How to apply:** When introducing a new top-level IR entity that needs cross-module visibility, plan all three pieces from the start. Skipping any of them creates a silent gap.

**Evidence:**
- `specs/016-vec-const-dsl-primitive/artifacts/planning/iter1-gauge.md` BLOCKING:
  > "If `VecConst` is not a `ConstOperand`, it cannot be used in expressions or as a value for other `VecConst`/`Const` nodes, making it a 'leaf-only' primitive that violates the parity and reuse goals implied by FR-13 and US-1."
- `specs/016-vec-const-dsl-primitive/artifacts/planning/iter2-gauge.md` BLOCKING (carry-over after iter2 only addressed freeze): SV view side missing.
- `specs/016-vec-const-dsl-primitive/artifacts/planning/iter3-forge.md` introduced the three-piece pattern formally.

**Rationale:** Non-obvious because: (a) for `Const`, cross-module deps emerge naturally from expression walks (`_collect_const_refs`), so this looks "automatic"; (b) the spec's FR-13 said "the existing cross-module mechanism for `Const`" but the existing mechanism is for **types**, not constants — there is no existing cross-module Const import emission; (c) the user's literal text "import a_pkg::*;" was a non-existent wildcard syntax for this codebase. The three-piece pattern took 3 plan iterations to crystallize.

---

## Skill Updates

### S-1 — `/steel-tasks` should remind authors to include a "validate/engine.py extension" task when introducing a new IR top-level entity

**Skill:** `/steel-tasks` (file: `~/.claude/skills/steel-tasks` or wherever the slash command's instructions live).

**Issue found:** The `/steel-tasks` instructions say to "Break the plan into ordered, actionable tasks" and to "cross-check every file path and tool invocation cited in plan.md." But they don't enumerate the lockstep edit sites in `validate/engine.py` for new IR primitives. As a result, the task list for spec 016 (T1..T13) included `freeze.py`, `manifest/write_json.py`, `view.py`, the template, and the Constitution amendment — but had no discrete task for "extend validate/engine.py to fold the new IR entity into the four validation passes." The defect surfaced at validation iter1 BLOCKING.

Quote from `artifacts/validation/iter1-gauge.md`:
> "`src/piketype/validate/engine.py` is missing name validation for `VecConst`. ... This violates Constitution Principle 4 ('Correctness over convenience') and creates a significant safety gap compared to the legacy `Const` primitive."

**Proposed change:** Add to `/steel-tasks` step 3a a checklist hint:

> When the plan introduces a new IR top-level entity (a new field on `ModuleIR`, a new frozen dataclass alongside existing ones like `ConstIR`/`StructIR`/`EnumIR`), the task list MUST include a discrete task that extends `src/piketype/validate/engine.py` to fold the new entity into:
> 1. `validate_repo`'s duplicate-name `seen_names` set
> 2. `_validate_generated_identifier_collision`'s `const_names` set
> 3. `_validate_enum_literal_collision`'s `const_names` set
> 4. `_validate_reserved_keywords`' per-entity loop
>
> Use `grep -n 'module.constants' src/piketype/validate/engine.py` as a discoverability cross-check at task-breakdown time.

**Expected impact:** Would have eliminated the validation iter1 REVISE round (which itself burned ~3 minutes of gauge wait + ~2 forge edits). Future specs introducing more IR top-level entities (e.g., a future `Macro`, `Channel`, `Register`, etc.) get the same protection.

---

### S-2 — `systemverilog-core` skill could include a "verify against existing goldens" check before approving cross-module emission designs

**Skill:** `systemverilog-core`

**Issue found:** During planning iter1/iter2, the Forge wrote spec FR-13 with the literal phrase `"import a_pkg::*;"` — a wildcard-import syntax that does NOT match this codebase's per-symbol convention. The Forge could have caught this earlier by reading an existing cross-module golden (`tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv`) which uses `import foo_pkg::byte_t;` etc. The gauge eventually surfaced this in plan iter2.

**Proposed change:** Add to `systemverilog-core` activation procedure (point 1, after reading style-guide):

> 1.5. **Convention discovery:** when planning an SV emission shape, grep existing goldens for analogous emission patterns (e.g., `grep -r 'import.*::' tests/goldens/`) and adopt that style. Do NOT assume SV idioms from elsewhere (e.g., `import pkg::*;` wildcard syntax) without verifying against project goldens — the project may use a stricter or different convention.

**Expected impact:** Would have eliminated 1 plan iteration (iter2 BLOCKING) and 1 spec round-trip on the wildcard-vs-per-symbol confusion.

---

### S-3 — `/steel-implement` task forge artifact should include a "downstream-validation passes touched" line

**Skill:** `/steel-implement`

**Issue found:** When T3 (freeze logic) was implemented, the forge artifact described all the freeze changes but did not call out that `validate/engine.py` would need parallel updates. T8 (fixtures) discovered the validate-engine "no DSL objects" check needed extending and fixed it ad-hoc; the four name-collision passes were missed entirely until validation iter1.

**Proposed change:** Add to `/steel-implement` step 3b's forge artifact template:

> ## Downstream Validation Touchpoints
> List any production-code files that consume the IR or DSL surfaces touched in this task and that may need parallel updates. Specifically: when adding a new top-level IR entity, list every file that walks `module.constants` / `module.types` / etc. and may need to also walk the new entity. Format:
> - `src/piketype/validate/engine.py:<line>` — adds <new-entity> to <pass-name> (or: `[deferred to T<N>]`).
> - `src/piketype/backends/<lang>/<file>.py:<line>` — emits <new-entity> output (or: `[no-op per spec FR-N]`).

**Expected impact:** Would have surfaced the validate-engine four-pass gap during T3's forge artifact instead of validation iter1, saving the validation REVISE round.

---

## Process Improvements

### P-1 — Bottlenecks: planning needed 3 iterations because cross-module mechanism wasn't fully captured in the spec

**Issue:** The 3-iteration planning stage was not the Forge's fault per se — the spec's FR-13 was both **(a) under-specified** (didn't require any specific freeze/IR/view changes) and **(b) factually wrong about the codebase** (literal `*;` wildcard didn't match the per-symbol convention). Each plan iteration peeled back one layer of the gap:

- iter1: Forge claimed FR-13 was vacuous (since VecConst isn't a ConstOperand). Gauge rejected.
- iter2: Forge added `vec_const_definition_map` and dependency-edge emission in freeze. Gauge rejected (SV-side consumption missing + wildcard vs per-symbol).
- iter3: Forge added `VecConstImportIR` first-class IR node + per-symbol SV view extension + verified against existing golden's import style. Gauge approved.

**Evidence:**
- `artifacts/planning/iter1-gauge.md` (BLOCKING FR-13/AC-11)
- `artifacts/planning/iter2-gauge.md` (BLOCKING SV bridge + WARNING dedup)
- `artifacts/planning/iter3-gauge.md` (APPROVE)

**Classification:** Each REVISE was **(a) caught a real defect.** Zero unnecessary churn.

**Proposed fix:** S-2 (above): SystemVerilog-core skill should mandate convention-discovery against existing goldens before cross-module emission designs. Would have caught the wildcard error in spec/early-plan and shortened the planning loop to 2 iterations or fewer.

---

### P-2 — Forge-Gauge dynamics: gauge consistently catches real defects in spec 016 (zero churn this run)

**Classification of all 6 REVISE verdicts:**

| Stage | Iter | Severity | Defect category |
|-------|------|----------|-----------------|
| Spec | 1 | BLOCKING | (a) Real — Q-4 left C++/Py undefined, Principle 1 violation. |
| Plan | 1 | BLOCKING | (a) Real — FR-13 cross-module rule unbuildable as written. |
| Plan | 2 | BLOCKING | (a) Real — SV-side bridge missing in Component 5. |
| Implementation T4 | 1 | WARNING | (a) Real — VecConst.__init__ over-restrictive vs FR-2. |
| Validation | 1 | BLOCKING | (a) Real — 4 validate/engine.py passes didn't fold in `vec_constants`. |

**0 of 6 REVISE verdicts were churn or scope-expansion attempts.** This continues the pattern from spec 015 where the same gauge (gemini) was thorough and grounded.

**Proposed fix:** None — the dynamic is healthy. Memory M-2 (`reference_gemini_gauge_rate_limits.md`) from spec 015 about wall-clock waits remains accurate.

---

### P-3 — Constitution gaps

The Constitution's "Adding a New Type or Feature" section in §Development Guidelines lists 7 steps:
1. Define DSL node in `dsl/`.
2. Add frozen IR node in `ir/nodes.py`.
3. Add freeze logic in `dsl/freeze.py` and IR builder logic in `ir/builders.py`.
4. Add validation rules in `validate/engine.py`.
5. Add emission in each backend (`sv/emitter.py`, `cpp/emitter.py`, `py/emitter.py`).
6. Create fixture + golden.
7. Add integration test.

Step 4 says "Add validation rules" but does NOT enumerate the four lockstep passes (`validate_repo` duplicates, generated-identifier collision, enum-literal collision, reserved-keyword). This is the same gap that surfaced as validation iter1 BLOCKING.

**Proposed Constitution refinement** (NOT applied automatically — surface as a discussion point):

Update §Adding a New Type or Feature step 4 to:

> 4. Add validation rules in `validate/engine.py`. **For new IR top-level entities, fold names into FOUR existing passes in lockstep:** `validate_repo` duplicate-name check, `_validate_generated_identifier_collision`, `_validate_enum_literal_collision`, and `_validate_reserved_keywords`.

**Evidence:** `artifacts/validation/iter1-gauge.md` BLOCKING explicitly enumerates the four missed passes.

This change is judgment-call: the user may prefer to keep the Constitution terse and put the checklist in the `/steel-tasks` skill instead (per S-1 above). I recommend S-1 over the Constitution edit.

---

### P-4 — Workflow gaps

**None observed.** The 7-stage Steel-Kit flow (specification → clarification → planning → task_breakdown → implementation → validation → retrospect) covered every gap we hit. The validation REVISE in particular caught a real defect that no earlier stage caught — exactly what validation is for.

---

## Summary

- **23 forge-gauge cycles, 6 REVISE verdicts, 0 churn.** Every REVISE caught a real defect.
- **Three memories worth saving** (M-1 validate-engine four-pass lockstep; M-2 manifest in-place JSON patch; M-3 cross-module non-operand IR pattern).
- **Three skill updates worth applying** (S-1 `/steel-tasks` validate-engine checklist; S-2 `systemverilog-core` convention-discovery against goldens; S-3 `/steel-implement` downstream-validation touchpoints).
- **Constitution refinement candidate** (P-3) — judgment-call; recommend S-1 instead.
- **No workflow gaps** — Steel-Kit's 7-stage flow worked as intended.
