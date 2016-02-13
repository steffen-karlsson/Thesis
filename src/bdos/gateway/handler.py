# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from Pyro4 import Proxy

from bdos import NS

GATEWAY_URI_NAMESPACE = "bdos.gateway"


class GatewayHandler(object):
    def create(self, name):
        print "New dataset with name: ", name

    def append(self, name, url):
        print "Adding %s to %s" % (url, name)


class GatewayApi(object):

    def __init__(self, gateway_uri):
        self.uri = gateway_uri

    def __get_gateway_handler(self):
        return Proxy(NS.lookup(self.uri))

    def create(self, name):
        return self.__get_gateway_handler().create(name)

    def append(self, name, url):
        self.__get_gateway_handler().append(name, str(url))
