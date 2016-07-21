# Created by Steffen Karlsson on 07-20-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from unittest import TestCase, main
from abc import ABCMeta, abstractmethod
from functools import partial

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist
from bdae.templates.text_dataset import TextDataByLine, TextDataByWord
from sofa.foundation.operation import OperationContext
from sofa.error import DatasetAlreadyExistsException

M = 10
N = 10
L = 'a'


# Data generators

def generate_scientific_dataset(letter, delimitter, m, n):
    return delimitter.join([" ".join([letter * i for i in xrange(1, m + 1)]) for _ in xrange(1, n + 1)])


def text_test_operations(context):
    return [
        OperationContext.by(context, "letters", "[modify:combining, count_occurrences, sum]"),
        OperationContext.by(context, "lines", "[len, sum]"),
        OperationContext.by(context, "words", "[len, sum]")
    ]


# Datasets


class ExampleTextLineDataset(TextDataByLine):
    def preprocess(self, data_ref):
        return data_ref

    def get_operations(self):
        return text_test_operations(self)


class ExampleTextWordDataset(TextDataByWord):
    def preprocess(self, data_ref):
        return data_ref

    def get_operations(self):
        return text_test_operations(self)


def combining(blocks):
    return " ".join([block for block in sum(blocks, [])])


# Test cases


class ABCTextTest(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self._scientist = PyBDAEScientist("sofa:textdata:gateway:0")
        self._manager = PyBDAEManager("sofa:textdata:gateway:0")

    def set_up(self):
        try:
            self._manager.create_dataset(self.get_dataset())
            self._manager.append_to_dataset(self.get_dataset_name(), generate_scientific_dataset(L, "\n", M, N))
        except DatasetAlreadyExistsException:
            pass

    def wrapper_test_number_of_letters(self, assertEqual):
        def callback(res):
            assertEqual(res, N * sum(range(1, M + 1)))

        self._scientist.submit_job(self.get_dataset_name(), "letters", "a", callback=callback)

    @abstractmethod
    def get_dataset(self):
        pass

    @abstractmethod
    def get_dataset_name(self):
        return ""


class TextByLineTest(TestCase, ABCTextTest):
    def setUp(self):
        ABCTextTest.__init__(self)
        ABCTextTest.set_up(self)

    def get_dataset_name(self):
        return "a-line"

    def get_dataset(self):
        return ExampleTextLineDataset("a-line", description="Test dataset with a lot of a's")

    def test_number_of_letters(self):
        ABCTextTest.wrapper_test_number_of_letters(self, partial(TestCase.assertEqual, self))

    def test_number_of_lines(self):
        def callback(res):
            self.assertEqual(res, N)

        self._scientist.submit_job(self.get_dataset_name(), "lines", [], callback=callback)


class TextByWordTest(TestCase, ABCTextTest):
    def setUp(self):
        ABCTextTest.__init__(self)
        ABCTextTest.set_up(self)

    def get_dataset_name(self):
        return "a-word"

    def get_dataset(self):
        return ExampleTextWordDataset("a-word", description="Test dataset with a lot of a's")

    def test_number_of_letters(self):
        ABCTextTest.wrapper_test_number_of_letters(self, partial(TestCase.assertEqual, self))

    def test_number_of_words(self):
        def callback(res):
            self.assertEqual(res, N*M)

        self._scientist.submit_job(self.get_dataset_name(), "words", [], callback=callback)


if __name__ == '__main__':
    main()
