# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from marshal import dumps, loads
from types import FunctionType
from hashlib import sha256
from imp import load_source


def serialize(fun, args):
    return fun.__name__, dumps(fun.func_code), args


def deserialize(bundle):
    name, fun, args = bundle
    fun_code = loads(fun)
    return FunctionType(fun_code, globals(), name), args


def find_identifier(name):
    return sha256(name).hexdigest()


def import_class(cls):
    d = cls.rfind(".")
    classname = cls[d + 1:]
    m = __import__(cls[0:d], globals(), locals(), [classname])
    return getattr(m, classname)


def import_class_from_source(source_file, cls_name):
    mod = load_source(cls_name, source_file)
    if not hasattr(mod, cls_name):
        return None

    return getattr(mod, cls_name)
