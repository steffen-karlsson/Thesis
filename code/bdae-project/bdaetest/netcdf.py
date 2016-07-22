# Created by Steffen Karlsson on 07-21-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from os import getcwd
from os.path import exists
from unittest import TestCase, main

from netCDF4 import Dataset
from numpy import empty

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist
from bdae.templates.netcdf_dataset import NetCDFDatasetCollection
from bdaetest.number import ExampleNumberDataset
from sofa.error import DatasetAlreadyExistsException

M = 100


# Data generators

def generate_scientific_dataset(numbers, m):
    if exists('test.nc'):
        return

    test_dataset = Dataset('test.nc', 'w', format='NETCDF3_64BIT')
    test_dataset.createDimension('M', m)

    for number, name in numbers:
        array = test_dataset.createVariable(name, 'i4', ('M', 'M'))
        np_array = empty((m, m))
        np_array[:] = number
        array[:, :] = np_array


# Datasets


class ExampleNetCDFCollection(NetCDFDatasetCollection):
    def get_operations(self):
        return []

    def get_dataset_type(self, identifier):
        return ExampleNumberDataset(identifier)

    def get_identifiers(self):
        return ["ones", "twos", "threes"]


# Test cases


class NetCDFTest(TestCase):
    def setUp(self):
        generate_scientific_dataset([(1, "ones"), (2, "twos"), (3, "threes")], M)

        self._manager = PyBDAEManager("sofa:textdata:gateway:0")
        self._scientist = PyBDAEScientist("sofa:textdata:gateway:0")

        try:
            self._manager = PyBDAEManager("sofa:textdata:gateway:0")
            self._manager.initialize_collection(ExampleNetCDFCollection(name="netcdf"),
                                                with_new_data=getcwd() + '/test.nc')
        except DatasetAlreadyExistsException:
            pass

    def submit_global_count_job(self, dataset, callback):
        self._scientist.submit_job(dataset, "global count", [], callback=callback)

    def test_ones_sum(self):
        def callback(res):
            self.assertEqual(int(res), M * M * 1)

        self.submit_global_count_job("ones", callback)

    def test_twos_sum(self):
        def callback(res):
            self.assertEqual(int(res), M * M * 2)

        self.submit_global_count_job("twos", callback)

    def test_threes_sum(self):
        def callback(res):
            self.assertEqual(int(res), M * M * 3)

        self.submit_global_count_job("threes", callback)

    def test_combined_sum(self):
        combined_res = []

        def validate_results():
            if len(combined_res) != 3:
                return

            self.assertEqual(sum(combined_res), M * M * (1 + 2 + 3))

        def callback(res):
            combined_res.append(int(res))
            validate_results()

        self.submit_global_count_job("ones", callback)
        self.submit_global_count_job("twos", callback)
        self.submit_global_count_job("threes", callback)


if __name__ == '__main__':
    main()
