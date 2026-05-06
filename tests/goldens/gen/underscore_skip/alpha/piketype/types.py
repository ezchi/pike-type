from piketype.dsl import Struct

from alpha.piketype._helper import shared_t

main_t = Struct().add_member("v", shared_t)
