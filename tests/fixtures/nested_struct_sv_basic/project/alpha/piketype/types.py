from piketype.dsl import Bit, Const, Logic, Struct

W = Const(13)
addr_t = Bit(W)
flag_t = Bit(1)

header_t = (
    Struct()
    .add_member("addr", addr_t)
    .add_member("enable", flag_t)
)

packet_t = (
    Struct()
    .add_member("header", header_t)
    .add_member("mode", Logic(2))
    .add_member("error_code", Bit(3))
)
