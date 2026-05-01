# Gauge Review — Task Breakdown Iteration 1

## Summary

The task breakdown is structurally close: the A-F sequencing matches the spec staging, the core backend/freeze/validation work is represented, and most risks have concrete tasks. Do not approve this iteration: AC-7 is not fully evidenced, and NFR-3 / constitution constraint 6 has no explicit verification path.

## Coverage Audit

### Functional Requirements

| ID | Coverage | Verdict |
|----|----------|---------|
| FR-1 | T1-T4, T6 cover loader session, callers, helper migration, snapshot/restore tests (`spec.md:136-161`, `tasks.md:11-70`, `tasks.md:88-96`). | OK |
| FR-2 | T1 enables stable identity; T15 verifies cross-module `TypeRefIR`; T22-T25 exercise scalar/struct/enum/flags fixture (`spec.md:163-170`, `tasks.md:211-223`, `tasks.md:311-362`). | OK |
| FR-3 | T33 covers cross-module `.multiple_of()` fixture and golden test (`spec.md:172-176`, `tasks.md:470-481`). | OK |
| FR-4 | T12 implements dependency collection; T15 tests type/const refs and sorted dedupe (`spec.md:178-191`, `tasks.md:172-181`, `tasks.md:211-223`). | OK |
| FR-5 | T13 removes rejection and changes lookup/error; T16 tests unknown target; T25 exercises accepted cross-module refs (`spec.md:193-200`, `tasks.md:185-194`, `tasks.md:227-236`, `tasks.md:353-362`). | OK |
| FR-6 | T29 implements repo-level cycles; T31 tests 2-node/3-node/mixed; T34 adds fixture or RepoIR fallback (`spec.md:202-211`, `tasks.md:409-418`, `tasks.md:441-452`, `tasks.md:485-495`). | OK |
| FR-7 | T7-T11 cover repo index and all SV/Python/C++ emitter/view plumbing (`spec.md:213-234`, `tasks.md:102-166`). | OK |
| FR-8 | T30 implements name conflicts; T31 tests all four cases (`spec.md:236-248`, `tasks.md:422-437`, `tasks.md:441-452`). | OK |
| FR-9 | T19 implements synth imports and layout; T23/T25 verify fixture/goldens (`spec.md:250-259`, `tasks.md:268-279`, `tasks.md:327-336`, `tasks.md:353-362`). | OK |
| FR-9a | T32 implements unconditional duplicate-basename validation and message (`spec.md:261-270`, `tasks.md:456-466`). | OK, but see warning on omitted test file. |
| FR-10 | T19 covers test-package synth/test import blocks and CL-3 layout (`spec.md:272-282`, `tasks.md:268-279`). | OK |
| FR-11 | T20 covers Python import view model/template; T25 verifies generated output (`spec.md:284-292`, `tasks.md:283-293`, `tasks.md:353-362`). | OK |
| FR-12 | T21 covers C++ include and qualification; T26 covers `--namespace=proj::lib` goldens/assertion (`spec.md:294-307`, `tasks.md:297-307`, `tasks.md:366-376`). | OK |
| FR-13 | T18 moves same-module import into template; T24 adds AC-23 AST guard (`spec.md:309-317`, `tasks.md:254-264`, `tasks.md:340-349`). | OK |
| FR-14 | T14 serializes dependencies; T23/T25 cover manifest golden (`spec.md:319-331`, `tasks.md:198-207`, `tasks.md:327-362`). | OK |
| FR-15 | T36 replaces constitution constraint; T37 final verification checks amendment applied (`spec.md:333-343`, `tasks.md:513-542`). | OK |
| FR-16 | T4, T15, T16, T22-T27, T31, T33, T34 cover listed tests/fixtures/goldens/runtime/idempotency (`spec.md:345-363`, `tasks.md:57-70`, `tasks.md:211-236`, `tasks.md:311-391`, `tasks.md:441-495`). | Partial: AC-7 same-process identical-IR evidence is missing. |

### Non-Functional Requirements

