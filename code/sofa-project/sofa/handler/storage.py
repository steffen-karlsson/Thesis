# -*- coding: utf-8 -*-

# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from collections import Iterable
from collections import defaultdict
from inspect import isfunction, isbuiltin
from itertools import izip_longest
from logging import info
from multiprocessing.pool import ThreadPool
from os.path import basename, isfile
from re import compile
from shelve import open
from sys import getsizeof
from simplejson import loads, dumps

from numpy import ndarray

from sofa.cache import CacheSystem
from sofa.delegation import DelegationHandler
from sofa.delegation.responsible_dispatch import with_responsible_dispatch, find_responsible
from sofa.delegation.queue import with_forward_count, with_forward_queue, with_required_queue
from sofa.error import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, STATUS_SUCCESS, \
    STATUS_PROCESSING, STATUS_NO_DATA, is_error
from sofa.foundation.operation import Sequential as SequentialOperation, Parallel as ParallelOperation
from sofa.handler import get_class_from_source
from sofa.handler.api import _InternalStorageApi, _InternalGatewayApi
from sofa.secure import secure_load
from sofa.tree_barrier import TreeBarrier

RESULT = 0
REQUEST_COUNT = 1
ROOT_IS_WORKING = 2
GATEWAY = 3
STATE = 4

BLOCKS = 0
QUERY = 1

PRIMARY_REPLICA = 0


def _forward_and_extract(fun, max_num_args):
    # Forwards to the right function (fun) with possible extracted arguments based on the pattern
    # defined in KEYWORDS and as argument to _forward_extract_args.
    def _forward_extract_args(handler, args, fun_name, operation_context_args):
        has_arguments = ':' in fun_name
        expects_arguments = max_num_args > 0
        if has_arguments and expects_arguments:
            key_fun_args = fun_name.split(":")[1:]
            return fun(handler, args, operation_context_args, tuple(key_fun_args))
        else:
            return fun(handler, args, operation_context_args)

    return _forward_extract_args


# Function for KEYWORD: neighborhood
def _exchange_neighborhood(handler, args, operation_context_args, ghost_count=(1, 1)):
    operation_context, didentifier, fidentifier, process_state, meta_data = operation_context_args

    # Use block-state = 'partial' such that arguments (with ghosts) for next function
    # is based on previous results and not raw blocks
    process_state['block-state'] = 'partial'

    # Save the temporary result in the storage result cache system
    handler.save_partial_value_state(didentifier, fidentifier, args[BLOCKS])

    # Set ghost properties on the context
    ghost_count = tuple(int(count) for count in ghost_count) if len(ghost_count) == 2 else int(ghost_count[0])
    operation_context.with_initial_ghosts(ghost_count, use_cyclic=False)

    all_others = handler.get_num_storage_nodes(True)
    is_local_transfer = all_others == 1

    def done_callback_handler(is_ready, left, right):
        # left and right is tuples with node reference and data to send
        l_neighbor, right_ghost = left
        r_neighbor, left_ghost = right
        fun_args = (operation_context.needs_both_ghosts(), didentifier, fidentifier, meta_data, process_state)

        # Ghost is required
        if is_local_transfer:
            handler.handle_received_ghosts(left_ghost, right_ghost, *fun_args)
        else:
            if operation_context.send_left and r_neighbor:
                info("Sending ghost left from: " + str(handler) + ": " + str(right_ghost))
                l_neighbor.send_ghost(None, right_ghost, *fun_args)

            if operation_context.send_right and r_neighbor:
                info("Sending ghost right from: " + str(handler) + ": " + str(left_ghost))
                r_neighbor.send_ghost(left_ghost, None, *fun_args)

    handler.handle_ghosts(didentifier, operation_context, done_callback_handler,
                          self_data=args[BLOCKS], is_local_transfer=is_local_transfer)


def _get_operation_context(function_name, meta_data):
    if meta_data['num-blocks'] == 0:
        # No data found for data identifier
        return STATUS_NOT_FOUND

    source = secure_load(meta_data['digest'], meta_data['source'])
    context = get_class_from_source(source, meta_data['class-name'])

    for operation_context in context.get_operations():
        if operation_context.fun_name == function_name:
            return operation_context

    return STATUS_NOT_FOUND


