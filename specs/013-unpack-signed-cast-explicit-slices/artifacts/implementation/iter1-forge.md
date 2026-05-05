# Implementation — Iteration 1 (Forge)

Both tasks T-001 and T-002 were applied. Repo state: feature branch
`feature/013-unpack-signed-cast-explicit-slices`, two new commits on top
of the planning approval.

## Commit A — T-001: pre-compute slice indices and signedness in view

**Commit hash.** `53f7586`
**Title.** `refactor(sv): pre-compute unpack slice indices and signedness in view`

### Files Changed
- `src/piketype/backends/sv/view.py` — extended
  `SvSynthStructUnpackFieldView` and `_build_struct_pack_unpack`.

### Surface change
Three new fields added to the dataclass at the tail of the existing field
list:

```python
slice_low: int
slice_high: int
is_signed: bool   # True only when effective type is signed AND not type-ref
```

### Builder logic
A running `low: int = 0` accumulator over `reversed(type_ir.fields)`.
Per field:

```python
fw = _field_data_width(field=field, repo_type_index=repo_type_index)
is_signed_eff = _is_field_signed(field=field, repo_type_index=repo_type_index)
has_signed_padding = field.padding_bits > 0 and is_signed_eff
is_type_ref = isinstance(field.type_ir, TypeRefIR)
slice_low = low
slice_high = low + fw - 1
is_signed = is_signed_eff and not is_type_ref
# ... construct view with both old and new fields, then:
low += fw
```

Note the explicit `assert isinstance(field.type_ir, TypeRefIR)` inside
the type-ref branch. This is a basedpyright type-narrowing aid: the bool
`is_type_ref` was extracted to a separate variable for use in the
`is_signed` formula, but pyright's narrowing does not propagate from a
bool back to the variable. The assert provides the narrow.

### Behaviour delta
None (template still emits the old form). Test suite green:
`303 tests in 5.807s, OK (skipped=3)`.

### Verification (T-001 verify checklist)
- ✓ basedpyright reports the same 100 pre-existing errors with no new errors
  introduced. (The 100-error baseline is a pre-existing condition not
  tied to this feature; it predates the branch.)
- ✓ `python -m unittest` passes 303/303 (3 skipped) — all goldens
  unchanged because the template still emits the old form.
- (Spot-check `print` was performed inline during development and
  removed before commit, per task note. Did not commit the print.)

### Plan deviations
None.

---

## Commit B — T-002: emit cast + literal slices, refresh goldens

**Commit hash.** `eb8d5cb`
**Title.** `feat(sv): emit signed cast and explicit slice indices in unpack`

### Files Changed
- `src/piketype/backends/sv/templates/_macros.j2` — `synth_unpack_fn`
  macro: scalar_alias branch and struct branch.
- `tests/goldens/gen/<fixture>/sv/<...>/*_pkg.sv` for the 18 affected
  fixtures (full list: see Goldens Refresh section below).

Total stat: `18 files changed, 66 insertions(+), 163 deletions(-)`.
The deletions outweigh insertions because each struct unpack body lost
two lines per field (`offset += W;` and the `int unsigned offset; / offset = 0;`
preamble), partially offset by the slightly longer `signed'(a[h:l])`
form in signed cases.

### Template edit — scalar_alias branch (FR-1.4)

Before
```jinja
{% if view.kind == "scalar_alias" %}
    return a;
```

After
```jinja
{% if view.kind == "scalar_alias" %}
{% if view.signed %}
    return signed'(a);
{% else %}
    return a;
{% endif %}
```

The `view.signed` flag is the existing `SvScalarAliasView.signed` field
already used to gate the `signed` modifier in the typedef line earlier
in the macro.

### Template edit — struct branch (FR-1.1, FR-2.1, FR-2.2)

Before
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
...
```

After
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
...
```

Removed: `int unsigned offset;` declaration, the `offset = 0;`
initialiser, and every `offset += ...;` accumulation line.
Branch order (type-ref → signed inline → plain inline) is mutually
exclusive by construction: T-001 forces `is_signed=False` whenever
`is_type_ref=True`.

### Goldens refresh

A throwaway script `/tmp/regen_goldens.py` was used: walk every
`tests/fixtures/<name>/`, copy the `project/` tree to a temp dir, run
`piketype.commands.gen.run_gen` against the first `.py` file under
`piketype/`, and replace `tests/goldens/gen/<name>/` with the new
output. Two goldens that test the `--namespace` flag
(`namespace_override` and `cross_module_type_refs_namespace_proj`) were
regenerated separately by `/tmp/regen_namespace.py` with the proper
namespace argument.

