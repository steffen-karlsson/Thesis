# Created by Steffen Karlsson on 04-08-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta
from msgpack import packb, unpackb
from msgpack_numpy import encode, decode

import numpy

from bdae.templates.import_utils import map_function_binder, module_binder, reduce_function_binder
from bdae.dataset import AbsMapReduceDataset


class NumpyArrayDataset(AbsMapReduceDataset):
    __metaclass__ = ABCMeta

    def serialize(self, data):
        return packb(data, default=encode)

    def deserialize(self, data):
        if isinstance(data, unicode):
            data = data.encode("ascii")

        return unpackb(data, object_hook=decode)

    def is_serialized(self):
        return True

    def get_map_functions(self):
        return module_binder(numpy, map_function_binder, ['floor', 'ceil', 'round', 'sum'])

    def get_reduce_functions(self):
        return module_binder(numpy, reduce_function_binder, ['min', 'max', 'add.reduce', 'average'])\
               + module_binder(numpy, reduce_function_binder, ['sum'], ['rsum'])
