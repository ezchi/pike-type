from piketype.dsl import Logic, Struct

foo_t = (
    Struct()
    .add_member("type", Logic(2))
    .add_member("payload", Logic(8))
)
