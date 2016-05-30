# Created by Steffen Karlsson on 05-30-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta, abstractmethod
from math import floor


class Dispatcher:
    __metaclass__ = ABCMeta

    def __init__(self, my_idx, key_space_size):
        self.__my_idx = my_idx
        self.__key_space_size = key_space_size

    @abstractmethod
    def get_responsible(self, index):
        pass

    def me(self):
        return self.__my_idx

    def get_key_space(self):
        return self.__key_space_size


def dispatch(func):
    def func_wrapper(*args):
        context = args[0]
        if not isinstance(context, Dispatcher):
            raise AttributeError("self has to be of type Dispatcher")

        # Check whether its self who is responsible
        identifier = args[1]
        responsible_idx = int(floor(identifier / context.get_key_space()))

        if context.me() == responsible_idx:
            # My self to handle the data
            return func(*args)

        responsible = context.get_responsible(responsible_idx)
        return getattr(responsible, func.__name__)(*args[1:])

    return func_wrapper
