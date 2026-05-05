# Gauge Code Review — Task 1, Iteration 1

You are the **Gauge** in the Forge-Gauge implementation loop. Review the
forge's code for **Task 1 only** (the template edit). Task 2 (golden
refresh) gets a separate review.

## Task description

**Task 1: Edit synth_pack_fn enum branch in _macros.j2**

Replace `return logic'(a);` with `return LP_{{ view.upper_base }}_WIDTH'(a);`
at line 98 of `src/piketype/backends/sv/templates/_macros.j2` (inside the
`synth_pack_fn` macro, enum branch). Single-line edit; no Python touch.

## Spec / Plan / Constitution context

- Spec: `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/spec.md`
  (post-clarification). Particularly FR-1.1, FR-1.2, FR-1.3, FR-1.4,
  NFR-1, AC-5.
- Plan: `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/plan.md`
  section C-1.
- Constitution:
  `/Users/ezchi/Projects/pike-type/.steel/constitution.md`
  (Principle 5 Template-first, Coding Standards / Generated Code).
- Forge artifact:
  `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/artifacts/implementation/task1-iter1-forge.md`

## Code under review

### Git diff (the only file changed by Task 1)

```diff
diff --git a/src/piketype/backends/sv/templates/_macros.j2 b/src/piketype/backends/sv/templates/_macros.j2
index e6933bb..946b054 100644
--- a/src/piketype/backends/sv/templates/_macros.j2
+++ b/src/piketype/backends/sv/templates/_macros.j2
@@ -95,7 +95,7 @@
 {% elif view.kind == "flags" %}
     return {{ '{' }}{% for n in view.field_names %}a.{{ n }}{% if not loop.last %}, {% endif %}{% endfor %}{{ '}' }};
 {% elif view.kind == "enum" %}
-    return logic'(a);
+    return LP_{{ view.upper_base }}_WIDTH'(a);
 {% elif view.kind == "struct" %}
     return {{ '{' }}{% for p in pack_unpack.pack_parts %}{{ p.expr }}{% if not loop.last %}, {% endif %}{% endfor %}{{ '}' }};
 {% endif %}
```

### Full content of the modified macro (synth_pack_fn, lines 91-103)

```jinja
{% macro synth_pack_fn(view, pack_unpack) %}
  function automatic logic [LP_{{ view.upper_base }}_WIDTH-1:0] pack_{{ view.base }}({{ view.name }} a);
{% if view.kind == "scalar_alias" %}
    return a;
{% elif view.kind == "flags" %}
    return {{ '{' }}{% for n in view.field_names %}a.{{ n }}{% if not loop.last %}, {% endif %}{% endfor %}{{ '}' }};
{% elif view.kind == "enum" %}
    return LP_{{ view.upper_base }}_WIDTH'(a);
{% elif view.kind == "struct" %}
    return {{ '{' }}{% for p in pack_unpack.pack_parts %}{{ p.expr }}{% if not loop.last %}, {% endif %}{% endfor %}{{ '}' }};
{% endif %}
  endfunction
{%- endmacro %}
```

You may also read the surrounding template at
`/Users/ezchi/Projects/pike-type/src/piketype/backends/sv/templates/_macros.j2`
to verify the context.

## Review checklist

1. **Correctness.** Is the new line `return LP_{{ view.upper_base }}_WIDTH'(a);`
   syntactically correct Jinja AND syntactically correct SystemVerilog
   after rendering? Does the `view.upper_base` token resolve to the
   same identifier used on the function-return-type line above?
2. **Width-correctness in rendered SV.** Walk through the rendering
   for a hypothetical `color_t` with `LP_COLOR_WIDTH = 4`. Result:
   `return LP_COLOR_WIDTH'(a);`. Is that a 4-bit cast that returns
   the encoded enum value, not the LSB?
3. **1-bit enum case.** Walk through the rendering for `flag_t`
   with `LP_FLAG_WIDTH = 1`. Result: `return LP_FLAG_WIDTH'(a);`.
   Is that a 1-bit cast that returns `a`'s LSB (which is the only
   bit it has)?
4. **No scope leak.** Confirm the diff is a single -1/+1 hunk and no
   other line in `_macros.j2` is touched. Run
   `git diff HEAD~1 -- src/piketype/backends/sv/templates/_macros.j2`
   to verify.
5. **No Python touch.** Confirm
   `git diff HEAD~1 -- src/piketype/` shows only this template file.
6. **Constitution compliance.**
   - Principle 5 (Template-first): yes, the change is template-only.
     Verify.
   - Generated code header / formatting rules: the macro emits inside
     a function body at indent level 4 spaces — is the new line's
     indentation correct (4 spaces, matching surrounding lines)?
7. **Indentation / whitespace.** The new line should have 4 leading
   spaces. The Jinja line ends without trailing whitespace.
8. **Test coverage.** Task 1 adds no new tests. Spec NFR-6 / AC-8
   relies on existing golden tests. Acceptable for this stage.
9. **Security / performance / N+1 / OWASP.** Likely N/A for a Jinja
   template literal; confirm no concerns.

## Output

```
# Gauge Code Review — Task 1, Iteration 1

## Summary
(2-4 sentences)

## Issues

### BLOCKING
(or "None.")

### WARNING
(or "None.")

### NOTE

## Constitution Compliance
(One paragraph.)

## Verdict

VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Be strict. End with the verdict line verbatim.
