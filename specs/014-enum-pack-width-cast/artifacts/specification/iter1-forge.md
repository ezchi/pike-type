# Specification — 014 Enum Pack Width Cast

## Overview

The SystemVerilog `pack_<base>` function emitted for `enum` types currently
contains a width-incorrect cast in its body. The function declares the correct
return type — `logic [LP_<UPPER>_WIDTH-1:0]` — but the body is:

```systemverilog
return logic'(a);
```

The cast operator `logic'(...)` casts to the type `logic`, which is a **single
bit** in SystemVerilog. For any multi-bit enum (e.g. a 3-bit `status_t` with 5
members, or the existing `color_t`/`cmd_t`/`big_t` fixtures), the cast first
truncates `a` to its LSB and then the assignment to the wider return value
zero-extends it back to `LP_<UPPER>_WIDTH` bits. The pack function therefore
returns `{(W-1){1'b0}, a[0]}` instead of the enum's encoded bit pattern, which
is wrong for every enum value other than 0 and 1.

The bug is silent in the existing golden-file test suite because the generated
verification helper class for enums (`test_enum_helper` macro,
`_test_pkg`) returns `value` directly via `to_slv()` and does not exercise the
synthesizable `pack_<base>` function. The `from_bytes` / `to_bytes` round trip
in the helper class uses the underlying typedef (`logic [W-1:0]`) directly and
bypasses the buggy pack body. Downstream SystemVerilog code that imports the
synth `_pkg` and calls `pack_<base>(my_enum)` directly — which is the
documented public API of the synth package, listed in the cross-module bundle
`{T_t, LP_<UPPER>_WIDTH, pack_<base>, unpack_<base>}` (`view.py:780`) — sees
data corruption.

This feature replaces the broken cast in the enum branch of the `synth_pack_fn`
macro with a width-correct expression and refreshes the affected goldens. It
does not touch `unpack_<base>` (already correct: `return <enum_t>'(a);`),
the scalar-alias / flags / struct branches of `synth_pack_fn`, the
verification-only `_test_pkg` helper classes, or the C++ / Python backends.

## User Stories

- **US-1.** As an RTL engineer integrating a generated `*_pkg.sv` into a
  larger design, I want `pack_<enum>(my_enum)` to return the enum's encoded
  bit pattern at the declared width, so downstream concatenations and bus
  packing produce the value I see in the typedef declaration rather than a
  zero-extended LSB.

- **US-2.** As a hardware reviewer reading a diff of a generated synth
  package, I want the body of `pack_<enum>` to make the returned width
  obvious at the cast site, so I do not have to mentally evaluate
  SystemVerilog's implicit width-extension rules to verify correctness.

- **US-3.** As a Verilator / commercial-lint user, I want the pack body
  to be free of suspect single-bit casts inside a multi-bit return context,
  so the generated package does not contribute width-mismatch warnings to
  my lint baseline.

## Functional Requirements

### Codegen change (FR-1 series)

