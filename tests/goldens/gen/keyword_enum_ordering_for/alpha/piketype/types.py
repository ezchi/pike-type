from piketype.dsl import Enum

# AC-11: enum value `for` (lowercase) violates the existing UPPER_CASE rule.
# That structural defect should fire BEFORE the new keyword check; the
# resulting error must be the UPPER_CASE error, not the keyword error.
state_t = (
    Enum()
    .add_value("IDLE", 0)
    .add_value("for", 1)
)
