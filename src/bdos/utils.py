from marshal import dumps, loads
from types import FunctionType
from hashlib import sha256

# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.


def serialize(fun, args):
    return fun.__name__, dumps(fun.func_code), args


def deserialize(bundle):
    name, fun, args = bundle
    fun_code = loads(fun)
    return FunctionType(fun_code, globals(), name), args


def find_identifier(name):
    return sha256(name).hexdigest()
