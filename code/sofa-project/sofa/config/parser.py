# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: configparser
"""

from ConfigParser import SafeConfigParser
from logging import basicConfig, INFO, debug
from os.path import exists
from os import makedirs

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
        # SOFA Configuration
        #

        [general]
        project-path =
        log-file =
        keyspace-size =
        mount-point =
        instance-name =

        # Defined in seconds
        heartbeat_scheduler_delay =

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

        [storage]
        addresses =

        [monitor]
        addresses =


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

    if not config.has_option("general", "instance-name"):
        raise ParameterRequiredException("instance-name in general is required")
    instance_name = global_config.instance_name = config.get("general", "instance-name")

    if config.has_option("general", "mount-point"):
        global_config.mount_point = config.get("general", "mount-point")

    if not exists(global_config.mount_point):
        makedirs(global_config.mount_point)

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

            if idx == 0:
                global_config.node = "sofa:%s:%s:%d" % (instance_name, node, index)
                global_config.node_idx = index
                global_config.port = int(addresses[index].split(":")[1])

                if len(addresses) > 1:
                    others = ["sofa:%s:%s:%d" % (instance_name, node, i) for i in range(num_nodes)]
                    others.__delitem__(index)
                    global_config.others[node] = others
            else:
                global_config.others[node] = ["sofa:%s:%s:%d" % (instance_name, node, i) for i in range(num_nodes)]
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
        self.instance_name = None
        self.use_logging = False
        self.block_size = DEFAULT_BLOCK_SIZE
        self.node = None
        self.node_idx = None
        self.others = {}
        self.keyspace_size = DEFAULT_KEYSPACE_SIZE
        self.port = DEFAULT_PORT
        self.heartbeat_scheduler_delay = DEFAULT_HEARTBEAT_DELAY
        self.mount_point = "/mnt/sofa/"

    def get_mount_point(self):
        return self.mount_point if self.mount_point.endswith('/') else "%s/" % self.mount_point

if __name__ == "__main__":
    # Only used for test the parsing of .cfg file
    parse_project_cfg("../sofa.cfg", 0, ["gateway", "storage"])
