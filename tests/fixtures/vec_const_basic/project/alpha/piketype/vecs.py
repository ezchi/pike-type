from piketype.dsl import Const, VecConst

A = Const(5)
B = VecConst(width=8, value=A * 3, base="dec")
LP_ETHERTYPE_VLAN = VecConst(width=16, value=0x8100, base="hex")
LP_IP_PROTOCOL_TCP = VecConst(width=8, value=6, base="dec")
LP_IP_PROTOCOL_UDP = VecConst(width=8, value=17, base="dec")
LP_NIBBLE_F = VecConst(width=4, value=0xF, base="hex")
LP_PADDED_HEX = VecConst(width=8, value=0x0F, base="hex")
LP_PADDED_BIN = VecConst(width=8, value=0xF, base="bin")
LP_AB16 = VecConst(width=16, value=0xAB, base="hex")
