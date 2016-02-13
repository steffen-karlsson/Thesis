# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: absdatasetcontext
"""


from abc import abstractmethod

class AbsDatasetContext:
    """
    Abstract and not initializable class to define the context of a dataset by overriding it.
    """

    _PRIVATE = "You should not create an instance yourself"

    _identifier = None

    def __init__(self, token):
        if token is not self._PRIVATE:
            raise NotImplemented(self._PRIVATE)

    @abstractmethod
    def get_map_functions(self):
        pass

    @abstractmethod
    def get_reduce_functions(self):
        pass

    @abstractmethod
    def get_operations_functions(self):
        pass

    @abstractmethod
    def next_entry(self):
        pass

    @staticmethod
    def _initialize(identifier):
        cls = AbsDatasetContext(AbsDatasetContext._PRIVATE)
        cls._identifier = identifier
        return cls
