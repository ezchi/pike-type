# Specification: VecConst DSL primitive for arbitrary-width logic vector constants

**Spec ID:** 016-vec-const-dsl-primitive
**Branch:** feature/016-vec-const-dsl-primitive
**Status:** Clarified (post-Clarification iteration 1)

## Overview

Add a new top-level DSL primitive, `VecConst`, that declares a fixed-width logic vector constant with an explicit base for SystemVerilog literal rendering (hex / decimal / binary). The new primitive is distinct from the existing `Const`. Existing `Const` continues to mean "32/64-bit integer parameter" (emitted as `localparam int FOO = 32'sd3;`); `VecConst` means "arbitrary-width typed logic vector constant" (emitted as `localparam logic [N-1:0] <NAME> = N'<base-letter><value>;`).

This unblocks declaring protocol-style named values such as `LP_ETHERTYPE_VLAN`, `LP_IP_PROTOCOL_TCP`, `LP_IP_PROTOCOL_UDP`, etc., directly from the DSL with both width and base preserved into the generated SV.

The Project Constitution §Constraints item 5 must be amended to scope its 32/64-bit restriction to `Const()` only.

## Background

- Existing `Const()` (`src/piketype/dsl/const.py:122`) accepts only `width=None|32|64` and emits `localparam int FOO = 32'sd3;` via `_render_sv_const` at `backends/sv/view.py:312`.
- The Constitution §Constraints item 5 reads: *"Constant widths restricted to 32/64 bits. Arbitrary-width constants are not supported; the validation layer rejects other widths."* This was written when `Const()` was the only constant primitive.
- Generated SV today does not have a way to express, e.g., `localparam logic [15:0] LP_ETHERTYPE_VLAN = 16'h8100;` from a DSL declaration.

## User Stories

- **US-1.** As a hardware designer, I want to declare named protocol values (ethertypes, IP protocol numbers, opcode tables) in the DSL with explicit width and base, so that the generated SV uses the natural form for the literal (`16'h8100`, `8'd17`, `4'b1010`) rather than `32'sd<int>`.
- **US-2.** As a DSL author, I want to compute a `VecConst`'s value from existing `Const` references and arithmetic (e.g., `value=A * 3` where `A = Const(5)`), and have the generator evaluate it at generation time and emit the resolved literal — not the symbolic expression.
- **US-3.** As a maintainer, I want overflow to be a hard error: if `value` does not fit in `width` bits (unsigned), gen fails with a clear validation message at the DSL site, not silently truncates.

## Functional Requirements

### Surface

- **FR-1.** A new public DSL constructor MUST be exported as `VecConst` from the same import path users currently use for `Const` (i.e., `from piketype.dsl import VecConst`, alongside `Const`).
- **FR-2.** The signature MUST be `VecConst(width: ConstOperand, value: ConstOperand, *, base: str = "dec")`. `width` and `value` accept any `ConstOperand` (int, Const, ConstExpr, OR another VecConst — see post-016 follow-up below). `base` is keyword-only and defaults to `"dec"`.
- **FR-3.** `base` MUST accept exactly the three string values `"hex"`, `"dec"`, `"bin"`. Any other value MUST raise `ValidationError` at construction time with a clear message naming the offending value.
- **FR-4.** `width` MUST resolve (after evaluating any expression) to a positive int. Width = 0 or negative MUST raise `ValidationError`.
- **FR-5.** `width` upper bound MUST be 64 — matching the existing 64-bit ceiling on signed scalar widths and the natural SV typed-literal range.

### Evaluation semantics

- **FR-6.** When `value` is a `Const` reference, `ConstExpr` (e.g., `A * 3`), or int literal, the generator MUST evaluate it at IR-build time and emit the resolved scalar integer in the SV literal. The generated SV MUST NOT contain the symbolic expression — it must contain only the final integer rendered in the chosen base.
- **FR-7.** Overflow check: the resolved integer value MUST satisfy `0 <= value <= 2**width - 1`. Values outside that range MUST raise `ValidationError` at construction or validation time with a message that includes (a) the offending integer value, (b) the declared width N, and (c) the upper bound rendered as the formula `2**N - 1` (with N substituted) — e.g., for `width=8, value=300`: `"VecConst(width=8, value=300) overflows: value must satisfy 0 <= value <= 2**8 - 1 (= 255)"`. The exact phrasing is not mandated, but the three substrings (value, width, formula `2**N - 1`) MUST appear.
- **FR-8.** Negative resolved values are rejected.

