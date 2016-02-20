# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from inspect import getsourcefile
from sys import getsizeof
from contextlib import closing
from urllib2 import urlopen
from random import choice, randint
from ujson import dumps as udumps, loads as uloads

from Pyro4 import Proxy, locateNS

from bdos.utils import find_identifier, import_class, is_error
from bdos.secure import secure_load, secure_load2, secure_send, secure
from bdos.storage import api as storage_api


def _dataset_from_source(source, name):
    exec source
    return eval("%s()" % name)


class GatewayHandler(object):
    def __init__(self, block_size, storage_uris):
        self.__block_size = block_size
        self.__num_storage_nodes = len(storage_uris)
        self.__storage_nodes = [storage_api(storage_uri) for storage_uri in storage_uris]

    def __get_storage_node(self):
        return choice(self.__storage_nodes)

    def create(self, bundle):
        name, dataset_source, dataset_name = secure_load(bundle)
        digest, pdata = secure(dataset_source)
        dataset = udumps({'digest': digest,
                          'name': dataset_name,
                          'source': pdata})
        return self.__get_storage_node().create(find_identifier(name), dataset)

    def append(self, name, url):
        identifier = find_identifier(name)
        res = self.__get_storage_node().get_meta_from_identifier(identifier)
        if is_error(res):
            # TODO: decide whether to try again
            pass

        jdataset = uloads(res)
        source = secure_load2(jdataset['digest'], jdataset['source'])
        dataset = _dataset_from_source(source, jdataset['name'])

        with closing(urlopen(url)) as f:
            start = randint(0, self.__num_storage_nodes - 1)
            for block in self.next_block(dataset, f.read()):
                self.__storage_nodes[start].append(identifier, block)
                # TODO: Save response and check if correct is saved and received
                start = (start + 1) ^ self.__num_storage_nodes

    def next_block(self, dataset, data):
        block = []
        block_size = 0
        for entry in dataset.next_entry(data):
            entry_size = getsizeof(entry)
            if block_size + entry_size > self.__block_size:
                yield block
                block = []
                block_size = 0
            else:
                block_size += entry_size
                block.append(entry)

        if block:
            # Check if block is not empty and yield rest
            yield block


class GatewayApi(object):
    def __init__(self, gateway_uri):
        super(GatewayApi, self).__init__()

        self.api = GatewayApi.__get_gateway_handler(gateway_uri)

    @staticmethod
    def __get_gateway_handler(gateway_uri):
        return Proxy(locateNS().lookup(gateway_uri))

    def create(self, name, dataset_type):
        with open(getsourcefile(import_class(dataset_type)), "r") as f:
            return secure_send((name, f.read(), dataset_type.rsplit(".", 1)[1]), self.api.create)

    def append(self, name, url):
        return self.api.append(name, str(url))
