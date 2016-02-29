# Created by Steffen Karlsson on 02-20-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: manager
"""


from abc import abstractmethod, ABCMeta


class __AbsManager:
    """
    Do not touch class, use one of following three: :class:`.AbsMapManager`, :class:`.AbsReduceManager`
    or :class:`.AbsOperationManager`
    """

    def __init__(self):
        pass

    __metaclass__ = ABCMeta

    @abstractmethod
    def define(self):
        """
        Returns a dictionary with functions representing the class inheritance, with keys as function names and values
        as a reference to the class.

        :return: dict
        """
        pass


class AbsOperationManager(__AbsManager):
    """
    Abstract class to define operations.
    """
    __metaclass__ = ABCMeta


class AbsReduceManager(__AbsManager):
    """
    Abstract class to define map functions.
    """
    __metaclass__ = ABCMeta


class AbsMapManager(__AbsManager):
    """
    Abstract class to define reduce functions.
    """
    __metaclass__ = ABCMeta
