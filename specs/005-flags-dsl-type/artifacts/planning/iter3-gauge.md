# Gauge Review — Plan Iteration 3

- **WARNING** — Step 11 command should be `uv run typist gen <path>`, not `uv run python3 -m typist gen`.
- **NOTE** — FlagsIR.alignment_bits default 0 weakens IR invariant slightly but freeze always computes it.
- **NOTE** — Add direct DSL test for `Flags().add_flag(...).width == 3` (AC-1).

VERDICT: APPROVE
