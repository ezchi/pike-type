from piketype.dsl import Struct

from dir0.piketype.a import a_t
from dir1.piketype.b import b_t

c_t = Struct().add_member("a", a_t).add_member("b", b_t)
