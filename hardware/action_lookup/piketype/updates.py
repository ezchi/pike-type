from piketype.dsl import Logic, Struct

from .table import Addr, CoherentId

LlTableUpdate = (
    Struct()
    .add_member("next_addr", Addr)
    .add_member("action_addr", Addr)
    .add_member("expected_id", CoherentId)
    .add_member("not_last", Logic(1))
    .align_to_bits(32)
)

Action = (
    Struct()
    .add_member("symbol", Logic(64))
    .add_member("price", Logic(64, signed=True))
    .add_member("volume", Logic(64, signed=True))
    .add_member("side", Logic(1))
    .add_member("order_type", Logic(2))
    .add_member("life_time", Logic(2))
)

ActionTableUpdate = (
    Struct()
    .add_member("stored_id", CoherentId)
    .add_member("action", Action)
    .align_to_bits(32)
)
