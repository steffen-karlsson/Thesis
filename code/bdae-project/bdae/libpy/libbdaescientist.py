# Created by Steffen Karlsson on 03-28-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: libbdaescientist
"""

from time import sleep

from sofa.error import verify_error, is_processing
from bdae.api import GatewayScientistApi


class PyBDAEScientist:
    """
    Abstract class to override in order to implement a scientist gateway to the framework
    """

    def __init__(self, gateway_uri):
        if gateway_uri:
            self._api = GatewayScientistApi(gateway_uri)

    # TODO: Add possibility to show description of dataset?

    def get_datasets(self):
        res = self._api.get_datasets()
        verify_error(res)
        return res

    def get_api_proxy(self):
        return self._api

    def submit_job(self, name, function, query, callback=None, poll_delay=0.2):
        """
        Submits a map reduce job to bdae with a potential async callback for when the job has executed

        :param name: Name of the dataset
        :type name: str
        :param function: Name of the function to execute
        :type function: str
        :param query: Arguments for the function
        :type query: str
        :param poll_delay: Delay for polling for result in seconds, default = 0.2
        :type poll_delay: float
        :param callback: Executed when the job has terminated with one argument, the result
        :raises DatasetNotExistsException: If the name of the dataset doesn't exists
        """

        self._api.submit_job(name, function, query)

        while True:
            # Sleep and try to poll again
            sleep(poll_delay)

            res = self._api.poll_for_result(name, function, query)
            if is_processing(res):
                continue

            verify_error(res)
            if callback:
                # Return result in callback
                callback(res[1])
            return
