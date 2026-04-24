# Gauge Review — Iteration 4

**Reviewer:** codex (gpt-5.5)

## BLOCKING

- **to_slv/from_slv still exist** in `src/typist/backends/sv/emitter.py`. The spec must either require their removal or define padded-layout semantics for them.

- **Inline scalar >64 bits** — `Logic(65)` as anonymous inline field has no type name. FR-13 validation error uses `<type_name>` but inline fields have none. Add validation and diagnostics for inline scalar field width.

## WARNING

- SV `to_bytes()` says "serializes padding" — must explicitly state padding bits are always zero (not reading _pad field values).
- NFR-2 mandates direct code generation — needs explicit exception language vs constitution principle 5.

## NOTE

- Iteration 3 blockers (FR-13 unconditional, scalar from_bytes masking, baz example, FR-12/FR-13 ACs) are resolved.

VERDICT: REVISE
