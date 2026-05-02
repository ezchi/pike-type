# Clarifications — 014 Enum Pack Width Cast

This document resolves the open questions and tightens implicit assumptions in
`spec.md` before the planning stage.

## C-1. OQ-1: SystemVerilog testbench harness for AC-4 — REJECT broadening scope. [NO SPEC CHANGE]

**Question.** Should AC-4 mandate adding a SystemVerilog testbench harness
that compiles and executes `pack_<enum>` calls, rather than accepting
hand-inspection plus golden diff?

**Resolution.** Keep an SV-execution harness out of scope. The bug is a
single-line template typo with a deterministic and trivially auditable
fix. AC-4 already permits hand-inspection plus golden diff as the evidence
path, and the resulting golden lines (`return LP_<UPPER>_WIDTH'(a);`) make
correctness obvious by inspection: the cast type matches the function
return type, so the output is the enum's bit pattern at the declared
width. Adding a Verilator-driven SV simulation harness would (a) require
new project infrastructure that does not exist today, (b) widen the
feature far beyond a one-line bug fix, and (c) is unjustified by
constitution principle 4 ("Correctness over convenience") because the
golden-file mechanism *is* this project's primary correctness gate.

**Spec impact.** The Open Questions section already marks OQ-1 as pending
clarification. Resolved here as out-of-scope; remove the
`[NEEDS CLARIFICATION]` marker and replace OQ-1 with a resolved entry.

## C-2. OQ-2: Grep for other `logic'(...)` instances — confirmed isolated to enum pack site. [SPEC UPDATE]

**Question.** Is there any other generated SystemVerilog site (outside
`synth_pack_fn`) that uses the `logic'(...)` single-bit cast inside a
multi-bit return / assignment context?

**Resolution.** Grep performed during clarification:

```
grep -rn "logic'(" src/piketype/backends/sv/templates/
src/piketype/backends/sv/templates/_macros.j2:98:    return logic'(a);
```

Only one match — the buggy enum-pack site under fix. No sibling
instances elsewhere in the templates. Confirmed by also grepping
`src/piketype/`:

```
grep -rn "logic'(" src/piketype/ --include="*.py"
(no matches)
```

No Python emitter builds an inline `logic'(...)` string either.

**Spec impact.** Drop the `[NEEDS CLARIFICATION]` marker on OQ-2; replace
with a resolved-by-grep entry.

## C-3. FR-3.1 affected-goldens enumeration is incomplete — add 2 fixtures. [SPEC UPDATE]

**Issue.** FR-3.1 lists three affected goldens (`enum_basic`,
`struct_enum_member`, `keyword_enum_value_while_passes`). A grep over
`tests/goldens/` for the buggy line `return logic'(a);` returns 8 hits
across **5** fixtures, not 3:

```
grep -rn "logic'(a);" tests/goldens/
tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv:46:    return logic'(a);
tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv:46:    return logic'(a);
tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv:13:    return logic'(a);
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv:13:    return logic'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:13:    return logic'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:26:    return logic'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:39:    return logic'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:52:    return logic'(a);
```

The two missing fixtures are `cross_module_type_refs` (defines `cmd_t` enum
in `foo_pkg.sv`) and `cross_module_type_refs_namespace_proj` (the namespace
flag variant of the same fixture). Both contain a single enum and will
therefore see exactly one pack-body line change apiece.

**Resolution.** Update FR-3.1 to enumerate all five affected goldens.
This is a hard requirement, not a "list-of-examples" — the regeneration
must produce byte-parity across the whole tree.

**Spec impact.** Replace the 3-fixture list in FR-3.1 with the full
5-fixture list. The "Any other golden that, on inspection, emits a
buggy line" catch-all clause stays as belt-and-suspenders.

## C-4. AC-2 expected-match list missing cross_module fixtures. [SPEC UPDATE]

