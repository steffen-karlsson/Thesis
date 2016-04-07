# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from shelve import open
from math import floor
from sys import getsizeof
from logging import info
from ujson import loads as uloads, dumps as udumps
from multiprocessing.pool import ThreadPool
from collections import defaultdict
from itertools import izip_longest, chain
from inspect import isfunction, isbuiltin

from sofa.handler import get_class_from_source
from sofa.error import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, STATUS_SUCCESS, \
    STATUS_PROCESSING, STATUS_NO_DATA, is_error
from sofa.secure import secure_load, secure_load2
from sofa.tree_barrier import TreeBarrier
from sofa.cache import CacheSystem
from sofa.handler.api import _InternalStorageApi, _InternalGatewayApi
from sofa.operation import Sequential as SequentialOperation, Parallel as ParallelOperation

RESULT = 0
REQUEST_COUNT = 1
IS_WORKING = 2
GATEWAY = 3


class StorageHandler(object):
    def __init__(self, config, others):
        self.__config = config
        self.__tb = None
        self.__srcs = CacheSystem(defaultdict, args=dict)  # Storage Result Cache System
        self.__dgcs = CacheSystem(defaultdict, args=dict)  # Dataset Ghosts Cache System
        self.__RAW = open("sofa_raw.db", writeback=True)
        self.__FLAG = open("sofa_flag.db", writeback=True)

        if 'storage' in others:
            self.__storage_nodes = [_InternalStorageApi(storage_uri) for storage_uri in others['storage']]
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

    def __handle_ghosts(self, didentifier, fidentifier, root, function_name, meta_data, query, local_transfer=False):
        info("Handle ghosts at " + str(self.__config.node))
        res = self.__get_operation_context(None, function_name, meta_data=meta_data)
        if is_error(res):
            self.__terminate_job(didentifier, fidentifier, STATUS_NO_DATA)

        operation_context, _ = res
        if not operation_context.needs_ghost():
            # We don't need to handle ghosts
            info("No need for ghosts at " + str(self.__config.node))
            self.__report_ready(didentifier, fidentifier, function_name, meta_data, query)
            return

        is_root = self.__config.node == root
        left_ghost, right_ghost, l_neighbor, r_neighbor = (None,) * 4
        if not local_transfer:
            l_neighbor, r_neighbor = self.__get_neighbors()

        send_left = operation_context.ghost_right and (l_neighbor or local_transfer)
        send_right = operation_context.ghost_left and (r_neighbor or local_transfer)

        self_data = self.__get_raw_data_block(didentifier, is_root)
        if send_left:
            # Only the blocks and the edge between nodes, that's why 0
            right_ghost = [block[0][:operation_context.ghost_count] for block in self_data]

            if local_transfer or is_root:
                if operation_context.use_cyclic:
                    overflow = right_ghost[0]
                    # TODO: No wrapping supported, implement on last node for this dataset
                    pass

                # Only storage node in the system or previous node doesn't need first when sending left
                right_ghost = right_ghost[1:]

        if send_right:
            # Only the blocks and the edge between nodes, that's why -1
            left_ghost = [block[-1][-operation_context.ghost_count:] for block in self_data]

            if operation_context.use_cyclic:
                overflow = left_ghost[-1]
                # TODO: No wrapping supported, implement on last node for this dataset
                pass

        assert left_ghost is not None or right_ghost is not None

        needs_both = operation_context.ghost_right and operation_context.ghost_left
        fun_args = (didentifier, fidentifier, needs_both, (function_name, meta_data, root, query))

        if local_transfer:
            self.__local_send_ghost(left_ghost, right_ghost, *fun_args)
            return

        if send_left:
            info("Sending ghost left from: " + self.__config.node + ": " + str(right_ghost))
            l_neighbor.send_ghost(None, right_ghost, *fun_args)

        if send_right:
            info("Sending ghost right from: " + self.__config.node + ": " + str(left_ghost))
            r_neighbor.send_ghost(left_ghost, None, *fun_args)

    def create(self, bundle):
        identifier, meta_data, is_update = secure_load(bundle)

        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.create(identifier, meta_data, is_update)

        if is_update:
            # TODO: Block from calling any other operation on that dataset, while update is finishing
            pass

        meta_data = uloads(meta_data)
        meta_data['root-idx'] = self.__config.node_idx

        # Else do the job self.
        if self.__dataset_exists(identifier) and not is_update:
            return STATUS_ALREADY_EXISTS, "Dataset already exists"

        info("Creating dataset with identifier %s on %s." % (identifier, self.__config.node))

        self.__FLAG[str(identifier)] = True
        self.__RAW[str(identifier)] = [udumps(meta_data)]
        return STATUS_SUCCESS

    def append(self, bundle):
        # TODO: Block from calling any other operation on that dataset, while append is finishing
        identifier, block, create_new_stride = secure_load(bundle)

        res = self.get_meta_from_identifier(identifier)
        if is_error(res):
            return res, "Dataset doesn't exists"

        info("Writing block of size %d to datatset with identifier %s on %s." % (
            getsizeof(block), identifier, self.__config.node))

        identifier = str(identifier)
        if identifier not in self.__RAW:
            self.__RAW[identifier] = []

        if create_new_stride:
            self.__RAW[identifier].append([block])
        else:
            self.__RAW[identifier][-1].append(block)

        # Delete local cache, since dataset is appended
        self.__srcs.delete(identifier)

        return STATUS_SUCCESS

    def delete(self, identifier):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.delete(identifier)

        # Else do the job self.
        # TODO: Block from calling any other operation on that dataset
        # TODO: Delete all blocks

        # Delete local cache, since dataset is removed
        self.__srcs.delete(identifier)
        # TODO: delete identifier from self.__dgcs
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

        meta_data = uloads(res)
        if update_type == 'append':
            meta_data[key] += value

        if update_type == 'override':
            meta_data[key] = value

        info("%s is %s with %d" % (key, update_type, value))

        self.__RAW[str(identifier)][0] = udumps(meta_data)
        return STATUS_SUCCESS

    def __get_raw_data_block(self, didentifier, is_root, iflatten=False):
        blocks = self.__RAW[str(didentifier)][1 if is_root else 0:]
        return chain(*blocks) if iflatten else blocks

    def __get_operation_context(self, didentifier, function_name, meta_data=None):
        if not meta_data:
            res = self.get_meta_from_identifier(didentifier)
            if is_error(res):
                return res
            meta_data = uloads(res)

        if meta_data['num-blocks'] == 0:
            # No data found for data identifier
            return STATUS_NOT_FOUND

        source = secure_load2(meta_data['digest'], meta_data['source'])
        dataset = get_class_from_source(source, meta_data['class-name'])

        # TODO: check for get_operations
        for operation_context in dataset.get_operations():
            if operation_context.fun_name == function_name:
                return operation_context, meta_data

        return STATUS_NOT_FOUND

    def __get_operations_and_arguments(self, didentifier, fidentifier, operation_context, query, is_root):
        # Get operations and blocks to work on
        # TODO: check for get_operations
        operations = operation_context.get_operations()

        def _get_blocks_with_ghost():
            ghosts = self.__dgcs.get(fidentifier)

            # Merge ghosts into blocks
            for l, m, r in izip_longest(ghosts['ghost-left'] if 'ghost-left' in ghosts else [None],
                                        self.__get_raw_data_block(didentifier, is_root),
                                        ghosts['ghost-right'] if 'ghost-right' in ghosts else [None]):
                # Ensure all data is lists for list concatenation
                if not l:
                    l = []
                if not r:
                    r = []

                yield l + sum(m, []) + r

        if self.__dgcs.contains(fidentifier):
            blocks = _get_blocks_with_ghost()
        else:
            # Use chain generator method (iflatten) to reduce memory consumption
            blocks = self.__get_raw_data_block(didentifier, is_root, iflatten=True)

        if operation_context.has_multiple_args():
            args = [blocks] + str(query).split(operation_context.delimiter)
        else:
            args = [blocks, query]

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
        all_nodes = self.__num_storage_nodes + 1
        self.__srcs.get(didentifier)[fidentifier] = [None, all_nodes, True, gateway]

        res = self.get_meta_from_identifier(didentifier)
        if is_error(res):
            return res
        meta_data = uloads(res)

        root = self.__config.node
        common = (didentifier, fidentifier, function_name, meta_data, root, query)
        if all_nodes > 1:
            # Broadcast storm to all nodes
            info("Pool _wrapper_initialize_execution")
            args = [(self, common)] + [(node, common) for node in self.__storage_nodes]
            ThreadPool(all_nodes).map_async(_wrapper_initialize_execution, args)
        else:
            # Calculate self
            self.initialize_execution(*common)

    def __terminate_job(self, didentifier, fidentifier, status):
        data = self.__srcs.get(didentifier)[fidentifier]

        if is_error(status):
            # Remove existing result if an error occurs
            del self.__srcs.get(didentifier)[fidentifier]

        _InternalGatewayApi(data[GATEWAY]).set_status_result(didentifier, fidentifier, status, data[RESULT])

    # Internal Api
    def initialize_execution(self, didentifier, fidentifier, function_name, meta_data, root, query):
        info("Initialize execution at " + str(self.__config.node))

        self.__tb = TreeBarrier(self.__config.node,
                                list(self.__config.others['storage']) if 'storage' in self.__config.others else [],
                                root)

        # If im the only node in the system
        use_local_transfer = self.__num_storage_nodes == 0

        # Find ghosts from local neighbors if needed else execute
        self.__handle_ghosts(didentifier, fidentifier, root, function_name, meta_data, query,
                             local_transfer=use_local_transfer)

    def execute_function(self, itr, didentifier, fidentifier, function_name, meta_data, root, query, recv_value):
        info("Execute function " + function_name + " at " + str(self.__config.node))

        is_root = self.__config.node == root
        first_iteration = itr == 0

        operation_context, _ = self.__get_operation_context(None, function_name, meta_data=meta_data)
        operations = operation_context.get_operations()
        reduce_operation = operations[-1]

        # See if its first iteration or the cache has the value
        has_result = self.__srcs.contains(didentifier) \
                     and fidentifier in self.__srcs.get(didentifier) \
                     and self.__srcs.get(didentifier)[fidentifier][RESULT]

        if not has_result:
            _, args = self.__get_operations_and_arguments(didentifier, fidentifier, operation_context,
                                                          query, is_root)
            res = _local_execute(operations, args)
            info("Result for " + self.__config.node + " is: " + str(res))
            if is_root:
                gateway = self.__srcs.get(didentifier)[fidentifier][GATEWAY]
                self.__srcs.get(didentifier)[fidentifier] = [res, None, True, gateway]
            else:
                self.__srcs.get(didentifier)[fidentifier] = [res]

        try:
            res = self.__srcs.get(didentifier)[fidentifier][RESULT]
            if self.__tb.should_send(itr):
                receiver = self.__storage_nodes[self.__tb.get_receiver_idx()]
                info("Sending from " + self.__config.node + " to the next")
                receiver.execute_function(itr + 1, didentifier, fidentifier, function_name, meta_data, root, None, res)
                return

            if not first_iteration:
                self.__srcs.get(didentifier)[fidentifier] = [reduce_operation((recv_value, res))]
        except StopIteration:
            data = self.__srcs.get(didentifier)[fidentifier]

            if first_iteration:
                res = data[RESULT]
            else:
                res = reduce_operation((recv_value, data[RESULT]))

            info("Finishing with result: " + str(res))
            self.__srcs.get(didentifier)[fidentifier] = [res, None, False, data[GATEWAY]]
            self.__terminate_job(didentifier, fidentifier, STATUS_SUCCESS)
            pass

    def __report_ready(self, didentifier, fidentifier, function_name, meta_data, query):
        responsible = self.__find_responsibility(didentifier)
        args = didentifier, fidentifier, function_name, meta_data, query
        if responsible:
            info("Reporting ready for other at: " + self.__config.node)
            responsible.ready(*args)
        else:
            info("Reporting ready for self")
            self.__local_ready(*args)

    def ready(self, bundle):
        self.__local_ready(*secure_load(bundle))

    def __local_ready(self, didentifier, fidentifier, function_name, meta_data, query):
        self.__srcs.get(didentifier)[fidentifier][REQUEST_COUNT] -= 1
        info("Local request count: " + str(self.__srcs.get(didentifier)[fidentifier][REQUEST_COUNT]))

        if self.__srcs.get(didentifier)[fidentifier][REQUEST_COUNT] < 1:
            common = (0, didentifier, fidentifier, function_name, meta_data, self.__config.node, query, 0)

            if self.__num_storage_nodes > 0:
                info("Pool _wrapper_execute_function")
                args = [(self, common)] + [(node, common) for node in self.__storage_nodes]
                all_nodes = self.__num_storage_nodes + 1
                ThreadPool(all_nodes).map_async(_wrapper_execute_function, args)
            else:
                self.execute_function(*common)

    def __local_send_ghost(self, left_ghost, right_ghost, didentifier, fidentifier, needs_both, fun_args):
        info("Receiving ghost at " + self.__config.node)

        assert left_ghost is not None or right_ghost is not None
        function_name, meta_data, root, query = fun_args

        if left_ghost is not None:
            is_ghost_right = False
            is_root = self.__config.node == root
            num_blocks = len(self.__RAW[str(didentifier)]) - (1 if is_root else 0)

            if root or len(left_ghost) < num_blocks:
                # Received too much and shifted data
                left_ghost = [None] + left_ghost[:-1]
            elif len(left_ghost) > num_blocks:
                # Received too much data
                left_ghost = left_ghost[:-1]

            info("Setting left ghost data: " + str(left_ghost) + ", needs both: " + str(needs_both))
            self.__dgcs.get(fidentifier)['ghost-left'] = left_ghost

        if right_ghost is not None:
            is_ghost_right = True
            info("Setting right ghost data: " + str(right_ghost) + ", needs both: " + str(needs_both))
            self.__dgcs.get(fidentifier)['ghost-right'] = right_ghost

        has_other_part = ('ghost-left' if is_ghost_right else 'ghost-right') in self.__dgcs.get(fidentifier)
        if has_other_part or not needs_both:
            self.__report_ready(didentifier, fidentifier, function_name, meta_data, query)

    def send_ghost(self, bundle):
        self.__local_send_ghost(*secure_load(bundle))

    # Internal Monitor Api
    def heartbeat(self):
        pass


def _wrapper_initialize_execution(args):
    return args[0].initialize_execution(*args[1])


def _wrapper_execute_function(args):
    args[0].execute_function(*args[1])


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
                subargs.append((list(suboperation if (isfunction(suboperation) or isbuiltin(suboperation))
                                     else suboperation.functions), args))

            res = pool.map(_wrapper_local_execute, subargs)
            return _local_execute(operations, res)

        if isfunction(operation) or isbuiltin(operation):
            res = operation(args)
            return _local_execute(operations, res)

    except IndexError:
        return args
