# Gauge Review — Iteration 2

**Reviewer:** codex (gpt-5.5)

## BLOCKING

- **Nested struct padding double-counts.** A struct-typed field's `inner_t` already includes its own padding in the packed typedef, but FR-1/FR-3 require emitting another `<field>_pad` before it. That double-counts padding.

- **The worked `pack_bar()` value is wrong.** For `flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0`, the compact bits equal `19'h7_FFF4`, not `19'h1_FFFA`. AC-3 and AC-4 therefore specify bad golden behavior.

- **Scope is internally inconsistent.** FR-1, FR-2, and FR-11 require changes in freeze, IR, and validation, but Out of Scope says changes are limited to SV/C++/Python emitters.

- **"Scalar widths > 64 bits are rejected by existing validation" is false.** Current validation only checks positive scalar width. The spec must either add new validation or define >64-bit scalar behavior.

## WARNING

- Scalar `from_bytes()` padding behavior is not specified. Padding bits for 13-bit or 37-bit scalars are not clearly handled.

- C++ "scalar fields use native types" is ambiguous for fields referencing named scalar aliases. State whether a `foo_t` field becomes `foo_ct`, `std::uint16_t`, or a generated C++ alias.

- The scalar typedef example hardcodes `logic`, while the next requirement says preserve `bit` vs `logic`. Use examples for both.

- The nested-struct acceptance criterion is still too weak. Needs exact expected nested bytes.

## NOTE

- "any `_t` suffix stripped" should say "one terminal `_t` suffix" to avoid edge-case ambiguity like `foo_t_t`.

VERDICT: REVISE
