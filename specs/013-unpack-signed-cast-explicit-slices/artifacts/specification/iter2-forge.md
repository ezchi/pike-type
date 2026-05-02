# Specification — 013 Unpack Signed Cast & Explicit Slices

## Overview

The SystemVerilog `unpack_<base>` functions emitted for `struct` types — and, by
extension, the `unpack_<base>` function emitted for `scalar_alias` types whose
underlying typedef is signed — currently exhibit two lint problems that block
clean integration into downstream synthesis/lint flows:

1. **Missing signed cast on assignment / return.** When a scalar alias is
   declared signed (e.g. `Logic(N, signed=True)`), the emitted unpack body is
   `return a;` where `a` is `logic [W-1:0]` (unsigned) and the return type
   is the signed typedef — an implicit unsigned-to-signed assignment that
   triggers Verilator `WIDTH`/`UNSIGNED` warnings (and equivalents on
   commercial tools). The same problem occurs in struct unpack bodies: when a
   field's underlying type is signed, the unpack body assigns an unsigned slice
   expression (`a[offset +: WIDTH]` or `a[high:low]`) directly to the signed
   target field. Both cases must add an explicit signed cast.
2. **Runtime `offset` accumulator in struct unpack.** The struct unpack body
   declares `int unsigned offset;`, sets `offset = 0;`, and then on each field
   uses `a[offset +: WIDTH]; offset += WIDTH;`. Every slice boundary is
   statically knowable at codegen time (the IR carries each field's bit
   width and the tool already computes a total in `LP_<UPPER>_WIDTH`). The
   runtime accumulator is unnecessary indirection that hides the actual slice
   in generated code, makes diff review harder, and leaves an unused local in
   structs whose lint flow flags dead stores. Generated SystemVerilog must use
   explicit `[high:low]` constants (e.g. `a[3:0]`, `a[27:13]`) computed at
   codegen time.

This feature changes only the synthesizable `unpack_<base>` functions for
`scalar_alias` and `struct` kinds. It does not touch `pack_<base>`, the flags
or enum unpack variants, the verification-only `_test_pkg` helper classes, or
the C++ and Python backends. Generated golden output for affected fixtures will
change byte-for-byte, and the goldens must be refreshed in the same commit
that ships the codegen change.

## User Stories

- **US-1.** As an RTL engineer integrating a generated `*_pkg.sv`, I want the
  generated `unpack_<base>` functions (struct AND signed scalar alias) to be
  lint-clean against signed/unsigned width-mismatch checks (Verilator strict,
  Spyglass, Verissimo equivalents) so I can include them in projects whose CI
  gates on zero lint warnings without adding waivers.

- **US-2.** As a hardware reviewer reading a diff of a generated package, I
  want each struct-unpack assignment to show the explicit bit slice it reads
  from the packed input (e.g. `a[27:13]`), so I can verify field placement
  against the struct layout at a glance without mentally simulating an
  `offset` accumulator.

- **US-3.** As a Verilator user, I want struct unpack functions not to declare
  an unused `int unsigned offset` local, so my generated code does not trip
  "variable assigned but never read" or similar dead-store style lints.

## Functional Requirements

### Signed cast (FR-1 series)

- **FR-1.1.** When a struct field's effective SystemVerilog type is signed,
  the struct-unpack body MUST cast the slice expression to a signed value
  before assigning it to the field. Concretely, the generated assignment for
  a signed inline (non-type-ref) field of width `W` MUST be:

  ```
  result.<name> = signed'(a[<high>:<low>]);
  ```

  For an inline unsigned field, the form is unchanged:

  ```
  result.<name> = a[<high>:<low>];
  ```

  For a type-ref field (signed or unsigned), the form is unchanged:

  ```
  result.<name> = unpack_<inner>(a[<high>:<low>]);
  ```

  because the inner `unpack_<inner>` already returns the correctly-signed
  declared type and adding an outer `signed'(...)` would be redundant.

- **FR-1.2.** "Effective signed" for an inline field is determined the same
  way the existing view builder does it — via `_is_field_signed` against the
  field IR and the repo type index. No new IR data is required; the
  `SvSynthStructUnpackFieldView` MUST gain a boolean flag (`is_signed`) to
  surface the existing decision to the template.

- **FR-1.3.** The signed-cast rule MUST NOT apply to type-ref struct fields.
  Wrapping a `unpack_<inner>(...)` call in `signed'(...)` is forbidden because
  `unpack_<inner>` already returns the typed value.

