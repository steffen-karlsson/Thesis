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

    def create(self, identifier, meta_data, is_update=False):
        self._validate_api()
        return secure_send((identifier, meta_data, is_update), self._api.create)

    def append(self, identifier, block, create_new_stride):
        self._validate_api()
        return secure_send((identifier, block, create_new_stride), self._api.append)

    def update_meta_key(self, identifier, update_type, key, value):
        self._validate_api()
        return secure_send((identifier, update_type, key, value), self._api.update_meta_key)

    def get_datasets(self, is_internal_call=False):
        # TODO: secure return
        return self._api.get_datasets(is_internal_call)

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

    def update(self, identifier, meta_data):
        self._validate_api()
        return secure_send((identifier, meta_data, True), self._api.create)

    def _validate_api(self):
        if not self._api:
            self._api = Proxy(locateNS().lookup(self._storage_uri))


class _StorageToMonitorApi(object):
    def __init__(self, storage_uri):
        self._api = Proxy(locateNS().lookup(storage_uri))

    def heartbeat(self):
        self._api.heartbeat()


class _InternalStorageApi(_StorageApi):
    def initialize_execution(self, didentifier, fidentifier, function_name, root, query):
        self._validate_api()
        async(self._api).initialize_execution(didentifier, fidentifier, function_name, root, query)

    def execute_function(self, itr, root, didentifier, fidentifier, function_name, meta_data, query, recv_value=0):
        self._validate_api()
        async(self._api).execute_function(itr, root, didentifier, fidentifier,
                                          function_name, meta_data, query, recv_value)

    def send_ghost(self, left_ghost, right_ghost, didentifier, fidentifier, root, needs_both):
        self._validate_api()
        secure_send((left_ghost, right_ghost, didentifier, fidentifier, root, needs_both), async(self._api).send_ghost)

    def ready(self, didentifier, fidentifier, function_name, meta_data, query):
        self._validate_api()
        secure_send((didentifier, fidentifier, function_name, meta_data, query), async(self._api).ready)


class GatewayApi(object):
    def __init__(self, gateway_uri):
        self._api = Proxy(locateNS().lookup(gateway_uri))

    def submit_job(self, name, function, query):
        async(self._api).submit_job(name, function, query)

    def poll_for_result(self, name, function, query):
        return self._api.poll_for_result(name, function, query)

    def get_operations(self, name):
        return self._api.get_operations(name)

    def get_datasets(self):
        return self._api.get_datasets()

    @staticmethod
    def _set_dataset_by_function(name, package, extra_meta_data, funcion):
        with open(getsourcefile(import_class(package)), "r") as f:
            return secure_send((name, f.read(), package, extra_meta_data), funcion)

    def create(self, name, package, extra_meta_data=None):
        return GatewayApi._set_dataset_by_function(name, package, extra_meta_data, self._api.create)

    def update(self, name, package):
        return GatewayApi._set_dataset_by_function(name, package, None, self._api.update)

    def append(self, name, path_or_url):
        return secure_send((name, path_or_url), self._api.append)

    def delete(self, name):
        return self._api.delete(name)

    def exists(self, name):
        return self._api.exists(name)

    def get_type(self, name):
        return self._api.get_type(name)

    def get_description(self, name):
        return self._api.get_description(name)


class _InternalGatewayApi(GatewayApi):
    def set_status_result(self, didentifer, fidentifer, status, result):
        return self._api.set_status_result(didentifer, fidentifer, status, result)
