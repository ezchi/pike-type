import collections
import enum
import inspect
import copy
import warnings

from . import utils
from .typist import TypistDef, NameSpace

class DataChunk(TypistDef):
    def __init__(self):
        self.associations = {}
        self.primitive_type = self.__class__.__name__
        super(DataChunk, self).__init__()

    def getWidth(self):
        return self._getMinWidth()

    def getAlignedWidth(self):
        return self._calculateStructAlignedSize()

    def isAddCommandCompatible(self):
        return False

    def isErrorStruct(self):
        return False

    def getFieldCommand(self):
        self.associations["field_command_type"] = namespace.field_command_t.getTyperef()
        return namespace.field_command_t

    def _getMinWidth(self):
        raise NotImplementedError("Subclasses of DataChunk must implement _getMinWidth()")

    def _calculateStructAlignedSize(self):
        return max(0, utils.next_power_of_2(self.getWidth()))

    def getTyperef(self):
        if self.isNamedType():
            return {"namespace": self.namespace.name, "reference": self.type_name}
        else:
            return self.toIRDict()

    def toIRDict(self):
        return {
            "type": self.primitive_type,
            "width": self.getWidth(),
            "aligned_width": self.getAlignedWidth(),
            "associations": self.associations,
            }

    def setRegAddress(self, address):
        self.associations["reg_address"] = address
        return self

class PaddableDataChunk(DataChunk):
    def __init__(self):
        self.maxSize = None
        self.padToBitMultiple = 1
        self.maxAlignedSize = None
        self.padAlignedBitMultiple = 1
        super(PaddableDataChunk, self).__init__()

    def getWidth(self):
        unpaddedWith = self._getMinWidth()
        paddedWith = utils.ceil(unpaddedWith, self.padToBitMultiple)
        if self.maxSize is not None and paddedWith > self.maxSize:
            raise RuntimeError(f"{self.fullTypeName()} is too large ({unpaddedWith} bits, {paddedWith} after padding) for its max size requirement ({self.maxSize} bits)")
        return paddedWith

    def getAlignedWidth(self):
        unpaddedWith = self._calculateStructAlignedSize()
        paddedWith = utils.ceil(unpaddedWith, self.padAlignedBitMultiple)
        if self.maxAlignedSize is not None and paddedWith > self.maxAlignedSize:
            raise RuntimeError(f"{self.fullTypeName()} is too large ({unpaddedWith} bits, {paddedWith} after padding) for its max aligned size requirement ({self.maxAlignedSize} bits)")
        return paddedWith

    def _getMinWidth(self):
        raise NotImplementedError("Subclasses of PaddableDataChunk must implement _getMinWidth()")

    def _finalTypeBits(self):
        return False

    @TypistDef.mutating
    def padToMultiple(self, bits):
        self.maxSize = None
        self.padToBitMultiple = bits
        return self

    @TypistDef.mutating
    def padToSize(self, sizeBits):
        self.maxSize = sizeBits
        self.padToBitMultiple = sizeBits
        return self

    @TypistDef.mutating
    def padToAlignedMultiple(self, bits):
        self.maxAlignedSize = None
        self.padAlignedBitMultiple = bits
        return self

    @TypistDef.mutating
    def padToAlignedSize(self, sizeBits):
        self.maxAlignedSize = sizeBits
        self.padAlignedBitMultiple = sizeBits
        return self

class DataChunkMember(object):
    def __init__(self, item):
        self.item = item
        self.start_bit = 0
        self.start_bit_aligned = 0
        self.associations = {}

    def toIRDict(self):
        return {
            "typeref": self.item.getTyperef() if allowTyperefs else self.item.toIRDict(),
            "start_bit": self.start_bit,
            "start_bit_aligned": self.start_bit_aligned,
            "associations": self.associations,
            }

    def getLastBit(self):
        return self.start_bit + self.item.getWidth() - 1

    def getLastAlignedBit(self):
        return self.start_bit_aligned + self.item.getAlignedWidth() - 1

    def _calculateStructAlignedSize(self):
        return self.item.getAlignedWidth()

    def getAlignedWidth(self):
        return self._calculateStructAlignedSize()

    def _finalTypeBits(self):
        return self.item._finalTypeBits()

