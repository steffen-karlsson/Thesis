# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from shelve import open
from math import floor
from sys import getsizeof
from logging import info
from ujson import loads as uloads, dumps as udumps
from types import FunctionType
from multiprocessing.pool import ThreadPool

from bdae.handler import get_class_from_source
from bdae.utils import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, \
    STATUS_SUCCESS, STATUS_PROCESSING, is_error
from bdae.secure import secure_load, secure_load2
from bdae.tree_barrier import TreeBarrier
from bdae.cache import CacheSystem
from bdae.handler.api import InternalStorageApi, InternalGatewayApi
from bdae.operation import Sequential as SequentialOperation, Parallel as ParallelOperation


class StorageHandler(object):
    def __init__(self, config, others):
        self.__config = config
        self.__tb = None
        self.__scs = CacheSystem(dict)
        self.__RAW = open("bdae_raw.db", writeback=True)
        self.__FLAG = open("bdae_flag.db", writeback=True)

        if 'storage' in others:
            self.__storage_nodes = [InternalStorageApi(storage_uri) for storage_uri in others['storage']]
        else:
            self.__storage_nodes = []

        self.__num_storage_nodes = len(self.__storage_nodes) + 1  # Plus self
        self.__space_size = self.__config.keyspace_size / self.__num_storage_nodes

    def __dataset_exists(self, identifier):
        return str(identifier) in self.__FLAG

    def __find_responsibility(self, identifier):
        responsible = int(floor(identifier / self.__space_size))
        if self.__config.node_idx == responsible:
            return None

        return self.__storage_nodes[responsible]

    def create(self, bundle):
        identifier, jdataset = secure_load(bundle)

        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.create(identifier, jdataset)

        # Else do the job self.
        info("Creating dataset with identifier %s on %s." % (identifier, self.__config.node))
        if self.__dataset_exists(identifier):
            return STATUS_ALREADY_EXISTS, "Dataset already exists"

        self.__FLAG[str(identifier)] = True
        self.__RAW[str(identifier)] = [jdataset]
        return STATUS_SUCCESS

    def append(self, bundle):
        identifier, block = secure_load(bundle)

        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.append(identifier, block)

        # Else do the job self.
        res = self.get_meta_from_identifier(identifier)
        if is_error(res):
            return res, "Dataset doesn't exists"

        info("Writing block of size %d to datatset with identifier %s on %s." % (
            getsizeof(block), identifier, self.__config.node))
        self.__RAW[str(identifier)].append(block)

        jdataset = uloads(res)
        jdataset['num-blocks'] = + 1

        self.__RAW[str(identifier)][0] = udumps(jdataset)
        return STATUS_SUCCESS

    def get_meta_from_identifier(self, identifier):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.get_meta_from_identifier(identifier)

        # Else do the job self.
        if not self.__dataset_exists(identifier):
            return STATUS_NOT_FOUND

        return self.__RAW[str(identifier)][0]

    def __get_functions(self, identifier, function_name, function_type, jdataset=None):
        if not jdataset:
            res = self.get_meta_from_identifier(identifier)
            if is_error(res):
                return res
            jdataset = uloads(res)

        if jdataset['num-blocks'] == 0:
            # No data found for data identifier
            return STATUS_NOT_FOUND

        if function_name not in jdataset[function_type]:
            return STATUS_NOT_FOUND

        source = secure_load2(jdataset['digest'], jdataset['source'])
        dataset = get_class_from_source(source, jdataset['dataset-name'])

        for operation_context in dataset.get_operations():
            if operation_context.fun_name == function_name:
                return operation_context, jdataset

    def submit_job(self, didentifier, fidentifier, function_type, function_name, query, gateway):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(didentifier)
        if responsible:
            return responsible.submit_job(didentifier, fidentifier, function_name, query, gateway)

        # Else do the job self.
        if self.__scs.contains(fidentifier):
            is_working, res, gateway = self.__scs.get(fidentifier)
            if is_working:
                # Similar job is in progress
                self.__terminate_job(fidentifier, STATUS_PROCESSING)
                return
            else:
                # Result already calculated with no dataset change
                self.__terminate_job(fidentifier, STATUS_SUCCESS)
                return

        operation_context, jdataset = self.__get_functions(didentifier, function_name, function_type)
        operations = list(operation_context.operations)
        initial_args = sum(self.__RAW[str(didentifier)][1:], []), query

        if len(self.__storage_nodes) == 0:
            # Im the only one
            res = _local_execute(operations, initial_args)
            self.__scs.put(fidentifier, (False, res, gateway))
            self.__terminate_job(fidentifier, STATUS_SUCCESS)
        else:
            # Broadcast storm to all other nodes
            for node in self.__storage_nodes:
                node.execute_function(0, self.__config.node, fidentifier, function_type,
                                      function_name, jdataset, query, 0)

            # If needed get ghosts from locals
            if operation_context.needs_ghost():
                # TODO Implement
                pass

            # Calculate self
            self.__scs.put(fidentifier, (True, _local_execute(operations, initial_args), gateway))

    def __terminate_job(self, fidentifier, status):
        _, res, gateway = self.__scs.get(fidentifier)
        InternalGatewayApi(gateway).set_status_result(fidentifier, status, res)

    # Internal Api
    def execute_function(self, itr, root, fidentifier, function_type, function_name, jdataset, query, prev_value):
        if itr == 0:
            self.__tb = TreeBarrier(self.__config.node, self.__storage_nodes, root)

            # TODO: Get operation_context, get ghosts if needed and calculate partial value

            # If needed get ghosts from locals

            partial_value = 0
            self.__scs.put(fidentifier, partial_value)  # TODO: triple as value

        try:
            if self.__tb.should_send(itr):
                self.__tb.get_receiver().execute_function(itr + 1, root, fidentifier, function_type, function_name,
                                                          jdataset, query)
                self.__scs.delete(fidentifier)
        except StopIteration:
            # TODO: Update __scs
            self.__terminate_job(fidentifier, STATUS_SUCCESS)
            pass

    # Internal Monitor Api
    def heartbeat(self):
        pass


def _is_function_type(operation):
    return isinstance(operation, FunctionType)


def _wrapper_local_execute(args):
    return _local_execute(*args)


def _local_execute(operations, args):
    try:
        operation = operations.pop(0)
        if isinstance(operation, SequentialOperation):
            return _local_execute(operations, _local_execute(list(operation.operations), args))

        if isinstance(operation, ParallelOperation):
            suboperations = operation.operations
            pool = ThreadPool(4)

            subargs = []
            for suboperation in suboperations:
                subargs.append((list(suboperation if _is_function_type(suboperation)
                                     else suboperation.operations), args))

            res = pool.map(_wrapper_local_execute, subargs)
            return _local_execute(operations, res)

        if _is_function_type(operation):
            res = operation(args)
            return _local_execute(operations, res)

    except IndexError:
        return args
