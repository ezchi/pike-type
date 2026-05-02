# Tasks — 013-unpack-signed-cast-explicit-slices

**Spec:** `specs/013-unpack-signed-cast-explicit-slices/spec.md`
**Plan:** `specs/013-unpack-signed-cast-explicit-slices/plan.md`
**Status:** draft (task_breakdown iteration 1)

## Plan corrections required

None at this iteration. Pre-flight checks confirmed:

- `SvSynthStructUnpackFieldView` is referenced only inside
  `src/piketype/backends/sv/view.py` (constructed in
  `_build_struct_pack_unpack`, exposed via `unpack_fields: tuple[...]` on
  the parent `SvSynthStructPackUnpackView`). No test or other module
  constructs it directly. The plan's C-5 ("View-test alignment") is
  therefore expected to be a no-op — confirmed but kept as a verify step
  inside T-002 rather than a separate task.
- The `view.signed` boolean exists on `SvScalarAliasView` (verified at
  `src/piketype/backends/sv/view.py` ~line 113). C-3.1 needs no
  view-builder edit.

---

## Conventions

- Each task is independently buildable. After every task
  `basedpyright --strict src/piketype` and `python -m unittest` MUST pass.
- Tasks are ordered by dependency. T-001 must complete before T-002.
- The byte-parity-per-commit preference applies: each commit leaves the
  test suite green. T-001 is safe because new view fields are unused
  by the template until T-002 lands. T-002 is the atomic
  template-edit-plus-goldens-refresh commit.
- File paths are relative to repo root. Verified existence noted with ✓.

---

## Commit A — view builder gains slice/is_signed fields (no behaviour change)

### T-001. Extend `SvSynthStructUnpackFieldView` and `_build_struct_pack_unpack`

**Description.** Add `slice_low: int`, `slice_high: int`, and
`is_signed: bool` fields to the `SvSynthStructUnpackFieldView` dataclass,
and populate them in `_build_struct_pack_unpack` via a running `low`
accumulator. The Jinja template still uses the old `offset +: width` form
in this commit; the new fields are populated but unread. Test suite
remains green because no template uses the new fields yet.

**Files to modify.**
- `src/piketype/backends/sv/view.py` ✓

**Files to create.** None.

**Implementation notes.**

- Add the three new fields to the `@dataclass(frozen=True, slots=True)`
  block at the END of the existing field list (after `sign_bit_index`),
  to minimise churn in any reader iterating the dataclass positionally.
  Field types and order:
  ```python
      slice_low: int
      slice_high: int
      is_signed: bool
  ```
- In `_build_struct_pack_unpack`, before the `for field in
  reversed(type_ir.fields):` loop, declare `low: int = 0`. Inside the
  loop, AFTER computing `fw = _field_data_width(...)` and `is_signed_eff
  = _is_field_signed(...)`, compute:
  ```python
  is_type_ref = isinstance(field.type_ir, TypeRefIR)
  slice_low = low
  slice_high = low + fw - 1
  is_signed = is_signed_eff and not is_type_ref
  ```
- Pass `slice_low`, `slice_high`, `is_signed` into BOTH branches of the
  `SvSynthStructUnpackFieldView(...)` construction (the type-ref branch
  and the inline branch). For the type-ref branch, `is_signed` is
  unconditionally `False` per the formula above; the redundant
  `not is_type_ref` is kept for readability rather than splitting the
  branches.
- After constructing the view object, increment the accumulator:
  `low += fw`. Place this AFTER the `unpack_fields.append(...)` call so
  the loop body's slice computation uses the pre-increment `low`.
- `fw` is the data width — the existing `_field_data_width` helper at
  `src/piketype/backends/sv/view.py:331` returns the data width
  excluding padding. Padding is emitted on the `_pad` line and must NOT
  enter the slice arithmetic. (Confirmed by Q2's worked example for
  `mixed_t`: `slice_high(field_s) = 8`, matching pack-side concat
  ordering of W=9 with field_u in low 5 bits.)
- Do not edit `_macros.j2` in this commit. The template still references
  `f.width` and uses the `offset +: ...` form; the new fields are
  unused but populated. Goldens are unchanged.

**Dependencies.** None (first task).

