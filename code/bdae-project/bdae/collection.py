# Created by Steffen Karlsson on 04-05-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: absdatasetcollection
"""

from abc import abstractmethod, ABCMeta


class AbsDatasetCollection:
    """
    Abstract and not initializable class to define a collection of datasets.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def get_dataset_type(self, identifier):
        """
        Returns the class type implementing :class:`.AbsDatasetContext` matching the
        identifier (i.e. variable name in netcdf or hdf5 context)

        :param identifier:
        :type identifier: str
        :return: Class type implementing :class:`.AbsDatasetContext`
        """
        pass

    @abstractmethod
    def get_identifiers(self):
        """
        :return: List of identifiers (to be stored) and available, default: None = all
        """
        return None

    @abstractmethod
    def load_collection(self, path_or_url):
        """
        Define how to load the collection (if needed) from the specified local path or url.

        :param path_or_url: Local path or url to the data
        :type path_or_url: str
        :raises: :class:`.NotImplementedError` - default: if the collections isn't parsed, but combined
        :return: Dictionary with specified :class:`get_identifiers` as keys and their respective data as values.
        """
        raise NotImplementedError()

    def use_all_identifiers(self):
        return self.get_identifiers() is None
