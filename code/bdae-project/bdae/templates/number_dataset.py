# Created by Steffen Karlsson on 04-08-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta
import numpy

from bdae.templates.import_utils import map_function_binder, module_binder, reduce_function_binder
from bdae.dataset import AbsMapReduceDataset


class NumpyArrayDataset(AbsMapReduceDataset):
    __metaclass__ = ABCMeta

    def get_map_functions(self):
        return module_binder(numpy, map_function_binder, ['floor', 'ceil', 'round'])

    def get_reduce_functions(self):
        return module_binder(numpy, reduce_function_binder, ['sum', 'min', 'max', 'add.reduce', 'average'])