**Verify.**
- `basedpyright --strict src/piketype` returns 0 errors.
- `python -m unittest` passes (all goldens unchanged because the
  template still emits the old form).
- Spot-check by adding a temporary `print(unpack_fields)` in
  `_build_struct_pack_unpack` for the `mixed_t` fixture (run via
  `piketype gen` against `tests/fixtures/struct_signed/`) and confirm:
  - For `field_u`: `slice_low=0, slice_high=4, is_signed=True`.
  - For `field_s`: `slice_low=5, slice_high=8, is_signed=False`
    (False because it is a type-ref).
  Remove the print before commit.

**Commit message.** `refactor(sv): pre-compute unpack slice indices and signedness in view`

---

## Commit B — template emits cast + literal slices, goldens refreshed atomically

### T-002. Edit `synth_unpack_fn` macro and refresh every affected golden

**Description.** Apply the two surgical edits to
`src/piketype/backends/sv/templates/_macros.j2` (scalar_alias branch and
struct branch), then regenerate every fixture's golden tree under
`tests/goldens/gen/`, then commit the template edit and the regenerated
goldens together as one atomic byte-parity-preserving change.

**Files to modify.**
- `src/piketype/backends/sv/templates/_macros.j2` ✓
- Every `tests/goldens/gen/<fixture>/sv/**/*.sv` whose generated content
  changes. Pre-flight scan from clarification Q3 enumerates at minimum:
  `nested_struct_sv_basic`, `struct_wide`, `struct_multiple_of`,
  `struct_signed`, `struct_flags_member`, `struct_enum_member`,
  `cross_module_type_refs`, `cross_module_type_refs_namespace_proj`,
  `scalar_sv_basic`, `scalar_signed_wide`. The implementer MUST
  enumerate the actual diff list at refresh time (running `piketype gen`
  over every fixture and `git diff --name-only tests/goldens/gen/`),
  not assume this list is exhaustive.

**Files to create.** None.

**Implementation notes.**

- **Edit 1 — scalar_alias branch (FR-1.4 / C-3.1).** Locate the macro
  body block that currently reads:
  ```jinja
  {% if view.kind == "scalar_alias" %}
      return a;
  ```
  Replace with:
  ```jinja
  {% if view.kind == "scalar_alias" %}
  {% if view.signed %}
      return signed'(a);
  {% else %}
      return a;
  {% endif %}
  ```
  The `view.signed` flag is the existing `SvScalarAliasView.signed`
  field, the same flag that gates the `signed` modifier in the typedef
  emission line earlier in the macro file. No view-builder edit needed.
- **Edit 2 — struct branch (FR-1.1, FR-2.1, FR-2.2 / C-3.2).** Locate
  the block that currently reads:
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
  Replace with the three-branch form:
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
  Note the removal of `int unsigned offset;`, the initialiser line
  `offset = 0;`, and every `offset += ...;` line. The signed-padding
  block is unchanged in form (FR-3.2 / Q4).
- **Branch ordering.** `f.is_type_ref` first, `f.is_signed` second,
  fallback (plain unsigned inline) last. Mutually exclusive by
  construction: T-001 forces `is_signed=False` whenever
  `is_type_ref=True`, so `elif f.is_signed` cannot fire on a type-ref
  field.
- **Golden refresh procedure.** From the repo root:
  1. `python -m unittest` — capture baseline failures (expected: every
     fixture in the C-4 list shows a mismatch in `_pkg.sv`).
  2. For each failing fixture, identify whether the project has a
     blessed "regen goldens" command. If yes, run it. If no, follow
     the manual refresh pattern: copy the fixture's `project/` to a
     temp dir, run `piketype gen`, copy the generated `gen/sv/` tree
     back to `tests/goldens/gen/<fixture>/sv/`. (Reuse whatever pattern
     prior specs in this repo established; e.g. `010-jinja-template-
     migration` regenerated all goldens — inspect that PR's history
     for the exact sequence.)
  3. After every fixture has been refreshed, run `python -m unittest`
     again; expect green.
