# Implementation Plan: 016-vec-const-dsl-primitive

**Spec:** `specs/016-vec-const-dsl-primitive/spec.md`
**Clarifications:** `specs/016-vec-const-dsl-primitive/clarifications.md`
**Branch:** `feature/016-vec-const-dsl-primitive`

## Architecture Overview

`VecConst` is a new top-level DSL primitive parallel to `Const`. It flows through the existing pipeline (Discovery → DSL → IR → Backends, per Constitution Principle 2) without changing any pipeline boundary. Each subsystem gets a small, additive change:

```
DSL                   IR                  Backends
├─ const.py           ├─ nodes.py          ├─ sv/view.py + module_synth.j2
│   └─ +VecConst      │   └─ +VecConstIR   │   └─ +SvVecConstantView, emit lines
└─ freeze.py          │   ModuleIR.        ├─ cpp/   (no-op per FR-16)
    └─ +freeze        │     +vec_constants └─ py/    (no-op per FR-17)
                                          manifest/write_json.py
                                              └─ +"vec_constants": [...]
.steel/constitution.md  ←  amend §Constraints item 5 (FR-14)
tests/  ←  new fixture + golden + validation negative tests
```

No new module is introduced; six existing files are edited and one new test file is added (plus fixture + golden tree).

## Components

### 1. DSL surface — `src/piketype/dsl/const.py`

**Change:** add a new top-level class `VecConst` exported from the same import path as `Const`.

```python
@dataclass(slots=True)
class VecConst(DslNode):
    """Fixed-width logic vector constant with explicit base."""

    SUPPORTED_BASES: ClassVar[set[str]] = {"hex", "dec", "bin"}

    width: int
    value: int
    base: str
    width_expr: ConstExpr
    value_expr: ConstExpr

    def __init__(
        self,
        *,
        width: int | Const | ConstExpr,
        value: int | Const | ConstExpr,
        base: str,
    ) -> None:
        # 1. base validation (FR-3)
        # 2. capture source via capture_source_info()
        # 3. coerce width and value via _coerce_operand
        # 4. (do NOT _eval_expr here — freeze evaluates with cross-module map)
        # 5. record raw expressions; resolved width/value computed at freeze time
```

VecConst does **not** define `__add__`, `__or__`, etc. — it is NOT a `ConstOperand`. Per spec it's a leaf "named literal", not an arithmetic operand for other constants. (See Risks R-3.)

`SUPPORTED_BASES` and `__init__` raise `ValidationError` for invalid base. Source-info captured at construction so error messages can locate the offending line (AC-13).

### 2. IR — `src/piketype/ir/nodes.py`

**Change:** add `VecConstIR` frozen dataclass and a new field on `ModuleIR`.

```python
@dataclass(frozen=True, slots=True)
class VecConstIR:
    """Frozen logic-vector constant definition."""

    name: str
    source: SourceSpanIR
    width: int       # resolved
    value: int       # resolved (already overflow-checked)
    base: str        # "hex" | "dec" | "bin"


@dataclass(frozen=True, slots=True)
class ModuleIR:
    ref: ModuleRefIR
    source: SourceSpanIR
    constants: tuple[ConstIR, ...]
    types: tuple[TypeDefIR, ...]
    dependencies: tuple[ModuleDependencyIR, ...]
    vec_constants: tuple[VecConstIR, ...] = ()   # NEW, with default for compat
```

**Compatibility note:** `vec_constants` is added with `= ()` default at the end so existing constructors that pass positional or kwargs without it keep working. All in-tree call sites use kwargs (verified via grep), so this is safe. (See Risks R-1.)

### 3. Freeze — `src/piketype/dsl/freeze.py`

**Change:** detect `VecConst` instances in module-level scan, evaluate expressions to ints using the same cross-module `definition_map` mechanism as `Const`, run validation, build `VecConstIR`.

Specifically:

- Extend the type-collection isinstance checks at lines ~82, 101, 127, 131 to include `VecConst`.
- New helper `_freeze_vec_const_storage(*, width: int, value: int, base: str, source: SourceSpanIR) -> VecConstIR` that:
  - asserts `width >= 1 and width <= 64` (FR-4, FR-5) — raises `ValidationError` otherwise.
  - asserts `0 <= value <= 2**width - 1` (FR-7, FR-8) — raises `ValidationError` with the formula-substring contract.
  - returns `VecConstIR(...)`.
