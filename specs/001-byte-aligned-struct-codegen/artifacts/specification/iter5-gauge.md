# Gauge Review — Iteration 5

**Reviewer:** codex (gpt-5.5)

## BLOCKING

- **Generated identifier collisions.** New package-scope SV identifiers (`LP_<TYPE>_WIDTH`, `LP_<TYPE>_BYTE_COUNT`, `pack_<base_name>`, `unpack_<base_name>`) can collide with user-defined constants. Example: `LP_FOO_WIDTH = Const(...)` plus `foo_t = Logic(13)` generates duplicate identifiers. Need collision validation.

## WARNING

- Add AC for `to_slv()` zeroing `_pad` fields / `from_slv()` ignoring padding.
- Add AC for inline `Struct().add_member("field", Logic(65))` rejection.
- Validation failures should be tested via unit/negative CLI tests, not golden files.

## NOTE

- Iteration 4 issues are otherwise resolved.

VERDICT: REVISE
