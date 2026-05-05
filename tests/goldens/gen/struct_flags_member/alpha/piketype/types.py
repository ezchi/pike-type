from piketype.dsl import Flags, Struct, Bit

status_t = Flags().add_flag("error").add_flag("warning").add_flag("ready")

report_t = (
    Struct()
    .add_member("status", status_t)
    .add_member("code", Bit(5))
)

aligned_report_t = (
    Struct()
    .add_member("flags", status_t)
    .add_member("data", Bit(3))
    .multiple_of(32)
)
