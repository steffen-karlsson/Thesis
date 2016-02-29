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
    def get_map_functions(self):
        """
        Defining the map operations

        :return: instance type of :class:`.AbsMapManager`
        """
        pass

    @abstractmethod
    def get_reduce_functions(self):
        """
        Defining the reduce operations

        :return: instance type of :class:`.AbsReduceManager`
        """
        pass

    @abstractmethod
    def get_operation_functions(self):
        """
        An operation is a function combining a map and a reduce function to be queried from ex. in the HTML interface.

        :return: instance type of :class:`.AbsOperationManager`
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
