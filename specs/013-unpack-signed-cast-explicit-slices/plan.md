# Implementation Plan — 013-unpack-signed-cast-explicit-slices

**Spec:** `specs/013-unpack-signed-cast-explicit-slices/spec.md` (post-clarification)
**Branch:** `feature/013-unpack-signed-cast-explicit-slices`
**Status:** draft (planning iteration 1)

## Architecture Overview

A purely additive change confined to two files in the SystemVerilog backend:

```
RepoIR ─► sv backend
              ├── view.py   (Python view-builder, adds slice/is_signed fields)
              └── templates/_macros.j2  (Jinja, gates cast + emits literal slices)
```

No IR change. No DSL change. No new validation. No change to `pack_<base>`,
flags / enum unpack, scalar-alias unpack signature, `_test_pkg` helpers,
C++ backend, Python backend, or runtime packages. The pipeline boundary
(Discovery → DSL → IR → Backends) is preserved: only the last hop
(IR → SV backend) gets the edit.

The change is byte-for-byte deterministic, so the implementation stage
also refreshes every affected golden under `tests/goldens/gen/` in the
same commit as the codegen edit. Test infrastructure (`tests/test_view_sv.py`,
`tests/test_render.py`, etc.) requires no new test files; existing golden
diffs are the verification mechanism (per project Constitution principle 4).

## Components

### C-1. `SvSynthStructUnpackFieldView` (extension)

**Location.** `src/piketype/backends/sv/view.py`, ~line 132.

**Responsibility.** Carry pre-computed slice indices and signedness gate
to the Jinja template. No behaviour change to the existing fields.

**Public surface (post-edit).**

```python
@dataclass(frozen=True, slots=True)
class SvSynthStructUnpackFieldView:
    """One field of a struct unpack body (in reversed declaration order)."""
    name: str
    width: int                # data width (unchanged)
    is_type_ref: bool         # unchanged
    inner_base: str           # unchanged
    inner_upper: str          # unchanged
    has_signed_padding: bool  # unchanged
    padding_bits: int         # unchanged
    sign_bit_index: int       # unchanged
    slice_low: int            # NEW: low bit index, computed in builder
    slice_high: int           # NEW: high bit index, slice_low + width - 1
    is_signed: bool           # NEW: True only if effective type is signed AND not type_ref
```

Field ordering is preserved at the head; new fields go at the tail to
minimise diff churn for any downstream Python that reads this dataclass
positionally (none today, but defensive).

### C-2. `_build_struct_pack_unpack` (extension)

**Location.** `src/piketype/backends/sv/view.py`, ~line 493.

**Responsibility.** Maintain a running `low: int` accumulator while
iterating `reversed(type_ir.fields)`. For each field, compute
`slice_low = low; slice_high = low + width - 1`, then `low += width`.
Set `is_signed` only for inline non-type-ref fields whose
`_is_field_signed` returns True.

**Pseudocode skeleton.**

```python
unpack_fields: list[SvSynthStructUnpackFieldView] = []
low = 0
for field in reversed(type_ir.fields):
    fw = _field_data_width(field=field, repo_type_index=repo_type_index)
    eff_signed = _is_field_signed(field=field, repo_type_index=repo_type_index)
    has_signed_padding = field.padding_bits > 0 and eff_signed
    is_type_ref = isinstance(field.type_ir, TypeRefIR)
    is_signed = eff_signed and not is_type_ref      # FR-1.3 / Q6
    unpack_fields.append(
        SvSynthStructUnpackFieldView(
            name=field.name,
            width=fw,
            is_type_ref=is_type_ref,
            inner_base=...,                          # unchanged
            inner_upper=...,                         # unchanged
            has_signed_padding=has_signed_padding,
            padding_bits=field.padding_bits,
            sign_bit_index=fw - 1 if has_signed_padding else 0,
            slice_low=low,
            slice_high=low + fw - 1,
            is_signed=is_signed,
        )
    )
    low += fw
```

