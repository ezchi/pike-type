# Clarifications — 013-unpack-signed-cast-explicit-slices

This document resolves the residual questions that survived the specification
stage and pins implicit assumptions before planning.

Each clarification is tagged:

- **[SPEC UPDATE]** — the resolution changes a requirement in `spec.md`.
- **[NO SPEC CHANGE]** — context only; does not alter contracts.

---

## Q1. Does an existing fixture already cover signed inline struct fields? (AC-4)

**Question.** AC-4 mandates a NEW fixture
`tests/fixtures/struct_signed_inline/`. Does the existing
`tests/fixtures/struct_signed/` already exercise the signed-inline path?

**Resolution.** Yes. `tests/fixtures/struct_signed/project/alpha/piketype/types.py`
declares `mixed_t` with `field_u = Logic(5, signed=True)` — a signed inline
(non-type-ref) struct field. The current golden
`tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv` shows the
unpack body emits

```sv
result.field_u = a[offset +: 5];
```

assigned into a typedef `logic signed [4:0] field_u`, which is the exact
lint-dirty pattern this feature targets. The same fixture also exercises:

1. The signed scalar alias path (`signed_4_t = Logic(4, signed=True)` with a
   top-level unpack function emitting `return a;`).
2. The signed type-ref struct field path (`field_s = signed_4_t`), which must
   remain unchanged per FR-1.3.
3. The signed-padding emission line (FR-3.2), since both `field_s` and
   `field_u` have `padding_bits > 0`.

**Action.**

- AC-4's "MUST add a NEW fixture" mandate is removed. AC-4 is rebound to the
  existing `tests/fixtures/struct_signed/` fixture.
- After regeneration, the golden for `mixed_t.unpack_mixed`'s `field_u` line
  MUST read `result.field_u = signed'(a[4:0]);`.
- After regeneration, the golden for `unpack_signed_4` and `unpack_signed_5`
  MUST read `return signed'(a);`.

**[SPEC UPDATE]** — AC-4 rewrite.

---

## Q2. How does the view builder compute `slice_high` / `slice_low`? (FR-2.4)

**Question.** Pack iterates in declaration order producing
`{pack_a, pack_b, pack_c}` (concat is MSB-first → first declared sits at the
highest bit). Unpack iterates `reversed(type_ir.fields)` so the first field
processed is the one at the lowest bit position. What are the formulas the
view builder must use?

**Resolution.** Given a field's data width `wi` and its 0-indexed position
`i` in the **reversed** field list:

```
slice_low(i)  = sum(w_j for j in 0..i-1)
slice_high(i) = slice_low(i) + w_i - 1
```

That is identical to the `offset` accumulator pattern the existing template
runs at simulation time, just pre-computed in Python and emitted as
constants. `wi` is the data width, NOT including the field's padding bits;
the padding bits are emitted on a separate line and are not part of the
slice.

**Verification on `mixed_t`** (W=9, declared fields = [field_s (w=4),
field_u (w=5)], reversed = [field_u, field_s]):

- field_u: `slice_low=0, slice_high=4` → `a[4:0]`
- field_s: `slice_low=5, slice_high=8` → `a[8:5]`

This matches the existing pack expression
`{pack_signed_4(a.field_s), a.field_u}` where `field_s` is the high 4 bits
and `field_u` is the low 5 bits.

**[NO SPEC CHANGE]** — implementation detail; pinned for planning.

---

## Q3. What is the exact list of goldens affected by the regeneration?

**Question.** Which goldens under `tests/goldens/gen/` will change
byte-for-byte? This affects the size of the goldens-refresh commit.

**Resolution.** Three categories, all of which the implementation stage
must regenerate:

1. **Every fixture containing a `Struct(...)`** (FR-2 — offset removal):
   among the current goldens, that includes at minimum
   `nested_struct_sv_basic`, `struct_wide`, `struct_multiple_of`,
   `struct_signed`, `struct_flags_member`, `struct_enum_member`,
   `cross_module_type_refs`, and any other fixture whose DSL declares a
   `Struct`.
2. **Every fixture containing a signed scalar alias `Logic(N, signed=True)`
   declared at module top level** (FR-1.4): at minimum `scalar_sv_basic`,
   `scalar_signed_wide`, and `struct_signed` (overlap with category 1).
3. **Every fixture containing a signed inline struct field `Logic(N,
   signed=True)`** (FR-1.1): at minimum `struct_signed`.

