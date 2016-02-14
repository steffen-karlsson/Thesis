# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: configparser
"""

from ConfigParser import SafeConfigParser
from logging import basicConfig, INFO, debug


class ParameterRequiredException(Exception):
    """
    Simple exception class to be thrown if a required parameter isn't present.
    """

    def __init__(self, message):
        super(ParameterRequiredException, self).__init__(message)


def parse_project_cfg(path):
    """
    Function to parse .cfg file defined by the parameter ``path``.

    Example:

    .. code-block:: cfg

        ##
        # Big Data Object-Based Storage System Configuration
        #

        [general]
        project-path =
        log-file =

        ##
        # Configuration of the gateway servers
        # Supported parameters:
        #   * name - class name of the python gateway implementation
        #   * file - file including the class implementation, relative to general path
        #   * addresses - list of ip addresses and port pairs (= number of gateways started)
        #   * ns-registry-name - identifier at the nameserver
        #

        [gateway]
        name =
        file =
        addresses =
        ns-registry-name =

    :param path: full path to the .cfg project configuration file
    :type path: str
    :returns :class:`.Configuration`
    """

    config = SafeConfigParser(allow_no_value=True)
    config.read(path)

    global_config = Configuration()
    if not config.has_option("general", "project-path"):
        raise ParameterRequiredException("project-path in general is required")

    global_config.project_path = config.get("general", "project-path")

    if config.has_option("general", "log-file"):
        basicConfig(filename=config.get("general", "log-file"), level=INFO)
        global_config.use_logging = True

    if config.has_section("gateway"):
        gateway = Configuration.GatewayConfiguration()
        if not config.has_option("gateway", "name") \
                or not config.has_option("gateway", "file") \
                or not config.has_option("gateway", "addresses"):
            raise ParameterRequiredException("name, file and ips in gateway is required")

        gateway.name = config.get("gateway", "name")
        gateway.file = config.get("gateway", "file")
        gateway.addresses = config.get("gateway", "addresses").split(",")

        if config.has_option("gateway", "ns-registry-name"):
            gateway.ns_registry_name = config.get("gateway", "ns-registry-name")

        global_config.gateway = gateway
    else:
        if global_config.use_logging:
            debug("Starting system without gateway")

    return global_config


class Configuration:
    """
    Container class for configuration parameters defined in the .cfg project configuration file
    """

    class GatewayConfiguration:
        def __init__(self):
            self.name = None
            self.file = None
            self.addresses = []
            self.ns_registry_name = "bdos.gateway"

        def get_port(self, i):
            return int(self.addresses[i].split(":")[1])

    def __init__(self):
        self.project_path = None
        self.use_logging = False
        self.gateway = None


if __name__ == "__main__":
    # Only used for test the parsing of .cfg file
    parse_project_cfg("../../bdos.cfg")
