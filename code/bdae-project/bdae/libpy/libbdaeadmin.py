# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: libbdaeadmin
"""

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.api import GatewayAdminApi


class PyBDAEAdmin(PyBDAEManager):
    """
    Abstract class to override in order to implement a administrator gateway to the framework
    """

    def __init__(self, gateway_uri):
        PyBDAEManager.__init__(self, None)
        self.__api = GatewayAdminApi(gateway_uri)
