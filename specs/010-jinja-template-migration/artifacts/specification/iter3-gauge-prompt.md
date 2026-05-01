# Gauge Review Prompt — Specification Iteration 3

You are the **Gauge** in a dual-agent Forge-Gauge loop.

This is **iteration 3**. Iteration 2 returned `VERDICT: REVISE` with these issues:

1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
2. BLOCKING — FR-21/AC-F7: lint patterns false-positived on legitimate target-language text inside templates (e.g., SystemVerilog `padded[WIDTH-1:0]`, C++ `BYTE_COUNT * 8`). Patterns must scan only Jinja-block contents.
3. WARNING — FR-8/FR-9/FR-15: `frozenset` was discouraged in one place and recommended in another. Pick one rule.
4. WARNING — FR-18/Q-3: location of view-model construction (in `view.py` vs. a separate `builder.py`) was still an open question. Decide now.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md` (iteration 3).
2. **Project Constitution:** `.steel/constitution.md`.
3. **Iteration-2 review for context:** `specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md`.

## Review Instructions

This is a delta review. For each iter2 issue (1–4), state whether it is **resolved**, **partially resolved**, or **not resolved**, citing the iter3 FR/NFR/AC identifier.

Then check for new issues introduced by the revision:

- **FR-9 forbids `frozenset`**: does any other section (FR-8, FR-15, FR-18, NFR-3) still permit it?
- **FR-21 Jinja-block scoping**: are the patterns themselves correct? Do they catch what they claim to catch when applied to the contents of `{{ ... }}` and `{% ... %}` only? Could pattern 5 (`[-+*/]\s*8\b|\b8\s*[-+*/]`) over-trigger on benign Jinja expressions like `{{ field.byte_count }}` (no, that has no 8) or `{{ width // 8 }}` (yes, that should be caught)? Is the design correct that `// 8` byte-conversion in a Jinja block IS forbidden? Confirm or flag.
- **NFR-1 / `tools/perf_bench.py`**: does the proposed bench helper actually work given that `run_gen` may write `gen/` artifacts under the input file's repo root? The spec says it copies to a temp dir; verify the spec describes a working flow.
- **FR-18 single-file rule**: does this conflict with the constitution's project-layout convention or coding standards?
- **AC-F5 wheel install**: is the proposed sequence (`pip wheel . -w /tmp/pike_wheel/`, then `pip install`, then `piketype gen <tmp-copy>/alpha/piketype/types.py`) executable as written? Are any pieces still wrong?
- **Open Questions Q-1..Q-4**: are any of them now answerable as FRs (i.e., the spec is implicitly committing to one answer already)?

Apply the same severity scheme: `BLOCKING`, `WARNING`, `NOTE`. End with exactly one of `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

Bias toward APPROVE only if iter2's blockers are genuinely fixed and no new blocker has been introduced. Open Questions that are properly framed as questions (not hidden contradictions) are acceptable for an APPROVE verdict — they will be resolved in the clarification stage.
