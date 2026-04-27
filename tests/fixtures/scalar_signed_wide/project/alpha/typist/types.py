from typist.dsl import Logic, Struct

wide_signed_t = Logic(65, signed=True)
wide_struct_t = (
    Struct()
    .add_member("field", Logic(65, signed=True))
)
