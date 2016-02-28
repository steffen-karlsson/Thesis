# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sys import getsizeof
from contextlib import closing
from urllib2 import urlopen
from random import choice, randint
from ujson import dumps as udumps, loads as uloads

from bdae.cache import CacheSystem
from bdae.utils import find_identifier, is_error, STATUS_INVALID_DATA, STATUS_NOT_FOUND, \
    STATUS_PROCESSING
from bdae.secure import secure_load, secure_load2, secure
from bdae.handler.storage import StorageApi
from bdae.handler import get_class_from_path, get_class_from_source


class GatewayHandler(object):
    def __init__(self, config, others):
        self.__config = config
        self.__block_size = config.block_size * 1000000  # To bytes from MB
        self.__gcs = CacheSystem(dict)
        self.__num_storage_nodes = len(others['storage'])
        self.__storage_nodes = [StorageApi(storage_uri) for storage_uri in others['storage']]

    def __find_identifier(self, name):
        return find_identifier(name, self.__config.keyspace_size)

    def __get_storage_node(self):
        return choice(self.__storage_nodes)

    def __get_class_from_identifier(self, identifier, key):
        res = self.__get_storage_node().get_meta_from_identifier(identifier)
        if is_error(res):
            # TODO: decide whether to try again
            pass

        jdataset = uloads(res)
        source = secure_load2(jdataset['digest'], jdataset['source'])
        if is_error(source):
            return STATUS_INVALID_DATA

        return get_class_from_source(source, jdataset[key])

    def create(self, bundle):
        name, dataset_source, dataset_name = secure_load(bundle)

        dataset = get_class_from_source(dataset_source, dataset_name)
        operation_name = get_class_from_path(dataset.get_operation_functions())
        reduce_name = get_class_from_path(dataset.get_reduce_functions())
        map_name = get_class_from_path(dataset.get_map_functions())
        digest, pdata = secure(dataset_source)

        ddata = {'digest': digest,
                 'dataset-name': dataset_name,
                 'source': pdata,
                 'num-blocks': 0}
        if operation_name is not None:
            ddata['operation-name'] = operation_name
        if reduce_name is not None:
            ddata['reduce-name'] = reduce_name
        if map_name is not None:
            ddata['map-name'] = map_name
        return self.__get_storage_node().create(self.__find_identifier(name.strip()), udumps(ddata))

    def update(self, bundle):
        pass

    def append(self, name, url):
        identifier = self.__find_identifier(name.strip())
        res = self.__get_class_from_identifier(identifier, 'dataset-name')
        if is_error(res):
            return res

        dataset = res
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
        identifier = self.__find_identifier(name.strip())
        res = self.__get_class_from_identifier(identifier, 'operation-name')
        if is_error(res):
            return res

        om = res
        return om.define().keys()

    def submit_job(self, name, function_type, function, query):
        didentifier = self.__find_identifier(name.strip())
        fidentifier = find_identifier("%s:%s:%s" % (didentifier, function, query), None)
        # TODO: Check if STATUS_PROCESSING for fidentifier

        self.__gcs.put(fidentifier, (STATUS_PROCESSING, None))
        self.__get_storage_node().submit_job(didentifier, fidentifier, function_type,
                                             function, query, self.__config.node)

    def poll_for_result(self, name, function, query):
        identifier = find_identifier("%s:%s:%s" % (self.__find_identifier(name.strip()), function, query), None)
        if not self.__gcs.contains(identifier):
            return STATUS_NOT_FOUND, None

        return self.__gcs.get(identifier)

    # Internal Result Api
    def set_status_result(self, fidentifier, status, result):
        self.__gcs.put(fidentifier, (status, result))