- **Spot-check assertions before committing.** Open
  `tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv` and
  confirm:
  - `unpack_signed_4` body is `return signed'(a);` (was `return a;`).
  - `unpack_signed_5` body is `return signed'(a);`.
  - `unpack_mixed` body contains `result.field_u = signed'(a[4:0]);`
    and `result.field_s = unpack_signed_4(a[8:5]);` (signed cast on
    inline; no cast on type-ref; explicit slice in both).
  - `unpack_mixed` body contains NO `int unsigned offset` declaration
    and NO `offset +=` assignment.
- **Out-of-scope spot-checks.** Confirm `pack_<base>` functions are
  unchanged, `unpack_<flag_or_enum>` functions are unchanged,
  `_test_pkg.sv` files have ZERO diffs (helper-class bodies were not
  edited), and C++/Python goldens have ZERO diffs.

**Dependencies.** T-001.

**Verify.**
- `basedpyright --strict src/piketype` returns 0 errors (AC-8).
- `python -m unittest` passes (AC-7) — all golden diffs are zero.
- `git diff --stat tests/goldens/gen/` shows changes ONLY in `*.sv`
  files under `sv/**/`. Zero diffs in `cpp/`, `py/`, `runtime/` golden
  subtrees.
- `grep -r 'int unsigned offset' tests/goldens/gen/ | grep -v _test_pkg`
  returns zero hits inside `unpack_*` function bodies (AC-1).
- `grep -r 'a\[offset' tests/goldens/gen/` returns zero hits inside
  `unpack_*` bodies (AC-2).
- `grep -r "signed'(a\[" tests/goldens/gen/struct_signed/` returns at
  least one hit on `unpack_mixed`'s `field_u` line (AC-4).
- `grep -rn "return signed'(a)" tests/goldens/gen/` returns hits in
  every fixture that contains a signed scalar alias (AC-5 — at minimum
  `scalar_sv_basic`, `scalar_signed_wide`, `struct_signed`).
- For at least one struct golden, hand-verify that the slice indices
  match the declared field widths (AC-3 — pick `nested_struct_sv_basic`'s
  `header_t`: enable=1 bit at [0:0], addr=4 bits at [4:1] given
  W=14... actually, the implementer should compute the expected slice
  table from the fixture's DSL and compare to the regenerated golden;
  this is the AC-3 round-trip check).

**Commit message.** `feat(sv): emit signed cast and explicit slice indices in unpack`

---

## Skipped tasks (rationale)

- **No T-003 fixture-creation task.** Q1 confirmed
  `tests/fixtures/struct_signed/` already covers the signed-inline-field
  path. Creating a new fixture would be churn for no coverage gain
  (AC-4 supersedes the original new-fixture mandate).
- **No T-004 view-test edit task.** Pre-flight scan confirmed no test
  module constructs `SvSynthStructUnpackFieldView` directly. The plan's
  C-5 collapses into a verify step inside T-001.
- **No T-005 lint-flow integration task.** AC-9's delta-check is a
  validation-stage activity, not implementation. The implementer SHOULD
  spot-check Verilator before committing T-002, but the formal lint
  delta belongs in the validation stage's task list, not here.

---

## Acceptance traceability

| AC    | Source FR     | Verified by |
|-------|---------------|-------------|
| AC-1  | FR-2.1        | T-002 grep check (`int unsigned offset` absent) |
| AC-2  | FR-2.2        | T-002 grep check (`a[offset` absent) |
| AC-3  | FR-2.3        | T-002 hand-verify on `nested_struct_sv_basic.header_t` |
| AC-4  | FR-1.1, FR-3.1 | T-002 grep check on `struct_signed/types_pkg.sv` |
| AC-5  | FR-1.4        | T-002 grep check across goldens with signed scalars |
| AC-6  | FR-1.3, FR-2.5 | T-002 spot-check on type-ref unpack bodies |
| AC-7  | NFR-4         | T-001 + T-002 `python -m unittest` |
| AC-8  | NFR-3         | T-001 + T-002 `basedpyright --strict` |
| AC-9  | NFR-5         | Validation stage (delta-check vs pre-feature baseline) |
| AC-10 | FR-2.2        | T-002 hand-verify on a 1-bit field (e.g. `flag_t` in `nested_struct_sv_basic`'s `header_t`) |
