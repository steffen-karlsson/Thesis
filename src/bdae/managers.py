# Created by Steffen Karlsson on 02-20-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import abstractmethod, ABCMeta


class __AbsManager:
    def __init__(self):
        pass

    __metaclass__ = ABCMeta

    @abstractmethod
    def define(self):
        pass


class AbsOperationManager(__AbsManager):
    __metaclass__ = ABCMeta


class AbsReduceManager(__AbsManager):
    __metaclass__ = ABCMeta


class AbsMapManager(__AbsManager):
    __metaclass__ = ABCMeta
