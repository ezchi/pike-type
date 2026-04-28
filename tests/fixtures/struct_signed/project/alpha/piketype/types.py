from piketype.dsl import Logic, Struct

signed_4_t = Logic(4, signed=True)
signed_5_t = Logic(5, signed=True)
mixed_t = (
    Struct()
    .add_member("field_s", signed_4_t)
    .add_member("field_u", Logic(5, signed=True))
)
