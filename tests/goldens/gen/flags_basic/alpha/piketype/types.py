from piketype.dsl import Flags

# 1 flag — 7 padding bits, uint8_t
single_t = Flags().add_flag("flag")

# 3 flags — 5 padding bits, uint8_t
triple_t = Flags().add_flag("a").add_flag("b").add_flag("c")

# 8 flags — no padding, uint8_t
byte_t = (
    Flags()
    .add_flag("f0")
    .add_flag("f1")
    .add_flag("f2")
    .add_flag("f3")
    .add_flag("f4")
    .add_flag("f5")
    .add_flag("f6")
    .add_flag("f7")
)

# 9 flags — 7 padding bits, uint16_t
wide_t = (
    Flags()
    .add_flag("f0")
    .add_flag("f1")
    .add_flag("f2")
    .add_flag("f3")
    .add_flag("f4")
    .add_flag("f5")
    .add_flag("f6")
    .add_flag("f7")
    .add_flag("f8")
)

# 33 flags — 7 padding bits, uint64_t
very_wide_t = (
    Flags()
    .add_flag("f0")
    .add_flag("f1")
    .add_flag("f2")
    .add_flag("f3")
    .add_flag("f4")
    .add_flag("f5")
    .add_flag("f6")
    .add_flag("f7")
    .add_flag("f8")
    .add_flag("f9")
    .add_flag("f10")
    .add_flag("f11")
    .add_flag("f12")
    .add_flag("f13")
    .add_flag("f14")
    .add_flag("f15")
    .add_flag("f16")
    .add_flag("f17")
    .add_flag("f18")
    .add_flag("f19")
    .add_flag("f20")
    .add_flag("f21")
    .add_flag("f22")
    .add_flag("f23")
    .add_flag("f24")
    .add_flag("f25")
    .add_flag("f26")
    .add_flag("f27")
    .add_flag("f28")
    .add_flag("f29")
    .add_flag("f30")
    .add_flag("f31")
    .add_flag("f32")
)
