import sys

from piketype.dsl import Const

# `for` is a Python hard keyword and cannot be used as a binding name with
# normal syntax (`for = Const(3)` is a syntax error). The freeze step walks
# `module.__dict__` and accepts any binding name, including hard keywords —
# so we install the binding via `setattr`/`__dict__` to exercise the
# keyword-validator's constant pathway with the AC-5 example identifier.
sys.modules[__name__].__dict__["for"] = Const(3)
