# Created by Steffen Karlsson on 02-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from inspect import getsourcefile
from simplejson import dumps

from Pyro4 import Proxy, locateNS, async

from sofa.handler import import_class


class _StorageApi(object):
    def __init__(self, storage_uri):
        self._api = None
        self._storage_uri = storage_uri

    def create(self, function_delegation, identifier, meta_data, is_update=False):
        self._validate_api()
        return self._api.create(function_delegation, identifier, dumps(meta_data), is_update)

    def append(self, function_delegation, identifier, block, create_new_stride):
        self._validate_api()
        return self._api.append(function_delegation, identifier, block, create_new_stride)

    def update_meta_key(self, function_delegation, identifier, update_type, key, value):
        self._validate_api()
        return self._api.update_meta_key(function_delegation, identifier, update_type, key, value)

    def get_datasets(self, is_internal_call=False):
        self._validate_api()
        # TODO: secure return
        return self._api.get_datasets(is_internal_call)

    def get_submitted_jobs(self, is_internal_call=False):
        self._validate_api()
        return self._api.get_submitted_jobs(is_internal_call)

    def get_meta_from_identifier(self, function_delegation, identifier):
        self._validate_api()
        # TODO: secure return
        return self._api.get_meta_from_identifier(function_delegation, identifier)

    def submit_job(self, function_delegation, didentifier, process_state, gateway):
        self._validate_api()
        async(self._api).submit_job(function_delegation, didentifier, process_state, gateway)

    def delete(self, function_delegation, identifier):
        self._validate_api()
        return self._api.delete(function_delegation, identifier)

    def update(self, identifier, meta_data):
        self._validate_api()
        return self._api.create(identifier, meta_data, True)

    def _validate_api(self):
        if not self._api:
            self._api = Proxy(locateNS().lookup(self._storage_uri))


class _StorageToMonitorApi(object):
    def __init__(self, storage_uri):
        self._api = Proxy(locateNS().lookup(storage_uri))

    def heartbeat(self):
        self._api.heartbeat()


class _InternalStorageApi(_StorageApi):
    def initialize_job(self, didentifier, fidentifier, function_name, root, query):
        self._validate_api()
        async(self._api).initialize_job(didentifier, fidentifier, function_name, root, query)

    def execute_function(self, didentifier, fidentifier, meta_data, process_state):
        self._validate_api()
        async(self._api).execute_function(didentifier, fidentifier, meta_data, process_state)

    def send_ghost(self, left_ghost, right_ghost, needs_both, didentifier, fidentifier, fun_args):
        self._validate_api()
        async(self._api).send_ghost(left_ghost, right_ghost, needs_both, didentifier, fidentifier, fun_args)

    def ready(self, didentifier, fidentifier, meta_data, process_state):
        self._validate_api()
        async(self._api).ready(didentifier, fidentifier, meta_data, process_state)


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

    def get_submitted_jobs(self):
        return self._api.get_submitted_jobs()

    @staticmethod
    def _set_dataset_by_function(name, package, extra_meta_data, funcion):
        with open(getsourcefile(import_class(package)), "r") as f:
            return funcion(name, f.read(), package, extra_meta_data)

    def create(self, name, package, extra_meta_data=None):
        return GatewayApi._set_dataset_by_function(name, package, extra_meta_data, self._api.create)

    def update(self, name, package):
        return GatewayApi._set_dataset_by_function(name, package, None, self._api.update)

    def append(self, name, path_or_url):
        return self._api.append(name, path_or_url)

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
