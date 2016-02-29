# Created by Steffen Karlsson on 02-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from inspect import getsourcefile

from Pyro4 import Proxy, locateNS, async

from bdae.secure import secure_send
from bdae.handler import import_class


class StorageApi(object):
    def __init__(self, storage_uri):
        self.api = Proxy(locateNS().lookup(storage_uri))

    def create(self, identifier, jdataset):
        return secure_send((identifier, jdataset), self.api.create)

    def append(self, identifier, block):
        return secure_send((identifier, block), self.api.append)

    def get_meta_from_identifier(self, identifier):
        # TODO: secure return
        return self.api.get_meta_from_identifier(identifier)

    def submit_job(self, didentifier, fidentifier, function_type, function, query, gateway):
        async(self.api).submit_job(didentifier, fidentifier, function_type, function, query, gateway)


class StorageToMonitorApi(object):
    def __init__(self, storage_uri):
        self.api = Proxy(locateNS().lookup(storage_uri))

    def heartbeat(self):
        self.api.heartbeat()


class InternalStorageApi(StorageApi):
    def execute_function(self, itr, fidentifier, function_type, function_name, jdataset, query, prev_value=0):
        async(self.api).execute_functionexecute_function(itr, root, fidentifier, function_type, function_name,
                                                         jdataset, query, prev_value)


class GatewayApi(object):
    def __init__(self, gateway_uri):
        super(GatewayApi, self).__init__()
        self.api = Proxy(locateNS().lookup(gateway_uri))

    def __set_dataset_by_function(self, name, dataset_type, funcion):
        with open(getsourcefile(import_class(dataset_type)), "r") as f:
            return secure_send((name, f.read(), dataset_type.rsplit(".", 1)[1]), funcion)

    def create(self, name, dataset_type):
        return self.__set_dataset_by_function(name, dataset_type, self.api.create)

    def update(self, name, dataset_type):
        return self.__set_dataset_by_function(name, dataset_type, self.api.update)

    def append(self, name, url):
        return self.api.append(name, str(url))

    def get_dataset_operations(self, name):
        return self.api.get_dataset_operations(name)

    def submit_job(self, name, function_type, function, query):
        async(self.api).submit_job(name, function_type, function, query)

    def poll_for_result(self, name, function, query):
        return self.api.poll_for_result(name, function, query)


class InternalGatewayApi(GatewayApi):
    def set_status_result(self, fidentifer, status, result):
        return self.api.set_status_result(fidentifer, status, result)
