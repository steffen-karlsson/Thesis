# Created by Steffen Karlsson on 04-05-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: absdatasetcollection
"""

from abc import abstractmethod, ABCMeta

from sofa.foundation.base import SofaBaseObject


class AbsDatasetCollection(SofaBaseObject):
    """
    Abstract and not initializable class to define a collection of datasets.
    """

    __metaclass__ = ABCMeta

    def __init__(self, name=None, description=None):
        super(AbsDatasetCollection, self).__init__("collection:%s" % name if name else None, description)

    @abstractmethod
    def get_dataset_type(self, identifier):
        """
        Returns the class type implementing :class:`.AbsDatasetContext` matching the identifier (i.e. variable name in netcdf or hdf5 context)

        :param identifier:
        :type identifier: str
        :return: Class type implementing :class:`.AbsDatasetContext`
        """
        pass

    def get_identifiers(self):
        """
        :return: List of identifiers (to be stored) and available, default: None = all
        """
        return None

    def use_all_identifiers(self):
        return self.get_identifiers() is None

    def next_entry(self, data):
        # Not needed for dataset collection
        pass
