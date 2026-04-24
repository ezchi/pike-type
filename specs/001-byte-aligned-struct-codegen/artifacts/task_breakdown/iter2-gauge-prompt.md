# Gauge Review: Task Breakdown — Iteration 2

You are the Gauge reviewer. This iteration addresses all 6 findings from iteration 1.

## Previous Findings
1. Task ordering: Task 22 (Python goldens) before Task 23 (struct_signed fixture creation)
2. Task 7 missing AC-18 inline coverage
3. AC-9 under-tested (missing 37-bit scalar)
4. Task 25 missing runtime vectors (AC-24 masking, AC-25, nested struct)
5. Task 11 pack/unpack verification too weak (AC-3/4/5/14)
6. Fixture paths inconsistent (should use `project/alpha/typist/types.py`)

## Changes Made
1. Added Task 20 "Create all new test fixtures" BEFORE Python backend tasks. Renumbered 20→21, 21→22, 22→23. Dependencies updated.
2. Task 7: `scalar_signed_wide` fixture now includes inline LogicSigned(65) + inline Logic(128) for AC-18.
3. `scalar_wide` fixture now includes 37-bit unsigned for AC-9.
4. Task 25 now lists all runtime vectors: AC-24 all-0xFF masking, AC-25 struct_wide 10-byte, nested struct, AC-7, AC-12, AC-15.
5. Task 11 verification now lists AC-3/4/5/14 with specific worked example values.
6. All fixture paths changed to `project/alpha/typist/types.py`.

## Files to Review
1. **Updated tasks:** `specs/001-byte-aligned-struct-codegen/tasks.md`
2. **Specification:** `specs/001-byte-aligned-struct-codegen/spec.md`

## Review Checklist
1. Do the changes resolve all 6 findings?
2. Is task ordering now correct (fixtures before goldens)?
3. Are dependencies consistent (no circular deps, correct task numbers)?
4. Are all 25 ACs covered?
5. Any remaining gaps?

End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