The implementation stage must enumerate the actual list at refresh time by
running `piketype gen` over every fixture under `tests/fixtures/` and
diffing against `tests/goldens/gen/`. Any fixture whose generated `.sv`
output changes must have its golden refreshed in the same commit.

**[NO SPEC CHANGE]** — operational note.

---

## Q4. Does the signed cast change the signed-padding emission line? (FR-3.2)

**Question.** FR-3.2 says signed-padding handling stays unchanged in form.
After the cast, the LHS `result.<name>` carries the same signed value it
did before. But is the `result.<name>[sign_bit_index]` access still well-
defined when the assignment was the result of `signed'(...)` rather than a
direct slice?

**Resolution.** Yes, no change required. The signed-padding line runs after
the assignment to `result.<name>` has completed. By that point
`result.<name>` is a packed signed value of width W; indexing it by an
integer literal `[sign_bit_index]` returns the 1-bit value at that
position. The bit value is the sign bit because of two's-complement bit-
level identity, not because the indexing operator inspects signedness.
The existing template line is correct under both the pre- and post-cast
generated forms.

**[NO SPEC CHANGE]**

---

## Q5. What does "the project's existing strict lint flag set" mean? (NFR-5, AC-9)

**Question.** NFR-5 and AC-9 reference "the project's existing strict lint
flag set" without naming it. Which Verilator flags?

**Resolution.** Unresolved at spec time. The project's lint flow lives
under `src/piketype/backends/lint/`; the implementation stage MUST inspect
the actual Verilator invocation used there and run regenerated goldens
through it. If the project does not yet pin a strict flag set, AC-9
collapses to "the regenerated goldens compile under Verilator without new
errors or warnings of category WIDTH/UNSIGNED/SIGNED/UNUSED relative to
the pre-feature baseline" — a delta check, not an absolute lint-clean
gate. This is the most we can guarantee without inventing a new lint
contract.

**Action.** Loosen AC-9's wording from "without new warnings on signed
cast or unused-variable categories" to the explicit delta-check form
above.

**[SPEC UPDATE]** — AC-9 rewrite.

---

## Q6. Where does `_is_field_signed` live, and what does it return for type-ref fields? (FR-1.2, FR-1.3)

**Question.** FR-1.2 reuses the existing `_is_field_signed` helper. Does it
return `True` for a struct field whose `type_ir` is a `TypeRefIR` to a
signed scalar alias? If so, FR-1.3's "skip the cast for type-ref" rule
must be enforced at the view-builder level (set `is_signed=False` on
type-ref unpack-field views) so that the template's branch on
`f.is_signed` does the right thing without an additional `f.is_type_ref`
check.

**Resolution.** Implementation contract:

- `_is_field_signed` (in `src/piketype/backends/sv/view.py`) is the source
  of truth for whether the underlying SV type carries a `signed` modifier.
  It MAY return `True` for a type-ref to a signed alias.
- The view builder MUST set `SvSynthStructUnpackFieldView.is_signed` to
  `True` only when both: (a) the field IR is signed AND (b) the field is
  inline (`is_type_ref == False`). For type-ref fields,
  `is_signed` is forced to `False` regardless of the alias's signedness,
  because the inner `unpack_<inner>` returns the signed value directly
  and the outer cast is forbidden by FR-1.3.

This keeps the template branch simple: `{% if f.is_signed %}` cleanly
gates the cast and there is no need for a parallel `f.is_type_ref` check
on the cast path.

**[NO SPEC CHANGE]** — implementation contract, captured in FR-1.2's
existing language ("a boolean flag (`is_signed`) to surface the existing
decision to the template"). Pinned here to remove ambiguity for the
planning stage.

---

## Spec Updates Summary

The following sections of `spec.md` are amended by the [SPEC UPDATE]
resolutions above. The amendments are applied in-place in `spec.md`; the
diff is recorded in `artifacts/clarification/iterN-spec-diff.md` per the
project convention.

| Section | Resolution | Source |
|---------|------------|--------|
| AC-4    | Drop NEW-fixture mandate; rebind to `tests/fixtures/struct_signed/`. Specify the exact post-regeneration content of `result.field_u` and `unpack_signed_*`. | Q1 |
| AC-9    | Replace "without new warnings on signed cast or unused-variable categories" with a delta-check form. | Q5 |
| Out of Scope | Strike the "new fixture" sentence in iteration-2 spec; the existing fixture is sufficient. | Q1 |
| NFR-4 | Drop the "A new fixture IS required for the signed-inline-field path" sentence. | Q1 |
