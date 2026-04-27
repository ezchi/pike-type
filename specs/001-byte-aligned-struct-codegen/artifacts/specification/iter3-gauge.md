# Gauge Review — Iteration 3

**Reviewer:** codex (gpt-5.5)

## BLOCKING

- **FR-13 is inconsistent with the current generator.** The spec says reject >64 scalars only "when the C++ backend is enabled" and preserve SV/Python behavior, but `run_gen()` always emits SV, Python, and C++ with no backend selector. Either reject >64 scalars for the current pipeline, or add backend selection to scope.

- **Scalar `from_bytes()` masking is still backend-ambiguous.** FR-6 specifies scalar masking under the SV verification package, while C++ scalar FR-7 only specifies `to_bytes()`, and Python FR-9 only covers structs. AC-15 does not say SV/C++/Python. The spec must explicitly require C++ and Python scalar wrappers to ignore upper padding bits too, including signed decode behavior.

## WARNING

- **Existing SV helper APIs are not specified.** The repo already emits `to_slv()` / `from_slv()` helper methods. After adding padding fields, those methods must zero padding on output and ignore/zero padding on input, or be explicitly out of scope.

- **FR-12 and FR-13 lack direct acceptance coverage.** Add tests for signed non-byte-width scalars, negative signed serialization, and the >64 C++ validation error.

- **The `baz -> baz` base-name example conflicts with current validation.** Current validation requires every type name to end in `_t`; either remove the example or state that the existing `_t` rule remains authoritative.

## NOTE

Iteration 2's nested-struct padding, `pack_bar()` value, scope, C++ scalar alias mapping, `bit`/`signed` examples, and nested acceptance coverage are materially improved.

VERDICT: REVISE
