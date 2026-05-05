# Specification — 013 Unpack Signed Cast & Explicit Slices

## Overview

The SystemVerilog `unpack_<base>` functions emitted for `struct` types currently
exhibit two lint problems that block clean integration into downstream
synthesis/lint flows:

1. **Missing signed cast on assignment.** When a struct field's underlying type
   is `signed` (e.g. a `Logic(N, signed=True)` scalar alias or a signed
   alias used inline), the unpack body assigns an unsigned slice expression
   directly to the signed target field. The right-hand side
   (`a[offset +: WIDTH]` or `a[high:low]`) is unsigned, while the left-hand side
   is `signed`, which produces sign-mismatch lint warnings such as Verilator
   `WIDTH`/`UNSIGNED`/`ASSIGNDLY` family warnings or equivalent
   commercial-tool warnings.
2. **Runtime `offset` accumulator.** The unpack body declares
   `int unsigned offset;`, sets `offset = 0`, and then on each field uses
   `a[offset +: WIDTH]; offset += WIDTH;`. Every slice boundary is statically
   knowable at codegen time (the IR carries each field's bit width and the
   tool already computes a total in `LP_<UPPER>_WIDTH`). The runtime
   accumulator is unnecessary indirection that hides the actual slice in
   generated code, makes diff review harder, and adds an unused local in
   simple structs. Generated SystemVerilog must use explicit `[high:low]`
   constants (e.g. `a[3:0]`, `a[27:13]`) computed at codegen time.

This feature changes only the synthesizable `unpack_<base>` function emitted for
struct types. It does not touch `pack_<base>`, scalar alias / flags / enum
unpack variants, the verification-only `_test_pkg` helper classes, or the C++
and Python backends. Generated golden output for affected fixtures will change
byte-for-byte and the goldens must be refreshed in the same commit that ships
the codegen change.

## User Stories

- **US-1.** As an RTL engineer integrating a generated `*_pkg.sv`, I want the
  generated `unpack_<base>` function to be lint-clean against signed/unsigned
  width-mismatch checks (Verilator strict, Spyglass, Verissimo equivalents) so
  I can include it in projects whose CI gates on zero lint warnings without
  adding waivers.

- **US-2.** As a hardware reviewer reading a diff of a generated package, I
  want each unpack assignment to show the explicit bit slice it reads from the
  packed input (e.g. `a[27:13]`), so I can verify field placement against the
  struct layout at a glance without mentally simulating an `offset` accumulator.

- **US-3.** As a Verilator user, I want unpack functions on small structs not
  to declare an unused `int unsigned offset` local, so my generated code does
  not trip "variable assigned but never read" or similar dead-store style lints.

## Functional Requirements

### Signed cast (FR-1 series)

- **FR-1.1.** When a struct field's effective SystemVerilog type is signed,
  the unpack body MUST cast the slice expression to a signed value before
  assigning it to the field. Concretely, the generated assignment for a signed
  field of width `W` MUST be:

  ```
  result.<name> = signed'(a[<high>:<low>]);
  ```

  for an inline (non-type-ref) field, and:

  ```
  result.<name> = unpack_<inner>(a[<high>:<low>]);
  ```

  unchanged for a type-ref field, because the inner `unpack_<inner>` already
  returns the correctly-signed declared type and adding an outer
  `signed'(...)` would be redundant.

- **FR-1.2.** "Effective signed" for an inline field is determined the same
  way the existing view builder does it — via `_is_field_signed` against the
  field IR and the repo type index. No new IR data is required; the
  `SvSynthStructUnpackFieldView` may gain a boolean flag (e.g. `is_signed`)
  to surface the existing decision to the template.

- **FR-1.3.** The signed-cast rule MUST NOT apply to type-ref fields. Wrapping
  a `unpack_<inner>(...)` call in `signed'(...)` is forbidden because
  `unpack_<inner>` already returns the typed value.

- **FR-1.4.** The signed-cast rule MUST NOT apply to flags, enum, or
  scalar-alias unpack functions. Those bodies are a single `return` and the
  declared return type already governs signedness; no per-field assignment is
  performed.

### Explicit slice indices (FR-2 series)

- **FR-2.1.** The unpack body for a struct MUST NOT declare or use the local
  `int unsigned offset`. The variable declaration, the `offset = 0;`
  initialiser, and every `offset += <expr>;` accumulation MUST be removed
  from generated output.

- **FR-2.2.** Each field assignment in the unpack body MUST use a closed-form
  `[<high>:<low>]` slice with literal integer constants computed by the
  Python view builder at codegen time. Examples:
  - 4-bit field at offset 0: `a[3:0]`.
  - 15-bit field starting at bit 13: `a[27:13]`.
  - 1-bit field at bit 31: `a[31:31]` (single-bit slices use the
    `[h:h]` form, not the bit-select form `a[31]`, to keep the template
    branch-free; see Open Questions).

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

