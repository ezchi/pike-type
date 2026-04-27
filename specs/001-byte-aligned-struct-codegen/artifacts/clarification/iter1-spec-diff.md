# Spec Diff — Iteration 1

## FR-5: unpack semantics (before → after)

**Before:**
```
**unpack semantics:** Input vector width = `WIDTH`. Result is initialized to `'0` to zero-fill all padding. Fields are extracted LSB-first with bit-slice indexing. For struct-typed fields, recursively call `unpack_<inner_base_name>`.
```

**After:**
```
**unpack semantics:** Input vector width = `WIDTH`. Result is initialized to `'0`. Fields are extracted LSB-first with bit-slice indexing. For struct-typed fields, recursively call `unpack_<inner_base_name>`. For **signed scalar fields with padding_bits > 0**, the corresponding `_pad` field SHALL be set to `{P{field[W-1]}}` (replicate the sign bit), where `P` = padding_bits and `W` = field data width. For **unsigned scalar fields**, padding remains zero.
```

## FR-6: to_bytes padding (before → after)

**Before:**
```
Padding bits are always serialized as zero — `to_bytes()` does NOT read the `_pad` member values from the struct typedef; it computes the byte array from field data values and fills padding positions with zero.
```

**After:**
```
For **unsigned scalar fields**, padding bits are serialized as zero. For **signed scalar fields**, padding bits are sign-extended (filled with the field's sign bit). `to_bytes()` does NOT read the `_pad` member values from the struct typedef; it computes the byte array from field data values, applying the appropriate padding fill (zero for unsigned, sign-extended for signed).
```

## FR-10a: to_slv padding (before → after)

**Before:**
```
- `to_slv()` SHALL return the padded struct value with all `_pad` fields set to zero.
```

**After:**
```
- `to_slv()` SHALL return the padded struct value with `_pad` fields set appropriately: zero for unsigned scalar fields, sign-extended (replicated sign bit) for signed scalar fields.
```

## FR-12: Signed Scalars as Struct Members (full rewrite)

**Before:** Brief bullet list stating "No sign extension occurs during pack/unpack" and "to_bytes serialization same as unsigned."

**After:** Detailed section specifying:
- `pack`: raw bit pattern (unchanged)
- `unpack`: sign-extended `_pad` for signed fields
- `to_bytes`: sign-extended padding for signed fields
- `from_bytes`: unchanged (extracts data bits, ignores padding)
- Includes worked example for 4-bit signed field

## AC-16 (before → after)

**Before:** `to_bytes()` = `{0x1F}` (upper 3 padding bits zero)

**After:** `to_bytes()` = `{0xFF}` (upper 3 padding bits sign-extended to 1). Added positive example: +5 → `{0x05}`.

## AC-19 (before → after)

**Before:** "all padding bits = 0"

**After:** "unsigned padding bits = 0, signed padding bits = sign-extended"
