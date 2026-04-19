from typist.dsl import Bit, Const, Logic

W = Const(13)
addr_t = Bit(W)
mask_t = Logic(8, signed=True)
flag_t = Bit(1)
