# Gauge Review — Plan Iteration 2

- **BLOCKING** — SV test helper from_bytes still wrong: casting bytes back to struct doesn't auto-zero _align_pad. Must explicitly mask/zero padding bits.
- **WARNING** — Runtime test planning doesn't specify explicit byte vectors for all 5 fixture types per AC-4/AC-11.

VERDICT: REVISE