Modified golden trees (18 files in 17 fixtures — the
`cross_module_type_refs` fixture has both `bar_pkg.sv` and `foo_pkg.sv`):

```
cross_module_struct_multiple_of/bar_pkg.sv
cross_module_type_refs/bar_pkg.sv
cross_module_type_refs/foo_pkg.sv
cross_module_type_refs_namespace_proj/bar_pkg.sv
cross_module_type_refs_namespace_proj/foo_pkg.sv
keyword_module_name_logic_passes/logic_pkg.sv
keyword_near_miss/types_pkg.sv
keyword_type_name_class_t_passes/types_pkg.sv
namespace_override/{various}_pkg.sv
nested_struct_sv_basic/types_pkg.sv
scalar_sv_basic/types_pkg.sv
struct_enum_member/types_pkg.sv
struct_flags_member/types_pkg.sv
struct_multiple_of/types_pkg.sv
struct_padded/types_pkg.sv
struct_signed/types_pkg.sv
struct_sv_basic/types_pkg.sv
struct_wide/types_pkg.sv
```

Zero diffs in any `_test_pkg.sv`, `cpp/`, `py/`, or `runtime/` golden
subtree. Confirmed via `git diff --stat`.

### Spot-check verification (T-002 verify checklist)

| Check | Result |
|-------|--------|
| `grep -r "int unsigned offset" tests/goldens/gen/` | 0 hits — AC-1 ✓ |
| `grep -r "a\[offset" tests/goldens/gen/` | 0 hits — AC-2 ✓ |
| `tests/goldens/gen/struct_signed/.../types_pkg.sv` line 50: `result.field_u = signed'(a[4:0]);` | match — AC-4 ✓ |
| `tests/goldens/gen/struct_signed/.../types_pkg.sv` `unpack_signed_4`/`unpack_signed_5` body: `return signed'(a);` | match — AC-5 ✓ |
| `tests/goldens/gen/scalar_sv_basic/.../types_pkg.sv` signed alias unpack: `return signed'(a);` | match — AC-5 ✓ |
| `result.field_s = unpack_signed_4(a[8:5]);` (type-ref, no cast, explicit slice) | match — AC-6 ✓ |
| `result.enable = unpack_flag(a[0:0]);` in `nested_struct_sv_basic.unpack_header` (1-bit field) | match — AC-10 ✓ |
| `python -m unittest` 303/303 passing | green — AC-7 ✓ |
| `basedpyright` no new errors over pre-existing baseline | unchanged — AC-8 ✓ (caveat: 100 pre-existing errors not introduced by this feature) |

### Slice-arithmetic verification (Q2 worked example, mirrored to AC-3)

`mixed_t` in `struct_signed`: declared fields = [`field_s` (w=4, type-ref),
`field_u` (w=5, inline signed)]. Reversed = [`field_u`, `field_s`].

| Step | low (in) | field | width | slice_low | slice_high | low (out) |
|------|----------|-------|-------|-----------|------------|-----------|
| 1    | 0        | field_u | 5   | 0         | 4          | 5         |
| 2    | 5        | field_s | 4   | 5         | 8          | 9         |

Generated body matches: `field_u = signed'(a[4:0])` (slice_high=4,
slice_low=0) and `field_s = unpack_signed_4(a[8:5])` (slice_high=8,
slice_low=5). Total = 9 = `LP_MIXED_WIDTH`. ✓

### Plan deviations

None.

### Skills used

None of the listed skills (systemverilog-core, sv-gen, etc.) were
formally invoked. The work was direct file edits guided by the spec /
plan / tasks.

---

## Implementation summary

| AC    | Status | Evidence |
|-------|--------|----------|
| AC-1  | ✓      | grep `int unsigned offset` returns 0 hits |
| AC-2  | ✓      | grep `a[offset` returns 0 hits |
| AC-3  | ✓      | Q2 worked example matches generated `mixed_t` body |
| AC-4  | ✓      | `result.field_u = signed'(a[4:0]);` in struct_signed golden |
| AC-5  | ✓      | `return signed'(a);` in struct_signed (signed_4_t, signed_5_t) and scalar_sv_basic |
| AC-6  | ✓      | `result.field_s = unpack_signed_4(a[8:5]);` (type-ref + explicit slice + no cast) |
| AC-7  | ✓      | `python -m unittest` 303/303 passing |
| AC-8  | ✓      | basedpyright introduces no new errors over baseline |
| AC-9  | ⏭      | Deferred to validation stage (Verilator delta-check) |
| AC-10 | ✓      | `result.enable = unpack_flag(a[0:0])` in nested_struct_sv_basic |
