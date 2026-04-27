from typist.dsl import Logic, Struct

collision_t = (
    Struct()
    .add_member("foo_pad", Logic(4))
    .add_member("bar", Logic(8))
)
