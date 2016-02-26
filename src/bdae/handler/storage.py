# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from shelve import open
from math import floor
from sys import getsizeof
from logging import info

from Pyro4 import Proxy, locateNS, async

from bdae.utils import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, STATUS_SUCCESS
from bdae.secure import secure_load, secure_send
from bdae.tree_barrier import TreeBarrier
from bdae.cache import CacheSystem


class StorageHandler(object):
    def __init__(self, config, others):
        self.__config = config
        self.__tb = None
        self.__scs = CacheSystem(dict)
        self.__RAW = open("bdae_raw.db", writeback=True)
        self.__FLAG = open("bdae_flag.db", writeback=True)

        if 'storage' in others:
            self.__storage_nodes = [_InternalStorageApi(storage_uri) for storage_uri in others['storage']]
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

    def submit_job(self, didentifier, fidentifier, function, query, gateway, callback):
        # Check whether its self who is responsible
        responsible = self.__find_responsibility(didentifier)
        if responsible:
            return responsible.submit_job(didentifier, fidentifier, function, query, gateway, callback)

        # Else do the job self.
        # TODO: Save fidentifier in cache for speedup and function recognition
        for node in self.__storage_nodes:
            async(node).execute_function(0, self.__config.node, didentifier, fidentifier, function, query)

        # TODO: Broadcast storm to all storage_nodes to execute_function and start self
        pass

    def execute_function(self, itr, root, didentifier, fidentifier, function, query):
        if itr == 0:
            self.__tb = TreeBarrier(self.__config.node, self.__storage_nodes, root)
            # TODO: Calculate partial value
            partial_value = 0
            self.__scs.put(fidentifier, partial_value)

        try:
            if self.__tb.should_send(itr):
                self.__tb.get_receiver().execute_function(itr + 1, root, didentifier, function, query)
        except StopIteration:
            # TODO: Send result back to gateway and save locally in metadata for didentifier
            pass

    # Internal Monitor Api
    def heartbeat(self):
        pass


class StorageApi(object):
    def __init__(self, storage_uri):
        self.api = Proxy(locateNS().lookup(storage_uri))

    def create(self, identifier, jdataset):
        return secure_send((identifier, jdataset), self.api.create)

    def append(self, identifier, block):
        return secure_send((identifier, block), self.api.append)

    def get_meta_from_identifier(self, identifier):
        # TODO: secure return
        return self.api.get_meta_from_identifier(identifier)

    def submit_job(self, didentifier, fidentifier, function, query, gateway, callback):
        return self.api.submit_job(didentifier, fidentifier, function, query, gateway, callback)

    def execute_function(self, itr, root, didentifier, function, query):
        return self.api.execute_function(itr, root, didentifier, function, query)


class InternalStorageMonitorApi(object):
    def __init__(self, storage_uri):
        self.api = Proxy(locateNS().lookup(storage_uri))

    def heartbeat(self):
        self.api.heartbeat()


class _InternalStorageApi(StorageApi):
    pass
