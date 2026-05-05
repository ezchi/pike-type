# Tasks: 016-vec-const-dsl-primitive

**Spec:** `specs/016-vec-const-dsl-primitive/spec.md`
**Plan:** `specs/016-vec-const-dsl-primitive/plan.md`
**Branch:** `feature/016-vec-const-dsl-primitive`

## Plan Corrections Required

None. All paths and tools cited in `plan.md` were verified against the current repo state at task-breakdown time:

- `src/piketype/ir/nodes.py`, `dsl/const.py`, `dsl/__init__.py`, `dsl/freeze.py`, `backends/sv/view.py`, `backends/sv/templates/module_synth.j2`, `manifest/write_json.py` — all exist.
- `tests/test_gen_const_sv.py` — exists; will be the template for the new `tests/test_gen_vec_const.py`.
- `tests/test_gen_cross_module.py`, `test_gen_enum.py`, `test_gen_flags.py` — additional templates available.
- `tests/fixtures/vec_const_basic/`, `tests/fixtures/vec_const_cross_module/`, `tests/goldens/gen/vec_const_basic/`, `tests/goldens/gen/vec_const_cross_module/` — do NOT exist (T8/T9 create them).
- `.venv/bin/python` and `.venv/bin/basedpyright` — available (per memory `project_venv_required_for_piketype.md`).
- Existing manifest goldens count: **24** under `tests/goldens/gen/*/piketype_manifest.json`. T11 regenerates all of them to add the new `"vec_constants": []` line per FR-18.

## Conventions

- Ad-hoc Python invocations MUST use `.venv/bin/python` (or via `.venv/bin/piketype` for the CLI console-script).
- Commits follow Conventional Commits per Constitution §Branching & Commits: `<type>(<scope>): <description>`. Recommended scope `dsl` for DSL/IR/freeze, `sv` for SV view/template, `manifest` for `manifest/write_json.py`, `test` for new tests.
- All Python files start with `from __future__ import annotations` (Constitution §Coding Standards Python).

## Task List

---

### T1. Add `VecConstIR` and `VecConstImportIR` to `ir/nodes.py`; extend `ModuleIR`

**Description:**
Add two new frozen dataclasses (`VecConstIR`, `VecConstImportIR`) and two new fields on `ModuleIR` (`vec_constants`, `vec_const_imports`) per Plan Component 2. Both new fields default to `()` so existing kwargs callers stay green.

**Files:** `src/piketype/ir/nodes.py` (modified)

**Dependencies:** none

**Verification:**
- `python -c "from piketype.ir.nodes import VecConstIR, VecConstImportIR, ModuleIR; print(VecConstIR.__match_args__)"` succeeds.
- `ModuleIR(...)` constructor still accepts existing kwargs without `vec_constants`/`vec_const_imports`.
- basedpyright clean on `ir/nodes.py`.

---

### T2. Add `VecConst` class to `dsl/const.py`; export from `dsl/__init__.py`

**Description:**
Add the `VecConst` mutable dataclass per Plan Component 1. Construction validates `base ∈ {"hex","dec","bin"}`. Captures source via `capture_source_info()`. Stores raw `width_expr` and `value_expr` (from `_coerce_operand`) — does NOT evaluate at construction time (freeze does that with the cross-module map). Does NOT define `__add__`/`__or__`/etc. — VecConst is NOT a `ConstOperand`.

Export the class from `dsl/__init__.py` so `from piketype.dsl import VecConst` works (AC-1).

**Files:** `src/piketype/dsl/const.py` (modified), `src/piketype/dsl/__init__.py` (modified)

**Dependencies:** T1

**Verification (covers FR-1, FR-2, FR-3):**
- `from piketype.dsl import VecConst` succeeds.
- `VecConst(width=8, value=0, base="oct")` raises `ValidationError` (AC-8 sentinel; full negative coverage in T4).
- basedpyright clean on the two modified files.

---

### T3. Implement freeze logic for VecConst in `dsl/freeze.py`

**Description:**
Implement Plan Component 3:

