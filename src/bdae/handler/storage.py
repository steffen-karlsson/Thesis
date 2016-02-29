# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from shelve import open
from math import floor
from sys import getsizeof
from logging import info
from ujson import loads as uloads, dumps as udumps

from bdae.handler import get_class_from_source
from bdae.utils import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, \
    STATUS_SUCCESS, STATUS_PROCESSING, is_error
from bdae.secure import secure_load, secure_load2
from bdae.tree_barrier import TreeBarrier
from bdae.cache import CacheSystem
from bdae.handler.api import InternalStorageApi, InternalGatewayApi


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
            return STATUS_ALREADY_EXISTS

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
        info("Writing block of size %d to datatset with identifier %s on %s." % (
            getsizeof(block), identifier, self.__config.node))
        self.__RAW[str(identifier)].append(block)

        res = self.get_meta_from_identifier(identifier)
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

    def __get_function(self, identifier, function_name, function_type, jdataset=None):
        if not jdataset:
            res = self.get_meta_from_identifier(identifier)
            if is_error(res):
                return res
            jdataset = uloads(res)

        if jdataset['num-blocks'] == 0:
            # No data found for data identifier
            return STATUS_NOT_FOUND

        source = secure_load2(jdataset['digest'], jdataset['source'])

        fm = get_class_from_source(source, jdataset["%s-name" % function_type])
        if function_name not in fm.define():
            # No function for name found
            return STATUS_NOT_FOUND

        return fm.define()[function_name], jdataset

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

        function, jdataset = self.__get_function(didentifier, function_name, function_type)

        def __root_execution():
            block_itr = (block for block in self.__RAW[str(didentifier)][1:])
            return function(block_itr, query)

        if len(self.__storage_nodes) == 0:
            # Im the only one
            res = __root_execution()
            self.__scs.put(fidentifier, (False, res, gateway))
            self.__terminate_job(fidentifier, STATUS_SUCCESS)
        else:
            # Broadcast storm to all other nodes
            for node in self.__storage_nodes:
                node.execute_function(0, self.__config.node, fidentifier, function_type,
                                      function_name, jdataset, query, 0)

            # Calculate self
            self.__scs.put(fidentifier, (True, __root_execution(), gateway))

    def __terminate_job(self, fidentifier, status):
        _, res, gateway = self.__scs.get(fidentifier)
        InternalGatewayApi(gateway).set_status_result(fidentifier, status, res)

    def execute_function(self, itr, root, fidentifier, function_type, function_name, jdataset, query, prev_value):
        if itr == 0:
            self.__tb = TreeBarrier(self.__config.node, self.__storage_nodes, root)

            # TODO: Calculate partial value
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
