# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from dataset import AbsDatasetContext
from Pyro4 import Proxy
from bdos import NS
from io import BytesIO
from urllib2 import urlopen

GATEWAY_URI_NAMESPACE = "bdos.gateway"


class GatewayHandler(object):
    def create(self, name):
        print "New dataset with name: ", name

    def append(self, name, url):
        print "Adding %s to %s" % (url, name)


class GatewayApi(object):
    @staticmethod
    def __get_gateway_handler():
        return Proxy(NS.lookup(GATEWAY_URI_NAMESPACE))

    @staticmethod
    def create(name):
        return GatewayApi.__get_gateway_handler().create(name)

    @staticmethod
    def append(name, url):
        GatewayApi.__get_gateway_handler().append(name, str(url))
