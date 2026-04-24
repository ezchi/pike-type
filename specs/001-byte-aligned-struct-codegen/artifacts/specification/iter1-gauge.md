# Gauge Review — Iteration 1

**Reviewer:** codex (gpt-5.5)

## BLOCKING

- **Nested struct sizing is contradictory.** FR-1 says struct fields use inner `BYTE_COUNT * 8`; FR-2 says `BYTE_COUNT` is derived from `ceil(field.resolved_width / 8)`. Those produce different answers for nested structs with internal padding. OQ-2 leaves this unresolved. Define data width, storage width, field byte count, and padding bits explicitly.

- **Generated name rules are underspecified.** The original requires `foo_t` -> `LP_FOO_WIDTH` and `pack_foo`, but FR-4 and FR-5 say `LP_<UPPER_NAME>` and `pack_<name>`. If `<name>` is the actual type name, implementations will emit `LP_FOO_T_WIDTH` and `pack_foo_t`, which contradicts the requirement.

- **Signed struct fields are both included and excluded.** FR-7 specifies signed scalar mapping, but Out of Scope says signed scalar struct members are out of scope. Existing DSL supports signed scalars. Either specify signed field packing/serialization or require validation to reject them.

- **Padding field name collisions are not handled.** FR-3 mandates `<field_name>_pad`, but a legal user field can already be named that. The spec must require collision validation or a deterministic escaping scheme.

- **`from_bytes()` padding behavior is undefined.** FR-6, FR-8, and FR-9 do not say whether nonzero padding bits are rejected, ignored, preserved, or zeroed. That is not testable.

- **The spec still contains open questions.** Cannot remain in an implementation-ready specification, especially OQ-2.

## WARNING

- FR-1 says `Struct().add_member()` computes padding. Widths are resolved during freeze, so the safer requirement is: `add_member()` records fields; freeze computes padding into frozen IR.

- FR-4 hardcodes scalar SV typedefs as `logic` and does not mention preserving `bit` vs `logic` or `signed`.

- The byte layout algorithm is not concrete enough. It should define per-field padded chunks, scalar signed two's-complement handling, nested struct byte expansion, and scalar widths greater than 64 bits or explicitly reject unsupported cases.

- Acceptance criteria are too weak. Add exact expected byte vectors for the 1/13/4/1 example, nested struct vectors, `unpack(pack(s))` data equivalence, and `from_bytes()` padding tests.

- NFR-2 says templates "should" be used. If template-first is a governing principle for this work, make it a SHALL or explicitly grant an exception.

## NOTE

- OQ-3 appears wrong: the original document shown in the review prompt already uses `LP_BAR_BYTE_COUNT`.

VERDICT: REVISE
