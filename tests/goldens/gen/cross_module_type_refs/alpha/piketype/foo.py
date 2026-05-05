from piketype.dsl import Bit, Enum, Flags, Logic, Struct

byte_t = Logic(8)

addr_t = (
    Struct()
    .add_member("hi", Bit(8))
    .add_member("lo", Bit(8))
)

cmd_t = (
    Enum()
    .add_value("IDLE", 0)
    .add_value("READ", 1)
    .add_value("WRITE", 2)
)

perms_t = Flags().add_flag("read").add_flag("write")
