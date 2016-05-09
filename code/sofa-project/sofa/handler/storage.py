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
from re import compile

from sofa.handler import get_class_from_source
from sofa.error import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, STATUS_SUCCESS, \
    STATUS_PROCESSING, STATUS_NO_DATA, is_error
from sofa.secure import secure_load, secure_load2
from sofa.tree_barrier import TreeBarrier
from sofa.cache import CacheSystem
from sofa.handler.api import _InternalStorageApi, _InternalGatewayApi
from sofa.foundation.operation import Sequential as SequentialOperation, Parallel as ParallelOperation

RESULT = 0
REQUEST_COUNT = 1
IS_WORKING = 2
GATEWAY = 3


def _forward_and_extract(fun, num_args):
    # Forwards to the right function (fun) with possible extracted arguments based on the pattern
    # defined in KEYWORDS and as argument to _forward_extract_args.
    def _forward_extract_args(fun_name, operation_context_args, args):
        has_arguments = ':' in fun_name
        expects_arguments = num_args > 0
        if has_arguments and expects_arguments:
            key_fun_args = fun_name.split(":")[1:]
            if key_fun_args != num_args:
                # TODO: throw exception
                pass

            return fun(args[0], args[1:], operation_context_args, tuple(key_fun_args))
        else:
            return fun(args[0], args[1:], operation_context_args)

    return _forward_extract_args


# Function for KEYWORD: neighborhood
def _exchange_neighborhood(self, args, operation_context_args, ghost_count=(1, 1)):
    pass