def _str_loads(s):
    while not isinstance(s, dict):
        s = loads(s)
    return s


class WillContinueExecuting(Exception):
    pass


class Keywords(dict):
    def __init__(self, **kwargs):
        super(Keywords, self).__init__(**kwargs)
        self[compile("neighborhood(?::\d){0,2}$")] = _forward_and_extract(_exchange_neighborhood, 2)

    def find_function(self, index):
        return self.values()[index]


KEYWORDS = Keywords()


class StorageHandler(DelegationHandler):
    def __init__(self, config, others):
        self.__config = config
        self.__tb = None
        self.__srcs = CacheSystem(defaultdict, args=dict)  # Storage Result Cache System
        self.__dgcs = CacheSystem(defaultdict, args=dict)  # Dataset Ghosts Cache System

        if 'storage' in others:
            self.__storage_nodes = [_InternalStorageApi(storage_uri) for storage_uri, _ in others['storage']]
        else:
            self.__storage_nodes = []

        self.__num_storage_nodes = len(self.__storage_nodes)
        self.__neighbors = self.__get_neighbors()
        space_size = self.__config.keyspace_size / self.get_num_storage_nodes(True)

        # Setup delegation with information needed
        super(StorageHandler, self).__init__(self.__config.node_idx, space_size)

        self.__DISK = {}
        self.__FLAG = open(self.__get_mounted_filename('sofa_flag.db'), writeback=True)
        # Create primary replica
        self.__create_replica(PRIMARY_REPLICA)

    def __create_replica(self, index):
        self.__DISK[index] = open(self.__get_mounted_filename("sofa_replica_%d.db" % index), writeback=True)

    def __find_replica(self, index):
        # See if replica with index exists
        if index not in self.__DISK:
            # Create new replica
            self.__create_replica(index)

        return self.__DISK[index]

    def __get_mounted_filename(self, filename):
        return "%s%s" % (self.__config.get_mount_point(), filename)

    def get_responsible(self, index):
        # Offset by this nodes position, since it's not part of storage nodes
        return self.__storage_nodes[index + (-1 if index >= self.__config.node_idx else 0)]

    def save_partial_value_state(self, didentifier, fidentifier, res):
        is_root = str(didentifier) in self.__FLAG
        if is_root:
            self.__srcs.get(didentifier)[fidentifier][RESULT] = res
        else:
            self.__srcs.get(didentifier)[fidentifier] = [res]

    def __str__(self):
        return self.__config.node

    def get_num_storage_nodes(self, including_self=False):
        return self.__num_storage_nodes + (1 if including_self else 0)

    def get_replication_factor(self, identifier):
        # Only callable on the node responsible for identifier i.e. identifier in self.__FLAGS
        res = self.__get_meta_from_identifier_and_replica(identifier, PRIMARY_REPLICA)
        if is_error(res):
            raise AttributeError("get_replication_factor not callable at servers which isn't root for " + str(identifier))

        meta_data = loads(res)
        return meta_data['replication-factor']

    def __get_neighbors(self):
        if self.get_num_storage_nodes() == 0:
            return None

        prev = self.__storage_nodes[(self.__config.node_idx - 1) % self.get_num_storage_nodes()]
        nxt = self.__storage_nodes[self.__config.node_idx % self.get_num_storage_nodes()]
        return prev, nxt

    def __get_ghosts(self, send_right, send_left, didentifier, operation_context, self_data, is_local_transfer):
        if isinstance(self_data, list) or isinstance(self_data, ndarray):
            self_data = self_data
        elif isinstance(self_data, Iterable):
            self_data = list(self_data)

        is_root = str(didentifier) in self.__FLAG
        left_ghost, right_ghost = (None,) * 2
        use_cyclic = operation_context.use_cyclic

        if send_left:
            # Only the blocks and the edge between nodes, that's why 0
            right_ghost = [block[:operation_context.get_ghost_count_left()] for block in self_data]

            if is_local_transfer or is_root:
                if use_cyclic:
                    overflow = right_ghost[0]
                    # TODO: No wrapping supported, implement on last node
                    pass

                # Only storage node in the system or previous node doesn't need first when sending left
                right_ghost = right_ghost[1:]

        if send_right:
            # Only the blocks and the edge between nodes, that's why -1
            left_ghost = [block[-operation_context.get_ghost_count_right():] for block in self_data]

            if use_cyclic:
                overflow = left_ghost[-1]
                # TODO: No wrapping supported, implement on last node
                pass

        return left_ghost, right_ghost

    def __context_exists(self, didentifier):
        return str(didentifier) in self.__FLAG

    def handle_ghosts(self, didentifier, operation_context, done_callback_handler,
                      self_data, is_local_transfer=False):
        left_ghost, right_ghost, l_neighbor, r_neighbor = (None,) * 4
        if not is_local_transfer:
            l_neighbor, r_neighbor = self.__get_neighbors()

        send_left = operation_context.send_left and (l_neighbor or is_local_transfer)
        send_right = operation_context.send_right and (r_neighbor or is_local_transfer)

        left_ghost, right_ghost = self.__get_ghosts(send_right, send_left, didentifier, operation_context,
                                                    self_data, is_local_transfer)

        if is_local_transfer:
            done_callback_handler(is_ready=False, left=(None, left_ghost), right=(None, right_ghost))
            return

        done_callback_handler(is_ready=False, left=(l_neighbor, right_ghost), right=(r_neighbor, left_ghost))

    def __get_meta_from_identifier_and_replica(self, identifier, replica_index):
        if not self.__context_exists(identifier):
            return STATUS_NOT_FOUND

        replica_blocks = self.__find_replica(replica_index)
        return replica_blocks[str(identifier)][0]

    @with_responsible_dispatch
    @with_required_queue
    @with_forward_count
    def create(self, function_delegation, identifier, meta_data, is_update):
        if is_update:
            # TODO: Block from calling any other operation on this context, while update is finishing
            pass

        meta_data = _str_loads(meta_data)
        meta_data['root-idx'] = self.__config.node_idx

        # Else do the job self.
        if self.__context_exists(identifier) and not is_update:
            return STATUS_ALREADY_EXISTS, "Dataset already exists"

        info("Creating context with identifier %s at replica %d on %s."
             % (identifier, function_delegation['replica-index'], self.__config.node))

        replica_blocks = self.__find_replica(function_delegation['replica-index'])

        identifier = str(identifier)
        self.__FLAG[identifier] = True
        replica_blocks[identifier] = [dumps(meta_data)]

        return STATUS_SUCCESS

    @with_required_queue
    @with_forward_count
    def append(self, function_delegation, identifier, block, create_new_stride):
        # TODO: Block from calling any other operation on this context, while append is finishing
        replica_index = function_delegation['replica-index']

        res = self.__get_meta_from_identifier_and_replica(identifier, replica_index)
        if is_error(res):
            return res, "Dataset doesn't exists"

        info("Writing block of size %d to datatset with identifier %s at replica %d on %s." % (
            getsizeof(block), identifier, replica_index, self.__config.node))

        # Find correct replica to append to -> 0 is primary
        replica_blocks = self.__find_replica(replica_index)

        identifier = str(identifier)
        if identifier not in replica_blocks:
            replica_blocks[identifier] = []

        if create_new_stride:
            replica_blocks[identifier].append(block)
        else:
            replica_blocks[identifier][-1].extend(block)

        # Delete local cache, since context is appended
        self.__srcs.delete(identifier)

        return STATUS_SUCCESS

    @with_responsible_dispatch
    @with_required_queue
    @with_forward_count
    def delete(self, function_delegation, identifier):
        # TODO: Block from calling any other operation on this context

        # # Delete all blocks
        # local_blocks = len(self.__RAW[identifier]) - 1  # Remove meta data from number of blocks
        # total_blocks = int(loads(self.__RAW[identifier][0])['num-blocks'])
        #
        # if local_blocks != total_blocks:
        #     # TODO delete the rest of the blocks on other storage nodes
        #     pass
        #
        # # Delete local blocks + meta data
        # del self.__RAW[identifier]
        #
        # # Delete local cache and ghosts, since context is removed
        # self.__srcs.delete(identifier)
        # self.__dgcs.delete(identifier)
        return STATUS_SUCCESS

    @with_responsible_dispatch
    @with_forward_queue
    @with_forward_count
    def get_meta_from_identifier(self, function_delegation, didentifier):
        return self.__get_meta_from_identifier_and_replica(didentifier, function_delegation['replica-index'])

    @with_responsible_dispatch
    @with_required_queue
    @with_forward_count
    def update_meta_key(self, function_delegation, identifier, update_type, key, value):
        replica_index = function_delegation['replica-index']

        res = self.__get_meta_from_identifier_and_replica(identifier, replica_index)
        if is_error(res):
            return res, "Dataset doesn't exists"

        meta_data = loads(res)
        if update_type == 'append':
            meta_data[key] += value

        if update_type == 'override':
            meta_data[key] = value

        info("%s is %s with %d" % (key, update_type, value))

        replica_blocks = self.__find_replica(replica_index)
        replica_blocks[str(identifier)][0] = dumps(meta_data)
        return STATUS_SUCCESS

    # Doesn't make sense to forward, since its contacting all other servers for data anyway
    @with_forward_count
    def get_datasets(self, is_internal_call=False):
        all_others = self.get_num_storage_nodes(True)

        def __self_datasets():
            datasets = []
            for key in self.__FLAG.iterkeys():
                # Only getting the datasets that this node is responsible for "self.__FLAGS"
                meta_data = loads(self.__get_meta_from_identifier_and_replica(int(key), PRIMARY_REPLICA))
                operations = [{'name': operation, 'num_arguments': num_arguments}
                              for operation, num_arguments in meta_data['operations']]
                datasets.append({'name': meta_data['name'],
                                 'description': meta_data['description'],
                                 'operations': operations})
            return datasets

        if not is_internal_call and all_others > 1:
            # Broadcast storm to all nodes
            info("Pool get_datasets")
            others_datasets = ThreadPool(all_others).map(_wrapper_get_datasets, self.__storage_nodes)
            return sum(__self_datasets() + others_datasets, [])
        else:
            # Calculate self
            return __self_datasets()

    # Doesn't make sense to forward, since its contacting all other servers for data anyway
    @with_forward_count
    def get_submitted_jobs(self, is_internal_call=False):
        all_others = self.get_num_storage_nodes(True)

        def __self_jobs():
            functions = []
            for key in self.__srcs.keys():
                for fidentifier in self.__srcs.get(key).keys():
                    data = self.__srcs.get(key)[fidentifier]
                    state = data[STATE]

                    query = state['query']
                    parameters = [query] if not isinstance(query, list) else [str(q) for q in query]
                    parameters = [basename(path) if isfile(path) else path for path in parameters]

                    function = {
                        'name': state['function-name'],
                        'identifier': state['fidentifier'],
                        'dataset_name': state['dataset-name'],
                        'result': data[RESULT] if not data[ROOT_IS_WORKING] else '',
                        'status': 0 if data[ROOT_IS_WORKING] else 1,
                        'parameters': parameters,
                        'data_type': state['data-type'],
                    }
                    functions.append(function)
            return functions

        if not is_internal_call and all_others > 1:
            # Broadcast storm to all nodes
            info("Pool get_submitted_jobs")
            other_jobs = ThreadPool(all_others).map(_wrapper_get_submitted_jobs, self.__storage_nodes)
            return sum(__self_jobs() + other_jobs, [])
        else:
            # Calculate self
            return __self_jobs()

    def __get_raw_blocks(self, didentifier, replica_index):
        # We only store meta data on primary replica = 0
        is_root = str(didentifier) in self.__FLAG and replica_index == 0

        replica_blocks = self.__find_replica(PRIMARY_REPLICA)
        return replica_blocks[str(didentifier)][1 if is_root else 0:]  # Blocks on self

    def __get_num_raw_blocks(self, didentifier, replica_index):
        return len(self.__get_raw_blocks(didentifier, replica_index))

    def __get_operations_and_arguments(self, didentifier, fidentifier, process_state):
        # Merge ghosts into blocks
        def _get_blocks_with_ghost():
            ghosts = self.__dgcs.get(fidentifier)
            _blocks = None

            # Get blocks to work on
            if process_state['block-state'] is 'raw':
                _blocks = self.__get_raw_blocks(didentifier, process_state['replica-index'])
            elif process_state['block-state'] is 'partial':
                # The result block is used for partial results in the case of built in functions with synchronization
                _blocks = self.__srcs.get(didentifier)[fidentifier][RESULT]

            assert _blocks is not None

            for l, m, r in izip_longest(ghosts['ghost-left'] if 'ghost-left' in ghosts else [None],
                                        _blocks,
                                        ghosts['ghost-right'] if 'ghost-right' in ghosts else [None]):
                # Ensure all data is lists for list concatenation
                if l is None:
                    l = []
                if r is None:
                    r = []

                yield l + m + r

        args = [None, None]

        if self.__dgcs.contains(fidentifier):
            blocks = _get_blocks_with_ghost()
        else:
            blocks = self.__get_raw_blocks(didentifier, process_state['replica-index'])

        args[BLOCKS] = blocks
        query = process_state['query']
        args[QUERY] = [query] if query and not isinstance(query, list) else query
        return args

    @with_responsible_dispatch
    @with_forward_queue
    @with_forward_count
    def submit_job(self, function_delegation, didentifier, process_state, gateway):
        fidentifier = process_state['fidentifier']

        has_result = self.__srcs.contains(didentifier) \
                     and fidentifier in self.__srcs.get(didentifier) \
                     and self.__srcs.get(didentifier)[fidentifier][RESULT]

        process_state.update({
            'iteration-count': 0,
            'function-count': 0,
            'partial-value': 0,
            'block-state': 'raw',
            'processing': False if has_result else True,
            'replica-index': function_delegation['replica-index']
        })

        if has_result:
            data = self.__srcs.get(didentifier)[fidentifier]
            if data[ROOT_IS_WORKING]:
                # Similar job is in progress
                self.__terminate_job(didentifier, fidentifier, STATUS_PROCESSING)
                return
            else:
                # Result already calculated with no context change
                self.__terminate_job(didentifier, fidentifier, STATUS_SUCCESS)
                return

        # Update is working state before anything else
        all_nodes = self.get_num_storage_nodes(True)  # Plus one for self
        self.__srcs.get(didentifier)[fidentifier] = [None, all_nodes, True, gateway, process_state]

        # Getting meta data for common arguments
        res = self.__get_meta_from_identifier_and_replica(didentifier, function_delegation['replica-index'])
        if is_error(res):
            # Dataset doesn't exists
            self.__terminate_job(didentifier, fidentifier, STATUS_NOT_FOUND)
            return

        meta_data = loads(res)

        root = self.__config.node
        common = (didentifier, process_state, root, meta_data)
        if all_nodes > 1:
            # Broadcast storm to all nodes
            info("Pool wrapper initialize job")
            args = [(node, common) for node in self.__storage_nodes] + [(self, common)]
            ThreadPool(all_nodes).map_async(_wrapper_initialize_job, args)
        else:
            # Calculate self
            self.initialize_job(*common)

    def __terminate_job(self, didentifier, fidentifier, status):
        data = self.__srcs.get(didentifier)[fidentifier]

        if is_error(status):
            # Remove existing result if an error occurs
            del self.__srcs.get(didentifier)[fidentifier]

        _InternalGatewayApi(data[GATEWAY]).set_status_result(didentifier, fidentifier, status, data[RESULT])

    # Internal Api
    def initialize_job(self, didentifier, process_state, root, meta_data):
        function_name = process_state['function-name']
        fidentifier = process_state['fidentifier']

        info("Initialize execution at " + str(self.__config.node) + " for function " + function_name)

        self.__tb = TreeBarrier(self.__config.node,
                                list(self.__config.others['storage']) if 'storage' in self.__config.others else [],
                                root)

        # If im the only node in the system
        is_local_transfer = self.get_num_storage_nodes() == 0

        res = _get_operation_context(function_name, meta_data)
        if is_error(res):
            self.__terminate_job(didentifier, fidentifier, STATUS_NO_DATA)
            return
        operation_context = res

        # Set return type
        process_state['data-type'] = operation_context.get_return_type()

        def done_callback_handler(is_ready, left, right):
            # left and right is tuples with node reference and data to send
            if is_ready:
                # There is no need for ghosts
                if is_local_transfer:
                    self.execute_function(didentifier, fidentifier, meta_data, process_state)
                else:
                    self.__report_ready(didentifier, fidentifier, meta_data, process_state)
                return

            l_neighbor, right_ghost = left
            r_neighbor, left_ghost = right
            fun_args = (operation_context.needs_both_ghosts(), didentifier, fidentifier, meta_data, process_state)

            # Ghost is required
            if is_local_transfer:
                self.handle_received_ghosts(left_ghost, right_ghost, *fun_args)
            else:
                if operation_context.send_left and r_neighbor:
                    info("Sending ghost left from: " + str(self) + ": " + str(right_ghost))
                    l_neighbor.send_ghost(None, right_ghost, *fun_args)

                if operation_context.send_right and r_neighbor:
                    info("Sending ghost right from: " + str(self) + ": " + str(left_ghost))
                    r_neighbor.send_ghost(left_ghost, None, *fun_args)

        if not operation_context.needs_ghost():
            # Check if ghosts is needed to complete the calculation
            info("No need for ghosts at " + str(self.__config.node))
            done_callback_handler(is_ready=True, left=None, right=None)
            return

        # Find ghosts from local neighbors if needed else execute
        replica_blocks = self.__get_raw_blocks(didentifier, process_state['replica-index'])

        self.handle_ghosts(didentifier, operation_context, done_callback_handler, replica_blocks,
                           is_local_transfer=is_local_transfer)

    def execute_function(self, didentifier, fidentifier, meta_data, process_state):
        function_name = process_state['function-name']
        info("Execute function " + function_name + " at " + str(self))

        res = _get_operation_context(function_name, meta_data)
        if is_error(res):
            self.__terminate_job(didentifier, fidentifier, STATUS_NOT_FOUND)
            return
        operation_context = res

        # Calculate results of functions, which isn't already processed, i.e. function-count
        functions = operation_context.get_functions()[process_state['function-count']:]
        last_function = functions[-1]

        if process_state['processing']:
            args = self.__get_operations_and_arguments(didentifier, fidentifier, process_state)
            if is_error(args):
                self.__terminate_job(didentifier, fidentifier, STATUS_NOT_FOUND)
                return

            is_root = str(didentifier) in self.__FLAG
            operation_context_args = (operation_context, didentifier, fidentifier, process_state, meta_data)
            try:
                res = _local_execute(self, functions, args, operation_context_args)
                process_state['processing'] = False
                info("Result for " + str(self) + " is: " + str(res))

                if is_root:
                    self.__srcs.get(didentifier)[fidentifier][RESULT] = res
                else:
                    self.__srcs.get(didentifier)[fidentifier] = [res]
            except WillContinueExecuting:
                # Only happens if its a built in function from KEYWORDS executing,
                # will return to this function later in the execution phase.
                return

        itr = int(process_state['iteration-count'])
        is_first_iteration = itr == 0

        try:
            res = self.__srcs.get(didentifier)[fidentifier][RESULT]
            if self.__tb.should_send(itr):
                receiver = self.__storage_nodes[self.__tb.get_receiver_idx()]
                info("Sending from " + str(self) + " to the next")

                process_state['iteration-count'] += 1
                process_state['partial-value'] = res
                receiver.execute_function(didentifier, fidentifier, meta_data, process_state)
                return

            if not is_first_iteration:
                self.__srcs.get(didentifier)[fidentifier] = [last_function((process_state['partial-value'], res))]
                return
        except StopIteration:
            data = self.__srcs.get(didentifier)[fidentifier]

            if is_first_iteration:
                res = data[RESULT]
            else:
                res = last_function((process_state['partial-value'], data[RESULT]))

            if operation_context.has_post_processing_step():
                res = operation_context.execute_post_process(res)

            # Formatting it to expected return representation
            res = operation_context.get_data_return_representation(res)

            info("Finishing with result: " + str(res))
            self.__srcs.get(didentifier)[fidentifier] = [res, None, False, data[GATEWAY], process_state]
            self.__terminate_job(didentifier, fidentifier, STATUS_SUCCESS)
            pass

    def __report_ready(self, didentifier, fidentifier, meta_data, process_state):
        responsible_idx = find_responsible(didentifier, self.get_key_space())
        responsible = None if responsible_idx == self.me() else self.get_responsible(responsible_idx)

        args = didentifier, fidentifier, meta_data, process_state
        if responsible:
            info("Reporting ready for other at: " + str(self))
            responsible.ready(*args)
        else:
            info("Reporting ready for self")
            self.__local_ready(*args)

    def ready(self, didentifier, fidentifier, meta_data, process_state):
        self.__local_ready(didentifier, fidentifier, meta_data, process_state)

    def __local_ready(self, didentifier, fidentifier, meta_data, process_state):
        self.__srcs.get(didentifier)[fidentifier][REQUEST_COUNT] -= 1
        info(str(self) + " request count: " + str(self.__srcs.get(didentifier)[fidentifier][REQUEST_COUNT]))

        if self.__srcs.get(didentifier)[fidentifier][REQUEST_COUNT] < 1:
            common = (didentifier, fidentifier, meta_data, process_state)

            if self.get_num_storage_nodes() > 0:
                info("Pool _wrapper_execute_function")
                args = [(node, common) for node in self.__storage_nodes] + [(self, common)]
                all_nodes = self.get_num_storage_nodes(True)
                ThreadPool(all_nodes).map_async(_wrapper_execute_function, args)
            else:
                self.execute_function(*common)

    def handle_received_ghosts(self, left_ghost, right_ghost, needs_both, didentifier,
                               fidentifier, meta_data, process_state):
        info("Receiving ghost at " + str(self))

        assert left_ghost is not None or right_ghost is not None

        if left_ghost is not None:
            is_ghost_right = False
            is_root = str(didentifier) in self.__FLAG
            num_blocks = self.__get_num_raw_blocks(didentifier, process_state['replica-index'])

            if is_root or len(left_ghost) < num_blocks:
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
            self.__report_ready(didentifier, fidentifier, meta_data, process_state)

    def send_ghost(self, left_ghost, right_ghost, needs_both, didentifier, fidentifier, meta_data, process_state):
        self.handle_received_ghosts(left_ghost, right_ghost, needs_both, didentifier,
                                    fidentifier, meta_data, process_state)

    # Internal Monitor Api
    def heartbeat(self):
        pass