**Issue.** AC-2 enumerates expected matches of
`return LP_<UPPER>_WIDTH'(a);` per enum, but the list only covers the
four enums in `enum_basic` and gestures at "one per enum in
struct_enum_member and keyword_enum_value_while_passes" without naming
them. With C-3 adding two more fixtures, the AC-2 list should be
exhaustive so verification is mechanical, not interpretive.

**Resolution.** Expand AC-2's expected-match list to include
`return LP_CMD_WIDTH'(a);` for both `cross_module_type_refs` (enum
`cmd_t` in `foo_pkg.sv`) and `cross_module_type_refs_namespace_proj`
(same enum, namespace variant). Also explicitly name the enums in
`struct_enum_member` and `keyword_enum_value_while_passes`:

- `struct_enum_member` defines a single enum `mode_t` (verify by
  inspection during implementation; the spec records the count as 1, the
  exact name is implementation-stage detail).
- `keyword_enum_value_while_passes` defines a single enum (similar).

Phrase AC-2 as "exactly one match per enum across the affected fixtures,
totalling exactly 8 matches" — the count comes directly from the count
of pre-fix `return logic'(a);` lines (8, per the grep above). This makes
AC-2 a single concrete number and a deterministic verification.

**Spec impact.** Update AC-2 to include the cross-module entries and
state the total expected count (8).

## C-5. Implicit assumption: golden regeneration uses the project-standard pattern. [NO SPEC CHANGE]

**Assumption made explicit.** The phrase "regenerate" in FR-3.1 refers to
the project-standard pattern: walk every fixture under `tests/fixtures/`,
run `piketype gen` against each, and replace the corresponding subtree
under `tests/goldens/gen/`. The implementation stage will use this
pattern; the spec does not need to re-state it. Recorded here so the
planning stage does not invent a different mechanism.

## C-6. Verilator size-cast compatibility for `LP_<UPPER>_WIDTH'(a)`. [NO SPEC CHANGE]

**Assumption made explicit.** The proposed cast form
`LP_<UPPER>_WIDTH'(a)` is a SystemVerilog size cast (LRM 6.24.1):
the prefix is required to be a constant integral expression and the
result has that bit width. `LP_<UPPER>_WIDTH` is declared
`localparam int LP_<UPPER>_WIDTH = ...;` immediately above the typedef
and pack/unpack functions, satisfying the constant-integral requirement.
Verilator (current project baseline 5.046) supports size casts with
parameter widths. No spec change required; recorded so the planning
stage does not propose alternative cast forms (`'(W)'`, `$bits` tricks,
`{{...}}` replication, etc.) that complicate the template for no gain.

## C-7. `view.upper_base` and `view.kind` availability. [NO SPEC CHANGE]

**Assumption made explicit.** The macro `synth_pack_fn` already uses
`view.upper_base` on its first line
(`pack_{{ view.base }}({{ view.name }} a)` and
`logic [LP_{{ view.upper_base }}_WIDTH-1:0]`). Reusing the same field
name in the enum branch requires no view-builder changes. Recorded to
foreclose any "we need a new view field" detour in planning.

## C-8. Per-commit byte-parity reaffirmed. [NO SPEC CHANGE]

**Assumption made explicit.** Per NFR-2 and the project memory directive
`feedback_byte_parity_per_commit.md`, the template change and the
golden refresh MUST land in the same commit. The implementation stage
MUST NOT commit the template edit alone, then commit the goldens in a
follow-up commit, because the intermediate state would fail
`piketype gen` byte-parity. Recorded here so the planning and task
stages produce a task structure that respects this.

## Summary of spec.md changes

The following sections of `spec.md` will be updated as a result of these
clarifications (see Changelog at bottom of spec.md):

- **FR-3.1** — replace 3-fixture list with the full 5-fixture list
  (C-3).
- **AC-2** — expand expected-match list to cover all 5 fixtures and
  state the exact total of 8 matches (C-4).
- **Open Questions** — replace the two `[NEEDS CLARIFICATION]` blocks
  with resolved entries pointing at C-1 and C-2 (C-1 + C-2).

No other section of spec.md changes.
