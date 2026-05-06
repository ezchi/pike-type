from piketype.dsl import Struct

from dir0.piketype.a import a_t

b_t = Struct().add_member("a", a_t)
