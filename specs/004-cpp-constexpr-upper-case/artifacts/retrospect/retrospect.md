# Retrospect — Spec 004: C++ constexpr UPPER_SNAKE_CASE

## Summary

Renamed all non-user-defined `constexpr` identifiers in generated C++ output from `kCamelCase`/lowercase to `UPPER_SNAKE_CASE`. Two Python emitter files modified, 21 golden files regenerated. 101 tests pass, zero new basedpyright errors.

## What Went Well

- **Mechanical change, clean execution.** The rename was purely string-literal substitutions in two files. No logic changes required.
- **Golden test coverage caught everything.** The existing test suite provided complete regression protection — every affected output file was already golden-tested.
- **Gauge reviews were valuable.** Codex caught three real issues: missing `mask` → `MASK` coverage, non-exhaustive reference update wording, and overstated constitution alignment claim.

## What Could Improve

- **Planning iteration overhead.** Three planning iterations were needed to get commands right (`python` vs `python3`, relative vs absolute paths, missing `struct_wide` fixture). For trivial changes, the planning stage overhead exceeds the implementation effort.
- **Constitution gap.** The constitution lacks explicit C++ constant naming rules. This spec was framed as a "project style decision" rather than constitutional compliance.

## Learnings

- The Gauge consistently catches scope-consistency issues between overview/FR/AC sections. This is its strongest contribution.
- Golden regeneration commands should always use absolute paths and match the exact test suite invocations.

## Memory Candidates

- **Feedback:** Use `python3` (not `python`) in plan commands — `python` is not on PATH in this environment.
- **Project:** Constitution does not prescribe C++ constant naming; Spec 004 established UPPER_SNAKE_CASE as the convention for generated C++ constexpr.
