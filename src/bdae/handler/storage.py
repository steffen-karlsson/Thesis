# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from shelve import open
from math import floor
from sys import getsizeof
from logging import info
from ujson import loads as uloads, dumps as udumps
from types import FunctionType
from multiprocessing.pool import ThreadPool
from collections import defaultdict
from itertools import izip_longest

from bdae.handler import get_class_from_source
from bdae.utils import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, \
    STATUS_SUCCESS, STATUS_PROCESSING, is_error
from bdae.secure import secure_load, secure_load2
from bdae.tree_barrier import TreeBarrier
from bdae.cache import CacheSystem
from bdae.handler.api import InternalStorageApi, InternalGatewayApi
from bdae.operation import Sequential as SequentialOperation, Parallel as ParallelOperation, OperationContext

RESULT = 0
FUNCTION_ARGUMENTS = 1
IS_WORKING = 2
GATEWAY = 3


class StorageHandler(object):
    def __init__(self, config, others):
        self.__config = config
        self.__tb = None
        self.__srcs = CacheSystem(defaultdict, args=dict)  # Storage Result Cache System
        self.__dgcs = CacheSystem(defaultdict, args=dict)  # Dataset Ghosts Cache System
        self.__RAW = open("bdae_raw.db", writeback=True)
        self.__FLAG = open("bdae_flag.db", writeback=True)

        if 'storage' in others:
            self.__storage_nodes = [InternalStorageApi(storage_uri) for storage_uri in others['storage']]
        else:
            self.__storage_nodes = []

        self.__num_storage_nodes = len(self.__storage_nodes)
        self.__neighbors = self.__get_neighbors()
        self.__space_size = self.__config.keyspace_size / (self.__num_storage_nodes + 1)  # Plus self

    def __get_neighbors(self):
        if self.__num_storage_nodes == 0:
            return None

        prev = self.__storage_nodes[(self.__config.node_idx - 1) % self.__num_storage_nodes]
        nxt = self.__storage_nodes[self.__config.node_idx % self.__num_storage_nodes]
        return prev, nxt

    def __dataset_exists(self, didentifier):
        return str(didentifier) in self.__FLAG

    def __find_responsibility(self, didentifier):
        responsible = int(floor(didentifier / self.__space_size))
        if self.__config.node_idx == responsible:
            return None

        return self.__storage_nodes[responsible - 1]  # Self is not included in __storage_nodes

    def __handle_ghosts(self, didentifier, fidentifier, operation_context, root, local_transfer=False):
        if not operation_context.needs_ghost():
            # We don't need to handle ghosts
            return False

        is_root = self.__config.node == root
        ghost, l_neighbor, r_neighbor = (None,) * 3
        if not local_transfer:
            l_neighbor, r_neighbor = self.__get_neighbors()

        send_left = operation_context.ghost_right and (l_neighbor or local_transfer)
        send_right = operation_context.ghost_left and (r_neighbor or local_transfer)

        self_data = self.__get_raw_data_block(didentifier, is_root)
        if send_left:
            if operation_context.ghost_type == OperationContext.GhostType.ENTRY:
                ghost = [block[:operation_context.ghost_count] for block in self_data]

                if is_root:
                    # No wrapping supported
                    ghost[0] = None

                if local_transfer:
                    # Only storage node in the system
                    ghost[0] = None

        if send_right:
            if operation_context.ghost_type == OperationContext.GhostType.ENTRY:
                ghost = [block[-operation_context.ghost_count:] for block in self_data]

        assert ghost is not None

        needs_both = operation_context.ghost_right and operation_context.ghost_left

        if local_transfer:
            # TODO: Send both right and left if needed
            self.__local_send_ghost(ghost, didentifier, fidentifier, root,
                                    is_ghost_right=operation_context.ghost_right,
                                    needs_both=needs_both)
            return True

        if send_left:
            l_neighbor.send_ghost(ghost, didentifier, fidentifier, root, True, needs_both)

        if send_right:
            r_neighbor.send_ghost(ghost, didentifier, fidentifier, root, False, needs_both)

    def create(self, bundle):
        identifier, jdataset = secure_load(bundle)

        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.create(identifier, jdataset)

        # Else do the job self.
        if self.__dataset_exists(identifier):
            return STATUS_ALREADY_EXISTS, "Dataset already exists"

        info("Creating dataset with identifier %s on %s." % (identifier, self.__config.node))

        self.__FLAG[str(identifier)] = True
        self.__RAW[str(identifier)] = [jdataset]
        return STATUS_SUCCESS

    def append(self, bundle):
        identifier, block = secure_load(bundle)

        res = self.get_meta_from_identifier(identifier)
        if is_error(res):
            return res, "Dataset doesn't exists"

        info("Writing block of size %d to datatset with identifier %s on %s." % (
            getsizeof(block), identifier, self.__config.node))

        identifier = str(identifier)
        if identifier not in self.__RAW:
            self.__RAW[identifier] = []
        self.__RAW[identifier].append(block)

        # Delete local cache, since dataset is appended
        self.__srcs.delete(identifier)

        return STATUS_SUCCESS

    def get_meta_from_identifier(self, didentifier):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(didentifier)
        if responsible:
            return responsible.get_meta_from_identifier(didentifier)

        # Else do the job self.
        if not self.__dataset_exists(didentifier):
            return STATUS_NOT_FOUND

        return self.__RAW[str(didentifier)][0]

    def update_meta_key(self, bundle):
        identifier, update_type, key, value = secure_load(bundle)

        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.update_meta_key(identifier, update_type, key, value)

        # Else do the job self.
        res = self.get_meta_from_identifier(identifier)
        if is_error(res):
            return res, "Dataset doesn't exists"

        jdataset = uloads(res)
        if update_type == 'append':
            jdataset[key] += value

        if update_type == 'override':
            jdataset[key] = value

        info("%s is %s with %d" % (key, update_type, value))

        self.__RAW[str(identifier)][0] = udumps(jdataset)
        return STATUS_SUCCESS

    def __get_raw_data_block(self, didentifier, is_root):
        return self.__RAW[str(didentifier)][1 if is_root else 0:]

    def __get_operation_context(self, didentifier, function_name, jdataset=None):
        if not jdataset:
            res = self.get_meta_from_identifier(didentifier)
            if is_error(res):
                return res
            jdataset = uloads(res)

        if jdataset['num-blocks'] == 0:
            # No data found for data identifier
            return STATUS_NOT_FOUND

        source = secure_load2(jdataset['digest'], jdataset['source'])
        dataset = get_class_from_source(source, jdataset['dataset-name'])

        for operation_context in dataset.get_operations():
            if operation_context.fun_name == function_name:
                return operation_context, jdataset

        return STATUS_NOT_FOUND

    def __get_operations_and_arguments(self, didentifier, fidentifier, operation_context, query, is_root):
        # Get operations and blocks to work on
        operations = list(operation_context.operations)
        blocks = self.__get_raw_data_block(didentifier, is_root)

        if self.__dgcs.contains(fidentifier):
            ghosts = self.__dgcs.get(fidentifier)
            # Merge ghosts into blocks

            for idx, (l, m, r) in enumerate(izip_longest(ghosts['ghost_left'] if 'ghost_left' in ghosts else [None],
                                                         blocks,
                                                         ghosts['ghost_right'] if 'ghost_right' in ghosts else [None])):
                # Ensure all data is lists for list concatenation
                if not l:
                    l = []
                if not r:
                    r = []

                blocks[idx] = l + m + r

        if operation_context.has_multiple_args():
            query = str(query).split(operation_context.delimiter)
        else:
            query = [query]

        args = [blocks] + query
        return operations, args

    def submit_job(self, didentifier, fidentifier, function_name, query, gateway):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(didentifier)
        if responsible:
            return responsible.submit_job(didentifier, fidentifier, function_name, query, gateway)

        # Else do the job self.
        has_result = self.__srcs.contains(didentifier) and fidentifier in self.__srcs.get(didentifier)
        if has_result:
            data = self.__srcs.get(didentifier)[fidentifier]
            if data[IS_WORKING]:
                # Similar job is in progress
                self.__terminate_job(didentifier, fidentifier, STATUS_PROCESSING)
                return
            else:
                # Result already calculated with no dataset change
                self.__terminate_job(didentifier, fidentifier, STATUS_SUCCESS)
                return

        # Update is working state before anything else
        self.__srcs.get(didentifier)[fidentifier] = [0, None, True, gateway]

        res = self.get_meta_from_identifier(didentifier)
        if is_error(res):
            return res
        jdataset = uloads(res)

        # Calculate self
        self.initialize_execution(didentifier, fidentifier, function_name, jdataset, self.__config.node, query)
        # TODO: Fork this execution into seperate process async to continue executing on other nodes
        # TODO: Fix potential deadlock if self hasn't executed yet before slaves has finished

        if len(self.__storage_nodes) > 0:
            # Broadcast storm to all other nodes
            for node in self.__storage_nodes:
                node.initialize_execution(didentifier, fidentifier, function_name, jdataset, self.__config.node, query)

    def __terminate_job(self, didentifier, fidentifier, status):
        data = self.__srcs.get(didentifier)[fidentifier]
        InternalGatewayApi(data[GATEWAY]).set_status_result(fidentifier, status, data[RESULT])

    # Internal Api
    def initialize_execution(self, didentifier, fidentifier, function_name, jdataset, root, query):
        self.__tb = TreeBarrier(self.__config.node,
                                list(self.__config.others['storage']) if 'storage' in self.__config.others else [],
                                root)

        use_local_transfer = len(self.__storage_nodes) == 0  # Im the only node in the system
        is_root = self.__config.node == root
        if not is_root:
            # Initialize function meta on rest except root, which is initialized in submit_job
            self.__srcs.get(didentifier)[fidentifier] = [0, None]

        operation_context, _ = self.__get_operation_context(None, function_name, jdataset=jdataset)
        fun_arguments = [0, didentifier, fidentifier, function_name, jdataset, root, query, 0]
        self.__srcs.get(didentifier)[fidentifier][FUNCTION_ARGUMENTS] = fun_arguments

        # Find ghosts from local neighbors if needed else execute
        if not self.__handle_ghosts(didentifier, fidentifier, operation_context, root,
                                    local_transfer=use_local_transfer):
            # Execute normally without ghosts
            self.execute_function(*fun_arguments)

    def execute_function(self, itr, didentifier, fidentifier, function_name, jdataset, root, query, recv_value):
        # Reset arguments to save space
        self.__srcs.get(didentifier)[fidentifier][FUNCTION_ARGUMENTS] = None

        is_root = self.__config.node == root
        first_iteration = itr == 0

        operation_context, _ = self.__get_operation_context(None, function_name, jdataset=jdataset)
        operations, args = self.__get_operations_and_arguments(didentifier, fidentifier, operation_context,
                                                               query, is_root)
        reduce_operation = operations[-1]

        # See if its first iteration or the cache has the value
        has_result = self.__srcs.contains(didentifier) and fidentifier in self.__srcs.get(didentifier)
        if first_iteration or not has_result:
            res = _local_execute(operations, args)
            if is_root:
                gateway = self.__srcs.get(didentifier)[fidentifier][GATEWAY]
                self.__srcs.get(didentifier)[fidentifier] = [res, None, True, gateway]
            else:
                self.__srcs.get(didentifier)[fidentifier] = [res, None]

        try:
            res = self.__srcs.get(didentifier)[fidentifier][RESULT]
            if self.__tb.should_send(itr):
                receiver = self.__storage_nodes[self.__tb.get_receiver_idx()]
                receiver.execute_function(itr + 1, didentifier, fidentifier,
                                          function_name, jdataset, root, None, res)
                return

            if not first_iteration:
                self.__srcs.get(didentifier)[fidentifier] = [reduce_operation((recv_value, res))]
        except StopIteration:
            data = self.__srcs.get(didentifier)[fidentifier]

            if first_iteration:
                res = data[RESULT]
            else:
                res = reduce_operation((recv_value, data[RESULT]))

            self.__srcs.get(didentifier)[fidentifier] = [res, None, False, data[GATEWAY]]
            self.__terminate_job(didentifier, fidentifier, STATUS_SUCCESS)
            pass

    def __local_send_ghost(self, data, didentifier, fidentifier, root, is_ghost_right, needs_both):
        is_root = self.__config.node == root
        if is_root:
            # No wrapping supported
            data = [None] + data[:-1]
        elif len(data) < len(self.__RAW[str(didentifier)]):
            # Received too much data
            data = data[:-1]

        self.__dgcs.get(fidentifier)['ghost_right' if is_ghost_right else 'ghost_left'] = data
        info("DATA: " + str(data) + " Is ghost right: " + str(is_ghost_right) + " Needs both: " + str(needs_both))

        has_other_part = 'ghost_left' if is_ghost_right else 'ghost_right' in self.__dgcs.get(fidentifier)
        if has_other_part or not needs_both:
            self.execute_function(*self.__srcs.get(didentifier)[fidentifier][FUNCTION_ARGUMENTS])

    def send_ghost(self, bundle):
        self.__local_send_ghost(*secure_load(bundle))

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
            return _local_execute(operations, _local_execute(list(operation.functions), args))

        if isinstance(operation, ParallelOperation):
            suboperations = operation.functions
            pool = ThreadPool(4)

            subargs = []
            for suboperation in suboperations:
                subargs.append((list(suboperation if _is_function_type(suboperation)
                                     else suboperation.functions), args))

            res = pool.map(_wrapper_local_execute, subargs)
            return _local_execute(operations, res)

        if _is_function_type(operation):
            res = operation(args)
            return _local_execute(operations, res)

    except IndexError:
        return args
