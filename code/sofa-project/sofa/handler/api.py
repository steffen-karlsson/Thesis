# Created by Steffen Karlsson on 02-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from inspect import getsourcefile

from Pyro4 import Proxy, locateNS, async

from sofa.secure import secure_send
from sofa.handler import import_class


class _StorageApi(object):
    def __init__(self, storage_uri):
        self._api = None
        self._storage_uri = storage_uri

    def create(self, identifier, jdataset):
        self._validate_api()
        return secure_send((identifier, jdataset, False), self._api.create)

    def append(self, identifier, block, create_new_stride):
        self._validate_api()
        return secure_send((identifier, block, create_new_stride), self._api.append)

    def update_meta_key(self, identifier, update_type, key, value):
        self._validate_api()
        return secure_send((identifier, update_type, key, value), self._api.update_meta_key)

    def get_meta_from_identifier(self, identifier):
        self._validate_api()
        # TODO: secure return
        return self._api.get_meta_from_identifier(identifier)

    def submit_job(self, didentifier, fidentifier, function, query, gateway):
        self._validate_api()
        async(self._api).submit_job(didentifier, fidentifier, function, query, gateway)

    def delete(self, identifier):
        self._validate_api()
        return self._api.delete(identifier)

    def update(self, identifier, jdataset):
        self._validate_api()
        return secure_send((identifier, jdataset, True), self._api.create)

    def _validate_api(self):
        if not self._api:
            self._api = Proxy(locateNS().lookup(self._storage_uri))


class _StorageToMonitorApi(object):
    def __init__(self, storage_uri):
        self._api = Proxy(locateNS().lookup(storage_uri))

    def heartbeat(self):
        self._api.heartbeat()


class _InternalStorageApi(_StorageApi):
    def initialize_execution(self, root, didentifier, fidentifier, function_name, jdataset, query):
        self._validate_api()
        async(self._api).initialize_execution(root, didentifier, fidentifier, function_name, jdataset, query)

    def execute_function(self, itr, root, didentifier, fidentifier, function_name, jdataset, query, prev_value=0):
        self._validate_api()
        async(self._api).execute_function(itr, root, didentifier, fidentifier, function_name, jdataset, query,
                                          prev_value)

    def send_ghost(self, left_ghost, right_ghost, didentifier, fidentifier, root, needs_both):
        self._validate_api()
        secure_send((left_ghost, right_ghost, didentifier, fidentifier, root, needs_both), async(self._api).send_ghost)

    def ready(self, didentifier, fidentifier, function_name, jdataset, query):
        self._validate_api()
        secure_send((didentifier, fidentifier, function_name, jdataset, query), async(self._api).ready)


class GatewayApi(object):
    def __init__(self, gateway_uri):
        self._api = Proxy(locateNS().lookup(gateway_uri))

    def submit_job(self, name, function, query):
        async(self._api).submit_job(name, function, query)

    def poll_for_result(self, name, function, query):
        return self._api.poll_for_result(name, function, query)

    def get_dataset_operations(self, name):
        return self._api.get_dataset_operations(name)

    @staticmethod
    def _set_dataset_by_function(name, dataset_type, funcion):
        with open(getsourcefile(import_class(dataset_type)), "r") as f:
            return secure_send((name, f.read(), dataset_type), funcion)

    def create(self, name, dataset_type):
        return GatewayApi._set_dataset_by_function(name, dataset_type, self._api.create)

    def update(self, name, dataset_type):
        return GatewayApi._set_dataset_by_function(name, dataset_type, self._api.update)

    def append(self, name, url):
        return secure_send((name, str(url)), self._api.append)

    def delete(self, name):
        return self._api.delete(name)

    def get_type(self, name):
        return self._api.get_type(name)


class _InternalGatewayApi(GatewayApi):
    def set_status_result(self, didentifer, fidentifer, status, result):
        return self._api.set_status_result(didentifer, fidentifer, status, result)