from piketype.dsl import Struct

from alpha.piketype.foo import byte_t

# Three byte_t fields = 24 bits; multiple_of(32) adds 8 bits trailing alignment.
bar_t = (
    Struct()
    .add_member("a", byte_t)
    .add_member("b", byte_t)
    .add_member("c", byte_t)
    .multiple_of(32)
)
