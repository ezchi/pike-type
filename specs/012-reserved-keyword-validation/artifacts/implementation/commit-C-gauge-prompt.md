# Gauge Code Review Prompt — Commit C (Tasks T-009..T-018)

You are the Gauge for the implementation stage. The Forge committed code for spec `012-reserved-keyword-validation`, commit C. Produce **ten separate VERDICT lines** — one per task.

You are NOT a cheerleader. Be strict. Reference file:line. Empty findings is a valid review when the code is clean.

## Inputs

1. Spec — `specs/012-reserved-keyword-validation/spec.md`
2. Tasks — `specs/012-reserved-keyword-validation/tasks.md` (T-009..T-018)
3. Constitution — `.steel/constitution.md` § Testing
4. Forge artifacts — `specs/012-reserved-keyword-validation/artifacts/implementation/task{9..18}-iter1-forge.md`
5. Code under review — git commit `072d368` at `/Users/ezchi/Projects/pike-type`. Inspect via `git show 072d368`.
   - 8 fixture trees under `tests/fixtures/keyword_*/project/`
   - 3 golden trees under `tests/goldens/gen/keyword_*/`
   - `tests/test_validate_keywords.py` (extended; 9 test methods total)

## Per-task review checklist

For each task verify the fixture is well-formed (single struct/flags/enum/const, two-field structs, etc.) and the corresponding test in `test_validate_keywords.py` exercises the AC the task targets.

### T-009 Negative — struct field `type`
- Fixture: `tests/fixtures/keyword_struct_field_type/project/alpha/piketype/types.py` defines `foo_t` with field `type` and a sibling field `payload`.
- Test: `test_struct_field_type_is_rejected` asserts non-zero exit and substring `field 'type' is a reserved keyword in target language(s): Python (soft), SystemVerilog`.

### T-010 Negative — flags field `try`
- Fixture: `mode_t` with `try` and `ready`.
- Test: substring `flag 'try' is a reserved keyword in target language(s): C++, Python`.

### T-011 Negative — constant `for`
- Fixture: installs `__dict__['for'] = Const(3)` because `for` is a Python hard keyword. **Verify the workaround is honest:** does the freeze step at `src/piketype/dsl/freeze.py:79` walk `module.__dict__` and accept any binding name?
- Test: substring `constant 'for' is a reserved keyword in target language(s): C++, Python, SystemVerilog`.

### T-012 Negative — module file `class.py`
- Fixture: `tests/fixtures/keyword_module_name_class/project/alpha/piketype/class.py` (file actually named `class.py`).
- Test: substring `module name 'class' is a reserved keyword in target language(s): C++, Python` (NOT SystemVerilog because the SV emitted form `class_pkg` is not a keyword).

### T-013 Positive — module file `logic.py`
- Fixture file actually named `logic.py`.
- Golden: complete generated tree (13 files).
- Test: `test_module_name_logic_is_accepted` uses `assert_trees_equal`.

### T-014 Positive — type `class_t`
- Fixture defines `class_t` struct with non-keyword fields.
- Golden: complete tree.
- Test: `test_type_name_class_t_is_accepted`.

### T-015 Positive — enum value `WHILE` (AC-3)
- Fixture: `state_t` enum with `IDLE` and `WHILE`.
- Golden: complete tree.
- Test: `test_enum_value_while_is_accepted`.
- This is the explicit AC-3 evidence that exact-case keyword matching works as advertised.

### T-016 Ordering — lowercase enum value `for` (AC-11)
- Fixture: `state_t` enum with `IDLE` and lowercase `for`.
- Test: asserts `"UPPER_CASE"` is in stderr AND `"reserved keyword"` is NOT, pinning the precedence (structural check fires before keyword check).
- Note: the UPPER_CASE check fires at DSL-construction time (in `Enum.add_value`), even earlier than the validate-stage check — this is fine, the precedence direction is the same.

### T-017 Tests — 8 new test methods
- Test method count in `tests/test_validate_keywords.py` should be 9 total (1 existing smoke + 8 new).
- Each method has a docstring referencing its AC.
- Negative tests use `assertNotEqual(returncode, 0)` + targeted `assertIn` substrings (exercise the FR-3 message structural part).
- Positive tests use `assertEqual(returncode, 0)` + `assert_trees_equal`.

### T-018 Verification
- Pyright at baseline (no new errors).
- `python -m unittest discover tests` shows 303 tests OK, 3 skipped.
- Existing goldens unchanged.

## Output format

```
# Gauge Code Review — Commit C

## Per-task assessment

### T-009 — struct field type negative
(Findings.)
VERDICT-T009: APPROVE | REVISE

### T-010 — flags field try negative
VERDICT-T010: APPROVE | REVISE

### T-011 — constant for negative
VERDICT-T011: APPROVE | REVISE

### T-012 — module class negative
VERDICT-T012: APPROVE | REVISE

### T-013 — module logic positive
VERDICT-T013: APPROVE | REVISE

### T-014 — type class_t positive
VERDICT-T014: APPROVE | REVISE

### T-015 — enum WHILE positive (AC-3)
VERDICT-T015: APPROVE | REVISE

### T-016 — ordering for (AC-11)
VERDICT-T016: APPROVE | REVISE

### T-017 — tests
VERDICT-T017: APPROVE | REVISE

### T-018 — verify byte parity
VERDICT-T018: APPROVE | REVISE

## Cross-task observations
```

Each VERDICT line is parsed verbatim. Use `VERDICT-T009:`, `VERDICT-T010:`, ... `VERDICT-T018:` exactly with `APPROVE` or `REVISE`.
