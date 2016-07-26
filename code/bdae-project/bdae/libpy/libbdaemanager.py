# Created by Steffen Karlsson on 03-28-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: libbdaemanager
"""

from inspect import isgeneratorfunction
from logging import debug
from cPickle import dumps as pickle_dumps

from bdae.libpy.libbdaescientist import PyBDAEScientist
from sofa.error import verify_error, DatasetAlreadyExistsException, DatasetNotExistsException, is_error
from bdae.api import GatewayManagerApi
from bdae.dataset import AbsMapReduceDataset
from bdae.collection import AbsDatasetCollection


class CollectionAlreadyExistsException(Exception):
    def __init__(self, message):
        super(CollectionAlreadyExistsException, self).__init__(message)


def _get_full_identifier(obj):
    return "%s.%s" % (obj.__module__, obj.__class__.__name__)


class PyBDAEManager(PyBDAEScientist):
    """
    Abstract class to override in order to implement a manager gateway to the framework
    """

    def __init__(self, gateway_uri):
        PyBDAEScientist.__init__(self, None)
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
            raise Exception("Use the constructor and specify name in order to "
                            "retrieve and work on the dataset later")

        reduce_functions = [fun.__name__ for fun in dataset.get_reduce_functions()]
        for operation_context in dataset.get_operations():
            if operation_context.get_functions()[-1].__name__ not in reduce_functions:
                raise Exception("Last operation of %s has to be a reduction" % operation_context.fun_name)

        for map_fun in dataset.get_map_functions():
            if not isgeneratorfunction(map_fun):
                debug("%s is not an generator i.e. yields" % map_fun.func_name)

        self.__finalize_create(dataset)

    def __finalize_create(self, context):
        description = context.get_description()
        meta_data = {'description': description if description else ""}

        package = _get_full_identifier(context)
        verify_error(self._api.create(context.get_name(), package, extra_meta_data=meta_data))

    def initialize_collection(self, collection, with_new_data=None):
        """
        Initializes a new collection with specified name

        :param collection: Reference to the collection.
        :type collection: Implementation of :class:`.AbsDatasetCollection`
        :param with_new_data: Specify path or url if the new collection has to be initialized from data - Otherwise (default: None) it will be combined of existing datasets.
        :type with_new_data: path or url
        :raises: :class:`.CollectionAlreadyExistsException` if a collection with that name is already specified.
        :raises: :class:`.DatasetNotExistsException` if one of the specified datasets doesn't exists, in the case where the collection is combined of existing datasets.
        """

        if not isinstance(collection, AbsDatasetCollection):
            raise Exception("Dataset has to be of type AbsDatasetContext")

        if not collection.get_name():
            raise Exception("Use the collection constructor and specify name in order to "
                            "retrieve and work on the dataset later")

        verify_specified_datasets = True
        if with_new_data:
            # Collection has to be initialized from path or url, by load_collection
            try:
                for identifier, data_ref in collection.preprocess(with_new_data):
                    dataset = collection.get_dataset_type(identifier)
                    # Create dataset
                    self.create_dataset(dataset)

                    # If it went fine, append data
                    self.append_data_to_dataset(dataset, data_ref)

                verify_specified_datasets = False
            except NotImplementedError:
                # Verify if dataset exists instead
                pass

        if verify_specified_datasets:
            # Collection is initialized from existing datasets, therefor check that all are there.
            for identifier in collection.get_identifiers():
                if is_error(self._api.exists(identifier)):
                    raise DatasetNotExistsException("Specified dataset: '%s' does not exists" % identifier)

        try:
            # A collection is represented as a dataset with a prefixed name internally in the storage system
            self.__finalize_create(collection)
        except DatasetAlreadyExistsException:
            name = collection.get_name().split(':')[1]
            raise CollectionAlreadyExistsException("Collection with name: '%s' already exists" % name)

    def append_data_to_dataset(self, dataset, data):
        """
        Method to append data from a url to an existing dataset created by :func:`create_dataset`.

        :param dataset: Dataset reference
        :type dataset: Implementation of :class:`.AbsMapReduceDataset`
        :param data: Actual data
        :type data: any
        :raises DatasetNotExistsException: If the dataset isn't already created by :func:`create_dataset`
        """

        data = dataset.serialize(data)
        self.__append(dataset, data, is_serialized=True)

    def append_path_to_dataset(self, dataset, path):
        """
        See append_url_to_dataset documentation
        """

        self.__append(dataset, path)

    def append_url_to_dataset(self, dataset, url):
        """
        Method to append data from a url to an existing dataset created by :func:`create_dataset`.

        :param dataset: Dataset reference
        :type dataset: Implementation of :class:`.AbsMapReduceDataset`
        :param url: The url from where the framework gateway needs to download the data
        :type url: str
        :raises DatasetNotExistsException: If the dataset isn't already created by :func:`create_dataset`
        """

        self.__append(dataset, url)

    def __append(self, dataset, url, is_serialized=False):
        verify_error(self._api.append(dataset.get_name(), url, is_serialized))

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