1. Extend the four existing isinstance check sites (~lines 82, 101, 127, 131) to include `VecConst`.
2. Add `build_vec_const_definition_map(*, loaded_modules) -> dict[int, tuple[ModuleRefIR, str]]` mirroring the existing `build_const_definition_map` (line 74). First-sighting wins.
3. Add `_freeze_vec_const_storage(*, width: int, value: int, base: str, source: SourceSpanIR, name: str) -> VecConstIR` that validates width 1..64 (FR-4, FR-5) and overflow `0 <= value <= 2**width - 1` (FR-7, FR-8). Error messages MUST contain the offending value, the width N, and the literal substring `2**N - 1` (with N substituted) per FR-7 contract.
4. Add `_freeze_vec_const(loaded_module, name, vec_const, *, const_definition_map, vec_const_definition_map) -> VecConstIR` that evaluates `width_expr` and `value_expr` via the existing `_eval_expr` machinery (line 463), then calls `_freeze_vec_const_storage`.
5. In `freeze_module`: build `local_vec_constants` for first-sightings; build `vec_const_imports` (list of `VecConstImportIR`) for non-local sightings; append matching `ModuleDependencyIR(target=defining_module_ref, kind="vec_const_import")` to dependencies, deduplicated against existing `(target, kind)` pairs.
6. Update `freeze_repo`'s call site to pass the new `vec_const_definition_map` arg through.

**Files:** `src/piketype/dsl/freeze.py` (modified)

**Dependencies:** T1, T2

**Verification (covers FR-4, FR-5, FR-6, FR-7, FR-8, FR-13 dep-edge half):**
- A unit-level smoke check: load a fixture with `LP_X = VecConst(width=8, value=0xAB, base="hex")` and verify `module.vec_constants` contains a `VecConstIR(name="LP_X", width=8, value=171, base="hex", ...)`.
- A cross-module smoke check: module A defines `LP_X`, module B does `from a import LP_X`. Verify `module_b.vec_const_imports` contains `VecConstImportIR(target_module_ref=A.ref, symbol_name="LP_X")` AND `module_b.dependencies` contains a `ModuleDependencyIR(target=A.ref, kind="vec_const_import")` (deduped).

(Both smoke checks happen as part of T4 / T10. T3 is correctness-by-construction; full verification is downstream.)

---

### T4. Validation negative tests in `tests/test_vec_const_validation.py`

**Description:**
Create new `tests/test_vec_const_validation.py` with five `unittest.TestCase` methods covering AC-4 through AC-8:

1. `test_overflow_8bit_300` — `VecConst(width=8, value=300, base="dec")` raises `ValidationError` whose message contains the substrings `"300"`, `"8"`, and `"2**8 - 1"` (FR-7 three-substring contract). [AC-4]
2. `test_negative_value_rejected` — `VecConst(width=8, value=-1, base="dec")` raises `ValidationError` naming the negative-value rejection. [AC-5]
3. `test_zero_or_negative_width_rejected` — `VecConst(width=0, value=0, base="dec")` raises; same for `width=-1`. [AC-6]
4. `test_width_above_64_rejected` — `VecConst(width=65, value=0, base="hex")` raises. [AC-7]
5. `test_unsupported_base_rejected` — `VecConst(width=8, value=0, base="oct")` raises naming the offending base value. [AC-8]

Each test constructs the offending DSL inline via `tempfile.TemporaryDirectory()` + minimal fixture file pattern (or, if the validation fires at `VecConst.__init__`, directly via `from piketype.dsl import VecConst; VecConst(...)`). Use `assertRaisesRegex` with substring-bearing patterns to enforce FR-7's three-substring rule for AC-4.

**Files:** `tests/test_vec_const_validation.py` (new)

**Dependencies:** T2 (DSL class), T3 (freeze validation — error messages from FR-7 fire at freeze time, so tests need a minimal repo+freeze pipeline OR direct `VecConst()` construction if we put validation at `__init__` for the simplest cases)

**Verification:** all 5 tests pass via `.venv/bin/python -m unittest tests.test_vec_const_validation -v`.

---

### T5. Update `manifest/write_json.py` to emit `vec_constants` array

**Description:**
Per Plan Component 8, in the per-module dict construction (line ~85), add a new `"vec_constants"` array sibling to `"constants"`. Each entry has fields: `name`, `width`, `value`, `base`, `source` (file:line). Legacy `"constants"` schema unchanged (FR-18 reinforced).

**Files:** `src/piketype/manifest/write_json.py` (modified)

**Dependencies:** T1, T3

**Verification (covers FR-18):**
- For a module with no VecConst declarations, the manifest entry contains `"vec_constants": []`.
- For a module with VecConst declarations, each entry has the five required fields.
- The legacy `"constants"` array's existing entries do NOT gain a `kind` field.
- (Full verification happens at T9/T10 against the new fixture goldens AND at T11 against regenerated existing manifests.)

