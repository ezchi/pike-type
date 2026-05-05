# Gauge Code Review — Task 5, Iteration 1

You are the **Gauge**.

## Task
Update `src/piketype/manifest/write_json.py` to emit a new `vec_constants` array per module (FR-18). Each entry: `name`, `width`, `value`, `base`, `source`. Legacy `constants` array unchanged.

## Diff (in `write_json.py` only — additions inside the per-module dict comprehension)

```python
                "dependencies": [...],
+               "vec_constants": [
+                   {
+                       "name": v.name,
+                       "width": v.width,
+                       "value": v.value,
+                       "base": v.base,
+                       "source": {
+                           "path": str(Path(v.source.path).resolve().relative_to(repo_root.resolve())),
+                           "line": v.source.line,
+                           "column": v.source.column,
+                       },
+                   }
+                   for v in module.vec_constants
+               ],
                "generated_outputs": {...},
```

## Forge artifact
`/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/implementation/task5-iter1-forge.md`

## Verification empirically run
- basedpyright on `write_json.py`: 0 errors / 0 warnings / 0 notes.
- Full unittest suite: 307 passing (after T11 manifest goldens regen).

## Review

1. Field set matches FR-18? (name, width, value, base, source)
2. Legacy `constants` array byte-identical? (no `kind` field added)
3. Output dumped with `sort_keys=True` so `vec_constants` lands alphabetically last per module — confirmed by goldens.

## Output

### Issues
**BLOCKING / WARNING / NOTE**, terse.

### Verdict
End with **EXACTLY** `VERDICT: APPROVE` or `VERDICT: REVISE`.
