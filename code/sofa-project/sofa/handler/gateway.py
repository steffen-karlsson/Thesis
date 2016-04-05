# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sys import getsizeof
from random import choice
from ujson import dumps as udumps, loads as uloads
from collections import defaultdict

from sofa.cache import CacheSystem
from sofa.error import is_error, STATUS_INVALID_DATA, STATUS_NOT_FOUND, STATUS_PROCESSING, STATUS_NOT_ALLOWED
from sofa.secure import secure_load, secure_load2, secure
from sofa.handler.api import _StorageApi
from sofa.handler import get_class_from_source
from sofa.operation import OperationContext


def find_identifier(name, mod):
    identifier = hash(name)
    return identifier if mod is None else identifier % mod


class GatewayHandler(object):
    def __init__(self, config, others):
        self.__config = config
        self.__block_size = config.block_size * 1000000  # To bytes from MB
        self.__gcs = CacheSystem(defaultdict, args=dict)
        self.__num_storage_nodes = len(others['storage'])
        self.__storage_nodes = [_StorageApi(storage_uri) for storage_uri in others['storage']]

    def __find_identifier(self, name):
        return find_identifier(name, self.__config.keyspace_size)

    def __virtualize_name(self, name):
        return "%s:%s" % (self.__config.instance_name, name.strip())

    def __get_storage_node(self):
        return choice(self.__storage_nodes)

    def __get_meta_from_name(self, name):
        return self.__get_meta_from_identifier(self.__find_identifier(self.__virtualize_name(name)))

    def __get_meta_from_identifier(self, identifier):
        res = self.__get_storage_node().get_meta_from_identifier(identifier)
        if is_error(res):
            return res

        return uloads(res)

    def __get_class_from_identifier(self, identifier, key):
        res = self.__get_meta_from_identifier(identifier)
        if is_error(res):
            return res

        jdataset = res
        source = secure_load2(jdataset['digest'], jdataset['source'])
        if is_error(source):
            return STATUS_INVALID_DATA

        return get_class_from_source(source, jdataset[key]), jdataset

    def create(self, bundle):
        name, dataset_source, dataset_type = secure_load(bundle)
        dataset_name = dataset_type.rsplit(".", 1)[1]
        dataset = get_class_from_source(dataset_source, dataset_name)

        operations = dataset.get_operations()
        if operations and (not isinstance(operations, list) or
                               not all(isinstance(k, OperationContext) for k in operations)):
            return STATUS_NOT_ALLOWED, "Keys of operations dict has to be of type OperationContext"

        digest, pdata = secure(dataset_source)
        jdataset = {'digest': digest,
                    'dataset-name': dataset_name,
                    'dataset-type': dataset_type,
                    'source': pdata,
                    'num-blocks': 0}
        if operations is not None:
            jdataset['operation'] = [operation.fun_name for operation in operations]

        virtualized_identifier = self.__find_identifier(self.__virtualize_name(name))
        return self.__get_storage_node().create(virtualized_identifier, udumps(jdataset))

    def get_type(self, name):
        res = self.__get_meta_from_name(name)
        if is_error(res):
            return res

        return res['dataset-type']

    def update(self, bundle):
        pass

    def delete(self, name):
        identifier = self.__find_identifier(self.__virtualize_name(name))

        # Remove global cached results by this dataset
        self.__gcs.delete(identifier)
        return self.__get_storage_node().delete(identifier)

    def append(self, bundle):
        name, path_or_url = secure_load(bundle)
        identifier = self.__find_identifier(self.__virtualize_name(name))
        res = self.__get_class_from_identifier(identifier, 'dataset-name')
        if is_error(res):
            return res

        dataset, jdataset = res
        start = jdataset['root-idx']

        block_count = 0
        local_block_count = 0
        max_stride = dataset.get_block_stride()
        num_storage_nodes = self.__num_storage_nodes
        create_new_stride = True

        data = dataset.load_data(path_or_url)
        for block in self.__next_block(dataset, data):
            # TODO: Save response and check if correct is saved and received
            self.__storage_nodes[start].append(identifier, block, create_new_stride)

            block_count += 1
            local_block_count += 1

            # Create new stride if only one storage node, is first iteration or max local block count reached
            create_new_stride = num_storage_nodes == 1 or local_block_count == max_stride

            if create_new_stride:
                local_block_count = 0
                start = (start + 1) % num_storage_nodes

        self.__get_storage_node().update_meta_key(identifier, 'append', 'num-blocks', block_count)

    def __next_block(self, dataset, data):
        block = []
        block_size = 0
        for entry in dataset.next_entry(data):
            entry_size = getsizeof(entry)
            if block_size + entry_size > self.__block_size:
                yield block
                block = [entry]
                block_size = 0
            else:
                block_size += entry_size
                block.append(entry)

        if block:
            # Check if block is not empty and yield rest
            yield block

    def get_dataset_operations(self, name):
        res = self.__get_meta_from_name(name)
        if is_error(res):
            return res

        return res['operation']

    def submit_job(self, name, function, query):
        didentifier = self.__find_identifier(self.__virtualize_name(name))
        fidentifier = find_identifier("%s:%s:%s" % (didentifier, function, query), None)

        dataset_result_cache = self.__gcs.get(didentifier)
        if fidentifier in dataset_result_cache:
            # We already have the value
            return

        dataset_result_cache[fidentifier] = (STATUS_PROCESSING, None)
        self.__get_storage_node().submit_job(didentifier, fidentifier, function, query, self.__config.node)

    def poll_for_result(self, name, function, query):
        didentifier = self.__find_identifier(self.__virtualize_name(name))
        fidentifier = find_identifier("%s:%s:%s" % (didentifier, function, query), None)

        dataset_result_cache = self.__gcs.get(didentifier)
        if fidentifier not in dataset_result_cache:
            return STATUS_NOT_FOUND, None

        return dataset_result_cache[fidentifier]

    # Internal Result Api
    def set_status_result(self, didentifier, fidentifier, status, result):
        self.__gcs.get(didentifier)[fidentifier] = (status, result)
