# Created by Steffen Karlsson on 02-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sofa.handler.api import GatewayApi


class GatewayScientistApi(object):
    def __init__(self, gateway_uri):
        self._api = GatewayApi(gateway_uri)

    def submit_job(self, name, function, query):
        self._api.submit_job(name, function, query)

    def poll_for_result(self, name, function, query):
        return self._api.poll_for_result(name, function, query)

    def get_operations(self, name):
        return self._api.get_operations(name)

    def get_datasets(self):
        return self._api.get_datasets()

    def get_submitted_jobs(self):
        return self._api.get_submitted_jobs()

    def get_description(self, name):
        return self._api.get_description(name)


class GatewayManagerApi(GatewayScientistApi):
    def __init__(self, gateway_uri):
        super(GatewayManagerApi, self).__init__(gateway_uri)

    def create(self, name, dataset_type, extra_meta_data=None):
        return self._api.create(name, dataset_type, extra_meta_data)

    def update(self, name, dataset_type):
        return self._api.update(name, dataset_type)

    def append(self, name, data_ref, is_serialized):
        return self._api.append(name, data_ref, is_serialized)

    def delete(self, name):
        return self._api.delete(name)

    def exists(self, name):
        return self._api.exists(name)

    def get_type(self, name):
        return self._api.get_type(name)


class GatewayAdminApi(GatewayManagerApi):
    def __init__(self, gateway_uri):
        super(GatewayAdminApi, self).__init__(gateway_uri)
