# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sys import getsizeof
from random import choice
from ujson import dumps as udumps, loads as uloads
from collections import defaultdict

from sofa.cache import CacheSystem
from sofa.error import is_error, STATUS_INVALID_DATA, STATUS_NOT_FOUND, STATUS_PROCESSING
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

        meta_data = res
        source = secure_load2(meta_data['digest'], meta_data['source'])
        if is_error(source):
            return STATUS_INVALID_DATA

        return get_class_from_source(source, meta_data[key]), meta_data

    def create(self, bundle):
        name, dataset_source, package, extra_meta_data = secure_load(bundle)
        class_name = package.rsplit(".", 1)[1]

        context = get_class_from_source(dataset_source, class_name)
        operations = context.get_operations()
        if operations and (not isinstance(operations, list) or
                           not all(isinstance(k, OperationContext) for k in operations)):
            raise NotImplementedError("Operations has to be of type OperationContext")

        if not extra_meta_data:
            extra_meta_data = {}

        # Update with the actual metadata
        digest, pdata = secure(dataset_source)
        extra_meta_data.update({'digest': digest,
                                'class-name': class_name,
                                'package': package,
                                'source': pdata,
                                'num-blocks': 0})
        extra_meta_data['operations'] = [operation.fun_name for operation in operations] if operations else []

        virtualized_identifier = self.__find_identifier(self.__virtualize_name(name))
        return self.__get_storage_node().create(virtualized_identifier, udumps(extra_meta_data))

    def exists(self, name):
        return self.__get_meta_from_name(name)

    def get_type(self, name):
        res = self.__get_meta_from_name(name)
        if is_error(res):
            return res

        return res['package']

    def update(self, bundle):
        pass

    def delete(self, name):
        identifier = self.__find_identifier(self.__virtualize_name(name))

        # Remove global cached results by this dataset
        self.__gcs.delete(identifier)
        return self.__get_storage_node().delete(identifier)

    def append(self, bundle):
        name, data_ref = secure_load(bundle)
        identifier = self.__find_identifier(self.__virtualize_name(name))
        res = self.__get_class_from_identifier(identifier, 'class-name')
        if is_error(res):
            return res

        context, meta_data = res
        start = meta_data['root-idx']

        block_count = 0
        local_block_count = 0
        max_stride = context.get_block_stride()
        num_storage_nodes = self.__num_storage_nodes
        create_new_stride = True

        # Clean function cache
        self.__gcs.delete(identifier)

        # TODO: Check if dataset already have blocks and append to there

        data = context.preprocess(data_ref)
        for block in self.__next_block(context, data):
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

    def __next_block(self, context, data):
        block = []
        block_size = 0
        for entry in context.next_entry(data):
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

    def get_operations(self, name):
        res = self.__get_meta_from_name(name)
        if is_error(res):
            return res

        return res['operation']

    def submit_job(self, name, function, query):
        didentifier = self.__find_identifier(self.__virtualize_name(name))
        fidentifier = find_identifier("%s:%s:%s" % (didentifier, function, query), None)

        result_cache = self.__gcs.get(didentifier)
        if fidentifier in result_cache:
            # We already have the value
            return

        result_cache[fidentifier] = (STATUS_PROCESSING, None)
        self.__get_storage_node().submit_job(didentifier, fidentifier, function, query, self.__config.node)

    def poll_for_result(self, name, function, query):
        didentifier = self.__find_identifier(self.__virtualize_name(name))
        fidentifier = find_identifier("%s:%s:%s" % (didentifier, function, query), None)

        result_cache = self.__gcs.get(didentifier)
        if fidentifier not in result_cache:
            return STATUS_NOT_FOUND, None

        return result_cache[fidentifier]

    # Internal Result Api
    def set_status_result(self, didentifier, fidentifier, status, result):
        self.__gcs.get(didentifier)[fidentifier] = (status, result)
