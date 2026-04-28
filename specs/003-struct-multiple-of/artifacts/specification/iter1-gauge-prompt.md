# Gauge Review: Specification 003 — Struct `multiple_of(N)` Alignment

You are a strict technical reviewer (the "Gauge"). Your job is to review the specification below for completeness, clarity, testability, consistency, and feasibility.

## Project Constitution (highest authority)

Read the file at: `.steel/constitution.md`

Key constraints from the constitution that apply to this spec:
1. **Packed types only** — all SV types must be `typedef struct packed`.
2. **Frozen dataclasses** for IR nodes.
3. **Golden-file integration tests** are the primary correctness mechanism.
4. **Template-first generation** — backends use Jinja2 templates for generated output.
5. **Adding a new feature** follows the 7-step process in the constitution (DSL → IR → freeze → validate → backends → fixture → test).
6. **basedpyright strict mode** must pass with zero errors.

## Specification to Review

Read the file at: `specs/003-struct-multiple-of/spec.md`

## Current Implementation Context

- `src/typist/dsl/struct.py` — The Struct DSL class. Currently has `add_member()` but no `multiple_of()`.
- `src/typist/ir/nodes.py` — IR nodes. `StructIR` currently has `name`, `source`, `fields` (no alignment field).
- `src/typist/dsl/freeze.py` — Freeze logic. Computes per-field `padding_bits` during freeze.
- Backends are in `src/typist/backends/{sv,cpp,py}/emitter.py` — they use Jinja2 templates.
- Per-field padding works by: each scalar field is padded to next byte boundary. Padding bits are MSB, unsigned for unsigned fields, sign-extended for signed fields.

## Review Checklist

Please evaluate:

1. **Completeness**: Are all layers of the pipeline covered (DSL → IR → freeze → validate → backends → tests)?
2. **Clarity**: Are requirements unambiguous? Could an implementer build this without guessing?
3. **Testability**: Are acceptance criteria concrete and measurable?
4. **Consistency**: Does the spec align with the project constitution and existing patterns?
5. **Feasibility**: Can this be implemented with the current architecture?

## Issues Format

List each issue as:

```
### ISSUE-N: <title>
**Severity:** BLOCKING / WARNING / NOTE
**Section:** <which section>
**Description:** <what's wrong and how to fix it>
```

## Verdict

End your review with exactly one of:
- `VERDICT: APPROVE`
- `VERDICT: REVISE`

Only use REVISE if there are BLOCKING issues.
