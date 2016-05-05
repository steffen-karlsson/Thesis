# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: absdatasetcontext
"""

from abc import abstractmethod, ABCMeta

from sofa.foundation.base import SofaBaseObject


class AbsMapReduceDataset(SofaBaseObject):
    """
    Abstract and not initializable class to define the context of a dataset by overriding it.
    """

    __metaclass__ = ABCMeta

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

    def verify_function(self, function_name):
        function_map = {func.func_name: func for func in self.get_reduce_functions()}
        function_map.update({func.func_name: func for func in self.get_map_functions()})
        return function_map[function_name] if function_name in function_map else None
