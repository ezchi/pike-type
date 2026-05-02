# Spec.md Diff — Clarification Iteration 1

Three sections of `spec.md` were modified. Below: before → after for each.

## 1. FR-3.1 — Affected goldens list (driven by C-3)

### BEFORE
```
- **FR-3.1.** Every existing golden that contains an enum's `pack_<base>`
  function MUST be regenerated as part of the same commit that ships the
  template change, so the repository remains byte-parity verifiable on
  every commit. Affected goldens (enumerated from the current
  `tests/goldens/gen/` tree, by inspection of which fixtures define enums):
  - `tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv`
    (defines `color_t`, `cmd_t`, `flag_t`, `big_t`)
  - `tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv`
  - `tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv`
  - Any other golden that, on inspection, emits a `pack_<enum>` body
    containing `return logic'(a);`. The regeneration mechanism (walk
    fixtures and run `piketype gen`, then tree-replace) is the
    project-standard pattern; it picks up every affected file
    automatically.
```

### AFTER
```
- **FR-3.1.** Every existing golden that contains an enum's `pack_<base>`
  function MUST be regenerated as part of the same commit that ships the
  template change, so the repository remains byte-parity verifiable on
  every commit. The complete enumerated list, derived from
  `grep -rn "return logic'(a);" tests/goldens/`, is exactly five fixtures:
  - `tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv`
    (defines `color_t`, `cmd_t`, `flag_t`, `big_t` — 4 pack bodies)
  - `tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv`
    (1 pack body)
  - `tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv`
    (1 pack body)
  - `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv`
    (defines `cmd_t` — 1 pack body)
  - `tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv`
    (namespace variant of the same fixture — 1 pack body)

  Total of 8 enum-pack-body lines change across these 5 files. The
  catch-all rule still applies: if any unenumerated golden emits a
  `return logic'(a);` line after regeneration, that is a regression
  signal. The regeneration mechanism (walk fixtures and run
  `piketype gen`, then tree-replace) is the project-standard pattern; it
  picks up every affected file automatically.
```

### Why
Grep over `tests/goldens/` for the buggy line returns 8 matches across
5 fixtures, not 3. Two fixtures (`cross_module_type_refs` and the
`_namespace_proj` namespace-flag variant) were missing from the
iteration-1 enumeration. Driven by C-3 in `clarifications.md`.

---

## 2. AC-2 — Expected-match list and total count (driven by C-4)

### BEFORE
```
- **AC-2.** A grep of the regenerated tree returns one match for
  `return LP_<UPPER>_WIDTH'(a);` per enum defined across all fixtures.
  The expected match list (from the affected fixtures enumerated in
  FR-3.1) is at minimum:
  - `return LP_COLOR_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_color`
  - `return LP_CMD_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_cmd`
  - `return LP_FLAG_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_flag` (1-bit case)
  - `return LP_BIG_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_big`
  - One per enum in `struct_enum_member` and `keyword_enum_value_while_passes`
  Exact match counts are confirmed by re-running `piketype gen` on each
  fixture and diffing against the regenerated goldens.
```

### AFTER
```
- **AC-2.** A grep of the regenerated tree returns exactly **8** matches
  for the pattern `return LP_[A-Z_]*_WIDTH'(a);` across the 5 fixtures
  enumerated in FR-3.1, distributed as follows:
  - `return LP_COLOR_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_color`
  - `return LP_CMD_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_cmd`
  - `return LP_FLAG_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_flag` (1-bit case)
  - `return LP_BIG_WIDTH'(a);` in `enum_basic/.../defs_pkg.sv` body of `pack_big`
  - One match in `struct_enum_member/.../types_pkg.sv` (the enum defined
    by that fixture)
  - One match in `keyword_enum_value_while_passes/.../types_pkg.sv`
    (the enum defined by that fixture)
  - `return LP_CMD_WIDTH'(a);` in `cross_module_type_refs/.../foo_pkg.sv`
    body of `pack_cmd`
  - `return LP_CMD_WIDTH'(a);` in
    `cross_module_type_refs_namespace_proj/.../foo_pkg.sv` body of
    `pack_cmd`
  Verified by:
  ```
  grep -r "return LP_[A-Z_]*_WIDTH'(a);" tests/goldens/gen/ | wc -l
  # expected: 8
  ```
  And `grep -r "return logic'(a);" tests/goldens/gen/` returns zero
  matches (per AC-1).
```

### Why
The previous AC-2 used hedging language ("at minimum", "one per enum")
that left the verifier interpreting how many matches to expect. The
clarified version pins exactly 8, names every fixture, and gives a
single concrete grep command. Driven by C-4 in `clarifications.md`.

---

## 3. Open Questions — resolved (driven by C-1 + C-2)

### BEFORE
Two `[NEEDS CLARIFICATION]` blocks for OQ-1 (SV testbench harness
question) and OQ-2 (grep for sibling `logic'(...)` instances).

### AFTER
```
## Open Questions

(All open questions raised in iteration 1 are resolved in
`clarifications.md`:
OQ-1 → keep SV-execution harness out of scope; AC-4 hand-inspection +
golden diff path stands. Resolved by C-1.
OQ-2 → grep confirms the buggy `logic'(...)` cast appears only at
`_macros.j2:98`; no sibling instances elsewhere in templates or Python.
Resolved by C-2.
No outstanding open questions remain.)
```

### Why
- OQ-1: SV-execution harness is unjustified scope expansion for a
  one-line template fix; existing golden-diff path is sufficient and
  matches the project's primary correctness mechanism.
- OQ-2: Grep proves the bug is isolated; no sibling sites exist.

Both `[NEEDS CLARIFICATION]` markers removed. C-1 and C-2 in
`clarifications.md` carry the resolution rationale.

---

## 4. Changelog section appended

A `## Changelog` section was added at the bottom of `spec.md` with
three entries documenting the FR-3.1, AC-2, and Open Questions changes.

---

## Sections NOT Modified

The following sections of `spec.md` were left untouched:

- Overview
- User Stories (US-1, US-2, US-3)
- FR-1 series (codegen change)
- FR-2 series (scope boundary)
- FR-3.2 and FR-3.3
- All Non-Functional Requirements (NFR-1 through NFR-6)
- AC-1, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10
- Out of Scope (entire section)
