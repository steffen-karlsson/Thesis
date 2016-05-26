# Created by Steffen Karlsson on 04-07-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: sofabasetyoe
"""

from abc import abstractmethod, ABCMeta
from sofa.handler.storage import KEYWORDS
from strategy import RoundRobin

class SofaBaseObject:
    """
    Abstract and not initializable class to define the context of a fundamental base sofa object
    """
    __metaclass__ = ABCMeta

    def __init__(self, name=None, description=None):
        self.__name = name
        self.__description = description

    def get_name(self):
        return self.__name

    def get_description(self):
        return self.__description

    @abstractmethod
    def preprocess(self, data_ref):
        """
        Define how to load the object (if needed) from the specified local path or url in the Gateway append method,
        it's recommended to implement load as a generator i.e. yield, since its supported and memory saving.

        :param data_ref: The actual data, local path or url to the data
        :type data_ref: str or data
        """
        pass

    @abstractmethod
    def get_operations(self):
        """
        Returns a list of available :class:`.OperationContext` on executable on the object: with function display name
        and operations as a :class:`.SequentialOperation`, which is a complex object with two or more functions,
        in sequential or :class:`.ParallelOperation` order, with the last element being a reduce function.

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

    def get_distribution_strategy(self):
        """
        Method to override in order to define a new distribution strategy from default e.g. Round Robin.
        NB! If number of storage nodes in the system is one, then this is ignored.

        :return: :class:`.RoundRobin`, :class:`.Tiles` or :class:`.Linear`
        """
        return RoundRobin()

    @abstractmethod
    def verify_function(self, function_name):
        """
        Only applicable for objects implementing get_operations!
        Return the function if its valid function_name or None

        :param function_name: Name of a function when instantiating and verifying operations
        :type function_name: str
        :return: function if its valid function_name or None
        """
        return function_name if any([keyword.findall(function_name) for keyword in KEYWORDS]) else None


def load_data_by_url(url):
    from urllib2 import urlopen
    from contextlib import closing

    with closing(urlopen(url)) as f:
        return f.read()


def load_data_by_path(path):
    from contextlib import closing

    with closing(open(path)) as f:
        return f.read()
