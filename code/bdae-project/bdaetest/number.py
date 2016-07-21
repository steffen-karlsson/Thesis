# Created by Steffen Karlsson on 07-21-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from unittest import TestCase, main

from numpy import empty, asarray, sum as npsum

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist
from bdae.templates.number_dataset import NumpyArrayDataset
from sofa.error import DatasetAlreadyExistsException
from sofa.foundation.operation import OperationContext

M = 100
N = 100
n = 1


# Data generators

def generate_scientific_dataset(number, m, n):
    data = empty((n, m))
    data[:] = number
    return data


def number_test_operations(context):
    return [
        OperationContext.by(context, "element count", "[element_sum, same]"),
        OperationContext.by(context, "global count", "[sum, sum]")
    ]


def element_sum(blocks, axis):
    return [npsum(block, axis) for block in sum(blocks, [])]


def same(blocks):
    return blocks[0][0] if all(len(set(block)) == 1 for block in blocks) else -1


# Datasets


class ExampleNumberDataset(NumpyArrayDataset):
    def get_operations(self):
        return number_test_operations(self)

    def get_reduce_functions(self):
        return NumpyArrayDataset.get_reduce_functions(self) + [same]

    def get_map_functions(self):
        return NumpyArrayDataset.get_map_functions(self) + [element_sum]

    def preprocess(self, data_ref):
        return asarray(data_ref)

    def next_entry(self, data):
        yield data


# Test cases


class NumberTest(TestCase):
    def setUp(self):
        self._manager = PyBDAEManager("sofa:textdata:gateway:0")
        self._scientist = PyBDAEScientist("sofa:textdata:gateway:0")

        try:
            self._manager = PyBDAEManager("sofa:textdata:gateway:0")
            self._manager.create_dataset(ExampleNumberDataset("numbers", description="a lot of the same numbers"))
            self._manager.append_to_dataset("numbers", generate_scientific_dataset(n, M, N).tolist())
        except DatasetAlreadyExistsException:
            pass

    def test_gloabl_count(self):
        def callback(res):
            self.assertEqual(res, M * N * n)

        self._scientist.submit_job("numbers", "global count", [], callback=callback)

    def test_element_count(self):
        def callback(res):
            self.assertNotEqual(res, -1)  # -1 means error
            self.assertEqual(res, M * n)

        self._scientist.submit_job("numbers", "element count", [1], callback=callback)


if __name__ == '__main__':
    main()
