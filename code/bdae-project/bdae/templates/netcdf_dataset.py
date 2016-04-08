# Created by Steffen Karlsson on 03-31-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta

from netCDF4 import Dataset

from bdae.collection import AbsDatasetCollection


class NetCDFDatasetCollection(AbsDatasetCollection):
    __metaclass__ = ABCMeta

    def preprocess(self, data_ref):
        dataset = Dataset(data_ref)
        for identifier in dataset.variables.keys() if self.use_all_identifiers() else self.get_identifiers():
            yield identifier, dataset.variables[identifier][:]
