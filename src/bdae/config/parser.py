# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: configparser
"""

from ConfigParser import SafeConfigParser
from logging import basicConfig, INFO, debug

DEFAULT_BLOCK_SIZE = 64
DEFAULT_PORT = 9090
DEFAULT_HEARTBEAT_DELAY = 5
DEFAULT_KEYSPACE_SIZE = pow(2, 64)


class ParameterRequiredException(Exception):
    """
    Simple exception class to be thrown if a required parameter isn't present.
    """

    def __init__(self, message):
        super(ParameterRequiredException, self).__init__(message)


def parse_project_cfg(path, index, node_types):
    """
    Function to parse .cfg file defined by the parameter ``path``.

    Example:

    .. code-block:: cfg

        ##
        # Big Data Analysis Engine Configuration
        #

        [general]
        project-path =
        log-file =

        # Defined in megabytes
        block-size =

        ##
        # Configuration of the nodes
        # Available section types:
        #   * gateway, storage, monitor
        #
        # Supported parameters:
        #   * addresses - list of ip addresses and port pairs (= number of gateways started)
        #   * ns-registry-name - identifier at the nameserver
        #

        [gateway]
        addresses =
        ns-registry-name =

        [storage]
        addresses =
        ns-registry-name =

        [monitor]
        addresses =
        ns-registry-name =


    :param path: full path to the .cfg project configuration file
    :param node_type: The node type to parse: gateway, storage, monitor
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

    if config.has_option("general", "block-size"):
        global_config.block_size = config.getfloat("general", "block-size")

    if config.has_option("general", "heartbeat-scheduler-delay"):
        global_config.heartbeat_scheduler_delay = config.getint("general", "heartbeat-scheduler-delay")

    if config.has_option("general", "keyspace-size"):
        global_config.keyspace_size = eval(config.get("general", "keyspace-size"))

    for idx, node in enumerate(node_types):
        if config.has_section(node):
            if not config.has_option(node, "addresses"):
                raise ParameterRequiredException("addresses in %s is required" % node)

            addresses = config.get(node, "addresses").split(",")
            num_nodes = len(addresses)

            ns_registry_name = node
            if config.has_option(node, "ns-registry-name"):
                ns_registry_name = config.get(node, "ns-registry-name")

            if idx == 0:
                global_config.node = "%s-%d" % (ns_registry_name, index)
                global_config.node_idx = index
                global_config.port = int(addresses[index].split(":")[1])

                if len(addresses) > 1:
                    others = ["%s-%d" % (ns_registry_name, i) for i in range(num_nodes)]
                    others.__delitem__(index)
                    global_config.others[node] = others
            else:
                global_config.others[node] = ["%s-%d" % (ns_registry_name, i)
                                              for i in range(num_nodes)]
        else:
            if global_config.use_logging:
                debug("Starting system without %s" % node)

    return global_config


class Configuration:
    """
    Container class for configuration parameters defined in the .cfg project configuration file
    """

    def __init__(self):
        self.project_path = None
        self.use_logging = False
        self.block_size = DEFAULT_BLOCK_SIZE
        self.node = None
        self.node_idx = None
        self.others = {}
        self.keyspace_size = DEFAULT_KEYSPACE_SIZE
        self.port = DEFAULT_PORT
        self.heartbeat_scheduler_delay = DEFAULT_HEARTBEAT_DELAY


if __name__ == "__main__":
    # Only used for test the parsing of .cfg file
    parse_project_cfg("../../bdae.cfg", 0, ["gateway", "storage"])
