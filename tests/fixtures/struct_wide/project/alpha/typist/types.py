from typist.dsl import Logic, Struct

big_t = (
    Struct()
    .add_member("data", Logic(65))
    .add_member("flag", Logic(1))
    .add_member("extra", Logic(128))
)
