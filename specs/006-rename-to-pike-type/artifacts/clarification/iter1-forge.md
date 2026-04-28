# Clarification Review — Spec 006: Rename Repository to pike-type

## Analysis

The specification has been through 3 Forge-Gauge iterations during the specification phase. All `[NEEDS CLARIFICATION]` markers were resolved:

1. **docs/rfc-v1.md handling** — Resolved: FR-13 explicitly requires updating it (it's the pyproject.toml readme).
2. **constitution update timing** — Resolved: FR-14 requires updating during implementation.

## Remaining Ambiguity Check

Reviewing each FR for implementation ambiguity:

| FR | Status | Notes |
|----|--------|-------|
| FR-1 | Clear | `git mv src/typist src/piketype` |
| FR-2 | Clear | Mechanical find-replace of import paths |
| FR-3 | Clear | 3 specific fields to change |
| FR-4 | Clear | Single line change |
| FR-5 | Clear | Function renames + string literal changes specified exactly |
| FR-6 | Clear | All file names and content changes enumerated |
| FR-7 | Clear | Path constants in one file |
| FR-8 | Clear | Single error message change |
| FR-9 | Clear | `TypistError` → `PikeTypeError`, subclasses inherit unchanged |
| FR-10 | Clear | Directory renames + import updates in fixtures + pycache cleanup |
| FR-11 | Clear | Golden file renames and content updates |
| FR-12 | Clear | Test file updates enumerated by category |
| FR-13 | Clear | All doc files listed explicitly with catch-all |
| FR-14 | Clear | Constitution sections to update listed |
| FR-15 | Clear | Docstring change, version explicitly stays unchanged |
| FR-16 | Clear | Run `uv lock` |

## Potential Implementation Ordering Concern

The rename is inherently atomic — most changes must happen together for the codebase to be consistent. Suggested ordering for implementation:
1. Rename `src/typist/` → `src/piketype/` (FR-1)
2. Update all source imports and symbols (FR-2, FR-4, FR-5, FR-7, FR-8, FR-9)
3. Update pyproject.toml (FR-3)
4. Update generated output names/content in emitters (FR-6)
5. Update test fixtures (FR-10) — delete pycache, rename dirs, update imports
6. Regenerate golden files by running the tool (FR-11)
7. Update test source files (FR-12)
8. Update docs (FR-13) and constitution (FR-14)
9. Update __init__.py (FR-15)
10. Regenerate uv.lock (FR-16)
11. Cleanup and verify (NFR-3, NFR-5, AC-4, AC-14)

## Conclusion

No clarification questions needed. The spec is unambiguous and implementation-ready.
