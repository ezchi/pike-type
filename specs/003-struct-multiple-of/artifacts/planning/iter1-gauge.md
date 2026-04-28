# Gauge Review — Planning Iteration 1

### ISSUE-1: Proposed fixture is invalid
**Severity:** BLOCKING
**Description:** Fixture uses wrong imports (`from typist import Struct, Bit, UBit`). Should be `from typist.dsl import ...` and `UBit` doesn't exist. Path should be `tests/fixtures/<name>/project/alpha/typist/types.py`.

### ISSUE-2: Freeze plan misses named scalar aliases
**Severity:** BLOCKING
**Description:** TypeRefIR can point to ScalarAliasIR, not just StructIR. Width computation must handle all field type variants.

### ISSUE-3: Freeze ordering assumption is false
**Severity:** BLOCKING
**Description:** freeze_module iterates dict and sorts after. Need ordering-independent width computation.

### ISSUE-4: StructType slots are underspecified
**Severity:** WARNING
**Description:** `@dataclass(slots=True)` requires field declarations, not just __init__ assignments.

### ISSUE-5: Negative test plan is incomplete
**Severity:** WARNING
**Description:** Need explicit test cases for all AC-3 values with message substrings.

VERDICT: REVISE
