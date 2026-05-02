from piketype.dsl import Logic, Struct

# `class_t` (full name) is NOT a keyword in any target language; the base
# form `class` IS a keyword in C++/Python/SV but is never emitted standalone
# (only as substring of `pack_class`, `LP_CLASS_WIDTH`, `class_ct` etc.).
# This fixture pins AC-2: type-name `class_t` is accepted.
class_t = (
    Struct()
    .add_member("addr", Logic(8))
    .add_member("payload", Logic(16))
)