- **FR-1.4.** When the unpacked type is a `scalar_alias` whose declared
  typedef is signed (i.e. the existing `view.signed` flag on the scalar-alias
  view is true), the scalar-alias unpack body MUST emit
  `return signed'(a);` instead of `return a;`. When the scalar alias is
  unsigned, the body MUST remain `return a;` — adding a redundant cast
  for the unsigned case is forbidden, because it would churn every
  unsigned-scalar golden in the repo and the cast carries no
  correctness benefit.

- **FR-1.5.** The signed-cast rule MUST NOT apply to flags or enum unpack
  functions. Flag unpack bodies assign individual bits to `bit` fields
  (always 1-bit, always unsigned in the generated typedef), and enum unpack
  is already a single `return <enum_t>'(a);` cast — both are out of scope
  for this feature.

### Explicit slice indices (FR-2 series, struct only)

- **FR-2.1.** The struct-kind branch of the unpack body MUST NOT declare or
  use the local `int unsigned offset`. The variable declaration, the
  `offset = 0;` initialiser, and every `offset += <expr>;` accumulation MUST
  be removed from generated output. (FR-2 does not apply to scalar_alias,
  flags, or enum unpack variants — none of them use the accumulator.)

- **FR-2.2.** Each field assignment in the struct-unpack body MUST use a
  closed-form `[<high>:<low>]` slice with literal integer constants computed
  by the Python view builder at codegen time. Examples:
  - 4-bit field at offset 0: `a[3:0]`.
  - 15-bit field starting at bit 13: `a[27:13]`.
  - 1-bit field at bit 31: `a[31:31]` (single-bit slices use the
    `[h:h]` part-select form, not the bit-select `a[31]`, to keep the
    template branch-free; OQ-1 in the previous iteration is resolved in
    favour of the part-select form).

- **FR-2.3.** Slice boundaries MUST match the existing pack ordering. The
  current pack expression concatenates fields in declaration order
  (`{pack_a, pack_b, pack_c}` etc.), and the existing unpack iterates
  `reversed(type_ir.fields)` so that the first field declared is at the
  highest bit position. The new explicit slices MUST preserve this exact
  bit-for-bit mapping; the same struct must pack and unpack to identical
  bytes before and after this change.

- **FR-2.4.** Slice arithmetic MUST be done in Python (in the view builder),
  never in the Jinja template. The template receives `slice_high` and
  `slice_low` integer fields on each unpack-field view object and emits them
  verbatim. This preserves the constitution's "Backend Python prepares view
  models; templates handle presentation only" rule.

- **FR-2.5.** `LP_<UPPER>_WIDTH` localparams used elsewhere (signal port
  widths, pack signatures, scalar-alias and enum unpack signatures) MUST
  remain unchanged. Type-ref struct fields MUST also use explicit `[high:low]`
  literals as the argument to the inner `unpack_<inner>(...)` call;
  consistency with FR-2.2 takes precedence over the convenience of writing
  `LP_<INNER>_WIDTH` inside the slice.

### Combined ordering & interaction (FR-3 series)

- **FR-3.1.** Where both rules apply (signed inline field in a struct), the
  cast wraps the slice: `result.x = signed'(a[7:0]);` — not the other way
  around.

- **FR-3.2.** Signed-padding handling (the existing
  `result.<name>_pad = {N{result.<name>[sign_bit]}};` block emitted when
  `has_signed_padding` is true) MUST remain unchanged in form. After this
  feature, `result.<name>` is signed, so `result.<name>[sign_bit]` reads
  the same bit it did before; no further edit to that line is required.

- **FR-3.3.** Form choice for the signed cast is `signed'(...)` (the
  SystemVerilog cast operator), not `$signed(...)` (the system function).
  Rationale: it composes cleanly with the existing `'(...)` pattern used in
  enum unpack (`{{ view.name }}'(a)`) and is the form preferred by the
  project's primary lint baseline (Verilator). OQ-2 in the previous
  iteration is resolved.

## Non-Functional Requirements

- **NFR-1. Template-first.** All formatting changes happen in
  `src/piketype/backends/sv/templates/_macros.j2` (the `synth_unpack_fn`
  macro: scalar-alias branch and struct branch) plus mechanical view-data
  additions in `src/piketype/backends/sv/view.py`. No inline string
  concatenation and no Python-side rendering of `[h:l]` strings; the template
  emits `a[{{ f.slice_high }}:{{ f.slice_low }}]` literally.
- **NFR-2. Determinism.** Generated output remains byte-for-byte
  deterministic. Slice boundaries are a pure function of the field list and
  their widths.
- **NFR-3. basedpyright strict mode** continues to pass with zero errors in
  `src/piketype/`.