- New helper `_freeze_vec_const(loaded_module, name, vec_const, *, definition_map) -> VecConstIR` that:
  - evaluates `vec_const.width_expr` and `vec_const.value_expr` to ints via the same `_eval_expr` machinery already used for `Const` (line 463). The cross-module `definition_map` parameter ensures `VecConst(value=A * 3)` where `A` is a Const from another module resolves correctly (and the dependency edge is naturally tracked through `_collect_const_refs`).
- In `freeze_module`, after the existing `local_constants` loop, add a parallel `local_vec_constants: list[VecConstIR]` loop, append to a new `vec_constants` arg passed to `ModuleIR(...)`.

### 4. Validation — `src/piketype/validate/engine.py`

**No changes for v1.** All `VecConst` validation is freeze-time (in `_freeze_vec_const_storage`), exactly mirroring how `Const` validation is freeze-time in `_validate_const_storage` (line 555). This keeps validation co-located with the IR build and produces clean error messages with source info. The validate engine's existing passes (cycles, namespace collisions, unique basenames) are not affected by VecConst because VecConst is module-local and is not a struct field type.

### 5. SV backend — `src/piketype/backends/sv/view.py` and `templates/module_synth.j2`

**Change in `view.py`:**

- Add new dataclass:
  ```python
  @dataclass(frozen=True, slots=True)
  class SvVecConstantView:
      name: str           # FR-12: verbatim
      sv_type: str        # "logic [N-1:0]"
      sv_expr: str        # "N'<L><digits>" — pre-rendered, FR-9..11
  ```
- Add helper `_render_sv_vec_literal(*, width: int, value: int, base: str) -> str` that produces the `N'<L><digits>` literal:
  - Map `base="hex" → "h", "dec" → "d", "bin" → "b"` (FR-9).
  - For hex: render value with `format(value, "x").upper()`, zero-pad to `width // 4` (rounded up for non-multiple-of-4 widths). Compute `pad_len = (width + 3) // 4` so a `width=12` hex value zero-pads to 3 hex digits. (FR-10, FR-11.)
  - For bin: render value with `format(value, "b")`, zero-pad to `width`. (FR-11.)
  - For dec: render value with `format(value, "d")` — no padding. (FR-11.)
- Add `_build_vec_constant_view(*, vec_const_ir: VecConstIR) -> SvVecConstantView`.
- Extend the module-view dataclass (~line 162) to add:
  ```python
  vec_constants: tuple[SvVecConstantView, ...]
  has_vec_constants: bool
  ```
- Wire up at the module-view assembly site (line ~717):
  ```python
  vec_constants=tuple(_build_vec_constant_view(vec_const_ir=v) for v in module.vec_constants),
  has_vec_constants=bool(module.vec_constants),
  ```

**Change in `templates/module_synth.j2`:** add a vec_constants emission block parallel to the existing constants block. The exact insertion point is just after the `constants` for-loop and before the types-block — this matches the user's example output (`localparam int A`, then `localparam logic [7:0] B`):

```jinja
{% for c in constants %}
  localparam {{ c.sv_type }} {{ c.name }} = {{ c.sv_expr }};
{% endfor %}
{% for v in vec_constants %}
  localparam {{ v.sv_type }} {{ v.name }} = {{ v.sv_expr }};
{% endfor %}
{% if (has_constants or has_vec_constants) and has_types %}

{% endif %}
```

The `has_constants and has_types` blank-line rule is extended to `(has_constants or has_vec_constants) and has_types`.

### 6. C++ backend — no-op per FR-16

The C++ emitter currently iterates `module.constants` and `module.types`. It does NOT iterate `vec_constants`, so VecConst declarations naturally produce no C++ output — exactly per FR-16. **No code change** in `backends/cpp/`. The plan explicitly verifies this in T6 by inspecting C++ goldens for the new fixture.

### 7. Python backend — no-op per FR-17

Same reasoning as C++. **No code change** in `backends/py/`. Verified in T6.

### 8. Manifest — `src/piketype/manifest/write_json.py`

**Change:** in the per-module dict construction (line ~85), add:

```python
"vec_constants": [
    {
        "name": v.name,
        "width": v.width,
        "value": v.value,
        "base": v.base,
        "source": _source_dict(v.source),
    }
    for v in module.vec_constants
],
```

The legacy `"constants"` array stays byte-identical (FR-18 reinforced clarification). For modules with no VecConst declarations, `vec_constants: []` is emitted. (See Risks R-2 — every existing manifest golden gains a `"vec_constants": []` line, breaking byte-identity. See R-2 mitigation.)

### 9. Constitution amendment — `.steel/constitution.md`

**Change:** edit `§Constraints` item 5 to the wording in spec FR-14:

