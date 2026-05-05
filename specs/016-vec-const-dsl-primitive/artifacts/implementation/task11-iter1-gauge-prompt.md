# Gauge Code Review — Task 11, Iteration 1

You are the **Gauge**.

## Task
Per Plan Risk R-2: regenerate every existing `tests/goldens/gen/*/piketype_manifest.json` to gain the new `"vec_constants": []` line per module.

## Approach
Used an in-place JSON patch script (vs re-running `piketype gen` per fixture):
```python
for path in Path('tests/goldens/gen').glob('*/piketype_manifest.json'):
    data = json.loads(path.read_text())
    for module in data.get('modules', []):
        if 'vec_constants' not in module:
            module['vec_constants'] = []
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
```

## Result
- 23 of 24 manifest goldens patched in-place.
- Full unittest suite: 307 passing (after the patch). The 26 integration tests that failed BEFORE the patch (every golden test) now pass — confirming the only diff was the missing `vec_constants` key.

## Forge artifact
`/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/implementation/task11-iter1-forge.md`

## Review criteria

1. Is the in-place JSON patch byte-identical to what `piketype gen` would produce post-T5? (Justification: `sort_keys=True` matches the writer at `write_json.py:152`; the only field added is `vec_constants: []`; existing field shapes unchanged.)
2. Did the patch touch only the manifest goldens? (Other goldens like `*.sv`, `*.hpp`, `*.py` should be unchanged.)
3. Did 307 tests pass? (Yes, empirically verified.)

## Output

### Issues
**BLOCKING / WARNING / NOTE**, terse.

### Verdict
End with **EXACTLY** `VERDICT: APPROVE` or `VERDICT: REVISE`.
