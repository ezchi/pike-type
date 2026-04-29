# Spec Diff — Clarification Iteration 1

## FR-6 (Auto-fill numbering)

**Before:**
> Auto-fill numbering: when `value` is `None`, the enumerator receives the smallest non-negative integer not yet used by any prior enumerator (explicit or auto-filled) in declaration order. The first auto-filled value with no prior explicit values is `0`. Example: `add_value("A", 0).add_value("B", 2).add_value("C").add_value("D")` yields `A=0, B=2, C=1, D=3`.

**After:**
> Auto-fill numbering: when `value` is `None`, the enumerator receives the previous enumerator's resolved value plus one. If there is no preceding enumerator, the value is `0`. This matches the standard C/C++/SystemVerilog convention. Example: `add_value("A", 0).add_value("B", 2).add_value("C").add_value("D")` yields `A=0, B=2, C=3, D=4`.

## AC-3 (Auto-fill acceptance criterion)

**Before:**
> Auto-fill numbering assigns the smallest unused non-negative integer, correctly handling gaps from explicit values.

**After:**
> Auto-fill numbering assigns the previous enumerator's value plus one (or `0` for the first enumerator), matching C/SV convention.

## FR-32 (Test example)

**Before:**
> Auto-fill gap behavior: explicit `0, 2` then two auto-fills → `0, 2, 1, 3`.

**After:**
> Auto-fill sequential behavior: explicit `0, 2` then two auto-fills → `0, 2, 3, 4`.