> **5. Const widths restricted to 32/64 bits.** The legacy `Const()` parameter primitive accepts width 32, 64, or unspecified (default int). The newer `VecConst()` primitive accepts arbitrary positive widths from 1 through 64 inclusive (see FR-5). Both are validated by the validation layer; widths outside their respective allowed ranges are rejected.

### 10. Tests

**New fixture:** `tests/fixtures/vec_const_basic/project/alpha/piketype/vecs.py`
```python
from piketype.dsl import Const, VecConst

A = Const(5)
B = VecConst(width=8, value=A * 3, base="dec")
LP_ETHERTYPE_VLAN = VecConst(width=16, value=0x8100, base="hex")
LP_IP_PROTOCOL_TCP = VecConst(width=8, value=6, base="dec")
LP_IP_PROTOCOL_UDP = VecConst(width=8, value=17, base="dec")
LP_NIBBLE_F = VecConst(width=4, value=0xF, base="hex")     # exercises non-mult-of-4 width pad
LP_PADDED_HEX = VecConst(width=8, value=0x0F, base="hex")   # → 8'h0F
LP_PADDED_BIN = VecConst(width=8, value=0xF, base="bin")    # → 8'b00001111
```

**New golden:** `tests/goldens/gen/vec_const_basic/sv/alpha/piketype/vecs_pkg.sv` (synth pkg with the 7 VecConst lines + 1 Const line) and the C++/Py/manifest goldens — Python and C++ headers contain ONLY the constants array entries (verifying FR-16/17 at golden level).

**New integration test:** `tests/test_gen_vec_const.py` — follows the existing golden-test pattern (`tests/test_gen_const_sv.py` is the model). Runs `piketype gen` against the fixture and compares the entire `gen/` tree byte-for-byte against the golden tree (Constitution §Testing pattern).

**New validation tests:** `tests/test_vec_const_validation.py` — focused negative tests for AC-4 through AC-8. Pattern: construct the offending DSL via `exec()`-like or direct API calls, assert `ValidationError` raised with the expected message substrings.

**Changelog:** existing manifest goldens that just gained `"vec_constants": []` will be regenerated as part of T9 (see R-2).

## Data Model

| Layer | Class / Field | Notes |
|-------|--------------|-------|
| DSL | `VecConst(DslNode)` | Mutable, `slots=True`. Stores `width`, `value`, `base`, `width_expr`, `value_expr`. |
| IR | `VecConstIR` | Frozen, `slots=True`. Stores resolved `width`, `value` (after overflow check), `base`, `name`, `source`. |
| IR | `ModuleIR.vec_constants: tuple[VecConstIR, ...] = ()` | Default-empty tuple; non-breaking on existing kwargs callers. |
| SV view | `SvVecConstantView` | Frozen view-model with pre-rendered `sv_type` and `sv_expr` strings. |
| Manifest | `vec_constants: [...]` | New per-module array. Each entry: `name`, `width`, `value`, `base`, `source`. |

## API Design

Public DSL surface added: `VecConst` from `piketype.dsl`.

Signature (FR-2):
```python
def VecConst(
    *,
    width: int | Const | ConstExpr,
    value: int | Const | ConstExpr,
    base: str,
) -> VecConst: ...
```

All three arguments are keyword-only. Existing `Const` API is unchanged.

## Dependencies

None added. The implementation uses only stdlib (`dataclasses`, `typing.ClassVar`) and existing internal helpers (`_coerce_operand`, `_eval_expr`, `capture_source_info`).

## Implementation Strategy

Single-feature, single-PR. Phased internally:

### Phase A — DSL + IR scaffolding (no behavior yet)
1. Add `VecConstIR` and the `vec_constants` field to `ModuleIR`. (T1)
2. Add `VecConst` class to `dsl/const.py` and export from `dsl/__init__.py`. (T2)

### Phase B — Freeze + validation
3. Implement freeze logic in `dsl/freeze.py` including `_freeze_vec_const_storage`. (T3)
4. Implement focused validation negative tests (T4) before SV emission, so failures surface at the freeze layer first.

### Phase C — Manifest + SV emission
5. Update manifest `write_json.py` to emit `vec_constants` array per module. (T5)
6. Update SV view + template to emit the new localparam lines. (T6)

### Phase D — Constitution + integration test + golden
7. Amend Constitution §Constraints item 5. (T7)
8. Create fixture under `tests/fixtures/vec_const_basic/`. (T8)
9. Generate goldens by running `piketype gen` against the fixture; commit the resulting tree as `tests/goldens/gen/vec_const_basic/`. (T9)
10. Add the integration test in `tests/test_gen_vec_const.py`. (T10)
11. Regenerate every existing manifest golden to add the empty `"vec_constants": []` line, per R-2. (T11)