class Constant(TypistDef):
    def __init__(self, value, width=None):
        super(Constant, self).__init__()
        self.primitive_type = self.__class__.__name__
        self.value = getattr(value, "value", value)
        self.width = width if width is not None else int(width)
        self.associations = {}

    @property
    def v(self):
        return self.value

    def __index__(self):
        return int(self.value)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return True if self.value else False

    def __eq__(self, other):
        return self.value == getattr(other, "value", other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.value < getattr(other, "value", other)

    def __le__(self, other):
        return self.value <= getattr(other, "value", other)

    def __gt__(self, other):
        return self.value > getattr(other, "value", other)

    def __ge__(self, other):
        return self.value >= getattr(other, "value", other)

    def __add__(self, other):
        return self.value + getattr(other, "value", other)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.value - getattr(other, "value", other)

    def __rsub__(self, other):
        return -self.__sub__(other)

    def __mul__(self, other):
        return self.value * getattr(other, "value", other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        return self.value // getattr(other, "value", other)

    def __rdiv__(self, other):
        return getattr(other, "value", other) // self.value

    def __truediv__(self, other):
        return self.value / getattr(other, "value", other)

    def __rtruediv__(self, other):
        return getattr(other, "value", other) / self.value

    def __floordiv__(self, other):
        return self.value // getattr(other, "value", other)

    def __rfloordiv__(self, other):
        return getattr(other, "value", other) // self.value

    def __pow__(self, other):
        return self.value ** getattr(other, "value", other)

    def __rpow__(self, other):
        return getattr(other, "value", other) ** self.value

    def __mod__(self, other):
        return self.value % getattr(other, "value", other)

    def __rmod__(self, other):
        return getattr(other, "value", other) % self.value

    def __and__(self, other):
        return self.value & getattr(other, "value", other)

    def __rand__(self, other):
        return self.__and__(other)

    def __or__(self, other):
        return self.value | getattr(other, "value", other)

    def __ror__(self, other):
        return self.__or__(other)

    def __lshift__(self, other):
        return self.value << getattr(other, "value", other)

    def __rlshift__(self, other):
        return getattr(other, "value", other) << self.value

    def __rshift__(self, other):
        return self.value >> getattr(other, "value", other)

    def __rrshift__(self, other):
        return getattr(other, "value", other) >> self.value

    def __invert__(self):
        return ~self.value

    def toIRDict(self):
        self.checkValue()
        ir = {
            "type": self.primitive_type,
            "value": self.value,
            "associations": self.associations,
            }

        if self.width is not None:
            ir["width"] = self.width

        return ir

    def checkValue(self):
        if self.value is None:
            raise TypeError(f"Constant value is None for {self.fullTypeName()}")

class RegisterMode(str, enum.Enum):
    RW = "RW"
    RO = "RO"
    WO = "WO"
    RC = "RC"
    RS = "RS"
    WC = "WC"
    WS = "WS"
    RWC = "RWC"
    RWS = "RWS"

class RegisterType(str, enum.Enum):
    Single = "Single"
    Array = "Array"
    Struct = "Struct"

class RegisterInsterfaceMemmber(object):
    def __init__(self, item, numRegs, item, address, mode):
        self.regType = regType
        self.numRegs = numRegs
        self.item = item
        self.address = address
        self.mode = mode

        assert numRegs == 1 or self.RegType != RegisterType.Single, f"Expected numRegs = 1 but got '{numRegs}' for RegisterType.Single"

    def toIRDict(self):
        ir = {
            "reg_type": self.regType,
            "num_regs": self.numRegs,
            "typeref": self.item.getTyperef() if allowTyperefs else self.item.toIRDict(),
            "address": self.address,
            "mode": self.mode.value,
            }
        return ir

class RegisterInterfaceMember(object):
    def __init__(self, regType, numRegs, item, address, mode):
        self.regType = regType
        self.numRegs = numRegs
        self.item = item
        self.address = address
        self.mode = mode

        assert numRegs == 1 or self.regType != RegisterType.Single, f"Expected numRegs = 1 but got '{numRegs}' for RegisterType.Single"

    def toIRDict(self):
        ir = {
            "reg_type": self.regType,
            "num_regs": self.numRegs,
            "typeref": self.item.getTyperef(),
            "address": self.address,
            "mode": self.mode.value,
            }
        return ir

class NaturalRange(TypistDef):
    def __init__(self, value_left, value_right):
        super(NaturalRange, self).__init__()
        self.primitive_type = self.__class__.__name__
        self.value_left = getattr(value_left, "value", int(value_left))
        self.value_right = getattr(value_right, "value", int(value_right))

    def toIRDict(self):
        return {
            "type": self.primitive_type,
            "value_left": self.value_left,
            "value_right": self.value_right,
            }

class primitives(NameSpace):
    class MemSpaceLeaf(TypistDef):
        def __init__(self, data_type, num_elements, bus_width, is_densely_packed):
            assert bus_width % 8 == 0, f"Bus width must be a multiple of 8 bits, got {bus_width} bits"
            self.data_type = data_type
            self.num_elements = getattr(num_elements, "value", num_elements)
            self.bus_width = getattr(bus_width, "value", bus_width)
            self.is_densely_packed = is_densely_packed
            super(primitives.MemSpaceLeaf, self).__init__()

        def getTyperef(self):
            if self.isNamedType():
                return {"namespace": self.namespace.name, "reference": self.type_name}
            else:
                return self.toIRDict()

        def toIRDict(self):
            return {
                "type": "MemSpaceLeaf",
                "data_type": {"tperef": self.data_type.getTyperef()},
                "num_elements": self.num_elements,
                "bus_width": self.bus_width,
                "is_densely_packed": self.is_densely_packed,
                }

        def getAddrWidth(self):
            words_per_item = utils.next_power_of_2(utils.ceil(self.data_type.getWidth(), self self.bus_width))
            sizeof_packed_item = words_per_item * self.bus_width / 8
            sizeof_self = sizeof_packed_item * self.num_elements

            return utils.clog2_min1bit(sizeof_self)

    class MemSpaceBranch(TypistDef):
        def __init__(self):
            self.sections = {}
            super(primitives.MemSpaceBranch, self).__init__()

        def getTyperef(self):
            if self.isNamedType():
                return {"namespace": self.namespace.name, "reference": self.type_name}
            else:
                return self.toIRDict()

        def addSection(self, name, section, num_instances):
            assert name not in self.sections, f"Section '{name}' already exists in MemSpaceBranch"
            assert isinstance(section, primitives.MemSpaceLeaf) or num_instances == 1, "Cannot add multiple instances of a MemSpaceBranch"MemSpaceBranch
            self.sections[name] = (section, num_instances)
            return self

        def toIRDict(self):
            assert len(self.sections) > 0, "Cannot have a MemSpaceBranch with no subsections"
            sections = {name: {"typeref": section.getTyperef(), "num_instances": num_instances} for name, (section, num_instances) in self.sections.items()}
            return {
                "type": "MemSpaceBranch",
                "sections": sections,
                }

        def getAddrWidth(self):
            max_section_addr_width = 0
            total_subsections = 0
            for _, (section, num_instances) in self.sections.items():
                max_section_addr_width = max(section.getAddrWidth(), max_section_addr_width)
                total_subsections += num_instances
