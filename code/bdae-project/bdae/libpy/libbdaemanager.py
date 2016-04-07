# Created by Steffen Karlsson on 03-28-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: libbdaemanager
"""

from abc import ABCMeta
from inspect import isgeneratorfunction

from bdae.libpy.libbdaescientist import AbsPyScientistGateway
from sofa.error import verify_error
from bdae.api import GatewayManagerApi
from bdae.dataset import AbsMapReduceDataset


class CollectionAlreadyExistsException(Exception):
    def __init__(self, message):
        super(CollectionAlreadyExistsException, self).__init__(message)


def _get_full_identifier(obj):
    return "%s.%s" % (obj.__module__, obj.__class__.__name__)


class AbsPyManagerGateway(AbsPyScientistGateway):
    """
    Abstract class to override in order to implement a manager gateway to the framework
    """

    __metaclass__ = ABCMeta

    def __init__(self, gateway_uri):
        super(AbsPyManagerGateway, self).__init__(None)
        self._api = GatewayManagerApi(gateway_uri)

    def create_dataset(self, dataset):
        """
        Method to create a new dataset based on a name and a class reference, e.g. mypackage.myfile.MyDatasetClass

        :param dataset: Dataset of class type implementing :class:`.AbsDatasetContext`
        :type dataset: :class:`.AbsDatasetContext`
        :raises :class:`.DatasetAlreadyExistsException` if the name of the dataset already exists
        :raises :class:`.NotImplementedError` if any of the operations in the dataset isn't of type :class:`.OperationContext`
        """

        if not isinstance(dataset, AbsMapReduceDataset):
            raise Exception("Dataset has to be of type AbsDatasetContext")

        if not dataset.get_name():
            raise Exception("Use the dataset constructor and specify name in order to "
                            "retrieve and work on the dataset later")

        reduce_functions = [fun.__name__ for fun in dataset.get_reduce_functions()]
        for operation_context in dataset.get_operations():
            if operation_context.get_functions()[-1].__name__ not in reduce_functions:
                raise Exception("Last operation of %s has to be a reduction" % operation_context.fun_name)

        for map_fun in dataset.get_map_functions():
            if not isgeneratorfunction(map_fun):
                raise Exception("%s is not an generator i.e. yields" % map_fun.func_name)

        description = dataset.get_description()
        meta_data = {'description': description if description else ""}

        package = _get_full_identifier(dataset)
        verify_error(self._api.create(dataset.get_name(), package, extra_meta_data=meta_data))

    def append_to_dataset(self, name, url):
        """
        Method to append data from a url to an existing dataset created by :func:`create_dataset`.

        :param name: Name of the dataset
        :type name: str
        :param url: The path from where the framework gateway needs to download the data
        :type url: str
        :raises DatasetNotExistsException: If the dataset isn't already created by :func:`create_dataset`
        """

        verify_error(self._api.append(name, url))

    def delete_dataset(self, name):
        """
        Deletes the dataset by name

        :param name: Name of the dataset
        :type name: str
        """

        verify_error(self._api.delete(name))

    def update_dataset(self, name):
        """
        Updates the dataset by name based on the file it was originally created from

        :param name: Name of the dataset
        :type name: str
        :raises: DatasetNotExistsException: If the name of the dataset doesn't exists
        """
        res = self._api.get_type(name)
        verify_error(res)

        dataset_type = res
        verify_error(self._api.update(name, dataset_type))
