# Gauge Review — Clarification Iteration 1

**Provider:** codex (gpt-5.5)

## Issues

1. **BLOCKING — Struct `WIDTH` / SV `LP_*_WIDTH` semantics not explicit.** Clarify that struct WIDTH uses data bits only (Flags contributes flag count), while BYTE_COUNT uses byte-aligned field width (Flags contributes byte-aligned size).

2. **BLOCKING — Dependency ordering contradictory.** FR-5 says "must appear before" but also "no topological sort." Clarify.

3. **WARNING — Cross-module rejection lacks AC.** Add AC for rejecting cross-module Flags member.

4. **WARNING — Manifest claim unsupported.** Clarify manifest handling.

VERDICT: REVISE
