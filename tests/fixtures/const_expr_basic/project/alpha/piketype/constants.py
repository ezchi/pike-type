from piketype.dsl import Const

A = Const(3)
B = Const(A + 5)
C = Const((A << 2) | 1)
D = Const(-A)
E = Const(~A)
