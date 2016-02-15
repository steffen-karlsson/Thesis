# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from inspect import getsourcefile

from Pyro4 import Proxy, locateNS

from bdos.utils import find_identifier, import_class_from_source, import_class
import bdos.tmp

CLASS_ERROR = "ExpectedDatasetClassNotExists"


class GatewayHandler(object):
    def create(self, name, dataset_source, dataset_type_name):
        tmp_location = bdos.tmp.__file__.rsplit("/", 1)[0]
        new_file = '%s/%s.py' % (tmp_location, name)
        with open(new_file, 'w+') as f:
            f.write(dataset_source)

        cls_inst = import_class_from_source(new_file, dataset_type_name)
        if cls_inst is None:
            return CLASS_ERROR

        identifier = find_identifier(name)
        dataset_cls = cls_inst.instance(identifier)
        print "New dataset with name: ", name, " created."
        return identifier

    def append(self, name, url):
        print "Adding %s to %s" % (url, name)


class GatewayApi(object):
    def __init__(self, gateway_uri):
        self.uri = gateway_uri

    def __get_gateway_handler(self):
        return Proxy(locateNS().lookup(self.uri))

    def create(self, name, dataset_type_name):
        with open(getsourcefile(import_class(dataset_type_name)), "r") as f:
            return self.__get_gateway_handler().create(name, f.read(), dataset_type_name)

    def append(self, name, url):
        self.__get_gateway_handler().append(name, str(url))