`fw` is the data width, NOT including padding — the existing
`_field_data_width` helper returns this. Padding bits live in a separate
emitted line (the `_pad` assignment) and do not enter the slice
arithmetic. This is consistent with Q2's verified worked example.

### C-3. `synth_unpack_fn` macro (Jinja edit)

**Location.** `src/piketype/backends/sv/templates/_macros.j2`, lines ~108–141.

**Responsibility.** Two surgical edits to the macro body:

#### C-3.1 scalar_alias branch (FR-1.4)

**Before**

```jinja
{% if view.kind == "scalar_alias" %}
    return a;
```

**After**

```jinja
{% if view.kind == "scalar_alias" %}
{% if view.signed %}
    return signed'(a);
{% else %}
    return a;
{% endif %}
```

The `view.signed` boolean already exists on `SvScalarAliasView` (used by
the typedef-emission line at macro line 34). No view-builder change needed
for this branch.

#### C-3.2 struct branch (FR-1.1, FR-2.1, FR-2.2)

**Before**

```jinja
{% elif view.kind == "struct" %}
    {{ view.name }} result;
    int unsigned offset;
    result = '0;
    offset = 0;
{% for f in pack_unpack.unpack_fields %}
{% if f.is_type_ref %}
    result.{{ f.name }} = unpack_{{ f.inner_base }}(a[offset +: LP_{{ f.inner_upper }}_WIDTH]);
    offset += LP_{{ f.inner_upper }}_WIDTH;
{% else %}
    result.{{ f.name }} = a[offset +: {{ f.width }}];
    offset += {{ f.width }};
{% endif %}
{% if f.has_signed_padding %}
    result.{{ f.name }}_pad = {{ '{' }}{{ f.padding_bits }}{{ '{result.' }}{{ f.name }}[{{ f.sign_bit_index }}]{{ '}' }}{{ '}' }};
{% endif %}
{% endfor %}
    return result;
```

**After**

```jinja
{% elif view.kind == "struct" %}
    {{ view.name }} result;
    result = '0;
{% for f in pack_unpack.unpack_fields %}
{% if f.is_type_ref %}
    result.{{ f.name }} = unpack_{{ f.inner_base }}(a[{{ f.slice_high }}:{{ f.slice_low }}]);
{% elif f.is_signed %}
    result.{{ f.name }} = signed'(a[{{ f.slice_high }}:{{ f.slice_low }}]);
{% else %}
    result.{{ f.name }} = a[{{ f.slice_high }}:{{ f.slice_low }}];
{% endif %}
{% if f.has_signed_padding %}
    result.{{ f.name }}_pad = {{ '{' }}{{ f.padding_bits }}{{ '{result.' }}{{ f.name }}[{{ f.sign_bit_index }}]{{ '}' }}{{ '}' }};
{% endif %}
{% endfor %}
    return result;
```

Three branches now; the cast branch sits between the type-ref and
plain-inline branches because `f.is_type_ref` and `f.is_signed` are
mutually exclusive by construction (C-2 sets `is_signed=False` when
`is_type_ref=True`). The signed-padding line is unchanged in form
(FR-3.2 / Q4).

### C-4. Golden refresh (mechanical)

**Location.** `tests/goldens/gen/**`.

Run `piketype gen` over every fixture under `tests/fixtures/` and commit
every byte-for-byte diff to the corresponding golden directory. From the
clarification Q3 enumeration, the affected goldens span at least:

- `nested_struct_sv_basic`, `struct_wide`, `struct_multiple_of`,
  `struct_signed`, `struct_flags_member`, `struct_enum_member`,
  `cross_module_type_refs` (+ namespaced variant) — struct unpack changes.
- `scalar_sv_basic`, `scalar_signed_wide`, `struct_signed` — signed
  scalar-alias unpack changes (`return a;` → `return signed'(a);`).

The implementation stage MUST verify the actual list at refresh time,
not assume this enumeration is exhaustive.

### C-5. View-test alignment (mechanical)

**Location.** `tests/test_view_sv.py`.