KEYWORDS = {compile("neighborhood(?::\d:\d)?$"): _forward_and_extract(_exchange_neighborhood, 2)}


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

    def __get_ghosts(self, is_left_ghost, is_right_ghost, ghost_count, didentifier, use_cyclic, is_local_transfer):
        # is_left_ghost = True if sending right
        # is_right_ghost = True if sending left

        is_root = str(didentifier) in self.__FLAG
        self_data = self.__get_raw_blocks(didentifier)
        left_ghost, right_ghost = (None,) * 2

        if is_right_ghost:
            # Only the blocks and the edge between nodes, that's why 0
            right_ghost = [block[0][:ghost_count] for block in self_data]

            if is_local_transfer or is_root:
                if use_cyclic:
                    overflow = right_ghost[0]
                    # TODO: No wrapping supported, implement on last node
                    pass

                # Only storage node in the system or previous node doesn't need first when sending left
                right_ghost = right_ghost[1:]

        if is_left_ghost:
            # Only the blocks and the edge between nodes, that's why -1
            left_ghost = [block[-1][-ghost_count:] for block in self_data]

            if use_cyclic:
                overflow = left_ghost[-1]
                # TODO: No wrapping supported, implement on last node
                pass

        return left_ghost, right_ghost

    def __context_exists(self, didentifier):
        return str(didentifier) in self.__FLAG

    def __find_responsibility(self, didentifier):
        responsible = int(floor(didentifier / self.__space_size))
        if self.__config.node_idx == responsible:
            return None

        return self.__storage_nodes[responsible - 1]  # Self is not included in __storage_nodes

    def __handle_ghosts(self, didentifier, operation_context, done_callback_handler, is_local_transfer=False):
        left_ghost, right_ghost, l_neighbor, r_neighbor = (None,) * 4
        if not is_local_transfer:
            l_neighbor, r_neighbor = self.__get_neighbors()

        send_left = operation_context.ghost_right and (l_neighbor or is_local_transfer)
        send_right = operation_context.ghost_left and (r_neighbor or is_local_transfer)

        left_ghost, right_ghost = self.__get_ghosts(send_right, send_left, operation_context.ghost_count, didentifier,
                                                    operation_context.use_cyclic, is_local_transfer)

        if is_local_transfer:
            done_callback_handler(is_ready=False, left=(None, left_ghost), right=(None, right_ghost))
            return

        done_callback_handler(is_ready=False, left=(l_neighbor, right_ghost), right=(r_neighbor, left_ghost))

    def create(self, bundle):
        identifier, meta_data, is_update = secure_load(bundle)

        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.create(identifier, meta_data, is_update)

        if is_update:
            # TODO: Block from calling any other operation on this context, while update is finishing
            pass

        meta_data = uloads(meta_data)
        meta_data['root-idx'] = self.__config.node_idx

        # Else do the job self.
        if self.__context_exists(identifier) and not is_update:
            return STATUS_ALREADY_EXISTS, "Dataset already exists"

        info("Creating context with identifier %s on %s." % (identifier, self.__config.node))

        self.__FLAG[str(identifier)] = True
        self.__RAW[str(identifier)] = [udumps(meta_data)]
        return STATUS_SUCCESS

    def append(self, bundle):
        # TODO: Block from calling any other operation on this context, while append is finishing
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

        # Delete local cache, since context is appended
        self.__srcs.delete(identifier)

        return STATUS_SUCCESS

    def delete(self, identifier):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(identifier)
        if responsible:
            return responsible.delete(identifier)

        # Else do the job self.
        # TODO: Block from calling any other operation on this context

        # Delete all blocks
        local_blocks = len(self.__RAW[identifier]) - 1  # Remove meta data from number of blocks
        total_blocks = int(uloads(self.__RAW[identifier][0])['num-blocks'])

        if local_blocks != total_blocks:
            # TODO delete the rest of the blocks on other storage nodes
            pass

        # Delete local blocks + meta data
        del self.__RAW[identifier]

        # Delete local cache and ghosts, since context is removed
        self.__srcs.delete(identifier)
        self.__dgcs.delete(identifier)
        return STATUS_SUCCESS

    def get_meta_from_identifier(self, didentifier):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(didentifier)
        if responsible:
            return responsible.get_meta_from_identifier(didentifier)

        # Else do the job self.
        if not self.__context_exists(didentifier):
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

    def get_datasets(self, is_internal_call=False):
        all_others = self.__num_storage_nodes

        def __self_datasets():
            return [uloads(self.get_meta_from_identifier(int(key)))['name'] for key in self.__FLAG.iterkeys()]

        if not is_internal_call and all_others > 0:
            # Broadcast storm to all nodes
            info("Pool get_datasets")
            others_datasets = ThreadPool(all_others).map(_wrapper_get_datasets, self.__storage_nodes)
            return sum(__self_datasets() + others_datasets, [])
        else:
            # Calculate self
            return __self_datasets()

    def __get_raw_blocks(self, didentifier, iflatten=False):
        is_root = str(didentifier) in self.__FLAG
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
        context = get_class_from_source(source, meta_data['class-name'])

        for operation_context in context.get_operations():
            if operation_context.fun_name == function_name:
                return operation_context, meta_data

        return STATUS_NOT_FOUND

    def __get_operations_and_arguments(self, didentifier, fidentifier, operation_context, query):
        # Get blocks to work on

        def _get_blocks_with_ghost():
            ghosts = self.__dgcs.get(fidentifier)

            # Merge ghosts into blocks
            for l, m, r in izip_longest(ghosts['ghost-left'] if 'ghost-left' in ghosts else [None],
                                        self.__get_raw_blocks(didentifier),
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
            blocks = self.__get_raw_blocks(didentifier, iflatten=True)

        args = [blocks]
        if query:
            if operation_context.has_multiple_args():
                args = args + str(query).split(operation_context.delimiter)
            else:
                args = args + [query]

        return operation_context.get_functions(), args

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
                # Result already calculated with no context change
                self.__terminate_job(didentifier, fidentifier, STATUS_SUCCESS)
                return

        # Update is working state before anything else
        all_nodes = self.__num_storage_nodes + 1  # Plus one for self
        self.__srcs.get(didentifier)[fidentifier] = [None, all_nodes, True, gateway]

        root = self.__config.node
        common = (didentifier, fidentifier, function_name, root, query)
        if all_nodes > 1:
            # Broadcast storm to all nodes
            info("Pool _wrapper_initialize_execution")
            args = [(node, common) for node in self.__storage_nodes] + [(self, common)]
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
    def initialize_execution(self, didentifier, fidentifier, function_name, root, query):
        info("Initialize execution at " + str(self.__config.node))

        self.__tb = TreeBarrier(self.__config.node,
                                list(self.__config.others['storage']) if 'storage' in self.__config.others else [],
                                root)

        # If im the only node in the system
        is_local_transfer = self.__num_storage_nodes == 0

        res = self.__get_operation_context(didentifier, function_name)
        if is_error(res):
            self.__terminate_job(didentifier, fidentifier, STATUS_NO_DATA)
            return
        operation_context, meta_data = res

        def done_callback_handler(is_ready, left, right):
            # left and right is tuples with node reference and data to send
            if is_ready:
                # # No extra requests for ghosts
                # self.__srcs.get(didentifier)[fidentifier][REQUEST_COUNT] = 0

                # There is no need for ghosts
                if is_local_transfer:
                    self.execute_function(0, didentifier, fidentifier, function_name,
                                          meta_data, self.__config.node, query, 0)
                else:
                    self.__report_ready(didentifier, fidentifier, function_name, meta_data, query)
                return

            fun_args = (didentifier, fidentifier, operation_context.needs_both_ghosts(),
                        (function_name, meta_data, root, query))

            l_neighbor, right_ghost = left
            r_neighbor, left_ghost = right

            # Ghost is required
            if is_local_transfer:
                self.__handle_received_ghosts(left_ghost, right_ghost, *fun_args)
            else:
                if operation_context.ghost_right and r_neighbor:
                    info("Sending ghost left from: " + self.__config.node + ": " + str(right_ghost))
                    l_neighbor.send_ghost(None, right_ghost, *fun_args)

                if operation_context.ghost_left and r_neighbor:
                    info("Sending ghost right from: " + self.__config.node + ": " + str(left_ghost))
                    r_neighbor.send_ghost(left_ghost, None, *fun_args)

        if not operation_context.needs_ghost():
            # Check if ghosts is needed to complete the calculation
            info("No need for ghosts at " + str(self.__config.node))
            done_callback_handler(is_ready=True, left=None, right=None)
            return

        # Find ghosts from local neighbors if needed else execute
        self.__handle_ghosts(didentifier, operation_context, done_callback_handler, is_local_transfer=is_local_transfer)

    def execute_function(self, itr, didentifier, fidentifier, function_name, meta_data, root, query, recv_value):
        info("Execute function " + function_name + " at " + str(self.__config.node))

        first_iteration = itr == 0

        operation_context, _ = self.__get_operation_context(None, function_name, meta_data=meta_data)
        # TODO: Unify and remove reduce word to generalize SOFA
        functions = operation_context.get_functions()
        reduce_function = functions[-1]

        # See if its first iteration or the cache has the value
        has_result = self.__srcs.contains(didentifier) \
                     and fidentifier in self.__srcs.get(didentifier) \
                     and self.__srcs.get(didentifier)[fidentifier][RESULT]

        if not has_result:
            _, args = self.__get_operations_and_arguments(didentifier, fidentifier, operation_context, query)
            operation_context_args = (operation_context, root, didentifier)
            res = _local_execute(self, functions, args, operation_context_args)
            info("Result for " + self.__config.node + " is: " + str(res))

            is_root = str(didentifier) in self.__FLAG
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
                self.__srcs.get(didentifier)[fidentifier] = [reduce_function((recv_value, res))]
        except StopIteration:
            data = self.__srcs.get(didentifier)[fidentifier]

            if first_iteration:
                res = data[RESULT]
            else:
                res = reduce_function((recv_value, data[RESULT]))

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

    def __handle_received_ghosts(self, left_ghost, right_ghost, didentifier, fidentifier, needs_both, fun_args):
        info("Receiving ghost at " + self.__config.node)

        assert left_ghost is not None or right_ghost is not None
        function_name, meta_data, root, query = fun_args

        if left_ghost is not None:
            is_ghost_right = False
            is_root = str(didentifier) in self.__FLAG
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
        self.__handle_received_ghosts(*secure_load(bundle))

    # Internal Monitor Api
    def heartbeat(self):
        pass


def _wrapper_initialize_execution(args):
    return args[0].initialize_execution(*args[1])


def _wrapper_execute_function(args):
    args[0].execute_function(*args[1])


def _wrapper_get_datasets(arg):
    return arg.get_datasets(is_internal_call=True)


def _wrapper_local_execute(args):
    return _local_execute(*args)


def _local_execute(self, functions, args, operation_context_args):
    try:
        possible_function = functions.pop(0)
        if isinstance(possible_function, SequentialOperation):
            res = _local_execute(self, list(possible_function.functions), args, operation_context_args)
            return _local_execute(self, functions, res, operation_context_args)

        if isinstance(possible_function, ParallelOperation):
            suboperations = possible_function.functions
            pool = ThreadPool(4)

            subargs = []
            for suboperation in suboperations:
                subargs.append((self, list(suboperation if (isfunction(suboperation) or isbuiltin(suboperation))
                                           else suboperation.functions), args, operation_context_args))

            res = pool.map(_wrapper_local_execute, subargs)
            return _local_execute(self, functions, res, operation_context_args)

        if isfunction(possible_function) or isbuiltin(possible_function):
            res = possible_function(args)
            return _local_execute(self, functions, res, operation_context_args)

        # Find keyword function and call it
        is_keyword_fun = [idx for idx, keyword in enumerate(KEYWORDS.keys()) if keyword.findall(possible_function)]
        if is_keyword_fun:
            res = KEYWORDS.values()[is_keyword_fun[0]](possible_function, operation_context_args, [self, args])
            return _local_execute(self, functions, res, operation_context_args)

    except IndexError:
        return args
