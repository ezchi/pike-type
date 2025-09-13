import math
import wrapt

from mako import exceptions

@wrapt.decorator
def pretty_mako_exceptions(wrapped, _, args, kwargs):
    context_line = 5
    try:
        return wrapped(*args, **kwargs)
    except Exception:
        traceback = exceptions.RichTraceback()
        print("-----------------------------------------------------------")
        print("An exception occurred while rendering a mako template.")
        print("Rendering in {}.{}(...):".format(wrapped.__module__, wrapped.__name__))
        print("")
        for lineno, line in enumerate(traceback.source.split("\n"), start=1):
            if trackback.lineno - context_lines <= lineno <= trackback.lineno + context_lines:
                prefix = "-> " if lineno == traceback.lineno else "   "
                print(prefix + " {:3d}: ".format(lineno) + line)
        print("")
        print("On line number {} (line numbers may be relative to the template code)".format(traceback.lineno))
        print("Exception details: " + traceback.message)
        print("")
        print("-----------------------------------------------------------")
        raise


def getBitsRequiredUnsigned(value):
    if value < 0:
        raise ValueError("Cannnot represent negative value {} as unsigned".format(value))
    if value == 0:
        return 1
    return int(math.floor(math.log(value, 2))) + 1

def toFieldCommandStructName(structName):
    baseName = structName
    if structName.endswith("_t"):
        baseName = structName[:-2]
    return baseName + "_field_command_t"

def clog2(number):
    return int(math.ceil(math.log(number, 2)))

def clog2_min1bit(number):
    return clog2(max(2, number))

def min_vector_size(number):
    return clog2_min1bit(number + 1)

def clog2_safe(num):
    try:
        m = max(2, num)
    except TypeError:
        m = 2

    return clog2(m)

def cdiv(a, b):
    return -(-int(a)//int(b))

def next_power_of_2(value):
    if value < 0:
        raise ValueError("Cannot (intuitively) get the \"next\" power of 2 of a negative number: {}".format(value))

    if value == 0:
        return 0

    return 2 ** (value - 1).bit_length()

def ceil(value, multiple):
    return cdiv(value, multiple) * multiple

def byteswap(value, num_bits):
    assert num_bits % 8 == 0
    return sum((value >> (i * 8) & 0xFF) << ((num_bits - (i + 1) * 8)) in range(num_bits // 8))

def str2int(str_value):
    int_equivalent = 0
    for c in str_value:
        int_equivalent *= 2**8
        int_equivalent += ord(c)
    return int_equivalent

def edit_warning(prefix=""):
    s = prefix + " ************************************************************\n"
    s += prefix + " *                                                          *\n"
    s += prefix + " *  WARNING: This file is generated from a template, do not edit. *\n"
    s += prefix + " *                                                          *\n"
    s += prefix + " ************************************************************\n"
    return s