- **NFR-4. Golden integration tests** continue to pass after the affected
  goldens are regenerated. No fixture additions are required as a
  prerequisite for the offset-removal path — the existing struct,
  nested-struct, and struct-multiple-of fixtures already cover it. A new
  fixture IS required for the signed-inline-field path (see AC-4).
- **NFR-5. Verilator-clean.** The regenerated unpack output for any existing
  fixture that contains a signed scalar alias OR a signed inline struct
  field MUST compile under Verilator with `--Wall -Wpedantic` (or the
  project's existing strict lint flag set) without producing new warnings.
  If no current fixture contains a signed inline struct field, a new fixture
  and golden MUST be added to cover that path so NFR-5 is testable for
  it. (Existing fixtures already exercise signed scalar aliases via
  `Logic(N, signed=True)`.)

## Acceptance Criteria

- **AC-1.** The `synth_unpack_fn` macro for `kind == "struct"` no longer
  emits `int unsigned offset;`, `offset = 0;`, or any `offset += ...;` line.
  Verified by grepping the regenerated goldens under
  `tests/goldens/gen/**/types_pkg.sv` and asserting no occurrence of
  `int unsigned offset` inside any `unpack_*` function body.

- **AC-2.** For every struct in every existing golden, each unpack-field
  assignment uses an `a[<int>:<int>]` slice with literal integer constants.
  Verified by a regex scan over the regenerated goldens that asserts no
  `a[offset` substring appears in any `unpack_*` body.

- **AC-3.** Field-to-slice mapping is preserved bit-for-bit. Verified by an
  existing or new round-trip test: for at least one struct fixture, a
  hand-computed expected per-field `[high:low]` table matches the regenerated
  golden exactly.

- **AC-4.** A NEW struct fixture (e.g. `tests/fixtures/struct_signed_inline/`)
  with at least one signed inline `Logic(W, signed=True)` field used directly
  (not via type-ref) MUST be added in this stage's implementation, with a
  matching golden under `tests/goldens/gen/struct_signed_inline/`. The
  regenerated golden's struct unpack function MUST show
  `result.<field> = signed'(a[<h>:<l>]);` with the correct slice boundaries.
  No existing fixture may be edited to add a signed inline field; a new
  fixture is mandated to keep churn isolated. (OQ-3 in the previous iteration
  is resolved.)

- **AC-5.** All regenerated goldens that contain a signed scalar alias
  emit `return signed'(a);` in that alias's unpack function. All regenerated
  goldens that contain an unsigned scalar alias continue to emit
  `return a;` unchanged. Verified by grep over regenerated goldens.

- **AC-6.** Type-ref fields in regenerated goldens use the form
  `result.<name> = unpack_<inner>(a[<h>:<l>]);` — explicit slice literal,
  no outer `signed'` wrapper, no `LP_<INNER>_WIDTH` inside the slice.

- **AC-7.** The full `unittest` suite passes after goldens are refreshed.

- **AC-8.** `basedpyright` reports zero errors over `src/piketype/`.

- **AC-9.** Verilator compiles every regenerated `_pkg.sv` golden with the
  project's existing strict lint flag set without new warnings on signed
  cast or unused-variable categories. Applies to any fixture that the
  current project Verilator-flow runs over; the spec does not introduce new
  CI steps.

- **AC-10.** Single-bit struct fields render as `a[<i>:<i>]` (part-select
  form, both endpoints equal), not as `a[<i>]` (bit-select), in the
  regenerated goldens.

## Out of Scope

- Any change to `pack_<base>` functions. Pack already uses Python-side
  expression strings and concatenation; it is unaffected.
- Any change to flags or enum unpack variants — they do not have signed
  fields and do not use slice accumulators.
- Any change to the verification-only `_test_pkg` helper classes
  (`to_bytes`, `from_bytes`, randomization helpers, etc.).
- Any change to the C++ or Python backends or to the runtime support
  packages.
- Lint-clean behaviour against tools other than Verilator. The acceptance
  criteria call out Verilator because it is the project's current lint
  baseline; commercial-tool clean-ness is a downstream consequence, not a
  spec gate.
- Replacing `+:` with `[h:l]` anywhere outside the struct-unpack body
  (e.g. inside `to_bytes` / `from_bytes` byte-loop slices). Those use
  `+:` deliberately because the index is a loop variable, not a constant.
- Adding redundant `signed'(...)` casts to unsigned scalar aliases or
  unsigned struct fields. The cast appears only where the target is signed.

## Open Questions

(All open questions raised in iteration 1 are resolved in this iteration:
OQ-1 → part-select `a[i:i]` form; OQ-2 → cast operator `signed'(...)` form;
OQ-3 → new fixture, do not edit existing fixtures. No outstanding open
questions remain.)
