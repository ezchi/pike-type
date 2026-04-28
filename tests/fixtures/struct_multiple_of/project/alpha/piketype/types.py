from piketype.dsl import Logic, Struct

# Case (a): struct that needs trailing padding (natural=24 bits, aligned=32 bits)
aligned_t = (
    Struct()
    .add_member("a", Logic(5))
    .add_member("b", Logic(12))
    .multiple_of(32)
)

# Case (b): struct where natural width already meets alignment (24 % 24 == 0)
no_extra_pad_t = (
    Struct()
    .add_member("a", Logic(5))
    .add_member("b", Logic(12))
    .multiple_of(24)
)

# Case (c): nested — inner aligned struct as field in outer struct
inner_t = (
    Struct()
    .add_member("x", Logic(3))
    .multiple_of(16)
)
outer_t = (
    Struct()
    .add_member("inner", inner_t)
    .add_member("y", Logic(8))
)
