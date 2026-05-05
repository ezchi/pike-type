from piketype.dsl import Logic, Struct

near_miss_t = (
    Struct()
    .add_member("type_id", Logic(2))
    .add_member("payload", Logic(8))
)