If this test asserts the literal field list of `SvSynthStructUnpackFieldView`
or constructs instances of it directly, those constructions must add the
three new fields. If the test only round-trips a built view through
emission, no edit is required. The implementation stage runs the full
`unittest` suite to surface any breakage; expect zero or one trivial
edit here.

## Test Strategy

The project's primary correctness mechanism is the golden-file integration
test (Constitution: "Golden-file integration tests are the primary
correctness mechanism"). For this feature:

1. **Pre-edit baseline.** Run `unittest` on `develop` (or this branch
   pre-edit). Confirm green; capture the exact failure mode that the
   golden tests will produce after the codegen edit but before goldens
   are refreshed (expected: every fixture in the C-4 list shows a diff
   in `_pkg.sv`).

2. **Codegen edit + golden refresh in one commit.** Apply the C-1 / C-2 /
   C-3 edits, regenerate goldens, and commit them together. This is the
   standard pattern used by every prior spec in this repo (e.g.
   `010-jinja-template-migration`, `005-flags-dsl-type`).

3. **Targeted assertions on `struct_signed`.** AC-4 mandates the exact
   post-regeneration content of `unpack_mixed`'s `field_u` line. That
   assertion is already enforced by the golden diff for
   `tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv`;
   no additional unit test is needed.

4. **Type checking.** Run `basedpyright` (strict) over `src/piketype/`.
   AC-8.

5. **Lint delta.** Run the existing Verilator lint flow over each
   regenerated `_pkg.sv` and confirm no new WIDTH / UNSIGNED / SIGNED /
   UNUSED warnings vs the pre-feature baseline. AC-9 / Q5.

No new test files. No new fixtures (Q1 / OQ-3).

## Migration / Rollout

This is a single-PR change. No feature flag, no config knob, no
compatibility shim. Once merged:

- Downstream consumers regenerate their `_pkg.sv` outputs by re-running
  `piketype gen`. Their generated unpack functions transition from the
  `int unsigned offset` form to the explicit-slice form.
- Hand-written downstream code that calls into `unpack_<base>` is
  unaffected — function signatures (parameter type, return type) are
  unchanged.
- Hand-written downstream code that depends on the literal text of
  generated `_pkg.sv` (e.g. doc snippets, inline-included files) breaks
  silently. Mitigation: the generated-file header comment already
  carries the source-DSL-module identifier; downstream consumers should
  not depend on body-text invariants. No mitigation called out in the
  spec.

## Risks

- **Risk R-1: Goldens-refresh forgotten.** A common failure mode is
  shipping the codegen edit without refreshing every golden. Mitigation:
  the implementation stage's task list explicitly enumerates "regenerate
  every golden" and runs `unittest` to fail loudly otherwise. Constitution
  principle 7 (stable, reproducible output) backstops this.
- **Risk R-2: View-builder slice arithmetic off-by-one.** Mitigation: Q2
  pins the formula `slice_high = slice_low + width - 1` and includes a
  worked `mixed_t` example. Implementation runs `unittest`; mismatched
  goldens flag the bug immediately.
- **Risk R-3: `is_signed` set on type-ref fields.** Mitigation: C-2's
  `is_signed = eff_signed and not is_type_ref` rule is explicit. Q6
  pins this contract. AC-6 verifies via golden inspection.
- **Risk R-4: New Verilator warnings introduced (not removed).**
  Mitigation: AC-9's delta-check is the safety net. If the implementation
  stage's lint run shows new warnings of the targeted categories, the
  task is not done.

## Constitution Alignment

- Principle 1 (Single source of truth) — DSL is unchanged; output remains
  derived.
- Principle 2 (Immutable boundaries) — backend-only edit; no IR change.
- Principle 3 (Deterministic output) — slice indices are a pure function
  of the field list; no environment-dependent input.
- Principle 4 (Correctness over convenience) — the lint-clean cast and
  the dead-store-free struct unpack both honour this principle.
- Principle 5 (Template-first generation) — slice arithmetic moves to
  Python (view builder); the template emits literals. No string
  building in Python beyond view-model construction.
- Principle 6 (Generated runtime) — unaffected; runtime packages do not
  contain the unpack body.
