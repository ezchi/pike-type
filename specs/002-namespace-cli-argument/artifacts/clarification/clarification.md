# Clarification — Spec 002: `--namespace` CLI Argument

## Status: No clarifications needed

The specification is self-contained. All functional requirements map directly to
existing code locations with clear modification points:

| FR | Code Location | Modification |
|----|--------------|--------------|
| FR-1 | `src/typist/cli.py:20-22` | Add `--namespace` to `gen` subparser only |
| FR-2 | New module: `src/typist/validate/namespace.py` | Validation function |
| FR-3 | `src/typist/backends/cpp/emitter.py:48` | Conditional namespace derivation |
| FR-4 | `src/typist/backends/cpp/emitter.py:47` | Conditional guard derivation |
| FR-5 | No change needed | Runtime emitter untouched |
| FR-6 | `src/typist/commands/gen.py:59` | Pass namespace to `emit_cpp` |
| FR-7 | `src/typist/backends/cpp/emitter.py:29-41` | Pass namespace through per-module loop |
| FR-8 | `src/typist/commands/gen.py` | Post-discovery basename check |

## Resolved Ambiguities (from spec iterations)

These were resolved during the Forge-Gauge specification loop:

1. **C++ keyword validation** — FR-2 rule 3 requires a keyword set.
2. **Reserved identifiers** — FR-2 rules 4-6 cover `_`, `__`, trailing `_`.
3. **Include guard safety** — FR-2 composition check validates the prefix only.
4. **Duplicate basenames** — FR-8 rejects post-discovery.
5. **Runtime headers** — FR-5 explicitly excludes them.
6. **Basename validation** — Explicitly out of scope with rationale.
