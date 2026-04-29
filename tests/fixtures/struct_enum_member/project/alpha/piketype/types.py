from piketype.dsl import Bit, Enum, Struct

cmd_t = Enum().add_value("IDLE", 0).add_value("READ", 1).add_value("WRITE", 2)

pkt_t = Struct().add_member("cmd", cmd_t).add_member("data", Bit(8))

aligned_pkt_t = (
    Struct()
    .add_member("cmd", cmd_t)
    .add_member("data", Bit(8))
    .multiple_of(32)
)