### SV emission

- **FR-9.** The SV synth-package emission MUST be exactly:
  ```
    localparam logic [N-1:0] <NAME> = N'<L><digits>;
  ```
  where `N` is the resolved width, `<NAME>` is the constant's emitted name (per FR-12), `<L>` is the base letter (`h`, `d`, `b` for hex/dec/bin respectively), and `<digits>` is the resolved value rendered in the chosen base **without the `0x` / `0b` prefix** that Python uses (e.g., hex `0x8100` → `8100`; bin `0b00001111` → `00001111`).
- **FR-10.** Hex digits MUST be uppercase (`8'hAB`, not `8'hab`). Aligns with existing SV style for type widths and improves diff readability against most IP vendor RTL.
- **FR-11.** Zero-padding for `base="hex"` and `base="bin"` MUST pad the rendered digits to the minimum number of digits needed to express the full `width` (`width // 4` for hex, `width` for bin), so e.g. `VecConst(width=8, value=15, base="hex")` emits `8'h0F`, not `8'hF`. Decimal MUST NOT be padded (e.g., `8'd15`, not `8'd015`).

### Naming

- **FR-12.** The emitted SV constant name MUST be the user's Python variable name verbatim — case preserved, no `LP_` prefix added by the generator. If the user names their Python variable `LP_ETHERTYPE_VLAN`, the SV emits `LP_ETHERTYPE_VLAN`; if they name it `Foo`, the SV emits `Foo`. This matches existing `Const()` behavior.

### Cross-module behavior

- **FR-13.** A `VecConst` declared in module A MAY be referenced from module B's DSL via cross-module import (the existing cross-module mechanism for `Const`). In SV, this MUST produce the appropriate `import a_pkg::*;` line on module B's synth package, exactly mirroring `Const`'s cross-module rules.

### Constitution amendment

- **FR-14.** As part of this spec's implementation, Constitution §Constraints item 5 MUST be amended to:
  > "**Const widths restricted to 32/64 bits.** The legacy `Const()` parameter primitive accepts width 32, 64, or unspecified (default int). The newer `VecConst()` primitive accepts arbitrary positive widths from 1 through 64 inclusive (see FR-5). Both are validated by the validation layer; widths outside their respective allowed ranges are rejected."
- **FR-15.** No other Constitution clause is touched.

### Cross-backend emission policy

- **FR-16.** **C++ backend:** a `VecConst` declaration emits one `constexpr std::uint{8|16|32|64}_t <NAME> = <literal>;` line in the generated C++ header, where the unsigned-int width rounds up to the smallest type fitting the VecConst's width, and `<literal>` honors the declared `base` (hex → `0x...` uppercase + zero-padded to `(width+3)//4` digits; dec → decimal; bin → `0b...` zero-padded to `width` digits). Suffix follows existing `Const` style: none for ≤16 bits, `U` for 32-bit, `ULL` for 64-bit.
- **FR-17.** **Python backend:** a `VecConst` declaration emits one `<NAME> = <literal>` line in the generated Python `_types.py`, with the same base-honoring literal rules as FR-16 (no suffix needed in Python).
- **(Note: FR-16 and FR-17 were rewritten post-016 release at user request; original v1 scope made both backends no-op. See git history.)**
- **FR-18.** **Manifest:** for v1, `VecConst` declarations MUST appear in the JSON manifest under a new `vec_constants` array (sibling to the existing `constants` array), with at minimum the fields `name`, `width`, `value`, `base`, and `source` (file:line). This is the minimum needed so cross-module reference validation and downstream tools can see them. The legacy `constants` array schema MUST remain byte-identical to pre-change — no `kind` discriminator is added to legacy entries.

## Non-Functional Requirements