| ID | Coverage | Verdict |
|----|----------|---------|
| NFR-1 | Integration checks T6/T11/T17/T28/T35/T37 assert existing tests/goldens byte-identical (`spec.md:367`, `tasks.md:88-96`, `tasks.md:158-166`, `tasks.md:240-248`, `tasks.md:395-403`, `tasks.md:499-507`, `tasks.md:526-542`). | OK |
| NFR-2 | Sort/dedupe requirements are built into T12/T14/T19/T20/T21; idempotency in T25; final check in T37 (`spec.md:368`, `tasks.md:172-181`, `tasks.md:198-207`, `tasks.md:268-307`, `tasks.md:353-362`, `tasks.md:526-542`). | OK |
| NFR-3 | The plan says stdlib + existing Jinja2 only (`plan.md:148-153`) and the constitution forbids extra runtime deps (`.steel/constitution.md:26`, `.steel/constitution.md:112`), but no task verifies dependency metadata or dependency growth. | GAP |
| NFR-4 | T5 adds perf baseline/gate; every commit integration task includes perf gate (`spec.md:370`, `plan.md:310-321`, `tasks.md:74-84`, `tasks.md:158-166`, `tasks.md:240-248`, `tasks.md:395-403`, `tasks.md:499-507`, `tasks.md:526-542`). | OK |
| NFR-5 | T1/T6/T37 run basedpyright (`spec.md:371`, `tasks.md:20-22`, `tasks.md:88-96`, `tasks.md:526-542`). | OK |
| NFR-6 | T36/T37 amend and verify constitution text (`spec.md:372`, `tasks.md:513-542`). | OK |
| NFR-7 | T18/T24/T28 enforce template-first import/include emission (`spec.md:373`, `tasks.md:254-264`, `tasks.md:340-349`, `tasks.md:395-403`). | OK |

### Acceptance Criteria

| ID | Coverage | Verdict |
|----|----------|---------|
| AC-1 | T22-T25 primary fixture, goldens, integration byte-compare (`spec.md:377`, `tasks.md:311-362`). | OK |
| AC-2 | T19 layout, T23 manual review, T25 golden byte-compare (`spec.md:378`, `tasks.md:268-279`, `tasks.md:327-362`). | OK |
| AC-3 | T19/T23/T25 cover unqualified SV type and helper symbols (`spec.md:379`, `tasks.md:268-279`, `tasks.md:327-362`). | OK |
| AC-4 | T19 implements ordered test-package import blocks; T25 byte-compares (`spec.md:380`, `tasks.md:268-279`, `tasks.md:353-362`). | OK |
| AC-5 | T20/T25 cover Python `from ... import` and unqualified annotation (`spec.md:381`, `tasks.md:283-293`, `tasks.md:353-362`). | OK |
| AC-6 | T21/T26 cover include and default/user namespace qualification (`spec.md:382`, `tasks.md:297-307`, `tasks.md:366-376`). | OK |
| AC-7 | T4 covers sequential different-repo sys.modules isolation and within-run identity; T25 covers generated tree idempotency, not same-process identical IR from loading the cross-module fixture twice (`spec.md:383`, `tasks.md:57-70`, `tasks.md:353-362`). | GAP |
| AC-8 | T13 preserves allowlist; T22/T25 exercise ScalarAliasIR, StructIR, FlagsIR, EnumIR via primary fixture (`spec.md:384`, `tasks.md:185-194`, `tasks.md:311-362`). | OK |
| AC-9 | T16 direct RepoIR unknown-type validation (`spec.md:385`, `tasks.md:227-236`). | OK |
| AC-10 | T29/T31/T34 cycle error tests (`spec.md:386`, `tasks.md:409-418`, `tasks.md:441-495`). | OK |
| AC-11 | T29 preserves same-module wording and verifies existing test (`spec.md:387`, `tasks.md:409-418`). | OK |
| AC-12 | T30/T31 local-vs-imported type conflict (`spec.md:388`, `tasks.md:422-452`). | OK |
| AC-13 | T30/T31 imported-vs-imported type conflict (`spec.md:389`, `tasks.md:422-452`). | OK |
| AC-14 | T30/T31 enum literal collision cases (`spec.md:390`, `tasks.md:422-452`). | OK |
| AC-15 | T12/T15 dependency sorted dedupe (`spec.md:391`, `tasks.md:172-181`, `tasks.md:211-223`). | OK |
| AC-16 | T14/T23/T25 manifest schema/golden (`spec.md:392`, `tasks.md:198-207`, `tasks.md:327-362`). | OK |
| AC-17 | T25 idempotency case (`spec.md:393`, `tasks.md:353-362`). | OK |
| AC-18 | T33 multiple-of fixture/goldens/test (`spec.md:394`, `tasks.md:470-481`). | OK |
| AC-19 | T27 Python runtime byte-value/round-trip test (`spec.md:395`, `tasks.md:380-391`). | OK |
| AC-20 | T6/T11/T17/T28/T35/T37 existing tests and goldens (`spec.md:396`, `tasks.md:88-96`, `tasks.md:158-166`, `tasks.md:240-248`, `tasks.md:395-403`, `tasks.md:499-507`, `tasks.md:526-542`). | OK |
| AC-21 | T36/T37 constitution change (`spec.md:397`, `tasks.md:513-542`). | OK |
| AC-22 | T6/T37 basedpyright (`spec.md:398`, `tasks.md:88-96`, `tasks.md:526-542`). | OK |
| AC-23 | T18/T24/T28 AST check over all six backend files (`spec.md:399-417`, `tasks.md:254-264`, `tasks.md:340-349`, `tasks.md:395-403`). | OK |
| AC-24 | T23 manual review against expected `bar_pkg.sv`; T25 golden comparison (`spec.md:418`, `tasks.md:327-362`). | OK |

