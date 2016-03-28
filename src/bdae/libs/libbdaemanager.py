# Created by Steffen Karlsson on 03-28-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta

from libbdaescientist import AbsPyScientistGateway
from bdae.utils import verify_error
from bdae.handler.api import GatewayManagerApi


class AbsPyManagerGateway(AbsPyScientistGateway):
    """
    Abstract class to override in order to implement a manager gateway to the framework
    """

    __metaclass__ = ABCMeta

    def __init__(self, gateway_uri):
        super(AbsPyManagerGateway, self).__init__(None)
        self._api = GatewayManagerApi(gateway_uri)

    def create_dataset(self, name, dataset_type):
        """
        Method to create a new dataset based on a name and a class reference, e.g. mypackage.myfile.MyDatasetClass

        :param name: Name of the dataset
        :type name: str
        :param dataset_type: Reference name of the dataset to be created
        :type dataset_type: str
        :raises DatasetAlreadyExistsException: If the name of the dataset already exists
        """

        verify_error(self._api.create(name, dataset_type))

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

        # TODO: Implement update and remove dataset
