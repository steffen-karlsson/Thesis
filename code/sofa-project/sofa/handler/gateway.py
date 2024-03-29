# -*- coding: utf-8 -*-

# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from collections import defaultdict
from inspect import isclass, getmembers
from math import floor, ceil
from os import path
from random import choice
from sys import getsizeof
from Pyro4 import expose

from ujson import loads

from sofa.cache import CacheSystem
from sofa.delegation import FunctionDelegation
from sofa.error import is_error, is_processing, STATUS_INVALID_DATA, STATUS_NOT_FOUND, STATUS_PROCESSING, \
    STATUS_SUCCESS, STATUS_NOT_ALLOWED
from sofa.foundation import strategy as sofa_strategies
from sofa.foundation.operation import OperationContext
from sofa.handler import get_class_from_source, unique_and_preserve
from sofa.handler.api import _StorageApi
from sofa.secure import secure_load, secure


def find_identifier(name, mod):
    identifier = hash(name)
    return identifier if mod is None else identifier % mod


def get_size(obj):
    size = getsizeof(obj)

    if isinstance(obj, dict):
        size += sum((get_size(v) for v in obj.values()))
        size += sum((get_size(k) for k in obj.keys()))
    elif hasattr(obj, 'nbytes'):
        size += eval("obj.nbytes")
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum((get_size(i) for i in obj))
    return size