- **NFR-1.** No new runtime dependency (Constitution: Jinja2 only).
- **NFR-2.** Deterministic output preserved: generated SV is byte-for-byte reproducible given the same DSL input.
- **NFR-3.** basedpyright strict mode passes with zero new errors on all modified Python files.
- **NFR-4.** No measurable performance regression in `piketype gen` end-to-end runtime on a fixture-typical project.
- **NFR-5.** Existing `Const()` behavior — including validation messages, SV emission shape, and the 32/64 width restriction — is BYTE-IDENTICAL to pre-change. No `Const`-using fixture or golden may need updating.

## Acceptance Criteria

- **AC-1.** `from piketype.dsl import VecConst` succeeds.
- **AC-2.** `VecConst(width=16, value=0x8100, base="hex")` declared as Python module-level `LP_ETHERTYPE_VLAN`, when `piketype gen` is run, emits exactly:
  ```
    localparam logic [15:0] LP_ETHERTYPE_VLAN = 16'h8100;
  ```
  in the synth-package SV file, and no other VecConst-related lines.
- **AC-3.** `A = Const(5); B = VecConst(width=8, value=A * 3, base="dec")` emits:
  ```
    localparam int A = 32'sd5;
    localparam logic [7:0] B = 8'd15;
  ```
  (Existing `Const()` emission for `A` unchanged; `B` emits the resolved 15, not the symbolic expression.)
- **AC-4.** `VecConst(width=8, value=300, base="dec")` raises `ValidationError` with a message including the literal value `300`, the width `8`, and the upper bound `255` (or `2**8 - 1`).
- **AC-5.** `VecConst(width=8, value=-1, base="dec")` raises `ValidationError` with a message naming negative-value rejection.
- **AC-6.** `VecConst(width=0, value=0, base="dec")` raises `ValidationError`. Same for negative width.
- **AC-7.** `VecConst(width=65, value=0, base="hex")` raises `ValidationError` (width upper bound).
- **AC-8.** `VecConst(width=8, value=0, base="oct")` raises `ValidationError` (unsupported base).
- **AC-9.** `VecConst(width=8, value=15, base="hex")` emits `8'h0F` (zero-padded). `VecConst(width=8, value=15, base="bin")` emits `8'b00001111`. `VecConst(width=8, value=15, base="dec")` emits `8'd15` (no padding).
- **AC-10.** Hex output uppercase: `VecConst(width=16, value=0xab, base="hex")` emits `16'h00AB`.
- **AC-11.** Cross-module reference: a `VecConst` named `X` defined in module `a.py` and used from `b.py` produces an `import a_pkg::*;` line on `b_pkg.sv`'s header (matching the existing `Const` cross-module reference rule).
- **AC-12.** `Const(width=32, signed=True, value=3)` continues to emit `localparam int FOO = 32'sd3;` byte-for-byte (NFR-5 regression sentinel).
- **AC-13.** Validation message clarity: each AC-4..AC-8 error message names the offending field by its source location (file + line) per existing `SourceInfo` capture.
- **AC-14.** A new fixture under `tests/fixtures/vec_const_basic/` and a golden under `tests/goldens/gen/vec_const_basic/` exercise AC-2, AC-3, AC-9, AC-10. A negative-test file (`tests/test_vec_const_validation.py` or addition to an existing validation test file) covers AC-4 through AC-8.
- **AC-15.** basedpyright strict reports zero errors on all changed Python files.
- **AC-16.** All pre-existing tests pass unchanged (NFR-5 transitive).

## Out of Scope

