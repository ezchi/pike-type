from typist.dsl import Const, Logic, Struct

foo_t = Logic(13)
bar_t = (
    Struct()
    .add_member("flag_a", Logic(1))
    .add_member("field_1", foo_t)
    .add_member("status", Logic(4))
    .add_member("flag_b", Logic(1))
)
