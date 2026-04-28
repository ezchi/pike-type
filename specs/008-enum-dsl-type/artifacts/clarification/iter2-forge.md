# Clarifications — Spec 008: Enum() DSL Type

## CLR-1: Auto-fill numbering uses sequential increment, not smallest-unused [SPEC UPDATE]

**Issue**: FR-6 specifies auto-fill as "the smallest non-negative integer not yet used by any prior enumerator." This contradicts the v1 product spec which says "default numbering starts at `0` and increments by `1`" — the standard C/SystemVerilog convention.

**Resolution**: Auto-fill assigns `previous_value + 1` where `previous_value` is the resolved value of the immediately preceding enumerator (explicit or auto-filled). The first auto-filled value with no predecessor is `0`. This matches C, C++, and SystemVerilog enum behavior.

**Example change**:
- Before: `add_value("A", 0).add_value("B", 2).add_value("C").add_value("D")` → `A=0, B=2, C=1, D=3`
- After: `add_value("A", 0).add_value("B", 2).add_value("C").add_value("D")` → `A=0, B=2, C=3, D=4`

**Rationale**: Sequential increment is universally expected by hardware engineers. The "smallest unused" algorithm is surprising and has no precedent in any hardware description language.

## CLR-2: Auto-fill can produce duplicate values — validation catches this [NO SPEC CHANGE]

**Issue**: With sequential increment, a user could write `add_value("A", 3).add_value("B").add_value("C", 1).add_value("D")` yielding `A=3, B=4, C=1, D=2` — no duplicates. But `add_value("A", 2).add_value("B").add_value("C", 3)` yields `A=2, B=3, C=3` — a duplicate. The DSL `add_value()` does not check for value collisions at call time (only name collisions). FR-15 validation catches duplicate resolved values after freeze.

**Resolution**: This is already correctly handled: `add_value()` validates names eagerly (FR-3, FR-4) and value sign eagerly (FR-5), but value uniqueness is checked by FR-15 validation after freeze resolves all auto-fills. No spec change needed beyond the FR-6 fix, but this interaction should be explicit.

## CLR-3: AC-3 wording must match new auto-fill semantics [SPEC UPDATE]

**Issue**: AC-3 says "assigns the smallest unused non-negative integer" which must be updated to match the corrected FR-6.

**Resolution**: Update AC-3 to say "assigns the previous enumerator's value plus one."

## CLR-4: FR-32 test example must match new auto-fill semantics [SPEC UPDATE]

**Issue**: FR-32 says "Auto-fill gap behavior: explicit `0, 2` then two auto-fills → `0, 2, 1, 3`." This is wrong under sequential increment.

**Resolution**: Update to: "Auto-fill sequential behavior: explicit `0, 2` then two auto-fills → `0, 2, 3, 4`."

## CLR-5: No [NEEDS CLARIFICATION] markers remain [NO SPEC CHANGE]

The spec has no unresolved `[NEEDS CLARIFICATION]` markers. The "Open Questions" section confirms "None."

## CLR-6: No contradictions between remaining requirements [NO SPEC CHANGE]

With the FR-6 fix applied, all requirements are internally consistent. The v1 product spec's "starts at 0 and increments by 1" is now faithfully represented.
