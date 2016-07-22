# Created by Steffen Karlsson on 05-30-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist

from bdae.templates.netcdf_dataset import NetCDFDatasetCollection
from bdaeexamples.netcdf_numpy import NetCDFNumpyDataset

LINK = "/home/steffenkarlsson/Downloads/pop.nc"


class PopDatasetCollection(NetCDFDatasetCollection):
    def get_dataset_type(self, identifier):
        if identifier == 'TEMP':
            return NetCDFNumpyDataset(name='pop-temperature')

    def get_operations(self):
        return []

    def get_identifiers(self):
        return ['TEMP']


if __name__ == '__main__':
    manager = PyBDAEManager("sofa:textdata:gateway:0")
    manager.initialize_collection(PopDatasetCollection(name='pop'), with_new_data=LINK)


    def callback(res):
        print res


    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("pop-temperature", "count", [(0, 1, 2)], callback=callback)
