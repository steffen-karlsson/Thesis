# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from inspect import getsourcefile
from sys import getsizeof
from contextlib import closing
from urllib2 import urlopen
from random import choice, randint
from ujson import dumps as udumps, loads as uloads

from Pyro4 import Proxy, locateNS

from bdae.utils import find_identifier, import_class, is_error, get_class_from_path, find_package
from bdae.secure import secure_load, secure_load2, secure_send, secure
from bdae.storage import api as storage_api


class GatewayHandler(object):
    def __init__(self, block_size, storage_uris):
        self.__block_size = block_size
        self.__num_storage_nodes = len(storage_uris)
        self.__storage_nodes = [storage_api(storage_uri) for storage_uri in storage_uris]

    def __get_storage_node(self):
        return choice(self.__storage_nodes)

    @staticmethod
    def __get_class_from_source(source, cls_name):
        exec (source, globals())
        return eval("%s()" % cls_name)

    def __get_source_from_identifier(self, identifier):
        res = self.__get_storage_node().get_meta_from_identifier(identifier)
        if is_error(res):
            # TODO: decide whether to try again
            pass

        jdataset = uloads(res)
        source = secure_load2(jdataset['digest'], jdataset['source'])
        if is_error(source):
            # TODO: decide what to do
            pass

        return jdataset, source

    def create(self, bundle):
        name, dataset_source, dataset_name = secure_load(bundle)

        dataset = GatewayHandler.__get_class_from_source(dataset_source, dataset_name)
        operation_name = get_class_from_path(find_package(dataset.get_operation_functions()))
        reduce_name = get_class_from_path(dataset.get_reduce_functions())
        map_name = get_class_from_path(dataset.get_map_functions())
        digest, pdata = secure(dataset_source)

        ddata = {'digest': digest,
                 'dataset-name': dataset_name,
                 'source': pdata}
        if operation_name is not None:
            ddata['operation-name'] = operation_name
        if reduce_name is not None:
            ddata['reduce-name'] = reduce_name
        if map_name is not None:
            ddata['map-name'] = map_name
        return self.__get_storage_node().create(find_identifier(name), udumps(ddata))

    def append(self, name, url):
        identifier = find_identifier(name)
        jdataset, source = self.__get_source_from_identifier(identifier)
        dataset = GatewayHandler.__get_class_from_source(source, jdataset['dataset-name'])

        with closing(urlopen(url)) as f:
            start = randint(0, self.__num_storage_nodes - 1)
            for block in self.__next_block(dataset, f.read()):
                self.__storage_nodes[start].append(identifier, block)
                # TODO: Save response and check if correct is saved and received
                start = (start + 1) ^ self.__num_storage_nodes

    def __next_block(self, dataset, data):
        block = []
        block_size = 0
        for entry in dataset.next_entry(data):
            entry_size = getsizeof(entry)
            if block_size + entry_size > self.__block_size:
                yield block
                block = []
                block_size = 0
            else:
                block_size += entry_size
                block.append(entry)

        if block:
            # Check if block is not empty and yield rest
            yield block

    def get_dataset_operations(self, name):
        identifier = find_identifier(name.strip())
        jdataset, source = self.__get_source_from_identifier(identifier)
        om = GatewayHandler.__get_class_from_source(source, jdataset['operation-name'])
        return om.define().keys()


class GatewayApi(object):
    def __init__(self, gateway_uri):
        super(GatewayApi, self).__init__()

        self.api = Proxy(locateNS().lookup(gateway_uri))

    def create(self, name, dataset_type):
        with open(getsourcefile(import_class(dataset_type)), "r") as f:
            return secure_send((name, f.read(), dataset_type.rsplit(".", 1)[1]), self.api.create)

    def append(self, name, url):
        return self.api.append(name, str(url))

    def get_dataset_operations(self, name):
        return self.api.get_dataset_operations(name)