- **FR-1.1.** The `enum` branch of the `synth_pack_fn` macro in
  `src/piketype/backends/sv/templates/_macros.j2` MUST emit a width-correct
  return expression for both 1-bit and multi-bit enums. The chosen form is:

  ```systemverilog
  return LP_<UPPER>_WIDTH'(a);
  ```

  where `<UPPER>` is the existing `view.upper_base` value (the same token
  already used to name the localparam on the immediately preceding lines and
  the function's declared return type). Concretely, the template body in the
  enum branch becomes:

  ```jinja
  return LP_{{ view.upper_base }}_WIDTH'(a);
  ```

- **FR-1.2.** The form `logic'(a)` (single-bit cast) MUST NOT appear in the
  enum pack body. The form `<enum_t>'(a)` (typed cast back to the same enum)
  MUST NOT appear here either — that form belongs in `unpack_<base>`,
  not `pack_<base>`.

- **FR-1.3.** No new view-data field, no helper function in `view.py`, and
  no new IR node is required. The `view.upper_base` value already used by
  the surrounding macro lines is sufficient. This change is template-only;
  `src/piketype/backends/sv/view.py` MUST remain untouched by FR-1.

- **FR-1.4.** The fix MUST apply uniformly to every enum, regardless of
  width. 1-bit enums (e.g. the existing `flag_t` in the `enum_basic`
  fixture, where `LP_FLAG_WIDTH = 1`) MUST also use the
  `LP_<UPPER>_WIDTH'(a)` form, not retain the old `logic'(a)` form. Branching
  on `view.is_one_bit` in this macro is forbidden — a single uniform form
  is simpler, matches the unpack side which is also branch-free, and avoids
  the need to special-case golden regeneration for 1-bit enums.

### Scope boundary (FR-2 series)

- **FR-2.1.** The change is limited to the `{% elif view.kind == "enum" %}`
  branch inside `synth_pack_fn`. The `scalar_alias`, `flags`, and `struct`
  branches of `synth_pack_fn` MUST remain unchanged.

- **FR-2.2.** `synth_unpack_fn` MUST remain unchanged. Its enum branch
  (`return <enum_t>'(a);`) is already width-correct and producing the
  correct typed result.

- **FR-2.3.** The `test_enum_helper` macro and other `_test_pkg` helper
  classes MUST remain unchanged. Although the helper's `to_slv()` /
  `from_slv()` path bypasses `pack_<base>`, this spec does not refactor
  the helper to call `pack_<base>` — that would broaden scope and re-churn
  every enum test golden for no correctness gain in the helper itself.

- **FR-2.4.** The C++ and Python backends, the runtime support package,
  and the `_pkg` import-bundle wiring (`view.py:780`-`view.py:791`) MUST
  remain unchanged.

### Golden refresh (FR-3 series)

- **FR-3.1.** Every existing golden that contains an enum's `pack_<base>`
  function MUST be regenerated as part of the same commit that ships the
  template change, so the repository remains byte-parity verifiable on
  every commit. Affected goldens (enumerated from the current
  `tests/goldens/gen/` tree, by inspection of which fixtures define enums):
  - `tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv`
    (defines `color_t`, `cmd_t`, `flag_t`, `big_t`)
  - `tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv`
  - `tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv`
  - Any other golden that, on inspection, emits a `pack_<enum>` body
    containing `return logic'(a);`. The regeneration mechanism (walk
    fixtures and run `piketype gen`, then tree-replace) is the
    project-standard pattern; it picks up every affected file
    automatically.

- **FR-3.2.** The corresponding `_test_pkg` goldens MUST NOT change as a
  byproduct of this feature, because the helper classes do not call
  `pack_<base>`. Any `_test_pkg` diff observed during regeneration is a
  signal that scope leaked beyond the pack body and MUST be investigated
  before commit.

- **FR-3.3.** Goldens for fixtures that contain no enum types MUST NOT
  change. Examples: `struct_signed`, scalar-alias-only fixtures, flags-only
  fixtures, runtime-only outputs (`piketype_runtime_pkg.sv`).

## Non-Functional Requirements

- **NFR-1. Template-first.** The codegen change happens entirely in
  `src/piketype/backends/sv/templates/_macros.j2`. No Python source file
  under `src/piketype/` is modified by this feature. This satisfies
  Constitution principle 5 ("Template-first generation") and matches the
  user-memory directive `feedback_template_first_strict.md`.

- **NFR-2. Byte-parity per commit.** The single feature commit MUST
  contain both the template edit and the regenerated goldens. Every commit
  on the feature branch (intermediate or final) MUST leave
  `python -m piketype.cli gen` output byte-identical to the committed
  goldens. This matches the user-memory directive
  `feedback_byte_parity_per_commit.md`.

- **NFR-3. Determinism.** Generated output remains byte-for-byte
  reproducible. The width substituted at codegen time is the existing
  `LP_<UPPER>_WIDTH` localparam name, which is already deterministic.

- **NFR-4. basedpyright strict mode** continues to pass with zero errors
  over `src/piketype/`. (No Python is touched by this feature, so this is
  effectively a regression guard, not a new gate.)

- **NFR-5. Verilator-clean.** The regenerated `_pkg.sv` outputs MUST
  compile under the project's existing Verilator lint flow without
  introducing new warnings of category WIDTH, UNSIGNED, SIGNED, CASTCONST,
  or ASSIGNDLY, measured as a delta against the pre-feature golden output
  for the same fixture. The pre-feature `return logic'(a);` form is
  already lint-clean on Verilator 5.046 (per
  `reference_verilator_signed_warning_gap.md` — Verilator does not flag
  the truncation), so the post-feature delta MUST also be silent. The
  spec does not introduce a new CI lint step.

- **NFR-6. Test suite.** The full `unittest` suite under `tests/` MUST
  pass after goldens are refreshed.

## Acceptance Criteria

- **AC-1.** A grep of the regenerated tree
  `tests/goldens/gen/**/*_pkg.sv` returns zero matches for the literal
  string `return logic'(a);`. Verified by:

  ```
  grep -r "return logic'(a);" tests/goldens/gen/ ; test $? -eq 1
  ```

- **AC-2.** A grep of the regenerated tree returns one match for
  `return LP_<UPPER>_WIDTH'(a);` per enum defined across all fixtures.
  The expected match list (from the affected fixtures enumerated in
  FR-3.1) is at minimum:
  - `return LP_COLOR_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_color`
  - `return LP_CMD_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_cmd`
  - `return LP_FLAG_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_flag` (1-bit case)
  - `return LP_BIG_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_big`
  - One per enum in `struct_enum_member` and `keyword_enum_value_while_passes`
  Exact match counts are confirmed by re-running `piketype gen` on each
  fixture and diffing against the regenerated goldens.

- **AC-3.** The 1-bit enum `flag_t` (`LP_FLAG_WIDTH = 1`) in the
  `enum_basic` fixture renders the same uniform form
  `return LP_FLAG_WIDTH'(a);` — not `return logic'(a);`, not `return a;`.
  Verified by reading the regenerated golden.

- **AC-4.** Pack/unpack round-trip is bit-for-bit correct for every enum
  member of every enum in the `enum_basic` fixture. Verified by either:
  (a) an existing golden test that emits a SystemVerilog testbench
  exercising `pack_color(RED)`, `pack_color(GREEN)`, `pack_color(BLUE)`,
  etc., compares the result to the typedef-encoded bit pattern, and
  passes; or (b) hand-inspection of the regenerated golden plus a
  written-out value table in the validation stage. The spec does not
  prescribe (a); whichever route the implementation chooses MUST produce
  evidence that `pack_color(GREEN) == 4'd5` (and analogous for the other
  members) holds in the regenerated package.

- **AC-5.** No file under `src/piketype/` other than
  `backends/sv/templates/_macros.j2` is modified by the implementation
  diff for this feature. Verified by `git diff --stat
  master..feature/014-enum-pack-width-cast -- src/piketype/`.

- **AC-6.** No `_test_pkg.sv` golden under `tests/goldens/gen/` is
  modified by the regeneration. Verified by
  `git diff --stat master..feature/014-enum-pack-width-cast --
  tests/goldens/gen/**/*_test_pkg.sv` returning empty.

- **AC-7.** No golden for a fixture without an enum changes. Verified by
  diff inspection: the only changed `_pkg.sv` files are those listed in
  FR-3.1 (or, if a not-yet-listed fixture has an enum, that fixture's
  pkg should also change — and only its pack body lines).

- **AC-8.** The full `unittest` suite passes after goldens are refreshed.

- **AC-9.** `basedpyright` reports zero errors over `src/piketype/`.

- **AC-10.** Verilator compiles every regenerated `_pkg.sv` golden under
  the project's existing lint flow with no new errors and no new
  warnings, measured as a delta against the pre-feature output for the
  same fixture.

## Out of Scope

- Any change to `synth_unpack_fn` or to the unpack form
  `return <enum_t>'(a);`. Unpack is correct; touching it would churn
  every enum unpack golden for no gain.
- Any change to `pack_<base>` for `scalar_alias`, `flags`, or `struct`
  kinds. The bug is enum-only.
- Any change to `_test_pkg` helper classes. The helpers' `to_slv()` /
  `from_slv()` already handle enums correctly via direct typedef
  assignment; refactoring the helper to route through `pack_<base>` is a
  separate scope.
- Any change to the C++ or Python backends. The bug does not exist in
  those backends — they pack enums via direct integer cast in their
  respective languages.
- Adding a regression test that compiles and executes a SystemVerilog
  testbench calling `pack_<enum>` and asserts the result. Such a test
  would require introducing a Verilator-driven SV simulation harness,
  which is not present today and is out of scope for this fix. AC-4
  permits hand-inspection plus golden diff as the evidence path.
- Replacing the `LP_<UPPER>_WIDTH'(a)` cast form with bare `return a;`.
  Although bare `a` is legal SystemVerilog (enum-to-base assignment is
  permitted), the explicit width-cast is preferred for diff readability
  and parallels the existing `view.name'(a)` form on the unpack side.
- Lint-clean behaviour against tools other than Verilator. Commercial
  tools (Spyglass, Verissimo) may or may not have flagged the original
  buggy form; aligning with their warning sets is downstream of this
  spec.

## Open Questions

- **OQ-1.** Should AC-4 mandate adding a SystemVerilog testbench harness
  that actually compiles and executes `pack_<enum>` calls, rather than
  accepting hand-inspection + golden diff as evidence? The current spec
  treats this as out of scope on the grounds that no SV-execution
  harness exists today. If the project intends to add such a harness as
  part of a broader testing initiative, this feature could be the
  forcing function — but doing so widens scope significantly. **Pending
  human decision in the clarification stage.** [NEEDS CLARIFICATION]

- **OQ-2.** Is there any other generated SystemVerilog site (outside
  `synth_pack_fn`) that uses the `logic'(...)` single-bit cast inside a
  multi-bit return / assignment context and is silently masked the same
  way? A grep over the templates and the regenerated goldens before
  applying the fix would either confirm enum pack is the only instance
  or expose siblings. The implementation stage MUST run this grep and
  report results. **Pending implementation-stage verification.**
  [NEEDS CLARIFICATION]