### Phase E — Verification
12. Run the full unittest suite; confirm green. (T12)
13. Run basedpyright strict on every changed Python file; confirm zero new errors. (T13)

### Files touched

| File | Status | Approx LOC |
|------|--------|------|
| `src/piketype/ir/nodes.py` | modified | +12 (VecConstIR + vec_constants field) |
| `src/piketype/dsl/const.py` | modified | +60 (VecConst class) |
| `src/piketype/dsl/__init__.py` | modified | +1 (export VecConst) |
| `src/piketype/dsl/freeze.py` | modified | +60 (freeze logic) |
| `src/piketype/backends/sv/view.py` | modified | +30 (view + render helper) |
| `src/piketype/backends/sv/templates/module_synth.j2` | modified | +3 (template block) |
| `src/piketype/manifest/write_json.py` | modified | +12 (manifest array) |
| `.steel/constitution.md` | modified | one-paragraph amendment |
| `tests/fixtures/vec_const_basic/project/alpha/piketype/vecs.py` | new | ~10 |
| `tests/goldens/gen/vec_const_basic/` | new | tree |
| `tests/test_gen_vec_const.py` | new | ~40 |
| `tests/test_vec_const_validation.py` | new | ~80 |
| Existing `tests/goldens/gen/*/piketype_manifest.json` (10 fixtures) | regenerated | +1 line each |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **R-1.** Adding `vec_constants` to `ModuleIR` breaks existing callers that pass positional args. | Low — verified all in-tree callers use kwargs. | Medium if hit (compile error at module load). | Default value `= ()` at the end of `ModuleIR` field list. Phase A test (T1) verifies all modules still load. |
| **R-2.** Adding `"vec_constants": []` to every per-module manifest dict breaks byte-identity of every existing manifest golden (NFR-2 / Constitution Principle 3). | Certain — every manifest currently exists without this field. | Medium (10+ goldens to regenerate; PR diff inflates). | Acknowledged. Phase D step 11 explicitly regenerates all manifest goldens. The diff is one new line per module — mechanical, easily reviewed. NFR-5 *intent* (existing `Const()` SV emission unchanged) is preserved; only manifest format gains a new always-present-but-often-empty field. |
| **R-3.** Future user wants `Const + VecConst` arithmetic and finds VecConst is not a `ConstOperand`. | Low — user did not request it; values are typically opaque protocol literals. | Low (raises clear `ValidationError` at construction time of the surrounding expression). | Acknowledged. Documented in spec OOS-3. Lifting later is a non-breaking spec change. |
| **R-4.** SV literal renderer produces incorrect zero-padding for non-multiple-of-4 hex widths (e.g., `width=12, base=hex` should render exactly 3 hex digits). | Low — explicit test cases in fixture (`LP_NIBBLE_F` width=4). | Medium (silent SV miscompile if 13'h or similar over/under-pads). | Padding helper is a single function with explicit tests (AC-9, AC-10). |
| **R-5.** Cross-module `VecConst` references via `from a import LP_X` create unexpected SV import lines. | Low — VecConst is not a `ConstOperand`, so it cannot appear in expressions; `_collect_const_refs` doesn't see VecConst. The `from a import` only affects Python namespace, not freeze deps. | Low. | No mitigation needed; behavior is consistent with FR-13's permissive "MAY" wording. The SV `import a_pkg::*;` line will only appear when module B uses an actual `Const` from A in an expression (existing mechanism). VecConst alone does not trigger the import. |
| **R-6.** Constitution amendment language conflicts with §Adding a New Type or Feature (which lists DSL → IR → freeze → validate → backend). | Low — the amendment is to §Constraints item 5 only, not §Adding a New Type. | Low. | Amend exactly the cited paragraph; verify by full read after edit. |

## Testing Strategy

Per Constitution §Testing.

1. **Golden-file integration test** (T10) — primary correctness mechanism per Constitution. New `tests/test_gen_vec_const.py` runs `piketype gen` against `tests/fixtures/vec_const_basic/` and diffs the generated `gen/` tree against `tests/goldens/gen/vec_const_basic/` byte-for-byte. Covers AC-1, AC-2, AC-3, AC-9, AC-10, AC-11.
2. **Validation negative tests** (T4) — `tests/test_vec_const_validation.py` exercises AC-4, AC-5, AC-6, AC-7, AC-8. Uses `unittest.TestCase`; constructs `VecConst(...)` with each invalid argument shape and asserts `ValidationError` raised with the expected substrings (per FR-7's three-substring contract).
3. **Existing-test regression** (T12) — full `python -m unittest discover -s tests -v` must pass after the manifest-golden regeneration (R-2). Specifically: `test_gen_const_sv` and the 10 other golden tests must still pass with the regenerated `piketype_manifest.json` files.
4. **basedpyright strict** (T13) — zero new errors on modified files (per memory `project_basedpyright_baseline_drift.md`, delta-only measurement).
5. **AC-12 regression sentinel** — covered transitively by step 3: if `Const()` SV emission changed, `test_gen_const_sv` would fail. The plan does not modify `_render_sv_const` or the `constants` template loop.

**Not pursued:**
- Performance benchmark — NFR-4 is "no measurable regression"; no change in hot paths.
- C++ / Python emission tests for VecConst — FR-16/17 declare them no-op; the existing C++ and Py golden checks for the new fixture verify absence transitively (the goldens contain only Const-derived output, no VecConst output).

## Acceptance Criteria Mapping

| AC | Verification step |
|----|-------------------|
| AC-1 | Import works: covered by `from piketype.dsl import VecConst` in fixture (T8). |
| AC-2 | Golden line `localparam logic [15:0] LP_ETHERTYPE_VLAN = 16'h8100;` in `vecs_pkg.sv` (T9, T10). |
| AC-3 | Golden lines for `A` (Const) and `B` (VecConst with `A * 3` resolved to 15) in `vecs_pkg.sv` (T9, T10). |
| AC-4 | `tests/test_vec_const_validation.py::test_overflow_8bit_300` (T4). |
| AC-5 | `tests/test_vec_const_validation.py::test_negative_value_rejected` (T4). |
| AC-6 | `tests/test_vec_const_validation.py::test_zero_or_negative_width_rejected` (T4). |
| AC-7 | `tests/test_vec_const_validation.py::test_width_above_64_rejected` (T4). |
| AC-8 | `tests/test_vec_const_validation.py::test_unsupported_base_rejected` (T4). |
| AC-9 | Golden lines `8'h0F` and `8'b00001111` in `vecs_pkg.sv` (T9). |
| AC-10 | Golden line `16'h00AB` would appear if `LP_AB = VecConst(width=16, value=0xab, base="hex")` is added; fixture includes a similar entry. (T8, T9). |
| AC-11 | Cross-module test deferred to a separate fixture if needed; FR-13 is permissive ("MAY"). For v1, included as `tests/fixtures/vec_const_cross_module/` only if effort permits — otherwise documented as covered by existing Const cross-module tests since VecConst doesn't introduce new cross-module mechanisms. (See Risks R-5.) |
| AC-12 | Existing `test_gen_const_sv` regression-sentinel passes unchanged (T12). |
| AC-13 | Validation messages include `source.path:source.line` per existing `SourceInfo` capture; spot-checked in T4 negative tests. |
| AC-14 | T8 (fixture), T9 (golden), T4 (validation tests) — all created. |
| AC-15 | T13 — basedpyright strict zero errors. |
| AC-16 | T12 — full unittest suite green. |

## Constitution Compliance Check

| Constitution clause | Compliance |
|---------------------|------------|
| Principle 1 (single source of truth) | Preserved — VecConst defined once in DSL; SV emission and manifest are both derived. C++/Py no-op is explicit, not silent (FR-16/17). |
| Principle 2 (immutable boundaries) | Preserved — DSL → freeze → IR → SV view, no boundary leakage. |
| Principle 3 (deterministic output) | Preserved — VecConst rendering is purely deterministic (zero-pad rules); manifest gains a fixed-shape array. |
| Principle 4 (correctness over convenience) | Strengthened — overflow check is a hard error per FR-7 with formula-substring contract. |
| Principle 5 (template-first) | Honored — emission moved into Jinja template (`module_synth.j2`), not Python string-build. |
| Principle 6 (generated runtime) | N/A. |
| §Constraints item 5 (32/64 widths) | Amended per FR-14 (planned in T7); kept consistent with VecConst's 1–64 range. |
| §Coding Standards Python (`from __future__ import annotations`, `UPPER_SNAKE_CASE`, basedpyright strict) | Verified at T13. |
| §Testing (golden-file pattern, `unittest.TestCase`) | Honored — T10 is golden-file; T4 uses `unittest.TestCase`. |
| §Adding a New Type or Feature steps | Followed exactly: DSL → IR → freeze → (no validation pass needed) → backend → fixture + golden + integration test. |

## Open Items

None. All clarifications resolved; spec acceptance criteria all map to a verification step.
