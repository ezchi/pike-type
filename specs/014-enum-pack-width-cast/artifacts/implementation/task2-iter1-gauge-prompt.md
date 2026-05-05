# Gauge Code Review — Task 2, Iteration 1

You are the **Gauge** in the Forge-Gauge implementation loop. Review the
forge's golden refresh for **Task 2 only**. Task 1 (template edit) was
reviewed separately and approved.

## Task description

**Task 2: Regenerate all 5 affected goldens**

For each of the 5 fixtures with an enum, run `python -m piketype.cli gen`
against a temp copy of the fixture and overwrite the corresponding
`tests/goldens/gen/<name>/` subtree. One fixture
(`cross_module_type_refs_namespace_proj`) does not have a fixture
directory of its own — its golden is generated from the
`cross_module_type_refs` fixture with the extra arg
`--namespace=proj::lib`.

## Spec / Plan / Constitution context

- Spec: `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/spec.md`
  (FR-3.1, FR-3.2, FR-3.3, AC-1, AC-2, AC-6, AC-7).
- Plan: `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/plan.md`
  Phase 2.
- Tasks (with the per-fixture invocation table):
  `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/tasks.md`
- Constitution:
  `/Users/ezchi/Projects/pike-type/.steel/constitution.md`
  (Principle 3 Deterministic output, Testing section).
- Forge artifact:
  `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/artifacts/implementation/task2-iter1-forge.md`

## Code under review

### Git diff (all 5 golden files; HEAD~2 is the pre-implementation state)

```diff
diff --git a/tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv b/tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv
@@ -43,7 +43,7 @@ package foo_pkg;
   typedef enum logic [LP_CMD_WIDTH-1:0] {IDLE = 0, READ = 1, WRITE = 2} cmd_t;
 
   function automatic logic [LP_CMD_WIDTH-1:0] pack_cmd(cmd_t a);
-    return logic'(a);
+    return LP_CMD_WIDTH'(a);
   endfunction

diff --git a/tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv
@@ -43,7 +43,7 @@ package foo_pkg;
   typedef enum logic [LP_CMD_WIDTH-1:0] {IDLE = 0, READ = 1, WRITE = 2} cmd_t;
 
   function automatic logic [LP_CMD_WIDTH-1:0] pack_cmd(cmd_t a);
-    return logic'(a);
+    return LP_CMD_WIDTH'(a);

diff --git a/tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv
@@ -10,7 +10,7 @@ package defs_pkg;
   typedef enum logic [LP_COLOR_WIDTH-1:0] {RED = 0, GREEN = 5, BLUE = 10} color_t;
   function automatic logic [LP_COLOR_WIDTH-1:0] pack_color(color_t a);
-    return logic'(a);
+    return LP_COLOR_WIDTH'(a);
@@ -23,7 +23,7 @@
   typedef enum logic [LP_CMD_WIDTH-1:0] {NOP = 0, READ = 5, WRITE = 6, RESET = 7} cmd_t;
   function automatic logic [LP_CMD_WIDTH-1:0] pack_cmd(cmd_t a);
-    return logic'(a);
+    return LP_CMD_WIDTH'(a);
@@ -36,7 +36,7 @@
   typedef enum logic {SET = 0} flag_t;
   function automatic logic [LP_FLAG_WIDTH-1:0] pack_flag(flag_t a);
-    return logic'(a);
+    return LP_FLAG_WIDTH'(a);
@@ -49,7 +49,7 @@
   typedef enum logic [LP_BIG_WIDTH-1:0] {SMALL = 0, LARGE = 9223372036854775808} big_t;
   function automatic logic [LP_BIG_WIDTH-1:0] pack_big(big_t a);
-    return logic'(a);
+    return LP_BIG_WIDTH'(a);

diff --git a/tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv
@@ -10,7 +10,7 @@ package types_pkg;
   typedef enum logic {IDLE = 0, WHILE = 1} state_t;
   function automatic logic [LP_STATE_WIDTH-1:0] pack_state(state_t a);
-    return logic'(a);
+    return LP_STATE_WIDTH'(a);

diff --git a/tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv
@@ -10,7 +10,7 @@ package types_pkg;
   typedef enum logic [LP_CMD_WIDTH-1:0] {IDLE = 0, READ = 1, WRITE = 2} cmd_t;
   function automatic logic [LP_CMD_WIDTH-1:0] pack_cmd(cmd_t a);
-    return logic'(a);
+    return LP_CMD_WIDTH'(a);
```

8 lines changed total. No `_test_pkg.sv` lines change. No runtime,
C++, or Python golden lines change.

### Independent verification

Run from the project root:

1. `git diff --stat HEAD~2 -- tests/goldens/gen/` should list exactly:
   ```
   tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv       | 2 +-
   tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv | 2 +-
   tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv                    | 8 ++++----
   tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv     | 2 +-
   tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv         | 2 +-
   ```
   (Order may vary; total of 5 files.)
2. `grep -r "return logic'(a);" tests/goldens/gen/ | wc -l` should
   return `0`.
3. `grep -r "return LP_[A-Z_]*_WIDTH'(a);" tests/goldens/gen/ | wc -l`
   should return `8`.
4. `git diff --stat HEAD~2 -- tests/goldens/gen/ | grep _test_pkg.sv`
   should return empty.

## Review checklist

1. **Coverage.** All 5 enumerated fixtures from spec FR-3.1 have their
   `_pkg.sv` updated? No fixture in the list is omitted?
2. **Scope.** Did the regen leak into other files (cpp, py, runtime,
   `_test_pkg.sv`, manifest)? Verify via diff stat (item 1 above).
3. **Correctness of the specific replacement.** For each pack body,
   the new `LP_<UPPER>_WIDTH` matches the function's declared return
   type `logic [LP_<UPPER>_WIDTH-1:0]` and matches the typedef's
   underlying width? Cross-check by reading each diff hunk.
4. **Width-correct semantics.** For each fixture's enum, verify the
   typedef and the new cast use the same `LP_<NAME>_WIDTH`. Examples:
   - `enum_basic.color_t`: typedef `logic [LP_COLOR_WIDTH-1:0]`, cast
     `LP_COLOR_WIDTH'(a)`. Match.
   - `enum_basic.flag_t`: typedef `logic` (1-bit), cast
     `LP_FLAG_WIDTH'(a)` (LP_FLAG_WIDTH=1). Match (function returns
     `logic [LP_FLAG_WIDTH-1:0]` which is 1-bit; cast yields 1-bit).
   - `enum_basic.big_t`: 64-bit. Match.
   - `keyword_enum_value_while_passes.state_t`: 1-bit (IDLE=0,
     WHILE=1). Match.
   - others: verify.
5. **Constitution Principle 3 (Deterministic).** Will re-running
   `piketype gen` against the same fixture twice produce byte-equal
   output to the committed golden? (Hint: yes, because the only
   width-substituted token is the deterministic
   `view.upper_base`-derived parameter name.)
6. **Test coverage.** Existing golden tests cover all 5 fixtures.
7. **Security / OWASP / N+1 / performance.** N/A — these are
   generated text artifacts.

## Output

```
# Gauge Code Review — Task 2, Iteration 1

## Summary

## Issues

### BLOCKING
(or "None.")

### WARNING
(or "None.")

### NOTE

## Constitution Compliance

## Verdict

VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