### Clarifications

| ID | Coverage | Verdict |
|----|----------|---------|
| CL-1 | T19 implements exact SV synth whitespace (`clarifications.md:7-25`, `tasks.md:268-279`). | OK |
| CL-2 | T20 implements Python import placement with no runtime import (`clarifications.md:29-35`, `tasks.md:283-293`). | OK |
| CL-3 | T19 implements contiguous SV test-package import block (`clarifications.md:39-54`, `tasks.md:268-279`). | OK |
| CL-4 | T3 migrates test helpers and searches all callers (`clarifications.md:58-64`, `tasks.md:40-53`). | OK |
| CL-5 | T36 uses exact constitution text (`clarifications.md:68-80`, `tasks.md:513-522`). | OK |
| CL-6 | T29/T31 cover N-node cycle formatting and deterministic rotation (`clarifications.md:84-96`, `tasks.md:409-452`). | OK |
| CL-7 | T18/T24 make AC-23 allowlist empty after template refactor (`clarifications.md:100-109`, `tasks.md:254-264`, `tasks.md:340-349`). | OK |
| CL-8 | T32 preserves fragment assertions and adds no-namespace duplicate test (`clarifications.md:113-119`, `tasks.md:456-466`). | OK, but file list incomplete. |
| CL-9 | T14 preserves empty `dependencies: []` and existing manifest golden byte-parity (`clarifications.md:123-129`, `tasks.md:198-207`). | OK |
| CL-10 | T12/T15 collect cross-module const refs via dependency visitor without rewriting `_freeze_expr` (`clarifications.md:133-139`, `tasks.md:172-181`, `tasks.md:211-223`). | OK |

## Issues

### BLOCKING

- AC-7 is missing a required evidence task. The spec requires "Loading the cross-module fixture twice in the same Python process produces identical IR" and also different-fixture sys.modules cleanup (`spec.md:383`). T4 tests snapshot/restore, two different fixture repos, within-run object identity, and outside-scope errors (`tasks.md:57-70`), but it lands before the cross-module fixture exists and does not assert identical IR for loading that fixture twice. T25's idempotency case compares generated `gen/` trees (`tasks.md:353-362`), not same-process IR identity. Suggested fix: add a post-T22/T23 task, or extend T25, to load `cross_module_type_refs` twice in one Python process via `prepare_run`/`load_or_get_module`, freeze both runs, and compare the resulting `RepoIR` deterministically.

