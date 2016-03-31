# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: libbdaeadmin
"""

from abc import ABCMeta

from bdae.libpy.libbdaemanager import AbsPyManagerGateway
from bdae.api import GatewayAdminApi


class AbsPyAdminGateway(AbsPyManagerGateway):
    """
    Abstract class to override in order to implement a administrator gateway to the framework
    """

    __metaclass__ = ABCMeta

    def __init__(self, gateway_uri):
        super(AbsPyAdminGateway, self).__init__(None)
        self.__api = GatewayAdminApi(gateway_uri)
