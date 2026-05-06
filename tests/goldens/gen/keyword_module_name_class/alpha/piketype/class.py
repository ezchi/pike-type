from piketype.dsl import Logic, Struct

dummy_t = (
    Struct()
    .add_member("a", Logic(2))
    .add_member("b", Logic(2))
)
