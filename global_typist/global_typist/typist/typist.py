from __future__ import print_function
from six import with_metaclass

import inspect
import os
import wrapt
import collections

allNameSpaceTypes = set()
allNameSpaces = collections.OrderedDict()

def allNameSpacesToIRDict():
    importTypistCoreDefinitions()
    checkAllNameSpaces()
    return collections.OrderedDict(
        [(name, namespace.toIRDict()) for (name, namespace) in allNameSpaces.items()]
        )

def importTypistCoreDefinitions():
    import global_typist.typist.primitives

def checkAllNameSpaces():
    unmatchedNameSpaces = allNameSpacesTypes.copy()
    for name, ns in allNameSpaces.items():
        if not isinstance(ns, NameSpace):
            raise TypeError("Item {} in allNameSpaces is not a NameSpace class".format(name))

        if name not in allNameSpacesTypes:
            raise KeyError("Item {} in allNameSpaces is not in the list of namespaces classes defined - are you doing something wrong?".format(name))

        if name not in unmatchedNameSpaces:
            raise KeyError("Item {} is instantiated twice - are you doing something wrong?".format(name))

        unmatchedNameSpaces.remove(name)

    if len(unmatchedNameSpaces) != 0:
        raise KeyError("Some NameSpace ({}) were defined but not instantiated. Did you omit the instantiation 'namespace = {}()' at the end of your file?".format(", ".join([name for bame in unmatchedNameSpaces]), list(unmatchedNameSpaces)[0]))

def insertBefore(dest, before, item):
    pos = list(dest.keys()).index(before)
    items = list(dest.items())
    items.insert(pos, item)
    dest = collections.OrderedDict(items)
    return dest

class NameSpaceType(type):
    def __new__(cls, name, bases, attrs):
        if name != "NameSpace":
            allNameSpaceTypes.add(name)
        return type.__new__(cls, name, bases, attrs)

class NameSpace(with_metaclass(NameSpaceType, object)):
    def __init__(self, libraryName):
        self.libraryName = libraryName
        self.name = self.__class__.__name__
        self.definedAt = os.path.relpath(inspect.getsourcefile(self.__class__))
        self.members = collections.OrderedDict()
        self.add_inertnal = False
        self.create()
        self.add_internal = True
        self.create_internal()

        if self.name in allNameSpaces:
            raise NameError("Duplicate definition of NameSpace {}".format(self.name))
        allNameSpaces[self.name] = self

    def create(self):
        raise NotImplementedError("NameSpace {} must override create(self) to do anything useful".format(self.name))

    def create_internal(self):
        pass

    def typistDefinition(self):
        for name, m in self.members.items():
            yield (name, m)

    def addMember(self, name, value, beforeName=None):
        if name in self.members:
            raise NameError("Duplicate definition of {} in NameSpace {}".format(name, self.name))
        if value.isNamedType():
            raise ValueError("Type added multiple times: {} and {}.{}. Did you mean to use primitives.Typedef()?".format(value.fullTypeName(), self.name, name))

        value.type_name = name
        value.namespace = self

        if self.add_internal:
            value.associations["internal"] = True

        if beforeName is None:
            self.members[name] = value
        else:
            if beforeName not in self.members:
                raise KeyError("Tried to add type {} to NameSpace {} before type {}, but that type does not exist".format(name, self.name, beforeName))
            self.members = insertBefore(self.members, beforeName, (name, value))

        if hasattr(value, 'isErrorStruct') and value.isErrorStruct():
            for subset_name, subset in value.getErrorSubsets(base_type=name):
                self.addMember(subset_name, subset)

    def __setattr__(self, name, value):
        if isinstance(value, TypistDef):
            self.addMember(name, value)
        else:
            if hasattr(self, 'members') and name in self.members:
                raise ValueError("Tried to add property {} to NameSpace {}, but it's already defined as a type".format(name, self.name))
        object.__setattr__(self, name, value)

    def toIRDict(self):
        return {
            "definedAt": self.definedAt,
            "libraryName": self.libraryName,
            "members": collections.OrderedDict(
                [(name, m.toIRDict()) for (name, m) in self.members.items()]
                )
            }

class TypistDef(object):
    def __init__(self):
        self.type_name = None
        self.namespace = None

    def isNamedType(self):
        return self.type_name is not None and self.namespace is not None

    def fullTypeName(self):
        if not self.isNamedType():
            return "<Anonymous {}>".format(self.__class__.__name__)
        return "{}.{}".format(self.namespace.name, self.type_name)

    def toIRDict(self):
        raise NotImplementedError("Subclasses of TypistDef must implemented toIRDict")

    @staticmethod
    def _checkIsNamedType(instance, functionName, isNamedType):
        if instance is None or not isinstance(instance, TypistDef):
            raise TypeError("TypistDef.mutating or TypistDef.finalOnly decorator should only be applied to member functions of TypistDef derived types, not type {}".format(type(instance)))

        if instance.isNamedType() != isNamedType:
            raise RuntimeError("Attemped to call function {} {} type definition {} was finalized by adding it to a namespace".format(functionName, "before" if isNamedType else "after", instance.fullTypeName()))

    @staticmethod
    @wrapt.decorator
    def mutating(wrapped, instance, args, kwargs):
        TypistDef._checkIsNamedType(instance, wrapped.__name__, False)
        return wrapped(*args, **kwargs)

    @staticmethod
    @wrapt.decorator
    def namedTypeOnly(wrapped, instance, args, kwargs):
        TypistDef._checkIsNamedType(instance, wrapped.__name__, True)
        return wrapped(*args, **kwargs)