def _wrapper_initialize_job(args):
    return args[0].initialize_job(*args[1])


def _wrapper_execute_function(args):
    args[0].execute_function(*args[1])


def _wrapper_get_datasets(arg):
    return arg.get_datasets(is_internal_call=True)


def _wrapper_get_submitted_jobs(arg):
    return arg.get_submitted_jobs(is_internal_call=True)


def _wrapper_local_execute(args):
    return _local_execute(*args)


def _local_execute(self, functions, args, operation_context_args):
    try:
        operation_context, didentifier, fidentifier, process_state, meta_data = operation_context_args
        possible_function = functions.pop(0)
        fun_counter = operation_context.get_functions().index(possible_function)

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

        # Find keyword function and call it
        is_keyword_fun = [idx for idx, keyword in enumerate(KEYWORDS.keys())
                          if isinstance(possible_function, str) and keyword.findall(possible_function)]
        if is_keyword_fun:
            # Update process state
            process_state['function-count'] = operation_context.get_functions().index(possible_function) + 1

            KEYWORDS.find_function(is_keyword_fun[0])(self, args, possible_function, operation_context_args)
            raise WillContinueExecuting()

        # Modify and format blocks if needed
        blocks = args[BLOCKS]
        query = args[QUERY]
        if operation_context.needs_block_formatting():
            blocks = operation_context.block_formatter(blocks, fun_counter)
        # If function is buit-in call it by the wrapper import utils function

        if isbuiltin(possible_function) or possible_function.__doc__ == 'wrapped':
            res = possible_function(blocks, query)
        else:
            # If its regular defined functions, unbox arguments properly
            if query is None:
                res = possible_function(blocks)
            else:
                res = possible_function(blocks, *query)

        # Append None as next arguments, if none is returned from previous function
        if not isinstance(res, tuple):
            res = (res, None)

        return _local_execute(self, functions, list(res), operation_context_args)

    except IndexError:
        return args[BLOCKS]
