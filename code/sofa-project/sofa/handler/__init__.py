# Created by Steffen Karlsson on 02-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from re import compile

CLASS_PATTERN = compile("\'(.*?)\'")


def import_class(cls):
    package, classname = split_class_path(cls)
    m = __import__(package, globals(), locals(), [classname])
    return getattr(m, classname)


def split_class_path(path):
    return path.rsplit(".", 1)


def get_class_from_path(path):
    if path is None:
        return None

    package = CLASS_PATTERN.findall(str(path))[0]
    return split_class_path(package)[1]


def get_function_from_source(source, func_name):
    def __load():
        return globals()[func_name]

    try:
        return __load()
    except AttributeError:
        exec (source, globals())
        return __load()


def get_class_from_source(source, cls_name):
    def __instantiate():
        return eval("%s()" % cls_name)

    try:
        return __instantiate()
    except NameError:
        exec (source, globals())
        return __instantiate()


def unique_and_preserve(data):
    return list(sorted(set(data), key=lambda x: data.index(x)))