---

### T6. SV emission: extend `backends/sv/view.py` and `module_synth.j2`

**Description:**
Per Plan Component 5:

1. Add `SvVecConstantView` dataclass with fields `name`, `sv_type`, `sv_expr`.
2. Add `_render_sv_vec_literal(*, width: int, value: int, base: str) -> str` exactly per the plan's concrete code:
   ```python
   match base:
       case "hex": return f"{width}'h{value:0{(width + 3) // 4}X}"
       case "dec": return f"{width}'d{value}"
       case "bin": return f"{width}'b{value:0{width}b}"
       case _: raise ValueError(f"unsupported base: {base!r}")
   ```
3. Add `_build_vec_constant_view(*, vec_const_ir: VecConstIR) -> SvVecConstantView` that calls `_render_sv_vec_literal` and constructs `sv_type = f"logic [{vec_const_ir.width - 1}:0]"`.
4. Extend the SV synth module-view dataclass (~line 162) with `vec_constants: tuple[SvVecConstantView, ...]` and `has_vec_constants: bool`.
5. Wire up at the module-view assembly site (line ~717).
6. Extend `_collect_cross_module_synth_imports` (line 774): after the existing `for ref in _iter_cross_module_typerefs(...)` loop, add:
   ```python
   for vci in module.vec_const_imports:
       pairs.add((f"{vci.target_module_ref.basename}_pkg", vci.symbol_name))
   ```
7. Extend `templates/module_synth.j2`: after the existing `{% for c in constants %}` block, add:
   ```jinja
   {% for v in vec_constants %}
     localparam {{ v.sv_type }} {{ v.name }} = {{ v.sv_expr }};
   {% endfor %}
   ```
   Update the blank-line conditional to `{% if (has_constants or has_vec_constants) and has_types %}`.

**Files:** `src/piketype/backends/sv/view.py` (modified), `src/piketype/backends/sv/templates/module_synth.j2` (modified)

**Dependencies:** T1, T3

**Verification (covers FR-9, FR-10, FR-11, FR-12, FR-13 SV-side):**
- `_render_sv_vec_literal(width=8, value=15, base="hex")` returns `"8'h0F"`.
- `_render_sv_vec_literal(width=12, value=0, base="hex")` returns `"12'h000"` (3 digits).
- `_render_sv_vec_literal(width=16, value=0xab, base="hex")` returns `"16'h00AB"` (uppercase).
- `_render_sv_vec_literal(width=8, value=15, base="bin")` returns `"8'b00001111"`.
- `_render_sv_vec_literal(width=8, value=15, base="dec")` returns `"8'd15"`.
- (Empirical SV-emission check happens at T9/T10 against fixture goldens.)

---

### T7. Amend Constitution `§Constraints` item 5

**Description:**
Edit `.steel/constitution.md` §Constraints item 5 to the wording in spec FR-14:

> **5. Const widths restricted to 32/64 bits.** The legacy `Const()` parameter primitive accepts width 32, 64, or unspecified (default int). The newer `VecConst()` primitive accepts arbitrary positive widths from 1 through 64 inclusive (see FR-5). Both are validated by the validation layer; widths outside their respective allowed ranges are rejected.

**Files:** `.steel/constitution.md` (modified)

**Dependencies:** none (independent of code changes)

**Verification:** the diff for constitution.md replaces exactly the cited paragraph; no other Constitution clause is touched (FR-15 / R-6).

---

### T8. Create fixtures: `vec_const_basic` and `vec_const_cross_module`

**Description:**
Create two fixture trees:

1. `tests/fixtures/vec_const_basic/project/alpha/piketype/vecs.py`:
   ```python
   from piketype.dsl import Const, VecConst

   A = Const(5)
   B = VecConst(width=8, value=A * 3, base="dec")
   LP_ETHERTYPE_VLAN = VecConst(width=16, value=0x8100, base="hex")
   LP_IP_PROTOCOL_TCP = VecConst(width=8, value=6, base="dec")
   LP_IP_PROTOCOL_UDP = VecConst(width=8, value=17, base="dec")
   LP_NIBBLE_F = VecConst(width=4, value=0xF, base="hex")
   LP_PADDED_HEX = VecConst(width=8, value=0x0F, base="hex")
   LP_PADDED_BIN = VecConst(width=8, value=0xF, base="bin")
   LP_AB16 = VecConst(width=16, value=0xab, base="hex")
   ```

