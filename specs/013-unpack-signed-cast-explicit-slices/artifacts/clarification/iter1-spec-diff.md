# Spec Diff — Clarification Iteration 1

Records exactly which sections of `spec.md` changed in clarification
iteration 1, with before/after content for each change.

---

## Change 1 — NFR-4 (Golden integration tests)

**Before**

> - **NFR-4. Golden integration tests** continue to pass after the affected
>   goldens are regenerated. No fixture additions are required as a
>   prerequisite for the offset-removal path — the existing struct,
>   nested-struct, and struct-multiple-of fixtures already cover it. A new
>   fixture IS required for the signed-inline-field path (see AC-4).

**After**

> - **NFR-4. Golden integration tests** continue to pass after the affected
>   goldens are regenerated. No fixture additions are required: the existing
>   `tests/fixtures/struct_signed/` already exercises both the signed scalar
>   alias path and the signed inline struct field path
>   (`field_u = Logic(5, signed=True)`).

**Source.** Q1 — pre-flight discovery that `struct_signed` already covers the
signed-inline-field path.

---

## Change 2 — AC-4 (signed inline field acceptance)

**Before**

> - **AC-4.** A NEW struct fixture (e.g. `tests/fixtures/struct_signed_inline/`)
>   with at least one signed inline `Logic(W, signed=True)` field used directly
>   (not via type-ref) MUST be added in this stage's implementation, with a
>   matching golden under `tests/goldens/gen/struct_signed_inline/`. The
>   regenerated golden's struct unpack function MUST show
>   `result.<field> = signed'(a[<h>:<l>]);` with the correct slice boundaries.
>   No existing fixture may be edited to add a signed inline field; a new
>   fixture is mandated to keep churn isolated. (OQ-3 in the previous iteration
>   is resolved.)

**After**

> - **AC-4.** The existing `tests/fixtures/struct_signed/` fixture already
>   exercises a signed inline `Logic(W, signed=True)` field used directly
>   (`mixed_t.field_u = Logic(5, signed=True)`). After regeneration, the
>   golden `tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv`
>   MUST show `result.field_u = signed'(a[4:0]);` inside `unpack_mixed`.
>   (Clarification Q1 supersedes the iteration-2 mandate to add a new
>   fixture; OQ-3 is resolved by reusing the existing fixture, not by
>   creating a new one.)

**Source.** Q1.

---

## Change 3 — AC-9 (Verilator lint check)

**Before**

> - **AC-9.** Verilator compiles every regenerated `_pkg.sv` golden with the
>   project's existing strict lint flag set without new warnings on signed
>   cast or unused-variable categories. Applies to any fixture that the
>   current project Verilator-flow runs over; the spec does not introduce new
>   CI steps.

**After**

> - **AC-9.** Verilator compiles every regenerated `_pkg.sv` golden under
>   the project's existing lint flow (in `src/piketype/backends/lint/`)
>   with no new errors and no new warnings of category WIDTH, UNSIGNED,
>   SIGNED, or UNUSED relative to the pre-feature baseline. The check is
>   a delta against the same fixture's pre-feature output, not an absolute
>   lint-clean gate. The spec does not introduce new CI steps. (Clarification
>   Q5 supersedes the iteration-2 wording.)

**Source.** Q5 — "strict lint flag set" was unspecified; replaced with a
concrete delta-check that the implementation stage can mechanise.

---

## Change Summary

Three sections edited (NFR-4, AC-4, AC-9). No new FRs, ACs, or NFRs added.
No existing items renumbered. The Out-of-Scope section is unchanged
because the iteration-2 wording there does not contain "new fixture"
language to strike.