@expose
class GatewayHandler(object):
    def __init__(self, config, others):
        self.__config = config
        self.__block_size = config.block_size * 1000000  # To bytes from MB
        self.__gcs = CacheSystem(defaultdict, args=dict)
        self.__num_storage_nodes = len(others['storage'])
        self.__storage_nodes = [_StorageApi(storage_uri) for storage_uri, _ in others['storage']]

    def __find_identifier(self, name):
        return find_identifier(name, self.__config.keyspace_size)

    def __virtualize_name(self, name):
        return "%s:%s" % (self.__config.instance_name, name.strip())

    def __get_storage_node(self):
        return choice(self.__storage_nodes)

    def __get_meta_from_name(self, name):
        return self.__get_meta_from_identifier(self.__find_identifier(self.__virtualize_name(name)))

    def __get_meta_from_identifier(self, identifier):
        fd = FunctionDelegation(identifier) \
            .as_forward_queue_delegation(None, self.__config.load_balancing_threshold, None)

        res = self.__get_storage_node().get_meta_from_identifier(fd, identifier)
        if is_error(res):
            return res

        return loads(res)

    # def __find_replicas(self, root_idx, replication_factor):
    #     return _generate_forward_queue(root_idx, replication_factor, self.__num_storage_nodes, include_self=False)

    def __get_class_from_identifier(self, identifier, key):
        res = self.__get_meta_from_identifier(identifier)
        if is_error(res):
            return res

        meta_data = res
        source = secure_load(meta_data['digest'], meta_data['source'])
        if is_error(source):
            return STATUS_INVALID_DATA

        return get_class_from_source(source, meta_data[key]), meta_data

    def __get_property(self, name, key):
        res = self.__get_meta_from_name(name)
        if is_error(res):
            return res

        return res[key]

    def create(self, name, dataset_source, package, extra_meta_data):
        print " ".join([storagenode.get_uri() for storagenode in self.__storage_nodes])
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
                                'name': name,
                                'class-name': class_name,
                                'package': package,
                                'source': pdata,
                                'replication-factor': context.get_replication_factor(),
                                'num-blocks': 0})
        extra_meta_data['operations'] = [(operation.fun_name, operation.get_num_arguments())
                                         for operation in operations] if operations else []

        virtualized_identifier = self.__find_identifier(self.__virtualize_name(name))

        fd = FunctionDelegation(virtualized_identifier) \
            .as_dispatch_delegation() \
            .as_required_queue_delegation(None, context.get_replication_factor())

        return self.__get_storage_node().create(fd, virtualized_identifier, extra_meta_data)

    def exists(self, name):
        return self.__get_meta_from_name(name)

    def get_type(self, name):
        return self.__get_property(name, 'package')

    def update(self, bundle):
        # TODO: Implement when needed
        pass

    def delete(self, name):
        identifier = self.__find_identifier(self.__virtualize_name(name))

        # Remove global cached results by this dataset
        self.__gcs.delete(identifier)
        return self.__get_storage_node().delete(identifier)

    def append(self, name, data, is_serialized):
        identifier = self.__find_identifier(self.__virtualize_name(name))
        res = self.__get_class_from_identifier(identifier, 'class-name')
        if is_error(res):
            return res

        class_context, meta_data = res

        strategy = class_context.get_distribution_strategy()
        if not isinstance(strategy, zip(*getmembers(sofa_strategies, isclass))[1]):
            return STATUS_NOT_FOUND, strategy.__class__.__name__, "is an invalid strategy"

        block_count = 0
        num_storage_nodes = self.__num_storage_nodes
        create_new_stride = True

        max_stride = 1
        if isinstance(strategy, sofa_strategies.Linear):
            # Using ceil to make sure that there isn't too many on last server
            # Example: Outcome of 100 / 3 should be 34, 34, 32 rather than 33, 33, 34
            max_stride = int(ceil(strategy.num_blocks / float(num_storage_nodes)))
        if isinstance(strategy, sofa_strategies.Tiles):
            max_stride = strategy.num_tiles

        # Include calculation on whether the dataset already has blocks
        start = int(floor((meta_data['root-idx'] + (meta_data['num-blocks'] / max_stride)) % self.__num_storage_nodes))
        current_stride = int(meta_data['num-blocks'] % max_stride)

        # Clean function cache
        self.__gcs.delete(identifier)

        if is_serialized and class_context.is_serialized():
            if isinstance(data, unicode):
                data = data.encode("ascii")

            data = class_context.deserialize(data)

        # Preprocess data if needed
        from netCDF4 import Dataset
        data = class_context.preprocess(data)

        replication_factor = class_context.get_replication_factor()
        if replication_factor > num_storage_nodes:
            return STATUS_NOT_ALLOWED, "Replication factor can't be larger than number of storage nodes"

        fd = FunctionDelegation(identifier) \
            .as_required_queue_delegation(None, class_context.get_replication_factor())

        nodes_with_blocks = []

        for block in self.__next_block(class_context, data):
            # Serialize data if needed
            if class_context.is_serialized():
                block = class_context.serialize(block)

            # Store at primary replica first
            storage_node = self.__storage_nodes[start]
            storage_node.append(fd, identifier, block, create_new_stride)
            nodes_with_blocks.append(storage_node.get_uri())

            block_count += 1
            current_stride += 1

            # Create new stride if first iteration or max local block count reached
            create_new_stride = current_stride == max_stride

            if create_new_stride:
                current_stride = 0
                start = (start + 1) % num_storage_nodes

        fd = FunctionDelegation(identifier) \
            .as_dispatch_delegation() \
            .as_required_queue_delegation(None, class_context.get_replication_factor())

        self.__get_storage_node().update_meta_key(fd, identifier, 'append', 'num-blocks', block_count)
        unique_nodes_with_blocks = unique_and_preserve(nodes_with_blocks)
        self.__get_storage_node().update_meta_key(fd, identifier, 'append', 'storage-nodes', unique_nodes_with_blocks)

    def __next_block(self, context, data):
        block = []
        block_size = 0
        for entry in context.next_entry(data):
            entry_size = get_size(entry)
            if entry_size == 0:
                continue

            if block_size + entry_size > self.__block_size:
                if len(block) == 0:
                    block.append(entry)

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
        return self.__get_property(name, 'operations')

    def get_datasets(self):
        return self.__get_storage_node().get_datasets()

    def get_submitted_jobs(self):
        return self.__get_storage_node().get_submitted_jobs()

    def get_description(self, name):
        return self.__get_property(name, 'description')

    def submit_job(self, name, function, query):
        didentifier = self.__find_identifier(self.__virtualize_name(name))
        fidentifier = find_identifier("%s:%s:%s" % (didentifier, function, query), None)

        result_cache = self.__gcs.get(didentifier)
        if fidentifier in result_cache:
            # We already have the value
            return

        process_state = {
            'function-name': function,
            'fidentifier': fidentifier,
            'dataset-name': name,
            'query': query,
        }

        result_cache[fidentifier] = (STATUS_PROCESSING, None)

        fd = FunctionDelegation(didentifier) \
            .as_dispatch_delegation() \
            .as_forward_queue_delegation(None, self.__config.load_balancing_threshold, None)

        self.__get_storage_node().submit_job(fd, didentifier, process_state, self.__config.node)

    def poll_for_result(self, name, function, query):
        didentifier = self.__find_identifier(self.__virtualize_name(name))
        fidentifier = find_identifier("%s:%s:%s" % (didentifier, function, query), None)

        result_cache = self.__gcs.get(didentifier)
        if fidentifier not in result_cache:
            return STATUS_NOT_FOUND, None

        job_res = result_cache[fidentifier]
        if is_processing(job_res):
            return STATUS_PROCESSING, None

        job_res = job_res[1]
        return STATUS_SUCCESS, (job_res, isinstance(job_res, str) and path.exists(job_res))

    # Internal Result Api
    def set_status_result(self, didentifier, fidentifier, status, result):
        self.__gcs.get(didentifier)[fidentifier] = (status, result)
