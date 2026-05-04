from piketype.dsl import Enum

# AC-3: UPPER_CASE enum literals like `WHILE` (lowercase `while` is a keyword
# in SV / C++ / Python; the UPPER_CASE form is exact-case-distinct from the
# keyword and must be accepted).
state_t = (
    Enum()
    .add_value("IDLE", 0)
    .add_value("WHILE", 1)
)