- **FR-2.5.** `LP_<UPPER>_WIDTH` localparams used elsewhere
  (signal port widths, pack signatures, type-ref unpack call slices) MUST
  remain unchanged. Type-ref fields MUST also use explicit `[high:low]`
  literals as the argument to the inner `unpack_<inner>(...)` call;
  consistency with FR-2.2 takes precedence over the convenience of writing
  `LP_<INNER>_WIDTH` inside the slice.

### Combined ordering (FR-3 series)

- **FR-3.1.** Where both rules apply (signed inline field), the cast wraps
  the slice: `result.x = signed'(a[7:0]);` — not the other way around.

- **FR-3.2.** Signed-padding handling (the existing
  `result.<name>_pad = {N{result.<name>[sign_bit]}};` block emitted when
  `has_signed_padding` is true) MUST remain unchanged in form. After this
  feature, `result.<name>` is signed, so `result.<name>[sign_bit]` reads
  the same bit it did before; no further edit is required there.

## Non-Functional Requirements

- **NFR-1. Template-first.** All formatting changes happen in
  `src/piketype/backends/sv/templates/_macros.j2` (the
  `synth_unpack_fn` macro) plus mechanical view-data additions in
  `src/piketype/backends/sv/view.py`. No `inline string concatenation` and no
  Python-side rendering of `[h:l]` strings; the template emits
  `a[{{ f.slice_high }}:{{ f.slice_low }}]` literally.
- **NFR-2. Determinism.** Generated output remains byte-for-byte deterministic.
  Slice boundaries are a pure function of the field list and their widths.
- **NFR-3. basedpyright strict mode** continues to pass with zero errors in
  `src/piketype/`.
- **NFR-4. Golden integration tests** continue to pass after the affected
  goldens are regenerated. No fixture additions are required as a
  prerequisite — the existing struct/nested-struct/struct-multiple-of
  fixtures already cover every code path being changed.
- **NFR-5. Verilator-clean.** The regenerated unpack output for any existing
  fixture that contains a signed inline field MUST compile under Verilator
  with `--Wall -Wpedantic` (or the project's existing strict lint flag set)
  without producing new warnings. If no current fixture contains a signed
  inline struct field, a new fixture and golden MUST be added to cover this
  path so NFR-5 is testable.

## Acceptance Criteria

- **AC-1.** The `synth_unpack_fn` macro for `kind == "struct"` no longer
  emits `int unsigned offset;`, `offset = 0;`, or any `offset += ...;` line.
  This is verified by grepping the regenerated goldens under
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

- **AC-4.** A struct fixture with at least one signed inline field
  (e.g. a `Logic(W, signed=True)` field used directly, not via type-ref)
  exists in `tests/fixtures/`, has a golden under `tests/goldens/gen/`, and
  the regenerated golden's unpack function for that struct shows
  `result.<field> = signed'(a[<h>:<l>]);` with the correct slice. If no such
  fixture currently exists, the implementation stage MUST add one.

- **AC-5.** Type-ref fields in regenerated goldens use the form
  `result.<name> = unpack_<inner>(a[<h>:<l>]);` — explicit slice literal,
  no outer `signed'` wrapper, no `LP_<INNER>_WIDTH` inside the slice.

- **AC-6.** The full `unittest` suite passes after goldens are refreshed.

- **AC-7.** `basedpyright` reports zero errors over `src/piketype/`.

- **AC-8.** Verilator compiles every regenerated `_pkg.sv` golden with the
  project's existing strict lint flag set without new warnings on signed
  cast or unused-variable categories. (Only applicable to fixtures that
  currently exercise Verilator in CI; the spec does not introduce new CI
  steps.)

- **AC-9.** Single-bit fields render as `a[<i>:<i>]` (and not as `a[<i>]`)
  in the regenerated goldens, unless Open Question OQ-1 is resolved in
  favour of the bit-select form.

## Out of Scope

- Any change to `pack_<base>` functions. Pack already uses Python-side
  expression strings and concatenation; it is unaffected.
- Any change to scalar alias, flags, or enum unpack variants — they do not
  use slices or accumulators.
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

## Open Questions

- **[NEEDS CLARIFICATION] OQ-1.** For 1-bit fields, should the generated
  form be `a[i:i]` (uniform with the multi-bit case) or `a[i]` (idiomatic
  bit-select)? The specification currently locks in `a[i:i]` (FR-2.2,
  AC-9) to keep the template branch-free, but a project preference for
  idiomatic single-bit syntax would flip this.
- **[NEEDS CLARIFICATION] OQ-2.** Is there a project preference between
  `signed'(a[h:l])` (SystemVerilog signed cast operator) and the
  alternative `$signed(a[h:l])` (system function form)? The spec
  currently selects the cast operator `signed'(...)` because it composes
  cleanly with the existing `'(...)` pattern used in enum unpack
  (`{{ view.name }}'(a)`). If commercial tools the team uses prefer
  `$signed`, this flips.
- **[NEEDS CLARIFICATION] OQ-3.** Should an existing fixture be edited
  to add a signed inline struct field, or should a new fixture be added
  alongside the existing ones? The spec mandates the field be covered
  (AC-4) but does not constrain placement. A new fixture is the safer
  default because it avoids churn in unrelated goldens.
