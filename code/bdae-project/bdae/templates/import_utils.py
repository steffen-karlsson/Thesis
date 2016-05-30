# Created by Steffen Karlsson on 03-31-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from inspect import getmembers, isfunction, isbuiltin
from logging import warn


def map_function_binder(new_name, py_fun):
    def _wrapped_py_fun(blocks, args):
        for block in blocks:
            if args is None:
                yield py_fun(block)
            else:
                yield py_fun(block, *args)

    _wrapped_py_fun.__name__ = new_name
    return _wrapped_py_fun


def reduce_function_binder(new_name, py_fun):
    def _wrapped_py_fun(blocks, args):
        if args is None:
            return py_fun(blocks)

        return py_fun(blocks, *args)

    _wrapped_py_fun.__name__ = new_name
    return _wrapped_py_fun


def module_binder(module, func_binder, funs, new_fun_names=None):
    wrapped_functions = []
    desired_functions = [o for o in getmembers(module) if (isfunction(o[1]) or isbuiltin(o[1])) and o[0] in funs]

    use_original_names = not new_fun_names or len(desired_functions) != len(new_fun_names)
    if use_original_names:
        warn("New names are not used, since the count isn't equal to number of desired functions")

    for idx, (name, fun) in enumerate(desired_functions):
        if not use_original_names:
            name = new_fun_names[idx]
        wrapped_functions.append(func_binder(name, fun))

    return wrapped_functions
