# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: absdatasetcontext
"""

from abc import abstractmethod, ABCMeta


class AbsDatasetContext:
    """
    Abstract and not initializable class to define the context of a dataset by overriding it.
    """

    def __init__(self):
        pass

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_operations(self):
        """
        Returns a list of :class:`.Function` with function display name and operations as a
        :class:`.SequentialOperation`, which is a complex object with two or more functions, in sequential or
        :class:`.ParallelOperation` order, with the last element being a reduce function.

        :return: list
        """
        pass

    @abstractmethod
    def get_map_functions(self):
        """
        Returns a list of appropriate map functions for this dataset

        :return: list
        """
        pass

    @abstractmethod
    def get_reduce_functions(self):
        """
        Returns a list of appropriate reduce functions for this dataset

        :return: list
        """
        pass

    @abstractmethod
    def next_entry(self, data):
        """
        Abstract method to override when implementing a new AbsDatasetContext implementation.

        Yields:
            A requirement for the method is to implement a generator.

        :param data: The full dataset
        """
        pass

    def get_block_stride(self):
        """
        Method to override in order to define a stride for the block distribution different from default e.g. 1.
        NB! If number of storage nodes in the system is one, then this is ignored.

        :return: int
        """
        return 1