- NFR-3 has no explicit verification path. The spec forbids runtime dependency growth (`spec.md:369`), the plan limits implementation to stdlib and existing Jinja2 (`plan.md:148-153`), and the constitution says no external runtime dependencies beyond Jinja2 / no network dependencies (`.steel/constitution.md:26`, `.steel/constitution.md:112`). T37's final checklist covers tests, goldens, AC-23, basedpyright, perf, and constitution amendment, but not dependency metadata or dependency growth (`tasks.md:526-535`). Suggested fix: add a T37 bullet or a small task that verifies `pyproject.toml` runtime dependencies remain unchanged and no new external dependency files or network/runtime packages were introduced.

### WARNING

- T32 promises a new duplicate-basename test but omits the test file from its file list. The plan explicitly says `tests/test_namespace_validation.py` is extended (`plan.md:90-96`), and T32 verification says a new case verifies duplicate basenames without `--namespace` (`tasks.md:456-466`), but T32's file list only includes `src/piketype/commands/gen.py` and `src/piketype/validate/namespace.py` (`tasks.md:460-463`). Add `tests/test_namespace_validation.py` to T32's files.

- R8's documentation mitigation is not assigned to a task. The plan says the named-type assumption should be documented in the freeze module docstring after FR-2 (`plan.md:269-273`). No task mentions that documentation. Add a sentence to T12 or T15 if the team still wants that mitigation.

- The plan requires adding a basedpyright CI gate if the project does not already have one (`plan.md:323-325`). The current source has basedpyright config in `pyproject.toml` (`pyproject.toml:44-49`), but this checkout has no `.github` workflow or other CI file. The tasks run basedpyright manually in T6/T37 (`tasks.md:88-96`, `tasks.md:526-542`), but they do not add CI. Either add a Commit-A CI task or remove that plan commitment.

### NOTE

- Dependency ordering mostly matches the staging note. Commit B starts only after T6 (`tasks.md:102-110`), Commit C after T11 (`tasks.md:172-192`), Commit D after T17 for backend work (`tasks.md:254-305`), Commit E after T28 (`tasks.md:409-479`), and Commit F after T35 (`tasks.md:513-520`), which matches the spec's A-F staging (`spec.md:38-49`).

- Parallelization opportunities exist and are worth stating explicitly: T8/T9/T10 can run in parallel after T7; T12 and T13 can run in parallel after T11; T20/T21 can run in parallel with T18/T19 after T17 where file ownership is disjoint; T29/T30/T32/T33 can start independently after T28, with T31 waiting on T29/T30.

- Integration-check tasks are clearly separate from implementation tasks: T6, T11, T17, T28, T35, and T37 have no file edits and only verify/commit (`tasks.md:88-96`, `tasks.md:158-166`, `tasks.md:240-248`, `tasks.md:395-403`, `tasks.md:499-507`, `tasks.md:526-542`).

## Strengths

- The task list respects the byte-parity-per-commit strategy: every commit ends with a full integration check, and the new output goldens wait until Commit D when emission is wired (`spec.md:40-49`, `tasks.md:546-559`).

- The template-first requirement is handled well. T18 removes the existing SV Python-side import string, and T24 hardens enforcement with an AST check over all backend view/emitter files (`spec.md:309-317`, `spec.md:399-417`, `tasks.md:254-264`, `tasks.md:340-349`).

- Risk coverage is strong for R1-R7: loader isolation, repo-wide index, SV helper imports, AC-23 false positives, perf, template byte-parity, and cycle-fixture infeasibility all map to concrete tasks (`plan.md:233-279`, `tasks.md:57-84`, `tasks.md:102-166`, `tasks.md:268-349`, `tasks.md:485-495`).

VERDICT: REVISE