- **OOS-1.** Signed `VecConst`. The user did not request a `signed=` flag and the request showed only positive values. Two's-complement representation of negative values is OUT for v1; raise `ValidationError` on negative resolved values.
- **~~OOS-3.~~** ~~VecConst is NOT a ConstOperand.~~ **Lifted post-016**: VecConst IS a ConstOperand and supports the full arithmetic surface (`+`, `-`, `*`, `//`, `%`, `&`, `|`, `^`, `<<`, `>>`, unary `+`/`-`/`~`). Eager resolution at `__init__` makes `VecConst.value` available to `_eval_expr`.
- **OOS-2.** Width >64. Both `Const` and existing scalar widths cap at 64 for signed; we mirror this. Wider vector constants are rare in practice and not requested.
- **OOS-3.** Bases other than `hex`/`dec`/`bin`. SV also has `'o` (octal) but it is rare; not requested.
- **OOS-4.** Don't-care or X/Z digits in the literal (e.g., `8'h?F`, `8'b1x_x_`). Out for v1.
- **OOS-5.** Underscore-separated digit grouping (e.g., `16'h81_00`). Not requested; could be added later as a render-style option.
- **OOS-6.** A `format=` string-template emission mode. Not requested.
- **OOS-7.** Auto-deriving `width` from value (e.g., `VecConst(value=0xFF, base="hex")` → 8 bits). Not requested; user always specifies width.
- **OOS-8.** Modifying `Const()`'s width restriction or its emission shape. The constitution amendment scopes the 32/64 restriction to `Const`, not the other way around.
- **OOS-9.** ~~Cross-language emission of `VecConst` to C++ and Python.~~ **No longer out of scope** — implemented in a post-016 follow-up edit per FR-16 / FR-17 (rewritten).

## Open Questions

(All open questions resolved in Clarification iteration 1. See `clarifications.md`.)

## Risks

- **R-1.** Constitution amendment breaks lint / cross-references in docs that quote Constraint 5. Mitigation: scan `docs/` and tests for the literal phrase "32/64 bits" and update the small number of references at amendment time.
- **R-2.** Naming-clash risk: a user happens to declare both `Const` and `VecConst` with the same Python variable name across modules — already covered by the cross-module unique-basename rule (Constitution §Constraints item 4); no new risk introduced here.
- **R-3.** Renderer drift: if the SV literal renderer for `VecConst` is implemented separately from `Const`'s renderer, the two could diverge in style (e.g., one zero-pads, one doesn't; one uppercases, one doesn't). Mitigation: place the new renderer adjacent to `_render_sv_const` and reuse the helper for the `<width>'<base><digits>` shape where feasible.

## References

- `src/piketype/dsl/const.py:122` — existing `Const` class.
- `src/piketype/backends/sv/view.py:312` — `_render_sv_const` (existing const SV renderer; will be reused/extended or paralleled).
- `src/piketype/backends/sv/templates/module_synth.j2:11` — synth-package localparam emission point.
- Project Constitution §Constraints item 5 — to be amended (FR-14).

## Changelog

- [Spec iter2] FR-7: tightened error-message contract to require the formula `2**N - 1` substring (gauge iter1 WARNING).
- [Spec iter2] FR-16, FR-17, FR-18 added: C++ and Python emit no VecConst output for v1; manifest gets a new `vec_constants` array. Resolves gauge iter1 BLOCKING (Q-4 left Principle 1 ambiguous). OOS-9 rewritten accordingly.
- [Spec iter2] Open Questions Q-4, Q-5, Q-6 removed (resolved by FR-16/17/18). Q-3 (width >64) renumbered to Q-4 to keep the lifting-discussion alive for clarification.
- [Clarification iter1] FR-5, FR-8, FR-12, FR-18, OOS-1, OOS-2: removed parenthetical Q-references (Q-1, Q-2, Q-3, Q-4 all resolved this round). FR-18 reinforced: legacy `constants` array stays byte-identical (no `kind` discriminator added). No FR/NFR/AC semantics changed.
- [Clarification iter1] Open Questions section emptied. All four user answers (reject signed / verbatim naming / Option A separate `vec_constants` array / keep width at 64) confirmed existing FR defaults.
- [Post-016 follow-up] FR-16, FR-17, OOS-9: rewritten/updated. C++ and Python backends now emit `constexpr std::uintN_t LP_X = <literal>;` and `LP_X = <literal>` respectively, honoring the user's `base` choice. Original v1 no-op behavior was lifted at user's direct request after spec 016 retrospect-complete.
- [Post-016 follow-up #2] FR-2 / OOS-3: signature gains default `base="dec"` (so `VecConst(5, 3)` is valid); OOS-3 lifted — VecConst is a ConstOperand. Width and value resolve eagerly at `__init__` (mirroring `Const`); validation moved from freeze-time to construction-time. Arithmetic operators added. Memory `project_vec_const_value_expr_dep_gap.md` becomes partially obsolete (eager resolution still produces literal output, so the dep-edge gap is now structural rather than a workflow risk).
