from piketype.dsl import Struct

from alpha.piketype.foo import addr_t, byte_t, cmd_t, perms_t

bar_t = (
    Struct()
    .add_member("field1", byte_t)
    .add_member("field2", byte_t)
    .add_member("hdr", addr_t)
    .add_member("op", cmd_t)
    .add_member("perm", perms_t)
)
