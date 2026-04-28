# Gauge Review — Planning Iteration 1

**BLOCKING:** Steps 2-4 create an inconsistent intermediate state. After `git mv src/typist src/piketype`, imports still point at `typist`. Need to combine the package move, pyproject.toml update, and import rewrites into a single atomic step.

**BLOCKING:** Step 7 says "for each fixture" run `piketype gen`, but the repo has negative fixtures (no_dsl, outside_typist, const_collision, etc.) that are supposed to fail. The plan must list only positive golden fixtures.

**BLOCKING:** AC-13 verification is incomplete. It checks `name = "pike-type"` but not that no stale `name = "typist"` exists.

**WARNING:** Step 12 uses `uv pip install -e .` but AC-1 says `pip install -e .`. Use exact AC command.

**WARNING:** grep exit code 1 = success for "no matches" but looks like failure in scripts. Use `! grep ...`.

**WARNING:** AC-12 not explicitly verified. Add check that PikeTypeError exists and subclasses inherit from it.

**NOTE:** Verification section not tightly mapped to all 14 ACs.

VERDICT: REVISE
