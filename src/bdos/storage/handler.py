# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from shelve import open

from Pyro4 import Proxy, locateNS

from bdos.utils import STATUS_ALREADY_EXISTS, STATUS_NOT_FOUND, STATUS_SUCCESS
from bdos.secure import secure_load, secure_send

# TODO: Generalize to support multiple storage handlers
class StorageHandler(object):
    def __init__(self, _, storage_uris):
        # self.__storage_nodes = [_InternalStorageApi(storage_uri) for storage_uri in storage_uris]
        self.__RAW = open("bdos_raw.db", writeback=True)
        self.__FLAG = open("bdos_flag.db", writeback=True)

    def create(self, bundle):
        identifier, jdataset = secure_load(bundle)
        if self.__dataset_exists(identifier):
            return STATUS_ALREADY_EXISTS

        self.__FLAG[identifier] = True
        self.__RAW[identifier] = [jdataset]
        return STATUS_SUCCESS

    def append(self, identifier, block):
        self.__RAW[identifier].append(block)
        return STATUS_SUCCESS

    def get_meta_from_identifier(self, identifier):
        if not self.__dataset_exists(identifier):
            return STATUS_NOT_FOUND

        return self.__RAW[identifier]

    def __dataset_exists(self, identifier):
        return identifier in self.__FLAG


class StorageApi(object):
    def __init__(self, storage_uri):
        self.api = Proxy(locateNS().lookup(storage_uri))

    def create(self, identifier, jdataset):
        return secure_send((identifier, jdataset), self.api.create)

    def append(self, identifier, block):
        return self.api.append(identifier, block)

    def get_meta_from_identifier(self, identifier):
        # TODO: secure return
        return self.api.get_meta_from_identifier(identifier)


class _InternalStorageApi(object):
    pass