2. `tests/fixtures/vec_const_cross_module/project/alpha/{a,b}/piketype/types.py`. Module `a` defines `LP_X = VecConst(width=16, value=0x1234, base="hex")`. Module `b` does `from alpha.a.piketype.types import LP_X` (or whatever the project's import convention dictates — match existing `tests/fixtures/cross_module_type_refs/` pattern).

Use the existing `tests/fixtures/const_sv_basic/project/` and `tests/fixtures/cross_module_type_refs/project/` layouts as templates (single-module and two-module respectively).

**Files:** new files under `tests/fixtures/vec_const_basic/project/alpha/piketype/vecs.py` and `tests/fixtures/vec_const_cross_module/project/alpha/{a,b}/piketype/types.py`

**Dependencies:** T2

**Verification:**
- The fixture imports succeed with `.venv/bin/python` against the new DSL surface.
- File layout matches the existing fixture conventions (basename, namespace_parts).

---

### T9. Generate goldens by running `piketype gen` against the new fixtures

**Description:**
For each new fixture, copy the project tree to a temp dir, run `piketype gen` against each DSL `.py` file (matching the existing test loop pattern in `test_gen_const_sv.py`), then commit the resulting `gen/` tree as the golden under `tests/goldens/gen/vec_const_basic/` and `tests/goldens/gen/vec_const_cross_module/`.

**Verification of each golden BEFORE commit (manual review — implementer is the gauge here):**
- `tests/goldens/gen/vec_const_basic/sv/alpha/piketype/vecs_pkg.sv` MUST contain:
  - `localparam int A = 32'sd5;` (existing Const emission unchanged — AC-12)
  - `localparam logic [7:0] B = 8'd15;` (AC-3 — `A * 3` evaluated to 15)
  - `localparam logic [15:0] LP_ETHERTYPE_VLAN = 16'h8100;` (AC-2)
  - `localparam logic [7:0] LP_IP_PROTOCOL_TCP = 8'd6;`
  - `localparam logic [7:0] LP_IP_PROTOCOL_UDP = 8'd17;`
  - `localparam logic [3:0] LP_NIBBLE_F = 4'hF;` (1 hex digit, `(4+3)//4=1`)
  - `localparam logic [7:0] LP_PADDED_HEX = 8'h0F;` (AC-9)
  - `localparam logic [7:0] LP_PADDED_BIN = 8'b00001111;` (AC-9)
  - `localparam logic [15:0] LP_AB16 = 16'h00AB;` (AC-10 — uppercase, zero-pad)
- `tests/goldens/gen/vec_const_cross_module/sv/alpha/b/piketype/types_pkg.sv` MUST contain `import a_pkg::LP_X;` (AC-11; per-symbol per Plan Component 5).
- C++ headers (`*_types.hpp`) and Python (`*_types.py`) files for the basic fixture must NOT contain any VecConst output (FR-16/17 verification by absence).
- The `piketype_manifest.json` for both fixtures MUST contain a `"vec_constants": [...]` array per module (FR-18); legacy `"constants"` array entries unchanged in shape.

**Files:** new tree under `tests/goldens/gen/vec_const_basic/` and `tests/goldens/gen/vec_const_cross_module/`.

**Dependencies:** T1–T8 (everything code-side)

---

### T10. Add integration test `tests/test_gen_vec_const.py`

**Description:**
Create new `tests/test_gen_vec_const.py` modeled on `tests/test_gen_const_sv.py`, with two test methods:

1. `test_vec_const_basic_generates_expected_tree` — runs `piketype gen` against `tests/fixtures/vec_const_basic/project/alpha/piketype/vecs.py` and diffs the generated `gen/` tree byte-for-byte against `tests/goldens/gen/vec_const_basic/`. Reuses the `assert_trees_equal` and `copy_tree` helpers (either by import from `test_gen_const_sv` or by duplicating the helpers — match existing project pattern).
2. `test_vec_const_cross_module_emits_per_symbol_import` — runs `piketype gen` against the cross-module fixture; diffs the full tree; additionally asserts that the emitted `b_pkg.sv` contains the literal substring `import a_pkg::LP_X;`. (AC-11 explicit assertion, in addition to the byte-for-byte tree compare.)

**Files:** `tests/test_gen_vec_const.py` (new)

**Dependencies:** T8, T9

**Verification:** both tests pass via `.venv/bin/python -m unittest tests.test_gen_vec_const -v`.

---

### T11. Regenerate every existing manifest golden to add `"vec_constants": []`

**Description:**
Per Risk R-2: every existing per-module manifest in `tests/goldens/gen/*/piketype_manifest.json` (24 files) gains an empty `"vec_constants": []` entry per module after T5. Re-run the existing golden tests' generation step to regenerate all manifest goldens, OR run `piketype gen` against each existing fixture and copy the regenerated `piketype_manifest.json` into the corresponding golden directory.

A scripted approach:
```bash
for fixture_dir in tests/fixtures/*/project; do
  name=$(basename $(dirname "$fixture_dir"))
  with tempfile.TemporaryDirectory() as tmp:
    copy_tree(fixture_dir, tmp)
    cd tmp && .venv/bin/piketype gen <appropriate-cli-arg>
    cp tmp/gen/piketype_manifest.json tests/goldens/gen/$name/piketype_manifest.json
done
```
(Implementer may script this in Python or shell as preferred. The single requirement is: the resulting manifest goldens differ from the pre-change goldens by ONLY the addition of `"vec_constants": []` per module entry.)

**Verification:**
- `git diff tests/goldens/gen/*/piketype_manifest.json` shows ONLY additions of `"vec_constants": []` lines (no other changes).
- All existing golden integration tests (`test_gen_const_sv`, `test_gen_cross_module`, `test_gen_enum`, `test_gen_flags`, etc.) pass after regeneration (T12 will catch any regression).

**Files:** modified — `tests/goldens/gen/*/piketype_manifest.json` (24 files)

**Dependencies:** T5

---

### T12. Run the full unittest suite and confirm green

**Description:**
Run `.venv/bin/python -m unittest discover -s tests -v` and confirm exit code 0. Specifically:

- All NEW tests pass (`test_vec_const_validation`, `test_gen_vec_const`).
- No PRE-EXISTING test fails. Pre-existing manifest golden tests (e.g., the manifest-shape assertion in `test_gen_const_sv` / `test_gen_cross_module` / etc.) MUST pass against the regenerated manifests from T11.
- 3 pre-existing skipped tests remain (the `develop` baseline includes them; T12 must not introduce new skips).

**Verification:**
- Exit code 0.
- `OK` line at the bottom of the output.
- Test count BEFORE this branch was 307 (per spec 015 retrospect). New count should be 307 + 5 (T4) + 2 (T10) = 314 (or thereabouts; minor variance OK as long as no regressions).

**Files:** none modified

**Dependencies:** T1–T11

---

### T13. Run basedpyright strict on all changed Python files

**Description:**
Run:
```
.venv/bin/basedpyright \
  src/piketype/ir/nodes.py \
  src/piketype/dsl/const.py \
  src/piketype/dsl/__init__.py \
  src/piketype/dsl/freeze.py \
  src/piketype/backends/sv/view.py \
  src/piketype/manifest/write_json.py \
  tests/test_vec_const_validation.py \
  tests/test_gen_vec_const.py
```

Confirm zero errors, zero warnings, zero notes on the listed files.

Per memory `project_basedpyright_baseline_drift.md`: develop has 100 pre-existing errors elsewhere; measure delta on changed files only.

**Verification (covers AC-7, AC-15, NFR-3):**
- `0 errors, 0 warnings, 0 notes` on the listed files.

**Files:** none modified

**Dependencies:** T1–T11

---

## Task Dependency Graph

```
T1 ──► T2 ──► T3 ──► T4
   │       │     │
   │       │     ├──► T5 ───────────┐
   │       │     │                  │
   │       │     ├──► T6 ───┐       │
   │       │     │          │       │
   │       │     └──► T8 ──► T9 ──► T10
   │       │                │       │
   T7 (independent)         │       │
                            └─►─────┴──► T11 ──► T12 ──► T13
```

T1 → T2 → T3 is the critical path. T4 follows T3. T5/T6 follow T3. T7 is independent. T8/T9 are sequenced. T10/T11 follow once code-side and goldens are stable. T12/T13 are gates.

## Out-of-Task Concerns

- **No CMake / build / pyproject.toml edits** — the change is pure Python + Jinja template + new tests/goldens.
- **No CI / settings.json edits** — the harness is unchanged.
- **No top-level docs / RFC updates** — the Constitution amendment in T7 IS the doc change.
- **No new external runtime dependency** — Jinja2-only constraint preserved (NFR-1 is "no new runtime dep").
