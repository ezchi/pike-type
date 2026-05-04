from piketype.dsl import Enum

# Explicit values, non-contiguous
color_t = (
    Enum()
    .add_value("RED", 0)
    .add_value("GREEN", 5)
    .add_value("BLUE", 10)
)

# Mixed explicit + auto-fill with gap, explicit width 8
cmd_t = (
    Enum(8)
    .add_value("NOP", 0)
    .add_value("READ", 5)
    .add_value("WRITE")
    .add_value("RESET")
)

# Single-value enum, width = 1
flag_t = (
    Enum()
    .add_value("SET", 0)
)

# Large value near 64-bit boundary
big_t = (
    Enum()
    .add_value("SMALL", 0)
    .add_value("LARGE", 2**63)
)
